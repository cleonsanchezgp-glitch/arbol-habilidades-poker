"""Bounded, source-ordered extraction from DOCX packages using Python stdlib."""

from __future__ import annotations

import io
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any

from .storage import StoreError


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"
V = "{urn:schemas-microsoft-com:vml}"
PKG_PARTS = {"[Content_Types].xml", "word/document.xml"}
MAX_PARTS = 2000
MAX_TOTAL_UNCOMPRESSED = 100_000_000
MAX_XML = 15_000_000
MAX_IMAGE = 15_000_000
PREVIEW_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


@dataclass
class Extraction:
    fragments: list[dict[str, Any]] = field(default_factory=list)
    images: dict[str, bytes] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _zip(data: bytes, filename: str) -> zipfile.ZipFile:
    if not filename.lower().endswith(".docx"):
        raise StoreError("Only DOCX files are supported")
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise StoreError("File is not a readable DOCX ZIP package")
    archive = zipfile.ZipFile(io.BytesIO(data))
    entries = archive.infolist()
    names = {entry.filename for entry in entries}
    if not PKG_PARTS.issubset(names):
        archive.close()
        raise StoreError("DOCX is missing required package parts")
    if len(entries) > MAX_PARTS or sum(entry.file_size for entry in entries) > MAX_TOTAL_UNCOMPRESSED:
        archive.close()
        raise StoreError("DOCX exceeds extraction limits")
    if any(entry.flag_bits & 1 for entry in entries):
        archive.close()
        raise StoreError("Encrypted DOCX packages are not supported")
    if any(entry.file_size > MAX_TOTAL_UNCOMPRESSED for entry in entries):
        archive.close()
        raise StoreError("DOCX contains an oversized part")
    if archive.getinfo("word/document.xml").file_size > MAX_XML:
        archive.close()
        raise StoreError("DOCX document XML exceeds extraction limit")
    return archive


def validate_docx(data: bytes, filename: str) -> None:
    with _zip(data, filename):
        pass


def _xml(archive: zipfile.ZipFile, path: str) -> ET.Element:
    try:
        return ET.fromstring(archive.read(path))
    except (ET.ParseError, KeyError, ValueError) as exc:
        raise StoreError(f"Invalid DOCX XML part: {path}") from exc


def _paragraph_text(element: ET.Element) -> str:
    pieces: list[str] = []
    for node in element.iter():
        if node.tag == W + "t" and node.text:
            pieces.append(node.text)
        elif node.tag == W + "tab":
            pieces.append("\t")
        elif node.tag in {W + "br", W + "cr"}:
            pieces.append("\n")
    return "".join(pieces).strip()


def _relationships(archive: zipfile.ZipFile) -> dict[str, str]:
    path = "word/_rels/document.xml.rels"
    if path not in archive.namelist():
        return {}
    if archive.getinfo(path).file_size > MAX_XML:
        raise StoreError("DOCX relationships XML exceeds extraction limit")
    result = {}
    for relation in _xml(archive, path):
        if relation.tag != PR + "Relationship" or relation.get("TargetMode") == "External":
            continue
        rel_id, target = relation.get("Id"), relation.get("Target")
        if not rel_id or not target:
            continue
        normalized = posixpath.normpath(target.lstrip("/") if target.startswith("/") else posixpath.join("word", target))
        if normalized.startswith("word/media/") and normalized in archive.namelist():
            result[rel_id] = normalized
    return result


def _image_references(element: ET.Element) -> list[str]:
    references = []
    for node in element.iter():
        if node.tag == A + "blip" and node.get(R + "embed"):
            references.append(node.get(R + "embed"))
        elif node.tag == V + "imagedata" and node.get(R + "id"):
            references.append(node.get(R + "id"))
    return references


def _append_images(result: Extraction, archive: zipfile.ZipFile, relationships: dict[str, str], element: ET.Element, locator: str) -> None:
    for image_number, rel_id in enumerate(_image_references(element), start=1):
        media_path = relationships.get(rel_id)
        image_locator = f"{locator}/image[{image_number}]"
        if not media_path:
            result.warnings.append(f"Image reference {image_locator} could not be resolved")
            result.fragments.append({"kind": "image", "locator": image_locator, "content": "Image reference unavailable", "image_name": None})
            continue
        extension = PurePosixPath(media_path).suffix.lower()
        if extension not in PREVIEW_EXTENSIONS:
            result.warnings.append(f"Image {image_locator} uses an unsupported preview format ({extension or 'unknown'})")
            result.fragments.append({"kind": "image", "locator": image_locator, "content": f"Image in original document: {media_path}", "image_name": None})
            continue
        if archive.getinfo(media_path).file_size > MAX_IMAGE:
            result.warnings.append(f"Image {image_locator} exceeds extraction limit")
            result.fragments.append({"kind": "image", "locator": image_locator, "content": "Image retained only in original document", "image_name": None})
            continue
        result.images[media_path] = archive.read(media_path)
        result.fragments.append({"kind": "image", "locator": image_locator, "content": f"Image from {media_path}; text inside image is not transcribed", "image_name": None, "media_path": media_path})


def extract_docx(data: bytes, filename: str) -> Extraction:
    result = Extraction()
    with _zip(data, filename) as archive:
        document = _xml(archive, "word/document.xml")
        body = document.find(W + "body")
        if body is None:
            raise StoreError("DOCX has no document body")
        relationships = _relationships(archive)
        paragraphs = tables = 0
        for block in body:
            if block.tag == W + "p":
                paragraphs += 1
                locator = f"body/paragraph[{paragraphs}]"
                content = _paragraph_text(block)
                if content:
                    result.fragments.append({"kind": "paragraph", "locator": locator, "content": content, "image_name": None})
                _append_images(result, archive, relationships, block, locator)
            elif block.tag == W + "tbl":
                tables += 1
                locator = f"body/table[{tables}]"
                table_rows = []
                for row in block.findall(W + "tr"):
                    table_rows.append(["\n".join(filter(None, (_paragraph_text(p) for p in cell.findall(".//" + W + "p")))) for cell in row.findall(W + "tc")])
                result.fragments.append({"kind": "table", "locator": locator, "content": json.dumps(table_rows, ensure_ascii=False), "image_name": None})
                _append_images(result, archive, relationships, block, locator)
                if any(node.tag in {W + "gridSpan", W + "vMerge"} for node in block.iter()):
                    result.warnings.append(f"Merged cells in {locator} may not preserve their visual layout")
                if any(node.tag == W + "tbl" for node in list(block.iter())[1:]):
                    result.warnings.append(f"Nested tables in {locator} may be flattened")
            elif block.tag not in {W + "sectPr"}:
                result.warnings.append(f"Unsupported document block {block.tag.rsplit('}', 1)[-1]} was not interpreted")
        extra_parts = [name for name in archive.namelist() if re.fullmatch(r"word/(header|footer)\d+\.xml|word/(footnotes|endnotes)\.xml", name)]
        if extra_parts:
            result.warnings.append("Headers, footers, footnotes, or endnotes are retained in the original but not indexed")
        if result.images:
            result.warnings.append("Text contained only inside images is not transcribed")
            result.warnings.append("Inline image positions relative to paragraph text may be approximate")
        if not result.fragments:
            result.warnings.append("No readable main-body content was found")
    return result
