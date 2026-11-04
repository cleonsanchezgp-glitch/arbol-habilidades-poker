"""Disposable API fixture for the optional browser smoke test."""

import json
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from backend.api import Handler, PokerRootsServer
from backend.storage import Store
from test_first_version_flow import FlowModel
from test_storage_api import sample_docx


def main():
    with tempfile.TemporaryDirectory(prefix="poker-roots-ui-") as directory:
        root = Path(directory)
        fixture = root / "lesson.docx"
        fixture.write_bytes(sample_docx())
        store = Store(root / "data")
        document, _ = store.save_document("lesson.docx", fixture.read_bytes())
        fragments = store.add_fragments(document["id"], [
            {"kind": "paragraph", "locator": "p1", "content": "Posiciones"},
            {"kind": "table", "locator": "t1", "content": "BTN y BB"},
        ])
        branches = [store.create_branch("Fundamentos")]
        for name in ("Preflop", "Postflop", "Flop Axx"):
            branches.append(store.create_branch(name, branches[-1]["id"]))
        topics = [
            store.create_topic({"title": "Posiciones", "summary": "BTN y BB", "difficulty": "basic"}),
            store.create_topic({"title": "Juego de ciegas", "summary": "Tema intermedio de prueba", "difficulty": "intermediate"}),
            store.create_topic({"title": "Flop Axx avanzado", "summary": "Tema avanzado de prueba", "difficulty": "advanced"}),
        ]
        for index, topic in enumerate(topics):
            store.link_evidence(topic["id"], fragments[min(index, 1)]["id"])
            store.place_topic(topic["id"], branches[min(index + 1, 3)]["id"])
            if index:
                store.add_prerequisite(topic["id"], topics[index - 1]["id"])

        class QuietHandler(Handler):
            def log_message(self, format, *args):
                pass

        server = PokerRootsServer(("127.0.0.1", 0), store, FlowModel())
        server.RequestHandlerClass = QuietHandler
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(json.dumps({"url": f"http://127.0.0.1:{server.server_port}/", "fixture": str(fixture)}), flush=True)
        try:
            sys.stdin.readline()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    main()
