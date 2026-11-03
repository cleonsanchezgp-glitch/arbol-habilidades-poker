"""Idempotently copy the classic Markdown planning hierarchy to GitHub Issues.

This intentionally leaves GitHub Projects and the management authority unchanged.
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
BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"
SOURCE = f"https://github.com/{OWNER}/{REPO}/blob/master"


def section(text, start, end=None):
    value = text.split(start, 1)[1]
    return value.split(end, 1)[0] if end else value


def field(text, name):
    match = re.search(rf"^\| {re.escape(name)} \| ([^|]+) \|$", text, re.M)
    return match.group(1).strip() if match else ""


def request(method, path, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "poker-roots-planning-migration",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"{method} {path}: HTTP {error.code}: {details}") from None


def source_url(path):
    return f"{SOURCE}/{path.as_posix()}"


def load_plan():
    paths = sorted((ROOT / "_context" / "_planning").glob("*.md"))
    specs = []
    parents = {}
    for path in paths:
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        identity = re.search(r"^(INI|PRJ|WP)-\d{3}", path.name).group()
        title = field(text, "Document")
        status = field(text, "Status")
        overview = section(text, "## 1. Overview", "## 2.").strip()
        parent = {"INI-001": None, "PRJ-001": "INI-001"}.get(identity)
        if identity.startswith("WP-"):
            parent = "PRJ-001"
        requirements = sorted(set(re.findall(r"\b(?:FR|NFR)-\d{3}\b", section(text, "## 3. Realizes", "## 4.")))) if identity.startswith("WP-") else []
        body = (
            f"Migrated from [the local planning source]({source_url(relative)}).\n\n"
            f"Canonical ID: `{identity}`  \n"
            f"Source status: {status}  \n"
            f"Parent: {parent or 'none'}  \n"
            f"Milestone: MS-001 (undated)  \n"
            f"Requirements: {', '.join(requirements) or 'see source'}\n\n"
            f"## Scope\n\n{overview}\n"
        )
        specs.append({"id": identity, "title": f"[{identity}] {title}", "body": body, "parent": parent})
        if identity.startswith("WP-"):
            parents[identity] = (text, relative, requirements)
    for parent_id, (text, relative, requirements) in parents.items():
        for match in re.finditer(r"^\| (TSK-\d{3}) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", section(text, "## 4. Tasks", "## 5."), re.M):
            identity, title, status, owner = (part.strip() for part in match.groups())
            body = (
                f"Migrated from [the local work package]({source_url(relative)}).\n\n"
                f"Canonical ID: `{identity}`  \n"
                f"Source status: {status}  \n"
                f"Parent: {parent_id}  \n"
                f"Owner in source: {owner}  \n"
                f"Requirements inherited from {parent_id}: {', '.join(requirements)}\n"
            )
            specs.append({"id": identity, "title": f"[{identity}] {title}", "body": body, "parent": parent_id})
    order = {"INI": 0, "PRJ": 1, "WP": 2, "TSK": 3}
    return sorted(specs, key=lambda item: (order[item["id"].split("-")[0]], item["id"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    specs = load_plan()
    print(json.dumps({"count": len(specs), "ids": [item["id"] for item in specs]}, ensure_ascii=False))
    if not args.apply:
        return
    token = os.environ.get("qualitas_token") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("No GitHub credential is visible to this process")
    issues = request("GET", "/issues?state=all&per_page=100", token)
    by_id = {}
    for issue in issues:
        match = re.match(r"^\[((?:INI|PRJ|WP|TSK)-\d{3})\]", issue["title"])
        if match:
            if match.group(1) in by_id:
                raise RuntimeError(f"Duplicate GitHub ID: {match.group(1)}")
            by_id[match.group(1)] = issue
    milestones = request("GET", "/milestones?state=all&per_page=100", token)
    milestone = next((item for item in milestones if item["title"].startswith("MS-001")), None)
    if milestone is None:
        milestone = request("POST", "/milestones", token, {
            "title": "MS-001 · First functional version",
            "description": "H-001: undated first functional version. Source: _context/_time/ROADMAP.md. No target date was committed by the owner.",
        })
        print(f"created milestone MS-001 #{milestone['number']}", flush=True)
    for spec in specs:
        if spec["id"] not in by_id:
            issue = request("POST", "/issues", token, {
                "title": spec["title"], "body": spec["body"], "milestone": milestone["number"],
            })
            by_id[spec["id"]] = issue
            print(f"created {spec['id']} #{issue['number']}", flush=True)
            time.sleep(1)
        else:
            print(f"existing {spec['id']} #{by_id[spec['id']]['number']}", flush=True)
    for spec in specs:
        if not spec["parent"]:
            continue
        parent = by_id[spec["parent"]]
        child = by_id[spec["id"]]
        current = request("GET", f"/issues/{parent['number']}/sub_issues?per_page=100", token)
        if any(item["id"] == child["id"] for item in current):
            print(f"linked {spec['parent']} -> {spec['id']} (existing)", flush=True)
            continue
        request("POST", f"/issues/{parent['number']}/sub_issues", token, {"sub_issue_id": child["id"]})
        print(f"linked {spec['parent']} -> {spec['id']}", flush=True)
        time.sleep(1)
    print("issue hierarchy reconciled", flush=True)


if __name__ == "__main__":
    main()
