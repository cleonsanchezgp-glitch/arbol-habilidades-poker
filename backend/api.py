"""Small loopback HTTP API with no third-party runtime dependency."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .imports import ImportService
from .local_model import LocalModel, ModelUnavailable
from .retrieval_index import RetrievalIndexer
from .search import SearchFailure, SearchService
from .study_path import StudyPathService
from .storage import Store, StoreError


MAX_JSON_BYTES = 1_000_000
MAX_DOCUMENT_BYTES = 25_000_000
SENT_FILE = object()
UI_ROOT = Path(__file__).resolve().parent.parent / "poker-roots-boceto" / "poker-roots"
UI_ASSETS = {f"drawn-{index}.jpg" for index in range(4)}


class PokerRootsServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], store: Store, model: LocalModel | None = None):
        super().__init__(address, Handler)
        self.store = store
        selected_model = model or LocalModel()
        self.indexer = RetrievalIndexer(store, selected_model)
        self.imports = ImportService(store, selected_model, self.indexer)
        self.search = SearchService(store, selected_model)
        self.study_path = StudyPathService(store)

    def server_close(self) -> None:
        self.imports.close()
        self.indexer.close()
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    server: PokerRootsServer

    def log_message(self, format: str, *args: object) -> None:
        # Do not log request bodies, document content, or future model prompts.
        super().log_message(format, *args)

    def _respond(self, status: HTTPStatus, data: object) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _file(self, path: Path, filename: str, disposition: str = "attachment") -> None:
        if not path.is_file():
            raise StoreError("Original document is unavailable")
        content = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "application/octet-stream")
        self.send_header("Content-Disposition", f"{disposition}; filename*=UTF-8''{_quote_filename(filename)}")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def _body(self, maximum: int) -> bytes:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise StoreError("Content-Length is required")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise StoreError("Invalid Content-Length") from exc
        if length < 0 or length > maximum:
            raise StoreError("Request body is too large")
        body = self.rfile.read(length)
        if len(body) != length:
            raise StoreError("Incomplete request body")
        return body

    def _json(self) -> dict:
        if self.headers.get_content_type() != "application/json":
            raise StoreError("Content-Type must be application/json")
        try:
            data = json.loads(self._body(MAX_JSON_BYTES))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise StoreError("Invalid JSON body") from exc
        if not isinstance(data, dict):
            raise StoreError("JSON body must be an object")
        return data

    def _segments(self) -> list[str]:
        path = urlsplit(self.path).path
        return [part for part in path.split("/") if part]

    def _handle(self, method: str) -> None:
        try:
            result = self._route(method, self._segments())
            if method in {"POST", "PUT", "DELETE"} and self._segments() not in (["api", "search"], ["api", "study-path"]):
                self.server.indexer.schedule()
            if result is SENT_FILE:
                return
            if result is None:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
            elif isinstance(result, tuple):
                self._respond(result[0], result[1])
            else:
                self._respond(HTTPStatus.OK, result)
        except ModelUnavailable as exc:
            self._respond(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc), "status": "model_unavailable"})
        except SearchFailure as exc:
            self._respond(HTTPStatus.BAD_GATEWAY, {"error": str(exc), "status": "search_failed"})
        except StoreError as exc:
            status = HTTPStatus.NOT_FOUND if "not found" in str(exc).lower() else HTTPStatus.BAD_REQUEST
            self._respond(status, {"error": str(exc)})
        except Exception:
            self._respond(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Internal server error"})

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")

    def do_PUT(self) -> None:
        self._handle("PUT")

    def do_DELETE(self) -> None:
        self._handle("DELETE")

    def _route(self, method: str, parts: list[str]):
        store = self.server.store
        if method == "GET":
            static = {(): "index.html", ("app.js",): "app.js", ("styles.css",): "styles.css"}
            name = static.get(tuple(parts))
            if name:
                self._file(UI_ROOT / name, name, "inline")
                return SENT_FILE
            if len(parts) == 2 and parts[0] == "assets" and parts[1] in UI_ASSETS:
                self._file(UI_ROOT / "assets" / parts[1], parts[1], "inline")
                return SENT_FILE
        if parts == ["api", "health"] and method == "GET":
            return {"status": "ok", "database_version": 3, "model_configured": self.server.imports.model.configured}
        if parts == ["api", "search"] and method == "POST":
            return self.server.search.search(self._json())
        if parts == ["api", "study-path"] and method == "POST":
            return self.server.study_path.build(self._json())
        if parts == ["api", "index", "status"] and method == "GET":
            return store.index_status(getattr(self.server.indexer.model, "embedding_name", ""))
        if parts == ["api", "index", "retry"] and method == "POST":
            store.retry_failed_embeddings()
            self.server.indexer.schedule()
            return HTTPStatus.ACCEPTED, store.index_status(getattr(self.server.indexer.model, "embedding_name", ""))
        if parts == ["api", "documents"]:
            if method == "GET":
                return {"documents": store.list_documents()}
            if method == "POST":
                filename = self.headers.get("X-Filename", "")
                if not filename:
                    raise StoreError("X-Filename is required")
                document, created = self.server.imports.submit(filename, self._body(MAX_DOCUMENT_BYTES))
                return (HTTPStatus.ACCEPTED if created else HTTPStatus.OK, {"document": document, "created": created})
        if len(parts) >= 3 and parts[:2] == ["api", "documents"]:
            document_id = parts[2]
            if len(parts) == 3 and method == "GET":
                return store.get_document(document_id)
            if len(parts) == 4 and parts[3] == "file" and method == "GET":
                doc = store.get_document(document_id)
                self._file(store.original_path(document_id), doc["filename"])
                return SENT_FILE
            if len(parts) == 4 and parts[3] == "fragments" and method == "GET":
                return {"fragments": store.list_fragments(document_id)}
            if len(parts) == 4 and parts[3] == "topics" and method == "GET":
                return {"topics": store.topics_for_document(document_id)}
            if len(parts) == 4 and parts[3] == "analyze" and method == "POST":
                return HTTPStatus.ACCEPTED, {"document": self.server.imports.analyze(document_id)}
            if len(parts) == 4 and parts[3] == "retry" and method == "POST":
                return HTTPStatus.ACCEPTED, {"document": self.server.imports.retry(document_id)}
            if len(parts) == 5 and parts[3] == "images" and method == "GET":
                self._file(store.image_path(document_id, parts[4]), parts[4], "inline")
                return SENT_FILE
        if parts == ["api", "topics"]:
            if method == "GET":
                return {"topics": store.list_topics()}
            if method == "POST":
                return HTTPStatus.CREATED, store.create_topic(self._json())
        if parts == ["api", "tree"] and method == "GET":
            return store.learning_tree()
        if len(parts) >= 3 and parts[:2] == ["api", "topics"]:
            topic_id = parts[2]
            if len(parts) == 3:
                if method == "GET":
                    return store.get_topic(topic_id)
                if method == "PUT":
                    return store.update_topic(topic_id, self._json())
            if len(parts) == 4 and parts[3] == "locations" and method == "GET":
                return store.topic_locations(topic_id)
            if len(parts) == 4 and parts[3] == "facets" and method == "PUT":
                return store.set_facets(topic_id, self._json())
            if len(parts) == 4 and parts[3] == "evidence" and method == "POST":
                data = self._json()
                return store.link_evidence(topic_id, data.get("fragment_id", ""), data.get("role", "supports"))
            if len(parts) == 4 and parts[3] == "placements" and method == "POST":
                return store.place_topic(topic_id, self._json().get("branch_id", ""))
            if len(parts) == 5 and parts[3] == "placements" and method == "DELETE":
                return store.remove_placement(topic_id, parts[4])
            if len(parts) == 4 and parts[3] == "prerequisites" and method == "POST":
                return store.add_prerequisite(topic_id, self._json().get("prerequisite_id", ""))
            if len(parts) == 5 and parts[3] == "prerequisites" and method == "DELETE":
                return store.remove_prerequisite(topic_id, parts[4])
        if parts == ["api", "branches"]:
            if method == "GET":
                return {"branches": store.list_branches()}
            if method == "POST":
                data = self._json()
                return HTTPStatus.CREATED, store.create_branch(data.get("name", ""), data.get("parent_id"), data.get("sort_order", 0))
        return None


def _quote_filename(filename: str) -> str:
    from urllib.parse import quote

    return quote(filename, safe="")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Poker Roots API")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address; loopback is the default")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path, default=None)
    args = parser.parse_args()
    store = Store(args.data_dir)
    server = PokerRootsServer((args.host, args.port), store)
    print(f"Poker Roots API: http://{args.host}:{server.server_port}/api/health", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
