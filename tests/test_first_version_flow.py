"""Repeatable first-version flow with a synthetic document and local fake model."""

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.api import PokerRootsServer
from backend.storage import Store
from test_storage_api import sample_docx


class FlowModel:
    configured = True
    embedding_name = ""

    def generate_json(self, system, prompt):
        if system.startswith("Interpreta"):
            return {"terms": [json.loads(prompt)["query"]], "facets": {}}
        if system.startswith("Responde"):
            return {"answer": "BTN y BB aparecen en la fuente consultada.",
                    "source_refs": ["F1"], "insufficient": False}

        def topic(title, summary, ref, difficulty):
            return {
                "title": title, "summary": summary,
                "explanation_blocks": [{"text": summary, "source_refs": [ref]}],
                "difficulty": difficulty, "source_refs": [ref],
                "examples": [], "facets": {"street": None}, "unknowns": [],
                "prerequisite_proposals": [],
            }

        return {"topics": [
            topic("Posiciones", "Posiciones", "F1", "basic"),
            topic("BTN y BB", "BTN y BB", "F2", "intermediate"),
        ]}


class FirstVersionFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.start_server()
        self.addCleanup(self.stop_server)

    def start_server(self):
        self.store = Store(self.path)
        self.server = PokerRootsServer(("127.0.0.1", 0), self.store, FlowModel())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def stop_server(self):
        if getattr(self, "server", None):
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=5)
            self.server = None

    def request(self, method, path, payload=None, raw=None, headers=None):
        body = raw if raw is not None else (json.dumps(payload).encode("utf-8") if payload is not None else None)
        request = Request(self.base + path, data=body, method=method,
                          headers=headers or ({"Content-Type": "application/json"} if payload is not None else {}))
        try:
            with urlopen(request, timeout=10) as response:
                content = response.read()
                return response.status, json.loads(content) if response.headers.get_content_type() == "application/json" else content
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def wait_document(self, document_id):
        for _ in range(100):
            document = self.request("GET", f"/api/documents/{document_id}")[1]
            if document["state"] in {"completed", "failed", "awaiting_model"}:
                return document
            time.sleep(0.02)
        self.fail("Document remained in a processing state")

    def test_import_edit_search_and_restart(self):
        original = sample_docx()
        status, imported = self.request("POST", "/api/documents", raw=original,
                                        headers={"X-Filename": "Lecci%C3%B3n.docx"})
        self.assertEqual(status, 202)
        document = self.wait_document(imported["document"]["id"])
        self.assertEqual(document["state"], "completed", document["error"])
        self.assertEqual(document["filename"], "Lecci\u00f3n.docx")
        document_id = document["id"]
        fragments = self.request("GET", f"/api/documents/{document_id}/fragments")[1]["fragments"]
        self.assertEqual([item["kind"] for item in fragments], ["paragraph", "table", "paragraph", "image"])
        imported_topics = self.request("GET", f"/api/documents/{document_id}/topics")[1]["topics"]
        self.assertEqual({item["title"] for item in imported_topics}, {"Posiciones", "BTN y BB"})
        self.assertTrue(all(item["evidence"] for item in imported_topics))
        topics = {item["title"]: item for item in imported_topics}

        status, branch = self.request("POST", "/api/branches", {"name": "Postflop"})
        self.assertEqual(status, 201)
        topic_id = topics["BTN y BB"]["id"]
        prerequisite_id = topics["Posiciones"]["id"]
        status, edited = self.request("PUT", f"/api/topics/{topic_id}", {
            "title": "BTN y BB corregido", "summary": "BTN y BB corregido",
            "difficulty": "advanced", "facets": {"street": "flop"},
            "placements": [branch["id"]], "prerequisites": [prerequisite_id],
        })
        self.assertEqual(status, 200)
        self.assertEqual(edited["facets"]["street"], "flop")
        self.assertEqual(edited["prerequisites"], [prerequisite_id])
        tree = self.request("GET", "/api/tree")[1]
        self.assertLess([item["id"] for item in tree["topics"]].index(prerequisite_id),
                        [item["id"] for item in tree["topics"]].index(topic_id))
        self.assertEqual(self.request("GET", f"/api/topics/{topic_id}/locations")[1]["locations"][0]["path"][-1]["name"], "Postflop")

        status, answer = self.request("POST", "/api/search", {"query": "BTN y BB corregido"})
        self.assertEqual(status, 200)
        self.assertEqual(answer["status"], "answered")
        self.assertTrue(answer["source_fragment_ids"])
        self.assertIn(topic_id, {item["id"] for item in answer["topics"]})
        self.assertTrue(any(item["id"] in answer["source_fragment_ids"] for item in fragments))
        status, path = self.request("POST", "/api/study-path", {"goal": "BTN y BB corregido"})
        self.assertEqual((status, path["status"]), (200, "ready"))
        self.assertEqual([item["topic_id"] for item in path["steps"]], [prerequisite_id, topic_id])

        status, invalid = self.request("PUT", f"/api/topics/{prerequisite_id}", {
            "summary": "Must not persist", "prerequisites": [topic_id],
        })
        self.assertEqual(status, 400)
        self.assertIn("cycle", invalid["error"])
        self.assertEqual(self.request("GET", f"/api/topics/{prerequisite_id}")[1]["summary"], "Posiciones")

        self.stop_server()
        self.start_server()
        self.assertEqual(self.request("GET", f"/api/documents/{document_id}/file")[1], original)
        reopened = self.request("GET", f"/api/topics/{topic_id}")[1]
        self.assertEqual((reopened["summary"], reopened["difficulty"]), ("BTN y BB corregido", "advanced"))
        self.assertEqual(reopened["placements"], [branch["id"]])
        self.assertEqual(reopened["prerequisites"], [prerequisite_id])
        self.assertTrue(reopened["evidence"])
        self.assertEqual(self.request("POST", "/api/search", {"query": "BTN y BB corregido"})[1]["status"], "answered")

    def test_invalid_import_and_empty_states(self):
        self.assertEqual(self.request("GET", "/api/tree")[1]["topics"], [])
        status, search = self.request("POST", "/api/search", {"query": "sin fuente"})
        self.assertEqual((status, search["status"]), (200, "empty_index"))
        status, path = self.request("POST", "/api/study-path", {"goal": "principiante"})
        self.assertEqual((status, path["status"]), (200, "insufficient_coverage"))
        status, error = self.request("POST", "/api/documents", raw=b"not a docx",
                                     headers={"X-Filename": "broken.docx"})
        self.assertEqual(status, 400)
        self.assertIn("DOCX", error["error"])
        self.assertEqual(self.request("GET", "/api/documents")[1]["documents"], [])


if __name__ == "__main__":
    unittest.main()
