"""Audit a supplied DOCX against extraction and disposable import persistence.

Run: python scripts/audit_docx.py path/to/document.docx
The document and extracted content are not copied into the repository.
"""

import hashlib
import json
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.docx_extract import extract_docx
from backend.imports import ImportService
from backend.local_model import LocalModel
from backend.storage import Store


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def text_of(element):
    pieces = []
    for node in element.iter():
        if node.tag == W + "t" and node.text:
            pieces.append(node.text)
        elif node.tag == W + "tab":
            pieces.append("\t")
        elif node.tag in {W + "br", W + "cr"}:
            pieces.append("\n")
    return "".join(pieces).strip()


def source_blocks(archive):
    root = ET.fromstring(archive.read("word/document.xml"))
    body = root.find(W + "body")
    blocks = []
    for item in body:
        if item.tag == W + "p":
            content = text_of(item)
            if content:
                blocks.append(("paragraph", content))
        elif item.tag == W + "tbl":
            rows = []
            for row in item.findall(W + "tr"):
                rows.append(["\n".join(filter(None, (text_of(p) for p in cell.findall(".//" + W + "p"))))
                             for cell in row.findall(W + "tc")])
            blocks.append(("table", json.dumps(rows, ensure_ascii=False)))
    return blocks, sum(1 for _ in root.iter(W + "sectPr"))


def main(path):
    data = path.read_bytes()
    extracted = extract_docx(data, path.name)
    with zipfile.ZipFile(path) as archive:
        expected, sections = source_blocks(archive)
        extra_parts = [name for name in archive.namelist() if name.startswith("word/") and
                       any(part in name for part in ("header", "footer", "footnotes", "endnotes", "media/"))]
    actual = [(item["kind"], item["content"]) for item in extracted.fragments if item["kind"] != "image"]
    body_match = expected == actual
    print("sha256", hashlib.sha256(data).hexdigest())
    print("sections", sections, "body_blocks", len(expected), "images", len(extracted.images),
          "extra_parts", len(extra_parts))
    print("body_order_and_content_match", body_match)
    print("extraction_warnings", extracted.warnings)
    with tempfile.TemporaryDirectory() as temp:
        store = Store(Path(temp))
        service = ImportService(store, LocalModel(name=""))
        try:
            document, created = service.submit(path.name, data)
            for _ in range(200):
                current = store.get_document(document["id"])
                if current["state"] in {"completed", "awaiting_model", "failed"}:
                    break
                time.sleep(0.02)
            persisted = store.list_fragments(document["id"])
            duplicate, duplicate_created = service.submit(path.name, data)
            original_match = store.original_path(document["id"]).read_bytes() == data
            persisted_match = [(item["kind"], item["content"]) for item in persisted] == [
                (item["kind"], item["content"]) for item in extracted.fragments]
            duplicate_reused = duplicate["id"] == document["id"] and not duplicate_created
            print("import_state", current["state"], "created", created, "fragments", len(persisted))
            print("original_match", original_match, "persisted_match", persisted_match,
                  "duplicate_reused", duplicate_reused)
            print("import_warnings", current["warnings"])
            if not all((body_match, created, current["state"] == "awaiting_model",
                        original_match, persisted_match, duplicate_reused)):
                raise SystemExit(1)
        finally:
            service.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/audit_docx.py path/to/document.docx")
    main(Path(sys.argv[1]))
