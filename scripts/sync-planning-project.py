"""Reconcile existing classic planning Issues into the dedicated GitHub Project.

Uses GitHub REST API version 2026-03-10. Run without --apply for a read-only plan.
"""

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNER = "cleonsanchezgp-glitch"
REPO = "arbol-habilidades-poker"
PROJECT = 6
API = "https://api.github.com"
ISSUES = f"/repos/{OWNER}/{REPO}/issues"
PROJECT_PATH = f"/users/{OWNER}/projectsV2/{PROJECT}"
TEXT_FIELDS = ("Canonical ID", "Domain", "Horizon", "Priority", "Urgency", "Specification")


def request(method, path, token, payload=None):
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        API + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "Content-Type": "application/json",
            "User-Agent": "poker-roots-project-reconciliation",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        message = error.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"{method} {path}: HTTP {error.code}: {message}") from None


def source_data():
    result = {}
    for path in sorted((ROOT / "_context" / "_planning").glob("*.md")):
        match = re.match(r"(INI|PRJ|WP)-(\d{3})", path.name)
        if not match:
            continue
        identity = match.group()
        content = path.read_text(encoding="utf-8")
        status_match = re.search(r"^\| Status \| ([^|]+) \|$", content, re.M)
        status = status_match.group(1).strip() if status_match else ""
        if identity.startswith(("INI-", "PRJ-")):
            overall = re.search(r"^\| Overall status \| ([^|]+) \|$", content, re.M)
            if overall:
                status = overall.group(1).strip()
        requirements = []
        if identity.startswith("WP-"):
            realized = content.split("## 3. Realizes", 1)[1].split("## 4. Tasks", 1)[0]
            requirements = sorted(set(re.findall(r"\b(?:FR|NFR)-\d{3}\b", realized)))
        result[identity] = {"status": status, "requirements": requirements}
        if identity.startswith("WP-"):
            tasks = content.split("## 4. Tasks", 1)[1].split("## 5. Status", 1)[0]
            for task in re.finditer(r"^\| (TSK-\d{3}) \| [^|]+ \| ([^|]+) \| [^|]+ \|$", tasks, re.M):
                result[task.group(1)] = {
                    "status": task.group(2).strip(),
                    "requirements": requirements,
                }
    return result


def project_status(source_status):
    value = source_status.lower()
    if value.startswith("planned") or value.startswith("draft"):
        return "Todo"
    if value == "implemented" or value.startswith("implemented; automated checks"):
        return "Done"
    return "In Progress"


def field_value(item, name):
    for field in item.get("fields", []):
        if field.get("name") == name:
            value = field.get("value")
            if isinstance(value, dict):
                if isinstance(value.get("name"), dict):
                    return value["name"].get("raw")
                return value.get("raw")
            return value
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("qualitas_token")
    if not token:
        raise SystemExit("qualitas_token is not visible to this process")
    sources = source_data()
    issues = request("GET", f"{ISSUES}?state=all&per_page=100", token)
    by_id = {}
    for issue in issues:
        match = re.match(r"^\[((?:INI|PRJ|WP|TSK)-\d{3})\]", issue["title"])
        if match:
            identity = match.group(1)
            if identity in by_id:
                raise RuntimeError(f"Duplicate issue ID: {identity}")
            by_id[identity] = issue
    if set(by_id) != set(sources):
        raise RuntimeError(f"Issue/source mismatch: missing={sorted(set(sources)-set(by_id))}, extra={sorted(set(by_id)-set(sources))}")
    project = request("GET", PROJECT_PATH, token)
    if project["number"] != PROJECT or project["owner"]["login"] != OWNER:
        raise RuntimeError("Project identity changed")
    fields = {f["name"]: f for f in request("GET", f"{PROJECT_PATH}/fields?per_page=100", token)}
    items = request("GET", f"{PROJECT_PATH}/items?per_page=100", token)
    print(f"project={PROJECT} issues={len(by_id)} items={len(items)} missing_fields={sorted(set(TEXT_FIELDS + ('PRJ',)) - set(fields))}", flush=True)
    if not args.apply:
        return

    for name in TEXT_FIELDS:
        if name not in fields:
            request("POST", f"{PROJECT_PATH}/fields", token, {"name": name, "data_type": "text"})
            fields = {f["name"]: f for f in request("GET", f"{PROJECT_PATH}/fields?per_page=100", token)}
            print(f"created field {name}", flush=True)
        if fields[name]["data_type"] != "text":
            raise RuntimeError(f"Field {name} has unexpected type")
    if "PRJ" not in fields:
        request("POST", f"{PROJECT_PATH}/fields", token, {
            "name": "PRJ", "data_type": "single_select",
            "single_select_options": [{"name": "PRJ-001", "color": "BLUE", "description": "Local first functional version"}],
        })
        fields = {f["name"]: f for f in request("GET", f"{PROJECT_PATH}/fields?per_page=100", token)}
        print("created field PRJ", flush=True)
    if fields["PRJ"]["data_type"] != "single_select":
        raise RuntimeError("PRJ has unexpected type")
    options = {o["name"]["raw"]: o["id"] for o in fields["PRJ"]["options"]}
    if "PRJ-001" not in options:
        raise RuntimeError("PRJ-001 lineage option is absent")
    status_options = {o["name"]["raw"]: o["id"] for o in fields["Status"]["options"]}
    if not {"Todo", "In Progress", "Done"}.issubset(status_options):
        raise RuntimeError("Unexpected Status options")
    selected = ",".join(str(fields[name]["id"]) for name in (*TEXT_FIELDS, "PRJ", "Status"))
    item_path = f"{PROJECT_PATH}/items?per_page=100&fields={selected}"
    items = request("GET", item_path, token)

    for identity in sorted(sources, key=lambda s: ({"INI": 0, "PRJ": 1, "WP": 2, "TSK": 3}[s.split("-")[0]], s)):
        issue = by_id[identity]
        current = next((item for item in items if item.get("content", {}).get("id") == issue["id"]), None)
        if current is None:
            request("POST", f"{PROJECT_PATH}/items", token, {"type": "Issue", "id": issue["id"]})
            for _ in range(5):
                items = request("GET", item_path, token)
                current = next((item for item in items if item.get("content", {}).get("id") == issue["id"]), None)
                if current is not None:
                    break
                time.sleep(1)
            if current is None:
                raise RuntimeError(f"Could not reconcile newly added {identity}")
            print(f"added {identity} item={current['id']}", flush=True)
        desired = {
            "Canonical ID": identity,
            "Horizon": "H-001",
            "Status": status_options[project_status(sources[identity]["status"])],
        }
        if identity.startswith(("PRJ-", "WP-", "TSK-")):
            desired["PRJ"] = options["PRJ-001"]
        if sources[identity]["requirements"]:
            desired["Specification"] = ", ".join(sources[identity]["requirements"])
        expected_names = {"Status": project_status(sources[identity]["status"]), "PRJ": "PRJ-001"}
        updates = [{"id": fields[name]["id"], "value": value} for name, value in desired.items()
                   if field_value(current, name) != expected_names.get(name, value)]
        if updates:
            request("PATCH", f"{PROJECT_PATH}/items/{current['id']}", token, {"fields": updates})
            print(f"updated {identity} fields={','.join(desired)}", flush=True)
    print("reconciled", flush=True)


if __name__ == "__main__":
    main()
