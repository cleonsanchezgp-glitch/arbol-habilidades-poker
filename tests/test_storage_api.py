import json
import io
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.api import PokerRootsServer
from backend.docx_extract import extract_docx
from backend.imports import ImportService
from backend.local_model import LocalModel, ModelUnavailable
from backend.retrieval_index import RetrievalIndexer
from backend.search import SearchFailure, SearchService
from backend.study_path import StudyPathService
from backend.topic_processor import TopicProcessor
from backend.storage import Store, StoreError


def sample_docx() -> bytes:
    document_xml = """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
        xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <w:body>
        <w:p><w:r><w:t>Posiciones</w:t></w:r></w:p>
        <w:tbl><w:tr><w:tc><w:p><w:r><w:t>BTN</w:t></w:r></w:p></w:tc>
          <w:tc><w:p><w:r><w:t>BB</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
        <w:p><w:r><w:t>Flop Axx</w:t></w:r><w:drawing><a:blip r:embed="rId1"/></w:drawing></w:p>
      </w:body></w:document>"""
    relationships = """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
        Target="media/example.png"/>
      </Relationships>"""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        package.writestr("word/document.xml", document_xml)
        package.writestr("word/_rels/document.xml.rels", relationships)
        package.writestr("word/media/example.png", b"image bytes")
    return output.getvalue()


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.store = Store(self.path)

    def test_persistence_duplicate_detection_and_atomic_fragments(self):
        document, created = self.store.save_document("lesson.docx", b"fixture docx")
        self.assertTrue(created)
        duplicate, created = self.store.save_document("second-name.docx", b"fixture docx")
        self.assertFalse(created)
        self.assertEqual(document["id"], duplicate["id"])
        self.assertEqual((self.store.original_path(document["id"])).read_bytes(), b"fixture docx")

        with self.assertRaises(StoreError):
            self.store.add_fragments(document["id"], [
                {"kind": "paragraph", "locator": "p1", "content": "Valid"},
                {"kind": "unknown", "locator": "p2", "content": "Invalid"},
            ])
        self.assertEqual(self.store.list_fragments(document["id"]), [])
        fragments = self.store.add_fragments(document["id"], [{"kind": "paragraph", "locator": "p1", "content": "Position: BB"}])
        topic = self.store.create_topic({"title": "BB basics", "difficulty": "basic"})
        self.store.link_evidence(topic["id"], fragments[0]["id"])
        self.store.update_topic(topic["id"], {"summary": "Corrected by user"})

        reopened = Store(self.path)
        self.assertEqual(reopened.get_document(document["id"])["sha256"], document["sha256"])
        self.assertEqual(reopened.get_topic(topic["id"])["summary"], "Corrected by user")
        self.assertEqual(reopened.get_topic(topic["id"])["evidence"][0]["fragment_id"], fragments[0]["id"])

    def test_prerequisite_cycle_rejected_without_partial_change(self):
        root = self.store.create_topic({"title": "Positions", "difficulty": "basic"})
        advanced = self.store.create_topic({"title": "BB vs BTN", "difficulty": "advanced"})
        self.store.add_prerequisite(advanced["id"], root["id"])
        with self.assertRaisesRegex(StoreError, "cycle"):
            self.store.add_prerequisite(root["id"], advanced["id"])
        self.assertEqual(self.store.get_topic(root["id"])["prerequisites"], [])
        self.assertEqual(self.store.get_topic(advanced["id"])["prerequisites"], [root["id"]])

    def test_facets_difficulty_and_multiple_placements_survive_restart(self):
        topic = self.store.create_topic({"title": "Defensa BB", "difficulty": "intermediate"})
        self.store.set_facets(topic["id"], {" street ": "flop", "pot type": None})
        first = self.store.create_branch("Defensa")
        second = self.store.create_branch("Juego postflop")
        self.store.place_topic(topic["id"], first["id"])
        self.store.place_topic(topic["id"], second["id"])

        with self.assertRaisesRegex(StoreError, "unique"):
            self.store.set_facets(topic["id"], {"street": "turn", " street ": "river"})
        reopened = Store(self.path).get_topic(topic["id"])
        self.assertEqual(reopened["facets"], {"street": "flop", "pot type": None})
        self.assertEqual(set(reopened["placements"]), {first["id"], second["id"]})
        self.assertEqual(reopened["difficulty"], "intermediate")
        self.assertEqual(reopened["prerequisites"], [])

    def test_learning_order_respects_dependencies_without_using_difficulty(self):
        prerequisite = self.store.create_topic({"title": "Z concepto previo", "difficulty": "advanced"})
        dependent = self.store.create_topic({"title": "A aplicación", "difficulty": "basic"})
        unrelated = self.store.create_topic({"title": "B independiente", "difficulty": "intermediate"})
        self.store.add_prerequisite(dependent["id"], prerequisite["id"])

        order = Store(self.path).ordered_topic_ids()
        self.assertEqual(set(order), {prerequisite["id"], dependent["id"], unrelated["id"]})
        self.assertLess(order.index(prerequisite["id"]), order.index(dependent["id"]))
        with self.assertRaisesRegex(StoreError, "cycle"):
            self.store.add_prerequisite(prerequisite["id"], dependent["id"])
        self.assertEqual(self.store.ordered_topic_ids(), order)

    def test_lexical_index_tracks_fragments_topics_edits_and_replacement(self):
        document, _ = self.store.save_document("lesson.docx", b"source")
        fragment = self.store.add_fragments(document["id"], [
            {"kind": "paragraph", "locator": "p1", "content": "Defensa ciega grande"},
        ])[0]
        topic = self.store.create_topic({"title": "Defensa BB", "summary": "Flop Axx", "difficulty": "basic"})
        self.store.link_evidence(topic["id"], fragment["id"])
        matches = self.store.lexical_matches("defensa")
        self.assertEqual({item["entity_id"] for item in matches}, {fragment["id"], topic["id"]})
        self.assertTrue(all(item["source_fragment_ids"] == [fragment["id"]] for item in matches))
        self.store.update_topic(topic["id"], {"summary": "Juego en turn"})
        self.assertEqual(self.store.lexical_matches("flop"), [])
        self.assertEqual(self.store.lexical_matches("turn")[0]["entity_id"], topic["id"])
        self.store.update_topic(topic["id"], {"examples": [{"text": "Chequeo defensivo"}]})
        self.assertEqual(self.store.lexical_matches("defensivo")[0]["entity_id"], topic["id"])
        self.store.replace_fragments(document["id"], [
            {"kind": "paragraph", "locator": "p1", "content": "Rangos de apertura"},
        ])
        self.assertEqual(self.store.lexical_matches("ciega"), [])
        self.assertEqual(len(self.store.lexical_matches("rangos")), 1)
        self.assertEqual(len(Store(self.path).lexical_matches("turn")), 1)

    def test_embedding_refresh_and_content_invalidation(self):
        class FakeEmbeddingModel:
            embedding_name = ""

            def embed(self, content):
                return [float(len(content)), 1.0]

        topic = self.store.create_topic({"title": "Rangos", "difficulty": "basic"})
        model = FakeEmbeddingModel()
        indexer = RetrievalIndexer(self.store, model)
        try:
            model.embedding_name = "local-test"
            self.assertEqual(indexer.refresh()["embedded"], 1)
            self.store.update_topic(topic["id"], {"summary": "Nuevos rangos"})
            self.assertEqual(self.store.index_status("local-test")["pending"], 1)
            self.assertEqual(indexer.refresh()["embedded"], 1)
            with self.store.read() as db:
                entry = db.execute("SELECT embedding_json,content FROM search_entries WHERE entity_id=?", (topic["id"],)).fetchone()
            self.assertEqual(json.loads(entry["embedding_json"]), [float(len(entry["content"])), 1.0])
            self.assertEqual(indexer.store.embedding_entries("local-test")[0]["vector"],
                             [float(len(entry["content"])), 1.0])
        finally:
            indexer.close()

    def test_embedding_failure_is_visible_and_retryable(self):
        class FlakyModel:
            embedding_name = ""
            available = False

            def embed(self, content):
                if not self.available:
                    raise ModelUnavailable("embedding service offline")
                return [1.0, 0.0]

        model = FlakyModel()
        self.store.create_topic({"title": "Rangos", "difficulty": "basic"})
        indexer = RetrievalIndexer(self.store, model)
        try:
            model.embedding_name = "local-test"
            indexer.refresh()
            self.assertEqual(self.store.index_status(model.embedding_name)["failed"], 1)
            self.assertEqual(len(self.store.lexical_matches("rangos")), 1)
            model.available = True
            self.store.retry_failed_embeddings()
            self.assertEqual(indexer.refresh()["embedded"], 1)
        finally:
            indexer.close()

    def test_version_two_migration_backfills_search_index(self):
        document, _ = self.store.save_document("lesson.docx", b"source")
        self.store.add_fragments(document["id"], [{"kind": "paragraph", "locator": "p1", "content": "Bote resubido"}])
        self.store.create_topic({"title": "Defensa", "difficulty": "basic"})
        with self.store.transaction() as db:
            db.execute("DROP TRIGGER search_entries_insert")
            db.execute("DROP TRIGGER search_entries_update")
            db.execute("DROP TRIGGER search_entries_delete")
            db.execute("DROP TABLE search_fts")
            db.execute("DROP TABLE search_entries")
            db.execute("PRAGMA user_version = 2")
        reopened = Store(self.path)
        self.assertEqual(len(reopened.lexical_matches("resubido")), 1)
        self.assertEqual(len(reopened.lexical_matches("defensa")), 1)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name))
        self.server = PokerRootsServer(("127.0.0.1", 0), self.store,
                                       LocalModel(name="", embedding_name=""))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def request(self, method, path, data=None, headers=None):
        body = None if data is None else json.dumps(data).encode("utf-8")
        request = Request(self.base + path, data=body, headers=headers or ({"Content-Type": "application/json"} if body else {}), method=method)
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def wait_document(self, document_id):
        for _ in range(100):
            current = self.request("GET", f"/api/documents/{document_id}")[1]
            if current["state"] in {"awaiting_model", "completed", "failed"}:
                return current
            time.sleep(0.01)
        self.fail("Document processing did not finish")

    def test_local_ui_is_served_with_api_and_only_allowlisted_assets(self):
        with urlopen(self.base + "/", timeout=5) as response:
            page = response.read().decode("utf-8")
            self.assertIn("id=\"treeRegion\"", page)
            self.assertIn("id=\"workspaceBody\"", page)
            self.assertIn("text/html", response.headers["Content-Type"])
        with urlopen(self.base + "/app.js", timeout=5) as response:
            script = response.read().decode("utf-8")
            self.assertIn("fetch('/api/tree'", script)
            self.assertNotIn("const nodes=[", script)
        with urlopen(self.base + "/workspace.js", timeout=5) as response:
            script = response.read().decode("utf-8")
            self.assertIn("/api/study-path", script)
            self.assertIn("/api/search", script)
        with urlopen(self.base + "/assets/drawn-0.jpg", timeout=5) as response:
            self.assertEqual(response.headers["Content-Type"], "image/jpeg")
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/backend/storage.py", timeout=5)
        self.assertEqual(error.exception.code, 404)
        error.exception.close()

    def test_topic_api_and_failed_update(self):
        status, topic = self.request("POST", "/api/topics", {"title": "Rangos", "difficulty": "basic"})
        self.assertEqual(status, 201)
        status, error = self.request("PUT", f"/api/topics/{topic['id']}", {"difficulty": "expert"})
        self.assertEqual(status, 400)
        self.assertIn("difficulty", error["error"])
        status, current = self.request("GET", f"/api/topics/{topic['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(current["difficulty"], "basic")
        self.assertEqual(self.request("GET", "/api/health")[1]["status"], "ok")
        self.assertEqual(self.request("GET", "/api/health")[1]["database_version"], 3)
        status, index = self.request("GET", "/api/index/status")
        self.assertEqual(status, 200)
        self.assertEqual(index["entries"], 1)
        self.assertEqual(index["pending"], 1)

    def test_search_reports_local_model_unavailable(self):
        self.store.create_topic({"title": "Rangos", "difficulty": "basic"})
        status, result = self.request("POST", "/api/search", {"query": "¿Qué rangos?"})
        self.assertEqual(status, 503)
        self.assertEqual(result["status"], "model_unavailable")
        self.assertEqual(self.store.list_topics()[0]["title"], "Rangos")

    def test_search_api_returns_fragment_link(self):
        document, _ = self.store.save_document("lesson.docx", b"source")
        fragment = self.store.add_fragments(document["id"], [
            {"kind": "paragraph", "locator": "p1", "content": "BB vs BTN en flop Axx tras open"},
        ])[0]
        topic = self.store.create_topic({"title": "BB vs BTN", "difficulty": "basic"})
        self.store.link_evidence(topic["id"], fragment["id"])
        model = SearchTests.Model()
        self.server.search.model = model
        status, result = self.request("POST", "/api/search", {"query": "BB vs BTN tras open"})
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["source_fragment_ids"], [fragment["id"]])
        self.assertEqual(result["sources"][0]["document_id"], document["id"])
        model.invalid_refs = True
        status, result = self.request("POST", "/api/search", {"query": "BB vs BTN tras open"})
        self.assertEqual(status, 502)
        self.assertEqual(result["status"], "search_failed")

    def test_study_path_api_reports_no_evidence(self):
        self.store.create_topic({"title": "Rangos", "difficulty": "basic"})
        status, result = self.request("POST", "/api/study-path", {"goal": "principiante"})
        self.assertEqual(status, 200)
        self.assertEqual((result["status"], result["reason"]),
                         ("insufficient_coverage", "no_sourced_topics"))

    def test_atomic_topic_edit_refreshes_tree_and_locations(self):
        root = self.store.create_branch("Fundamentos")
        child = self.store.create_branch("Postflop", root["id"])
        other = self.store.create_branch("Defensa")
        prerequisite = self.store.create_topic({"title": "Z conceptos", "difficulty": "advanced"})
        topic = self.store.create_topic({"title": "A defensa", "difficulty": "basic"})

        status, edited = self.request("PUT", f"/api/topics/{topic['id']}", {
            "summary": "Defensa corregida", "difficulty": "intermediate",
            "facets": {"street": "flop", "pot type": None},
            "placements": [child["id"], other["id"]],
            "prerequisites": [prerequisite["id"]],
        })
        self.assertEqual(status, 200)
        self.assertEqual(edited["summary"], "Defensa corregida")
        self.assertEqual(edited["facets"], {"street": "flop", "pot type": None})
        self.assertEqual(set(edited["placements"]), {child["id"], other["id"]})
        self.assertEqual(edited["prerequisites"], [prerequisite["id"]])
        tree = self.request("GET", "/api/tree")[1]
        self.assertEqual([item["id"] for item in tree["topics"]], [prerequisite["id"], topic["id"]])
        locations = self.request("GET", f"/api/topics/{topic['id']}/locations")[1]["locations"]
        self.assertEqual({tuple(part["name"] for part in location["path"]) for location in locations},
                         {("Fundamentos", "Postflop"), ("Defensa",)})
        self.assertEqual(Store(self.store.data_dir).get_topic(topic["id"])["summary"], "Defensa corregida")

        status, error = self.request("PUT", f"/api/topics/{prerequisite['id']}", {
            "summary": "Must roll back", "facets": {"street": "turn"},
            "placements": [root["id"]], "prerequisites": [topic["id"]],
        })
        self.assertEqual(status, 400)
        self.assertIn("cycle", error["error"])
        unchanged = self.store.get_topic(prerequisite["id"])
        self.assertEqual(unchanged["summary"], "")
        self.assertEqual(unchanged["facets"], {})
        self.assertEqual(unchanged["placements"], [])
        self.assertEqual(unchanged["prerequisites"], [])

        status, error = self.request("PUT", f"/api/topics/{topic['id']}", {
            "summary": "Must also roll back", "placements": ["missing-branch"],
        })
        self.assertEqual(status, 404)
        self.assertIn("Branch not found", error["error"])
        self.assertEqual(self.store.get_topic(topic["id"])["summary"], "Defensa corregida")

        status, corrected = self.request("PUT", f"/api/topics/{topic['id']}", {
            "difficulty": "advanced", "facets": {"street": "turn"},
            "placements": [other["id"]], "prerequisites": [],
        })
        self.assertEqual(status, 200)
        self.assertEqual(corrected["facets"], {"street": "turn"})
        self.assertEqual(corrected["placements"], [other["id"]])
        self.assertEqual(corrected["prerequisites"], [])
        self.assertEqual(self.request("GET", f"/api/topics/{topic['id']}/locations")[1]["locations"][0]["path"],
                         [{"id": other["id"], "name": "Defensa"}])
        self.assertEqual(self.request("GET", "/api/tree")[1]["topics"][0]["id"], topic["id"])

    def test_document_upload_and_original_download(self):
        original = sample_docx()
        upload = Request(
            self.base + "/api/documents", data=original,
            headers={"X-Filename": "lesson.docx"}, method="POST",
        )
        with urlopen(upload, timeout=5) as response:
            self.assertEqual(response.status, 202)
            document = json.load(response)["document"]
        current = self.wait_document(document["id"])
        self.assertEqual(current["state"], "awaiting_model", current.get("error"))
        self.assertIn("POKER_ROOTS_MODEL", current["error"])
        with urlopen(self.base + f"/api/documents/{document['id']}/file", timeout=5) as response:
            self.assertEqual(response.read(), original)
        fragments = self.request("GET", f"/api/documents/{document['id']}/fragments")[1]["fragments"]
        self.assertEqual([item["kind"] for item in fragments], ["paragraph", "table", "paragraph", "image"])
        self.assertEqual(json.loads(fragments[1]["content"]), [["BTN", "BB"]])
        with urlopen(self.base + f"/api/documents/{document['id']}/images/{fragments[3]['image_name']}", timeout=5) as response:
            self.assertEqual(response.read(), b"image bytes")
        with urlopen(upload, timeout=5) as response:
            duplicate = json.load(response)
            self.assertEqual(response.status, 200)
            self.assertFalse(duplicate["created"])
            self.assertEqual(duplicate["document"]["id"], document["id"])
        self.assertEqual(self.request("GET", "/api/documents")[1]["documents"][0]["id"], document["id"])
        self.assertEqual(self.request("GET", f"/api/documents/{document['id']}/topics")[1]["topics"], [])

    def test_invalid_docx_rejected_without_record(self):
        upload = Request(self.base + "/api/documents", data=b"not a docx", headers={"X-Filename": "bad.docx"}, method="POST")
        with self.assertRaises(HTTPError) as error:
            urlopen(upload, timeout=5)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()
        self.assertEqual(self.request("GET", "/api/documents")[1]["documents"], [])

    def test_failed_extraction_keeps_original_and_can_retry(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as package:
            package.writestr("[Content_Types].xml", "<Types/>")
            package.writestr("word/document.xml", "<broken")
        upload = Request(self.base + "/api/documents", data=output.getvalue(), headers={"X-Filename": "broken.docx"}, method="POST")
        with urlopen(upload, timeout=5) as response:
            document_id = json.load(response)["document"]["id"]
        failed = self.wait_document(document_id)
        self.assertEqual(failed["state"], "failed")
        self.assertIn("Invalid DOCX XML", failed["error"])
        with urlopen(self.base + f"/api/documents/{document_id}/file", timeout=5) as response:
            self.assertEqual(response.read(), output.getvalue())
        status, _ = self.request("POST", f"/api/documents/{document_id}/retry")
        self.assertEqual(status, 202)
        self.assertEqual(self.wait_document(document_id)["state"], "failed")


class ExtractionTests(unittest.TestCase):
    def test_source_order_and_image_warning(self):
        extracted = extract_docx(sample_docx(), "lesson.docx")
        self.assertEqual([item["kind"] for item in extracted.fragments], ["paragraph", "table", "paragraph", "image"])
        self.assertEqual(extracted.fragments[0]["content"], "Posiciones")
        self.assertTrue(any("Text contained only inside images" in warning for warning in extracted.warnings))


class LocalModelTests(unittest.TestCase):
    def test_embedding_adapter_uses_local_embed_contract(self):
        model = LocalModel(name="", embedding_name="test-embedding", base_url="http://127.0.0.1:11434")
        with patch("backend.local_model.build_opener") as build:
            build.return_value.open.return_value.__enter__.return_value = io.BytesIO(b'{"embeddings":[[0.25,-0.5]]}')
            self.assertEqual(model.embed("Flop Axx"), [0.25, -0.5])
            request = build.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/embed")
            self.assertEqual(json.loads(request.data), {"model": "test-embedding", "input": "Flop Axx"})


class SearchTests(unittest.TestCase):
    class Model:
        embedding_name = ""
        configured = True
        invalid_refs = False
        unsupported_number = False
        insufficient = False

        def embed(self, content):
            return [1.0, 0.0]

        def generate_json(self, system, prompt):
            if "Interpreta la pregunta" in system:
                query = json.loads(prompt)["query"]
                if "sin datos" in query:
                    return {"terms": ["inexistente"], "facets": {}}
                return {"terms": ["BB", "BTN", "Axx"],
                        "facets": {"preflop_action": "open"} if "tras open" in query else {}}
            if self.invalid_refs:
                return {"answer": "Tras open, continuar.", "source_refs": ["F99"], "insufficient": False}
            if self.unsupported_number:
                return {"answer": "Apostar 75% del bote.", "source_refs": ["F1"], "insufficient": False}
            if self.insufficient:
                return {"insufficient": True}
            return {"answer": json.loads(prompt)["fragments"][0]["content"],
                    "source_refs": ["F1"], "insufficient": False}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name))
        self.model = self.Model()
        self.service = SearchService(self.store, self.model)

    def _sourced_topic(self, document, title, content, action, condition):
        fragment = self.store.add_fragments(document["id"], [
            {"kind": "paragraph", "locator": title, "content": content},
        ])[0]
        topic = self.store.create_topic({"title": title, "summary": "BB vs BTN en flop Axx",
                                         "conditions": condition, "difficulty": "basic"})
        self.store.link_evidence(topic["id"], fragment["id"])
        self.store.set_facets(topic["id"], {"preflop_action": action})
        return topic, fragment

    def test_ambiguity_then_grounded_answer_with_source_and_tree_path(self):
        document, _ = self.store.save_document("lesson.docx", b"source")
        branch = self.store.create_branch("Postflop")
        open_topic, open_fragment = self._sourced_topic(
            document, "BB vs BTN open", "Tras open del BTN, BB juega flop Axx.", "open", "Tras open del BTN")
        self._sourced_topic(document, "BB vs BTN 3bet", "Tras 3bet, BB juega flop Axx.", "3bet", "Tras 3bet")
        self.store.place_topic(open_topic["id"], branch["id"])

        ambiguous = self.service.search({"query": "BB vs BTN en Axx"})
        self.assertEqual(ambiguous["status"], "clarification")
        self.assertEqual(ambiguous["options"], ["3bet", "open"])
        answer = self.service.search({"query": "BB vs BTN en Axx tras open"})
        self.assertEqual(answer["status"], "answered")
        self.assertEqual(answer["source_fragment_ids"], [open_fragment["id"]])
        self.assertEqual([source["id"] for source in answer["sources"]], [open_fragment["id"]])
        self.assertEqual(answer["conditions"][0]["text"], "Tras open del BTN")
        self.assertEqual(answer["topics"][0]["locations"][0]["path"][0]["name"], "Postflop")

    def test_empty_index_no_matches_and_invalid_citations_are_distinct(self):
        self.assertEqual(self.service.search({"query": "BB vs BTN"})["status"], "empty_index")
        document, _ = self.store.save_document("lesson.docx", b"source")
        self._sourced_topic(document, "BB vs BTN", "Tras open, flop Axx.", "open", "Tras open")
        missing = self.service.search({"query": "sin datos"})
        self.assertEqual((missing["status"], missing["reason"]), ("insufficient_coverage", "no_matches"))
        self.model.invalid_refs = True
        with self.assertRaisesRegex(SearchFailure, "source references"):
            self.service.search({"query": "BB vs BTN tras open"})
        self.model.invalid_refs = False
        self.model.unsupported_number = True
        with self.assertRaisesRegex(SearchFailure, "unsupported numeric"):
            self.service.search({"query": "BB vs BTN tras open"})
        self.model.unsupported_number = False
        self.model.insufficient = True
        self.assertEqual(self.service.search({"query": "BB vs BTN tras open"})["reason"],
                         "model_found_no_support")

    def test_semantic_match_can_retrieve_source_when_terms_do_not_match(self):
        document, _ = self.store.save_document("lesson.docx", b"source")
        fragment = self.store.add_fragments(document["id"], [
            {"kind": "paragraph", "locator": "p1", "content": "Defensa de ciega grande"},
        ])[0]
        topic = self.store.create_topic({"title": "Defensa", "difficulty": "basic"})
        self.store.link_evidence(topic["id"], fragment["id"])
        for entry in self.store.pending_embeddings("test"):
            self.store.save_embedding(entry["id"], entry["content"], "test", [1.0, 0.0])
        self.model.embedding_name = "test"
        result = self.service.search({"query": "BB vs BTN"})
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["source_fragment_ids"], [fragment["id"]])
        self.assertEqual(result["retrieval_warnings"], [])


class StudyPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name))
        self.service = StudyPathService(self.store)
        self.document, _ = self.store.save_document("lesson.docx", b"source")

    def sourced_topic(self, title, difficulty, content):
        fragment = self.store.add_fragments(self.document["id"], [
            {"kind": "paragraph", "locator": title, "content": content},
        ])[0]
        topic = self.store.create_topic({"title": title, "difficulty": difficulty})
        self.store.link_evidence(topic["id"], fragment["id"])
        return topic, fragment

    def test_beginner_and_goal_paths_keep_prerequisites_and_source_links(self):
        prerequisite, source_one = self.sourced_topic("Z conceptos", "advanced", "Conceptos base")
        dependent, source_two = self.sourced_topic("A juego Axx", "basic", "Juego en flop Axx")
        self.store.add_prerequisite(dependent["id"], prerequisite["id"])
        branch = self.store.create_branch("Postflop")
        self.store.place_topic(dependent["id"], branch["id"])

        for goal in ("principiante", "Axx"):
            path = self.service.build({"goal": goal})
            self.assertEqual(path["status"], "ready")
            self.assertEqual([step["topic_id"] for step in path["steps"]],
                             [prerequisite["id"], dependent["id"]])
            self.assertIn("A juego Axx", path["steps"][0]["reason"])
            self.assertEqual(path["steps"][0]["sources"][0]["fragment_id"], source_one["id"])
            self.assertEqual(path["steps"][1]["sources"][0]["fragment_id"], source_two["id"])
            self.assertEqual(path["steps"][1]["sources"][0]["document_url"],
                             f"/api/documents/{self.document['id']}/file")
            self.assertEqual(path["steps"][1]["topic_url"], f"/api/topics/{dependent['id']}")
            self.assertEqual(path["steps"][1]["locations"][0]["path"][0]["name"], "Postflop")

    def test_unsourced_prerequisite_blocks_a_sourced_target(self):
        missing = self.store.create_topic({"title": "Concepto sin fuente", "difficulty": "basic"})
        target, _ = self.sourced_topic("Juego Axx", "basic", "Juego en flop Axx")
        self.store.add_prerequisite(target["id"], missing["id"])
        result = self.service.build({"goal": "Axx"})
        self.assertEqual((result["status"], result["reason"]),
                         ("insufficient_coverage", "no_evidence"))
        self.assertEqual(result["steps"], [])
        self.assertEqual(result["excluded"][0]["reason"], "unsourced_prerequisite")
        self.assertEqual(result["excluded"][0]["missing_topic_ids"], [missing["id"]])
        unsourced = self.service.build({"goal": "Concepto sin fuente"})
        self.assertEqual(unsourced["excluded"][0]["reason"], "no_evidence")
        self.assertEqual(self.service.build({"goal": "inexistente"})["reason"], "no_matching_topics")

    def test_image_only_evidence_does_not_create_a_study_step(self):
        image = self.store.add_fragments(self.document["id"], [
            {"kind": "image", "locator": "image1", "content": "", "image_name": "image.png"},
        ])[0]
        topic = self.store.create_topic({"title": "Imagen", "difficulty": "basic"})
        self.store.link_evidence(topic["id"], image["id"])
        self.assertEqual(self.service.build({"goal": "beginner"})["reason"], "no_sourced_topics")

    def test_contradicting_source_alone_does_not_support_a_study_step(self):
        fragment = self.store.add_fragments(self.document["id"], [
            {"kind": "paragraph", "locator": "p1", "content": "Ejemplo Axx"},
        ])[0]
        topic = self.store.create_topic({"title": "Axx", "difficulty": "basic"})
        self.store.link_evidence(topic["id"], fragment["id"], "contradicts")
        self.assertEqual(self.service.build({"goal": "Axx"})["reason"], "no_sourced_topics")


