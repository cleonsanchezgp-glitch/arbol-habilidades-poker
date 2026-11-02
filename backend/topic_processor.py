"""Validate locally generated topic proposals against extracted source IDs."""

from __future__ import annotations

import json
import re
from typing import Any

from .local_model import LocalModel
from .storage import Store, StoreError


SYSTEM = """Eres un organizador de teoría de póker Texas Hold'em. Usa exclusivamente los fragmentos suministrados.
No eres un solver. No inventes frecuencias, rangos, tamaños de apuesta ni conclusiones.
Conserva posiciones, stacks, acciones previas, textura del board y toda condición que limite una estrategia.
Si falta un dato, déjalo como null y anótalo en unknowns. Si hay contradicción, repórtala con fuentes.
Separa cada tema real. Cada párrafo explicativo y condición debe citar los identificadores F de los fragmentos que lo respaldan.
Marca los ejemplos inventados solo como didácticos con origin=generated; no los presentes como fuente.
Responde solo un objeto JSON con la estructura pedida. No agregues contenido que no pueda revisarse contra los fragmentos."""

FACET_NAMES = ("street", "hero_position", "villain_position", "pot_type", "in_position", "board_texture", "concept")
NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:%|bb\b|x\s*(?:pot|bote)\b)", re.IGNORECASE)
MAX_CHUNK_CHARS = 12_000


def _text(value: Any, field: str, required: bool = False) -> str:
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > 20_000:
        raise StoreError(f"Invalid model field: {field}")
    return value.strip()


def _list(value: Any, field: str, maximum: int = 20) -> list:
    if not isinstance(value, list) or len(value) > maximum:
        raise StoreError(f"Invalid model list: {field}")
    return value


def _refs(value: Any, labels: dict[str, dict], field: str, required: bool = True) -> list[str]:
    raw = _list(value, field, 50)
    if (required and not raw) or any(not isinstance(label, str) or label not in labels for label in raw):
        raise StoreError(f"Model cited unknown or missing source in {field}")
    return sorted({labels[label]["id"] for label in raw})


def _check_numbers(text: str, referenced_ids: list[str], fragments_by_id: dict[str, dict]) -> None:
    source = " ".join(fragments_by_id[fragment_id]["content"] for fragment_id in referenced_ids).casefold()
    for match in NUMBER_PATTERN.finditer(text):
        if match.group().casefold() not in source:
            raise StoreError(f"Model proposed an unsupported numeric strategy detail: {match.group()}")


def _windows(fragments: list[dict]) -> list[tuple[str, dict[str, dict]]]:
    segments = []
    for fragment in fragments:
        if fragment["kind"] == "image":
            continue  # No vision model: an image cannot support a strategic claim.
        content = fragment["content"].strip()
        for start in range(0, len(content), 4_000):
            part = content[start:start + 4_000]
            if part:
                segments.append((fragment, part))
    windows = []
    current: list[tuple[dict, str]] = []
    size = 0
    for fragment, part in segments:
        if current and size + len(part) > MAX_CHUNK_CHARS:
            windows.append(current)
            current, size = [], 0
        current.append((fragment, part))
        size += len(part)
    if current:
        windows.append(current)
    result = []
    for window in windows:
        labels = {f"F{index}": fragment for index, (fragment, _) in enumerate(window, start=1)}
        prompt_fragments = [f"F{index} [{fragment['kind']}; {fragment['locator']}]: {part}" for index, (fragment, part) in enumerate(window, start=1)]
        prompt = "Propón uno o varios temas distintos de estos fragmentos:\n" + "\n\n".join(prompt_fragments)
        prompt += """

Devuelve JSON: {"topics":[{"title":"...","summary":"...","explanation_blocks":[{"text":"...","source_refs":["F1"]}],"conditions":[{"text":"...","source_refs":["F1"]}],"examples":[{"text":"...","origin":"generated","source_refs":[]}],"visuals":[],"difficulty":"basic|intermediate|advanced","tags":[],"facets":{"street":null,"hero_position":null,"villain_position":null,"pot_type":null,"in_position":null,"board_texture":null,"concept":null},"unknowns":[],"contradictions":[],"prerequisite_proposals":[],"source_refs":["F1"]}]}.
Cada explanation_block y condición requiere source_refs no vacío. Los ejemplos generados tienen origin=generated y source_refs vacío; si un ejemplo procede de la fuente, usa origin=source y cítala. Las propuestas de prerrequisito son texto para revisar, no enlaces automáticos. Si no hay teoría suficiente, devuelve topics=[]."""
        result.append((prompt, labels))
    return result


