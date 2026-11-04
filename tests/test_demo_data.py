"""The optional demo library is valid, sourced, and safe to seed twice."""

import tempfile
import unittest
from pathlib import Path

from backend.demo_data import seed
from backend.docx_extract import validate_docx
from backend.storage import Store


class DemoDataTests(unittest.TestCase):
    def test_seed_is_valid_sourced_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory))
            self.assertEqual(seed(store)["status"], "seeded")
            self.assertEqual(seed(store)["status"], "already_seeded")
            documents = store.list_documents()
            topics = store.list_topics()
            self.assertEqual((len(documents), len(topics), len(store.list_branches())), (2, 6, 6))
            for document in documents:
                validate_docx(store.original_path(document["id"]).read_bytes(), document["filename"])
                self.assertEqual(document["state"], "extracted")
                self.assertTrue(store.list_fragments(document["id"]))
                self.assertTrue(store.topics_for_document(document["id"]))
            self.assertTrue(all(topic["evidence"] and topic["placements"] for topic in topics))
            self.assertTrue(any(topic["prerequisites"] for topic in topics))
            self.assertTrue(any(topic["similar_candidates"] for topic in topics))
            self.assertTrue(all(topic["title"].startswith("Muestra · ") for topic in topics))

    def test_empty_only_keeps_existing_library_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory))
            existing = store.create_topic({"title": "Tema propio"})
            self.assertEqual(seed(store, empty_only=True)["status"], "skipped_nonempty")
            self.assertEqual([topic["id"] for topic in store.list_topics()], [existing["id"]])
            self.assertEqual(store.list_documents(), [])


if __name__ == "__main__":
    unittest.main()