class FakeModel:
    configured = True

    def __init__(self, invalid=False):
        self.invalid = invalid

    def generate_json(self, system, prompt):
        def topic(title, text, refs, difficulty):
            return {"title": title, "summary": text,
                    "explanation_blocks": [{"text": text, "source_refs": refs}],
                    "difficulty": difficulty, "source_refs": refs,
                    "examples": [{"text": "Ejemplo didáctico sin datos estratégicos adicionales.", "origin": "generated", "source_refs": []}],
                    "facets": {"street": None}, "unknowns": ["Acción preflop no indicada"],
                    "prerequisite_proposals": []}
        if self.invalid:
            return {"topics": [topic("Posiciones", "Posiciones", ["F1"], "basic"),
                               topic("Invención", "Apostar 75%", ["F1"], "advanced")]}
        return {"topics": [topic("Posiciones", "Posiciones", ["F1"], "basic"),
                           topic("BTN y BB", "BTN y BB", ["F2"], "intermediate")]}


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.store = Store(self.path)
        self.document, _ = self.store.save_document("lesson.docx", sample_docx())
        self.fragments = self.store.add_fragments(self.document["id"], [
            {"kind": "paragraph", "locator": "p1", "content": "Posiciones"},
            {"kind": "table", "locator": "t1", "content": "BTN y BB"},
        ])

    def test_two_sourced_topics_persist_and_find_similar_candidate(self):
        existing = self.store.create_topic({"title": "Posiciones", "summary": "Posiciones", "difficulty": "basic"})
        topics = TopicProcessor(self.store, FakeModel()).process(self.document["id"])
        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[0]["claims"][0]["source_fragment_ids"], [self.fragments[0]["id"]])
        self.assertEqual(topics[0]["examples"][0]["origin"], "generated")
        self.assertEqual(topics[0]["facets"]["street"], None)
        self.assertEqual(topics[0]["similar_candidates"][0]["candidate_id"], existing["id"])
        self.assertEqual(len(Store(self.path).topics_for_document(self.document["id"])), 2)

    def test_unsupported_numeric_detail_keeps_batch_empty(self):
        with self.assertRaisesRegex(StoreError, "unsupported numeric"):
            TopicProcessor(self.store, FakeModel(invalid=True)).process(self.document["id"])
        self.assertEqual(self.store.topics_for_document(self.document["id"]), [])
        self.assertFalse(self.store.analysis_exists(self.document["id"]))

    def test_api_analyzes_extracted_document(self):
        server = PokerRootsServer(("127.0.0.1", 0), self.store, FakeModel())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(f"http://127.0.0.1:{server.server_port}/api/documents/{self.document['id']}/analyze",
                              data=b"", method="POST")
            self.store.set_document_state(self.document["id"], "extracted")
            with urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 202)
            for _ in range(100):
                current = self.store.get_document(self.document["id"])
                if current["state"] in {"completed", "failed"}:
                    break
                time.sleep(0.01)
            self.assertEqual(current["state"], "completed", current["error"])
            self.assertEqual(len(self.store.topics_for_document(self.document["id"])), 2)
        finally:
            server.shutdown()
            server.server_close()

    def test_import_runs_extraction_and_analysis_automatically(self):
        service = ImportService(self.store, FakeModel())
        try:
            imported, created = service.submit("second.docx", sample_docx() + b"\n")
            self.assertTrue(created)
            for _ in range(100):
                current = self.store.get_document(imported["id"])
                if current["state"] in {"completed", "failed"}:
                    break
                time.sleep(0.01)
            self.assertEqual(current["state"], "completed", current["error"])
            self.assertEqual(len(self.store.topics_for_document(imported["id"])), 2)
        finally:
            service.close()


if __name__ == "__main__":
    unittest.main()
