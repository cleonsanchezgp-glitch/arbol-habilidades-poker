"""Durable local records and graph invariants for Poker Roots."""

from __future__ import annotations

import hashlib
import heapq
import json
import os
import re
import sqlite3
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DIFFICULTIES = {"basic", "intermediate", "advanced"}
TOPIC_FIELDS = {"title", "summary", "explanation", "conditions", "examples", "visuals", "difficulty", "tags", "review_status", "claims", "unknowns", "contradictions", "prerequisite_proposals"}


def _normalise_facets(facets: dict[str, str | None]) -> dict[str, str | None]:
    if not isinstance(facets, dict) or any(
        not isinstance(name, str) or not name.strip() or
        (value is not None and not isinstance(value, str))
        for name, value in facets.items()
    ):
        raise StoreError("Facets must be a map of names to text or null")
    normalised = {name.strip(): value for name, value in facets.items()}
    if len(normalised) != len(facets):
        raise StoreError("Facet names must be unique after trimming spaces")
    return normalised


def _similarity(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"\w+", left.casefold()))
    right_tokens = set(re.findall(r"\w+", right.casefold()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_data_dir() -> Path:
    override = os.environ.get("POKER_ROOTS_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "PokerRoots"


class StoreError(ValueError):
    """A requested record or relation is invalid."""


class Store:
    def __init__(self, data_dir: Path | str | None = None):
        self.data_dir = Path(data_dir or default_data_dir()).expanduser().resolve()
        self.originals_dir = self.data_dir / "originals"
        self.images_dir = self.data_dir / "images"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.originals_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "poker_roots.db"
        self._migrate()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        finally:
            connection.close()

    def _migrate(self) -> None:
        with self.transaction() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > 2:
                raise RuntimeError(f"Unsupported database version: {version}")
            if version == 2:
                return
            if version == 0:
                schema = """
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY, filename TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE,
                    stored_name TEXT NOT NULL UNIQUE, state TEXT NOT NULL,
                    warnings_json TEXT NOT NULL DEFAULT '[]', error TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE fragments (
                    id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    ordinal INTEGER NOT NULL, kind TEXT NOT NULL, locator TEXT NOT NULL,
                    content TEXT NOT NULL DEFAULT '', image_name TEXT,
                    UNIQUE(document_id, ordinal)
                );
                CREATE TABLE topics (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '',
                    explanation TEXT NOT NULL DEFAULT '', conditions TEXT NOT NULL DEFAULT '',
                    examples_json TEXT NOT NULL DEFAULT '[]', visuals_json TEXT NOT NULL DEFAULT '[]',
                    difficulty TEXT NOT NULL CHECK(difficulty IN ('basic','intermediate','advanced')),
                    tags_json TEXT NOT NULL DEFAULT '[]', review_status TEXT NOT NULL DEFAULT 'proposed',
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE topic_evidence (
                    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    fragment_id TEXT NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
                    role TEXT NOT NULL DEFAULT 'supports',
                    PRIMARY KEY(topic_id, fragment_id, role)
                );
                CREATE TABLE facets (
                    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    name TEXT NOT NULL, value TEXT,
                    PRIMARY KEY(topic_id, name)
                );
                CREATE TABLE branches (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, parent_id TEXT REFERENCES branches(id) ON DELETE RESTRICT,
                    sort_order INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE placements (
                    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    branch_id TEXT NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                    PRIMARY KEY(topic_id, branch_id)
                );
                CREATE TABLE prerequisites (
                    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    prerequisite_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    PRIMARY KEY(topic_id, prerequisite_id),
                    CHECK(topic_id <> prerequisite_id)
                );
                CREATE INDEX idx_fragments_document ON fragments(document_id);
                CREATE INDEX idx_prerequisites_required ON prerequisites(prerequisite_id);
            """
                for statement in schema.split(";"):
                    if statement.strip():
                        db.execute(statement)
            if version < 2:
                db.execute("ALTER TABLE topics ADD COLUMN claims_json TEXT NOT NULL DEFAULT '[]'")
                db.execute("ALTER TABLE topics ADD COLUMN unknowns_json TEXT NOT NULL DEFAULT '[]'")
                db.execute("ALTER TABLE topics ADD COLUMN contradictions_json TEXT NOT NULL DEFAULT '[]'")
                db.execute("ALTER TABLE topics ADD COLUMN prerequisite_proposals_json TEXT NOT NULL DEFAULT '[]'")
                db.execute("""CREATE TABLE document_analysis (
                    document_id TEXT PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
                    topic_count INTEGER NOT NULL, completed_at TEXT NOT NULL
                )""")
                db.execute("""CREATE TABLE topic_similarities (
                    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    candidate_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    score REAL NOT NULL,
                    PRIMARY KEY(topic_id,candidate_id)
                )""")
                db.execute("PRAGMA user_version = 2")

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row else None

    @staticmethod
    def _json_row(row: sqlite3.Row | None, fields: tuple[str, ...]) -> dict[str, Any] | None:
        result = Store._row(row)
        if result:
            for field in fields:
                result[field.removesuffix("_json")] = json.loads(result.pop(field))
        return result

    def save_document(self, filename: str, content: bytes, state: str = "stored") -> tuple[dict[str, Any], bool]:
        if not content:
            raise StoreError("Document is empty")
        clean_name = Path(filename).name.strip()
        if not clean_name or clean_name in {".", ".."}:
            raise StoreError("Document filename is invalid")
        digest = hashlib.sha256(content).hexdigest()
        with self.read() as db:
            existing = db.execute("SELECT * FROM documents WHERE sha256 = ?", (digest,)).fetchone()
        if existing:
            return self._json_row(existing, ("warnings_json",)), False

        document_id = uuid.uuid4().hex
        stored_name = f"{document_id}.docx"
        fd, temporary = tempfile.mkstemp(prefix="upload-", dir=self.originals_dir)
        target = self.originals_dir / stored_name
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            now = utc_now()
            try:
                with self.transaction() as db:
                    db.execute("INSERT INTO documents (id,filename,sha256,stored_name,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?)", (document_id, clean_name, digest, stored_name, state, now, now))
            except sqlite3.IntegrityError:
                target.unlink(missing_ok=True)
                with self.read() as db:
                    existing = db.execute("SELECT * FROM documents WHERE sha256 = ?", (digest,)).fetchone()
                if existing:
                    return self._json_row(existing, ("warnings_json",)), False
                raise
            return self.get_document(document_id), True
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            Path(temporary).unlink(missing_ok=True)

    def get_document(self, document_id: str) -> dict[str, Any]:
        with self.read() as db:
            row = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        if not row:
            raise StoreError("Document not found")
        return self._json_row(row, ("warnings_json",))

    def original_path(self, document_id: str) -> Path:
        document = self.get_document(document_id)
        return self.originals_dir / document["stored_name"]

    def list_documents(self) -> list[dict[str, Any]]:
        with self.read() as db:
            rows = db.execute("SELECT * FROM documents ORDER BY created_at DESC, id").fetchall()
        return [self._json_row(row, ("warnings_json",)) for row in rows]

    def set_document_state(self, document_id: str, state: str, warnings: list[str] | None = None, error: str | None = None) -> dict[str, Any]:
        if state not in {"stored", "queued", "extracting", "extracted", "awaiting_model", "analyzing", "completed", "failed"}:
            raise StoreError("Invalid document state")
        with self.transaction() as db:
            changed = db.execute("UPDATE documents SET state=?, warnings_json=?, error=?, updated_at=? WHERE id=?", (state, json.dumps(warnings or []), error, utc_now(), document_id)).rowcount
            if not changed:
                raise StoreError("Document not found")
        return self.get_document(document_id)

    def add_fragments(self, document_id: str, fragments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self.transaction() as db:
            if not db.execute("SELECT 1 FROM documents WHERE id=?", (document_id,)).fetchone():
                raise StoreError("Document not found")
            start = db.execute("SELECT COALESCE(MAX(ordinal), -1)+1 FROM fragments WHERE document_id=?", (document_id,)).fetchone()[0]
            result = []
            for offset, fragment in enumerate(fragments):
                kind = fragment.get("kind")
                if kind not in {"paragraph", "table", "image"}:
                    raise StoreError("Invalid fragment kind")
                fragment_id = uuid.uuid4().hex
                item = {"id": fragment_id, "document_id": document_id, "ordinal": start + offset, "kind": kind, "locator": str(fragment.get("locator", "")), "content": str(fragment.get("content", "")), "image_name": fragment.get("image_name")}
                db.execute("INSERT INTO fragments (id,document_id,ordinal,kind,locator,content,image_name) VALUES (:id,:document_id,:ordinal,:kind,:locator,:content,:image_name)", item)
                result.append(item)
            return result

    def replace_fragments(self, document_id: str, fragments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Replace extracted fragments atomically when retrying an import."""
        with self.transaction() as db:
            if not db.execute("SELECT 1 FROM documents WHERE id=?", (document_id,)).fetchone():
                raise StoreError("Document not found")
            db.execute("DELETE FROM fragments WHERE document_id=?", (document_id,))
            result = []
            for ordinal, fragment in enumerate(fragments):
                kind = fragment.get("kind")
                if kind not in {"paragraph", "table", "image"}:
                    raise StoreError("Invalid fragment kind")
                item = {"id": uuid.uuid4().hex, "document_id": document_id, "ordinal": ordinal,
                        "kind": kind, "locator": str(fragment.get("locator", "")),
                        "content": str(fragment.get("content", "")), "image_name": fragment.get("image_name")}
                db.execute("INSERT INTO fragments (id,document_id,ordinal,kind,locator,content,image_name) VALUES (:id,:document_id,:ordinal,:kind,:locator,:content,:image_name)", item)
                result.append(item)
            return result

    def list_fragments(self, document_id: str) -> list[dict[str, Any]]:
        self.get_document(document_id)
        with self.read() as db:
            return [dict(row) for row in db.execute("SELECT * FROM fragments WHERE document_id=? ORDER BY ordinal", (document_id,))]

    def image_path(self, document_id: str, image_name: str) -> Path:
        with self.read() as db:
            exists = db.execute("SELECT 1 FROM fragments WHERE document_id=? AND image_name=? AND kind='image'", (document_id, image_name)).fetchone()
        if not exists or Path(image_name).name != image_name:
            raise StoreError("Image not found")
        return self.images_dir / image_name

    @staticmethod
    def _topic_values(data: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
        unknown = set(data) - TOPIC_FIELDS
        if unknown:
            raise StoreError(f"Unknown topic fields: {', '.join(sorted(unknown))}")
        merged = {**(existing or {}), **data}
        title = merged.get("title")
        if not isinstance(title, str) or not title.strip():
            raise StoreError("Topic title is required")
        difficulty = merged.get("difficulty", "basic")
        if difficulty not in DIFFICULTIES:
            raise StoreError("Invalid difficulty")
        for name in ("summary", "explanation", "conditions", "review_status"):
            if not isinstance(merged.get(name, ""), str):
                raise StoreError(f"{name} must be text")
        for name in ("examples", "visuals", "tags", "claims", "unknowns", "contradictions", "prerequisite_proposals"):
            value = merged.get(name, [])
            if not isinstance(value, list):
                raise StoreError(f"{name} must be a list")
        return {
            "title": title.strip(), "summary": merged.get("summary", ""),
            "explanation": merged.get("explanation", ""), "conditions": merged.get("conditions", ""),
            "examples_json": json.dumps(merged.get("examples", []), ensure_ascii=False),
            "visuals_json": json.dumps(merged.get("visuals", []), ensure_ascii=False),
            "difficulty": difficulty, "tags_json": json.dumps(merged.get("tags", []), ensure_ascii=False),
            "review_status": merged.get("review_status", "proposed"),
            "claims_json": json.dumps(merged.get("claims", []), ensure_ascii=False),
            "unknowns_json": json.dumps(merged.get("unknowns", []), ensure_ascii=False),
            "contradictions_json": json.dumps(merged.get("contradictions", []), ensure_ascii=False),
            "prerequisite_proposals_json": json.dumps(merged.get("prerequisite_proposals", []), ensure_ascii=False),
        }

    def create_topic(self, data: dict[str, Any]) -> dict[str, Any]:
        values = self._topic_values(data)
        values.update(id=uuid.uuid4().hex, created_at=utc_now(), updated_at=utc_now())
        with self.transaction() as db:
            db.execute("""INSERT INTO topics (id,title,summary,explanation,conditions,examples_json,visuals_json,difficulty,tags_json,review_status,created_at,updated_at,claims_json,unknowns_json,contradictions_json,prerequisite_proposals_json)
                          VALUES (:id,:title,:summary,:explanation,:conditions,:examples_json,:visuals_json,:difficulty,:tags_json,:review_status,:created_at,:updated_at,:claims_json,:unknowns_json,:contradictions_json,:prerequisite_proposals_json)""", values)
        return self.get_topic(values["id"])

    def get_topic(self, topic_id: str) -> dict[str, Any]:
        with self.read() as db:
            row = db.execute("SELECT * FROM topics WHERE id=?", (topic_id,)).fetchone()
            if not row:
                raise StoreError("Topic not found")
            topic = self._json_row(row, ("examples_json", "visuals_json", "tags_json", "claims_json", "unknowns_json", "contradictions_json", "prerequisite_proposals_json"))
            topic["facets"] = {item["name"]: item["value"] for item in db.execute("SELECT name,value FROM facets WHERE topic_id=? ORDER BY name", (topic_id,))}
            topic["placements"] = [item[0] for item in db.execute("SELECT branch_id FROM placements WHERE topic_id=? ORDER BY branch_id", (topic_id,))]
            topic["prerequisites"] = [item[0] for item in db.execute("SELECT prerequisite_id FROM prerequisites WHERE topic_id=? ORDER BY prerequisite_id", (topic_id,))]
            topic["evidence"] = [dict(item) for item in db.execute("SELECT fragment_id,role FROM topic_evidence WHERE topic_id=? ORDER BY fragment_id", (topic_id,))]
            topic["similar_candidates"] = [dict(item) for item in db.execute("SELECT candidate_id,score FROM topic_similarities WHERE topic_id=? ORDER BY score DESC", (topic_id,))]
            return topic

    def list_topics(self) -> list[dict[str, Any]]:
        with self.read() as db:
            topic_ids = [row[0] for row in db.execute("SELECT id FROM topics ORDER BY title COLLATE NOCASE, id")]
        return [self.get_topic(topic_id) for topic_id in topic_ids]

    def ordered_topic_ids(self) -> list[str]:
        """Return prerequisites before their dependents, independent of difficulty."""
        with self.read() as db:
            topics = {row["id"]: row["title"] for row in db.execute("SELECT id,title FROM topics")}
            edges = db.execute("SELECT topic_id,prerequisite_id FROM prerequisites").fetchall()
        remaining = {topic_id: 0 for topic_id in topics}
        dependents = {topic_id: [] for topic_id in topics}
        for edge in edges:
            remaining[edge["topic_id"]] += 1
            dependents[edge["prerequisite_id"]].append(edge["topic_id"])
        ready = [(topics[topic_id].casefold(), topic_id) for topic_id, count in remaining.items() if count == 0]
        heapq.heapify(ready)
        order = []
        while ready:
            _, topic_id = heapq.heappop(ready)
            order.append(topic_id)
            for dependent_id in dependents[topic_id]:
                remaining[dependent_id] -= 1
                if remaining[dependent_id] == 0:
                    heapq.heappush(ready, (topics[dependent_id].casefold(), dependent_id))
        if len(order) != len(topics):
            raise StoreError("Prerequisite graph contains a cycle")
        return order

    def topics_for_document(self, document_id: str) -> list[dict[str, Any]]:
        self.get_document(document_id)
        with self.read() as db:
            topic_ids = [row[0] for row in db.execute("""SELECT DISTINCT te.topic_id FROM topic_evidence te
                JOIN fragments f ON f.id=te.fragment_id WHERE f.document_id=? ORDER BY te.topic_id""", (document_id,))]
        return [self.get_topic(topic_id) for topic_id in topic_ids]

    def analysis_exists(self, document_id: str) -> bool:
        with self.read() as db:
            return db.execute("SELECT 1 FROM document_analysis WHERE document_id=?", (document_id,)).fetchone() is not None

    def create_processed_topics(self, document_id: str, proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not proposals:
            raise StoreError("Model proposed no source-backed topics")
        created_ids = []
        with self.transaction() as db:
            if db.execute("SELECT 1 FROM document_analysis WHERE document_id=?", (document_id,)).fetchone():
                raise StoreError("Document already has processed topics")
            valid_fragments = {row[0] for row in db.execute("SELECT id FROM fragments WHERE document_id=?", (document_id,))}
            existing = [(row["id"], row["title"], row["summary"]) for row in db.execute("SELECT id,title,summary FROM topics")]
            for proposal in proposals:
                source_ids = proposal.get("source_fragment_ids")
                if not isinstance(source_ids, list) or not source_ids or any(source_id not in valid_fragments for source_id in source_ids):
                    raise StoreError("Every proposed topic needs valid source fragments from its document")
                facets = _normalise_facets(proposal.get("facets", {}))
                values = self._topic_values({key: value for key, value in proposal.items() if key in TOPIC_FIELDS})
                topic_id = uuid.uuid4().hex
                values.update(id=topic_id, created_at=utc_now(), updated_at=utc_now())
                db.execute("""INSERT INTO topics (id,title,summary,explanation,conditions,examples_json,visuals_json,difficulty,tags_json,review_status,created_at,updated_at,claims_json,unknowns_json,contradictions_json,prerequisite_proposals_json)
                              VALUES (:id,:title,:summary,:explanation,:conditions,:examples_json,:visuals_json,:difficulty,:tags_json,:review_status,:created_at,:updated_at,:claims_json,:unknowns_json,:contradictions_json,:prerequisite_proposals_json)""", values)
                for source_id in set(source_ids):
                    db.execute("INSERT INTO topic_evidence(topic_id,fragment_id,role) VALUES (?,?,?)", (topic_id, source_id, "supports"))
                for name, value in facets.items():
                    db.execute("INSERT INTO facets(topic_id,name,value) VALUES (?,?,?)", (topic_id, name, value))
                for candidate_id, title, summary in existing:
                    score = _similarity(values["title"] + " " + values["summary"], title + " " + summary)
                    if score >= 0.55:
                        db.execute("INSERT INTO topic_similarities(topic_id,candidate_id,score) VALUES (?,?,?)", (topic_id, candidate_id, score))
                created_ids.append(topic_id)
            db.execute("INSERT INTO document_analysis(document_id,topic_count,completed_at) VALUES (?,?,?)", (document_id, len(created_ids), utc_now()))
        return [self.get_topic(topic_id) for topic_id in created_ids]

    def update_topic(self, topic_id: str, data: dict[str, Any]) -> dict[str, Any]:
        current = self.get_topic(topic_id)
        values = self._topic_values(data, current)
        values.update(id=topic_id, updated_at=utc_now())
        with self.transaction() as db:
            db.execute("""UPDATE topics SET title=:title,summary=:summary,explanation=:explanation,
                          conditions=:conditions,examples_json=:examples_json,visuals_json=:visuals_json,
                          difficulty=:difficulty,tags_json=:tags_json,review_status=:review_status,
                          claims_json=:claims_json,unknowns_json=:unknowns_json,
                          contradictions_json=:contradictions_json,prerequisite_proposals_json=:prerequisite_proposals_json,
                          updated_at=:updated_at WHERE id=:id""", values)
        return self.get_topic(topic_id)

    def set_facets(self, topic_id: str, facets: dict[str, str | None]) -> dict[str, Any]:
        normalised = _normalise_facets(facets)
        with self.transaction() as db:
            if not db.execute("SELECT 1 FROM topics WHERE id=?", (topic_id,)).fetchone():
                raise StoreError("Topic not found")
            db.execute("DELETE FROM facets WHERE topic_id=?", (topic_id,))
            db.executemany("INSERT INTO facets(topic_id,name,value) VALUES (?,?,?)", [(topic_id, name, value) for name, value in normalised.items()])
        return self.get_topic(topic_id)

    def link_evidence(self, topic_id: str, fragment_id: str, role: str = "supports") -> dict[str, Any]:
        if role not in {"supports", "context", "contradicts"}:
            raise StoreError("Invalid evidence role")
        with self.transaction() as db:
            try:
                db.execute("INSERT INTO topic_evidence(topic_id,fragment_id,role) VALUES (?,?,?)", (topic_id, fragment_id, role))
            except sqlite3.IntegrityError as exc:
                raise StoreError("Topic or fragment missing, or evidence link already exists") from exc
        return self.get_topic(topic_id)

    def create_branch(self, name: str, parent_id: str | None = None, sort_order: int = 0) -> dict[str, Any]:
        if not isinstance(name, str) or not name.strip():
            raise StoreError("Branch name is required")
        branch_id = uuid.uuid4().hex
        with self.transaction() as db:
            try:
                db.execute("INSERT INTO branches(id,name,parent_id,sort_order) VALUES (?,?,?,?)", (branch_id, name.strip(), parent_id, sort_order))
            except sqlite3.IntegrityError as exc:
                raise StoreError("Parent branch not found") from exc
        return {"id": branch_id, "name": name.strip(), "parent_id": parent_id, "sort_order": sort_order}

    def list_branches(self) -> list[dict[str, Any]]:
        with self.read() as db:
            return [dict(row) for row in db.execute("SELECT * FROM branches ORDER BY sort_order,name")]

    def place_topic(self, topic_id: str, branch_id: str) -> dict[str, Any]:
        with self.transaction() as db:
            try:
                db.execute("INSERT INTO placements(topic_id,branch_id) VALUES (?,?)", (topic_id, branch_id))
            except sqlite3.IntegrityError as exc:
                raise StoreError("Topic or branch missing, or placement already exists") from exc
        return self.get_topic(topic_id)

    def remove_placement(self, topic_id: str, branch_id: str) -> dict[str, Any]:
        with self.transaction() as db:
            db.execute("DELETE FROM placements WHERE topic_id=? AND branch_id=?", (topic_id, branch_id))
        return self.get_topic(topic_id)

    def add_prerequisite(self, topic_id: str, prerequisite_id: str) -> dict[str, Any]:
        if topic_id == prerequisite_id:
            raise StoreError("A topic cannot require itself")
        with self.transaction() as db:
            if not db.execute("SELECT 1 FROM topics WHERE id=?", (topic_id,)).fetchone() or not db.execute("SELECT 1 FROM topics WHERE id=?", (prerequisite_id,)).fetchone():
                raise StoreError("Topic or prerequisite not found")
            cycle = db.execute("""WITH RECURSIVE ancestors(id) AS (
                SELECT prerequisite_id FROM prerequisites WHERE topic_id=?
                UNION
                SELECT p.prerequisite_id FROM prerequisites p JOIN ancestors a ON p.topic_id=a.id
            ) SELECT 1 FROM ancestors WHERE id=? LIMIT 1""", (prerequisite_id, topic_id)).fetchone()
            if cycle:
                raise StoreError("Prerequisite would create a cycle")
            try:
                db.execute("INSERT INTO prerequisites(topic_id,prerequisite_id) VALUES (?,?)", (topic_id, prerequisite_id))
            except sqlite3.IntegrityError as exc:
                raise StoreError("Prerequisite already exists") from exc
        return self.get_topic(topic_id)

    def remove_prerequisite(self, topic_id: str, prerequisite_id: str) -> dict[str, Any]:
        with self.transaction() as db:
            db.execute("DELETE FROM prerequisites WHERE topic_id=? AND prerequisite_id=?", (topic_id, prerequisite_id))
        return self.get_topic(topic_id)
