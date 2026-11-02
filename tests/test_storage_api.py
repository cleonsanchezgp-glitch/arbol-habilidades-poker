import json
import io
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.api import PokerRootsServer
from backend.docx_extract import extract_docx
from backend.imports import ImportService
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


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name))
        self.server = PokerRootsServer(("127.0.0.1", 0), self.store)
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
