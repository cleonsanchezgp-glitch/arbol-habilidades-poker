"""Source-bounded local query interpretation, retrieval, and answers."""

from __future__ import annotations

import json
import math
import sqlite3
from typing import Any

from .local_model import LocalModel, ModelUnavailable
from .storage import Store, StoreError
from .topic_processor import _check_numbers


class SearchFailure(StoreError):
    """The retrieval or local-model result failed after valid user input."""


INTERPRET_SYSTEM = """Interpreta la pregunta sobre teoría de póker para recuperar contenido local.
No contestes la pregunta. Extrae términos técnicos y cotidianos útiles para buscar.
Extrae facetas solo cuando el usuario las expresa; no adivines acciones ni condiciones ausentes.
Devuelve solo JSON: {"terms":["..."],"facets":{"nombre":"valor"}}."""

ANSWER_SYSTEM = """Responde la pregunta solo con los fragmentos F proporcionados.
No eres un solver. No inventes rangos, frecuencias, tamaños ni consejos sin respaldo.
Conserva posiciones, acciones anteriores, stacks, textura y demás condiciones aplicables.
Si los fragmentos no sustentan una respuesta, devuelve insufficient=true.
Devuelve solo JSON: {"answer":"...","source_refs":["F1"],"insufficient":false}.
Cada respuesta debe citar al menos un fragmento F real."""


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
    return sum(a * b for a, b in zip(left, right)) / denominator if denominator else 0.0


