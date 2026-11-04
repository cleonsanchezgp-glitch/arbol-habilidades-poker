"""Evidence-bounded study paths over the saved prerequisite graph."""

from __future__ import annotations

import unicodedata
from typing import Any

from .storage import Store, StoreError


BEGINNER_GOALS = {"beginner", "beginner path", "principiante", "ruta principiante", "ruta para principiantes",
                  "basico", "basica", "fundamentos"}


def _fold(value: str) -> str:
    return "".join(character for character in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(character)).strip()


class StudyPathService:
    def __init__(self, store: Store):
        self.store = store

    def build(self, data: dict[str, Any]) -> dict[str, Any]:
        goal = data.get("goal")
        if set(data) != {"goal"} or not isinstance(goal, str) or not goal.strip() or len(goal) > 1000:
            raise StoreError("Study path requires a nonempty goal of at most 1000 characters")
        goal = goal.strip()
        topics = {topic["id"]: topic for topic in self.store.list_topics()}
        source_by_topic = {topic_id: [source for source in self.store.fragments_by_ids(
            list({item["fragment_id"] for item in topic["evidence"] if item["role"] == "supports"}))
            if source["kind"] in {"paragraph", "table"} and source["content"].strip()]
            for topic_id, topic in topics.items()}
        sourced = {topic_id for topic_id, sources in source_by_topic.items() if sources}
        if not sourced:
            return {"status": "insufficient_coverage", "reason": "no_sourced_topics", "goal": goal,
                    "steps": [], "excluded": []}

        beginner = _fold(goal) in BEGINNER_GOALS
        if beginner:
            targets = {topic_id for topic_id, topic in topics.items() if topic["difficulty"] == "basic"}
        else:
            matches = self.store.lexical_matches(goal, 100)
            fragment_ids = [hit["entity_id"] for hit in matches if hit["kind"] == "fragment"]
            targets = {hit["entity_id"] for hit in matches if hit["kind"] == "topic"}
            targets.update(self.store.topic_ids_for_fragments(fragment_ids))
        if not targets:
            return {"status": "insufficient_coverage", "reason": "no_matching_topics", "goal": goal,
                    "steps": [], "excluded": []}

        selected: set[str] = set()
        required_for: dict[str, set[str]] = {}
        excluded = []
        for target_id in sorted(targets, key=lambda item: (topics[item]["title"].casefold(), item)):
            closure: set[str] = set()
            pending = [target_id]
            while pending:
                topic_id = pending.pop()
                if topic_id in closure:
                    continue
                closure.add(topic_id)
                pending.extend(topics[topic_id]["prerequisites"])
            missing = closure - sourced
            if missing:
                excluded.append({"topic_id": target_id, "title": topics[target_id]["title"],
                                 "reason": "no_evidence" if target_id in missing else "unsourced_prerequisite",
                                 "missing_topic_ids": sorted(missing)})
                continue
            selected.update(closure)
            for prerequisite_id in closure - {target_id}:
                required_for.setdefault(prerequisite_id, set()).add(topics[target_id]["title"])

        order = [topic_id for topic_id in self.store.ordered_topic_ids() if topic_id in selected]
        steps = []
        for topic_id in order:
            topic = topics[topic_id]
            sources = source_by_topic[topic_id]
            if topic_id in targets:
                reason = "Available basic topic for a beginner path" if beginner else "Matches the study goal"
            else:
                reason = "Prerequisite for " + ", ".join(sorted(required_for[topic_id])[:3])
            steps.append({"topic_id": topic_id, "title": topic["title"],
                          "topic_url": f"/api/topics/{topic_id}",
                          "reason": reason,
                          "difficulty": topic["difficulty"], "review_status": topic["review_status"],
                          "summary": topic["summary"], "conditions": topic["conditions"],
                          "prerequisite_ids": topic["prerequisites"],
                          "locations": self.store.topic_locations(topic_id)["locations"],
                          "sources": [{"fragment_id": source["id"], "document_id": source["document_id"],
                                       "locator": source["locator"],
                                       "document_url": f"/api/documents/{source['document_id']}/file"}
                                      for source in sources]})
        return {"status": "ready" if steps else "insufficient_coverage",
                "reason": None if steps else "no_evidence", "goal": goal,
                "steps": steps, "excluded": excluded}