def _validate_topic(raw: Any, labels: dict[str, dict]) -> dict:
    if not isinstance(raw, dict):
        raise StoreError("Model topic must be an object")
    by_id = {fragment["id"]: fragment for fragment in labels.values()}
    title = _text(raw.get("title"), "title", True)
    summary = _text(raw.get("summary"), "summary", True)
    difficulty = raw.get("difficulty")
    if difficulty not in {"basic", "intermediate", "advanced"}:
        raise StoreError("Model proposed an invalid difficulty")
    source_ids = _refs(raw.get("source_refs"), labels, "source_refs")
    blocks = []
    claims = []
    for block in _list(raw.get("explanation_blocks"), "explanation_blocks", 30):
        if not isinstance(block, dict):
            raise StoreError("Invalid explanation block")
        text = _text(block.get("text"), "explanation text", True)
        refs = _refs(block.get("source_refs"), labels, "explanation source_refs")
        _check_numbers(text, refs, by_id)
        blocks.append(text)
        claims.append({"kind": "explanation", "text": text, "source_fragment_ids": refs})
        source_ids.extend(refs)
    if not blocks:
        raise StoreError("Every topic needs sourced explanation blocks")
    conditions = []
    for item in _list(raw.get("conditions", []), "conditions"):
        if not isinstance(item, dict):
            raise StoreError("Invalid condition")
        text = _text(item.get("text"), "condition text", True)
        refs = _refs(item.get("source_refs"), labels, "condition source_refs")
        _check_numbers(text, refs, by_id)
        conditions.append(text)
        claims.append({"kind": "condition", "text": text, "source_fragment_ids": refs})
        source_ids.extend(refs)
    examples = []
    for item in _list(raw.get("examples", []), "examples"):
        if not isinstance(item, dict):
            raise StoreError("Invalid example")
        origin = item.get("origin")
        if origin not in {"generated", "source"}:
            raise StoreError("Example origin must be generated or source")
        refs = _refs(item.get("source_refs", []), labels, "example source_refs", origin == "source")
        if origin == "generated" and refs:
            raise StoreError("Generated examples cannot masquerade as source examples")
        text = _text(item.get("text"), "example text", True)
        _check_numbers(text, refs or source_ids, by_id)
        examples.append({"text": text, "origin": origin, "source_fragment_ids": refs})
        source_ids.extend(refs)
    visuals = []
    for item in _list(raw.get("visuals", []), "visuals"):
        if not isinstance(item, dict):
            raise StoreError("Invalid visual")
        origin = item.get("origin")
        if origin not in {"generated", "source"}:
            raise StoreError("Visual origin must be generated or source")
        refs = _refs(item.get("source_refs", []), labels, "visual source_refs", origin == "source")
        if origin == "generated" and refs:
            raise StoreError("Generated visuals cannot masquerade as source visuals")
        visuals.append({"kind": _text(item.get("kind"), "visual kind", True),
                        "description": _text(item.get("description"), "visual description", True),
                        "origin": origin, "source_fragment_ids": refs})
        source_ids.extend(refs)
    facets = raw.get("facets", {})
    if not isinstance(facets, dict) or any(not isinstance(key, str) or not key.strip() or (value is not None and not isinstance(value, str)) for key, value in facets.items()):
        raise StoreError("Invalid model facets")
    facets = {**dict.fromkeys(FACET_NAMES), **facets}
    unknowns = [_text(value, "unknown", True) for value in _list(raw.get("unknowns", []), "unknowns")]
    contradictions = []
    for item in _list(raw.get("contradictions", []), "contradictions"):
        if not isinstance(item, dict):
            raise StoreError("Invalid contradiction")
        refs = _refs(item.get("source_refs"), labels, "contradiction source_refs")
        contradictions.append({"text": _text(item.get("text"), "contradiction text", True), "source_fragment_ids": refs})
        source_ids.extend(refs)
    prerequisites = []
    for item in _list(raw.get("prerequisite_proposals", []), "prerequisite_proposals"):
        if not isinstance(item, dict):
            raise StoreError("Invalid prerequisite proposal")
        prerequisites.append({"title": _text(item.get("title"), "prerequisite title", True),
                              "reason": _text(item.get("reason"), "prerequisite reason", True)})
    tags = [_text(value, "tag", True) for value in _list(raw.get("tags", []), "tags")]
    _check_numbers(title, source_ids, by_id)
    _check_numbers(summary, source_ids, by_id)
    for value in tags:
        _check_numbers(value, source_ids, by_id)
    for value in facets.values():
        if value:
            _check_numbers(value, source_ids, by_id)
    return {"title": title, "summary": summary, "explanation": "\n\n".join(blocks),
            "conditions": "\n".join(conditions), "examples": examples, "visuals": visuals,
            "difficulty": difficulty, "tags": tags, "facets": facets, "unknowns": unknowns,
            "contradictions": contradictions, "prerequisite_proposals": prerequisites,
            "claims": claims, "source_fragment_ids": sorted(set(source_ids)), "review_status": "proposed"}


class TopicProcessor:
    def __init__(self, store: Store, model: LocalModel):
        self.store = store
        self.model = model

    def process(self, document_id: str) -> list[dict]:
        fragments = self.store.list_fragments(document_id)
        windows = _windows(fragments)
        if not windows:
            raise StoreError("Document has no readable text or tables for topic analysis")
        proposals = []
        for prompt, labels in windows:
            generated = self.model.generate_json(SYSTEM, prompt)
            raw_topics = _list(generated.get("topics"), "topics", 12)
            proposals.extend(_validate_topic(raw, labels) for raw in raw_topics)
        return self.store.create_processed_topics(document_id, proposals)