class SearchService:
    def __init__(self, store: Store, model: LocalModel):
        self.store = store
        self.model = model

    def _generate(self, system: str, prompt: str) -> dict[str, Any]:
        try:
            result = self.model.generate_json(system, prompt)
        except ModelUnavailable:
            raise
        except StoreError as exc:
            raise SearchFailure(f"Local model returned an unusable result: {exc}") from exc
        if not isinstance(result, dict):
            raise SearchFailure("Local model returned an invalid JSON object")
        return result

    def _interpret(self, query: str) -> tuple[list[str], dict[str, str]]:
        raw = self._generate(INTERPRET_SYSTEM, json.dumps({"query": query}, ensure_ascii=False))
        terms, facets = raw.get("terms"), raw.get("facets")
        if not isinstance(terms, list) or len(terms) > 12 or any(
            not isinstance(term, str) or not term.strip() or len(term) > 80 for term in terms
        ) or not isinstance(facets, dict) or len(facets) > 12 or any(
            not isinstance(name, str) or not name.strip() or len(name) > 60 or
            not isinstance(value, str) or not value.strip() or len(value) > 100
            for name, value in facets.items()
        ):
            raise SearchFailure("Local model returned invalid query interpretation")
        return [term.strip() for term in terms] or [query], {name.strip(): value.strip() for name, value in facets.items()}

    def _rank(self, terms: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
        lexical = self.store.lexical_matches(" ".join(terms), 50)
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for rank, entry in enumerate(lexical):
            item = {**entry, "rank_score": 0.7 / (rank + 1), "retrieval": ["lexical"]}
            merged[(entry["kind"], entry["entity_id"])] = item
        warnings = []
        name = getattr(self.model, "embedding_name", "")
        if name:
            vectors = self.store.embedding_entries(name)
            if vectors:
                try:
                    query_vector = self.model.embed(" ".join(terms))
                except ModelUnavailable:
                    warnings.append("Local embedding retrieval is unavailable; lexical results were used")
                except StoreError as exc:
                    raise SearchFailure(f"Local embedding query failed: {exc}") from exc
                else:
                    semantic = sorted(((max(0.0, _cosine(query_vector, item["vector"])), item)
                                       for item in vectors), key=lambda pair: pair[0], reverse=True)
                    for similarity, entry in semantic[:50]:
                        if similarity < 0.45:
                            continue
                        key = (entry["kind"], entry["entity_id"])
                        if key not in merged:
                            merged[key] = {key_: value for key_, value in entry.items() if key_ != "vector"}
                            merged[key].update(rank_score=0.0, retrieval=[])
                        merged[key]["rank_score"] += 0.3 * similarity
                        merged[key]["retrieval"].append("semantic")
            elif self.store.index_status(name)["pending"]:
                warnings.append("Local embeddings are pending; lexical results were used")
            elif self.store.index_status(name)["failed"]:
                warnings.append("Local embeddings failed; lexical results were used")
        return sorted(merged.values(), key=lambda item: (-item["rank_score"], item["kind"], item["entity_id"]))[:12], warnings

    def search(self, data: dict[str, Any]) -> dict[str, Any]:
        query = data.get("query")
        if set(data) != {"query"} or not isinstance(query, str) or not query.strip() or len(query) > 1000:
            raise StoreError("Search requires a nonempty query of at most 1000 characters")
        query = query.strip()
        index = self.store.index_status(getattr(self.model, "embedding_name", ""))
        if not index["entries"]:
            return {"status": "empty_index", "query": query, "message": "No imported or saved text is indexed yet",
                    "topics": [], "sources": [], "retrieval_warnings": []}

        terms, explicit_facets = self._interpret(query)
        try:
            ranked, warnings = self._rank(terms)
        except sqlite3.Error as exc:
            raise SearchFailure("Local retrieval index failed") from exc
        if not ranked:
            return {"status": "insufficient_coverage", "reason": "no_matches", "query": query,
                    "message": "No indexed material matches this question", "topics": [], "sources": [],
                    "retrieval_warnings": warnings}

        fragment_ids = list(dict.fromkeys(source_id for hit in ranked for source_id in hit["source_fragment_ids"]))
        linked_topic_ids = self.store.topic_ids_for_fragments(fragment_ids)
        topic_ids = list(dict.fromkeys([hit["entity_id"] for hit in ranked if hit["kind"] == "topic"] + linked_topic_ids))
        topics = []
        condition_claims: dict[str, list[dict[str, Any]]] = {}
        for topic_id in topic_ids[:12]:
            topic = self.store.get_topic(topic_id)
            if any(isinstance(topic["facets"].get(name), str) and
                   topic["facets"][name].casefold() != value.casefold()
                   for name, value in explicit_facets.items()):
                continue
            condition_claims[topic_id] = [claim for claim in topic["claims"] if isinstance(claim, dict)
                                          and claim.get("kind") == "condition"
                                          and isinstance(claim.get("text"), str)
                                          and isinstance(claim.get("source_fragment_ids"), list)]
            topics.append({"id": topic_id, "title": topic["title"], "conditions": topic["conditions"],
                           "facets": topic["facets"], "locations": self.store.topic_locations(topic_id)["locations"],
                           "source_fragment_ids": [item["fragment_id"] for item in topic["evidence"]]})

        values_by_facet: dict[str, set[str]] = {}
        for topic in topics:
            for name, value in topic["facets"].items():
                if isinstance(value, str) and value and name not in explicit_facets:
                    values_by_facet.setdefault(name, set()).add(value.casefold())
        ambiguous = [(name, sorted(values)) for name, values in values_by_facet.items() if len(values) > 1]
        if ambiguous:
            name, options = sorted(ambiguous)[0]
            return {"status": "clarification", "query": query, "facet": name, "options": options,
                    "question": f"¿Qué {name} se aplica: {', '.join(options)}?", "topics": topics,
                    "sources": [], "retrieval_warnings": warnings}

        allowed_ids = set(source_id for topic in topics for source_id in topic["source_fragment_ids"])
        unlinked_ids = set(fragment_ids) - set(self.store.topic_ids_for_fragments(fragment_ids, grouped=True))
        source_ids = list(dict.fromkeys(source_id for source_id in fragment_ids if source_id in allowed_ids or source_id in unlinked_ids))[:8]
        sources = self.store.fragments_by_ids(source_ids)
        if not sources:
            return {"status": "insufficient_coverage", "reason": "no_source_fragments", "query": query,
                    "message": "Related topics have no source fragments for a grounded answer", "topics": topics,
                    "sources": [], "retrieval_warnings": warnings}

        conditions = []
        selected_ids = set(source_ids)
        for topic in topics:
            if condition_claims[topic["id"]]:
                conditions.extend({"topic_id": topic["id"], "text": claim["text"],
                                   "source_fragment_ids": [source_id for source_id in claim["source_fragment_ids"]
                                                           if source_id in selected_ids]}
                                  for claim in condition_claims[topic["id"]]
                                  if any(source_id in selected_ids for source_id in claim["source_fragment_ids"]))
            elif topic["conditions"] and selected_ids.intersection(topic["source_fragment_ids"]):
                conditions.append({"topic_id": topic["id"], "text": topic["conditions"],
                                   "source_fragment_ids": [source_id for source_id in topic["source_fragment_ids"]
                                                           if source_id in selected_ids]})
        shown_sources = [{**source, "content": source["content"][:2500],
                          "content_truncated": len(source["content"]) > 2500} for source in sources]
        labels = {f"F{index}": source for index, source in enumerate(shown_sources, start=1)}
        prompt = json.dumps({"question": query, "conditions": conditions,
                             "fragments": [{"ref": label, "content": source["content"],
                                            "locator": source["locator"]} for label, source in labels.items()]},
                            ensure_ascii=False)
        raw = self._generate(ANSWER_SYSTEM, prompt)
        if raw.get("insufficient") is True:
            return {"status": "insufficient_coverage", "reason": "model_found_no_support", "query": query,
                    "message": "The retrieved fragments do not support a reliable answer", "topics": topics,
                    "sources": shown_sources, "retrieval_warnings": warnings}
        answer, refs = raw.get("answer"), raw.get("source_refs")
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 5000 or not isinstance(refs, list) or not refs or any(
            not isinstance(ref, str) or ref not in labels for ref in refs
        ):
            raise SearchFailure("Local model answer lacks valid source references")
        cited_ids = sorted({labels[ref]["id"] for ref in refs})
        try:
            _check_numbers(answer, cited_ids, {source["id"]: source for source in shown_sources})
        except StoreError as exc:
            raise SearchFailure(str(exc)) from exc
        return {"status": "answered", "query": query, "answer": answer.strip(),
                "source_fragment_ids": cited_ids, "sources": shown_sources, "conditions": conditions,
                "topics": topics, "retrieval_warnings": warnings}
