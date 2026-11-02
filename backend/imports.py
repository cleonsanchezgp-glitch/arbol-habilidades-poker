"""Background DOCX extraction jobs and their persistent states."""

from __future__ import annotations

import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import PurePosixPath

from .docx_extract import extract_docx, validate_docx
from .local_model import LocalModel, ModelUnavailable
from .storage import Store, StoreError
from .topic_processor import TopicProcessor


class ImportService:
    def __init__(self, store: Store, model: LocalModel | None = None):
        self.store = store
        self.model = model or LocalModel()
        self.processor = TopicProcessor(store, self.model)
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="docx-import")
        for document in store.list_documents():
            if document["state"] in {"queued", "extracting", "analyzing"}:
                if store.analysis_exists(document["id"]):
                    store.set_document_state(document["id"], "completed", document["warnings"])
                else:
                    store.set_document_state(document["id"], "failed", document["warnings"], "Processing was interrupted; retry")

    def close(self) -> None:
        self.pool.shutdown(wait=True, cancel_futures=True)

    def submit(self, filename: str, content: bytes) -> tuple[dict, bool]:
        validate_docx(content, filename)
        document, created = self.store.save_document(filename, content, state="queued")
        if created:
            self.pool.submit(self._process, document["id"])
        return document, created

    def retry(self, document_id: str) -> dict:
        document = self.store.get_document(document_id)
        if document["state"] != "failed":
            raise StoreError("Only failed imports can be retried")
        if self.store.analysis_exists(document_id):
            return self.store.set_document_state(document_id, "completed", document["warnings"])
        if self.store.list_fragments(document_id):
            self.store.set_document_state(document_id, "analyzing", document["warnings"])
            self.pool.submit(self._analyze, document_id)
        else:
            self.store.set_document_state(document_id, "queued", document["warnings"])
            self.pool.submit(self._process, document_id)
        return self.store.get_document(document_id)

    def analyze(self, document_id: str) -> dict:
        document = self.store.get_document(document_id)
        if document["state"] not in {"extracted", "awaiting_model"}:
            raise StoreError("Document is not ready for analysis")
        if not self.store.list_fragments(document_id):
            raise StoreError("Document has no extracted fragments")
        if not self.model.configured:
            raise ModelUnavailable("Set POKER_ROOTS_MODEL to an installed local model and restart the API")
        self.store.set_document_state(document_id, "analyzing", document["warnings"])
        self.pool.submit(self._analyze, document_id)
        return self.store.get_document(document_id)

    def _analyze(self, document_id: str) -> None:
        try:
            document = self.store.get_document(document_id)
            if self.store.analysis_exists(document_id):
                self.store.set_document_state(document_id, "completed", document["warnings"])
                return
            if not self.model.configured:
                self.store.set_document_state(document_id, "awaiting_model", document["warnings"],
                                              "Set POKER_ROOTS_MODEL to an installed local model and restart the API")
                return
            self.store.set_document_state(document_id, "analyzing", document["warnings"])
            self.processor.process(document_id)
            self.store.set_document_state(document_id, "completed", document["warnings"])
        except Exception as exc:
            try:
                self.store.set_document_state(document_id, "failed", error=str(exc))
            except Exception:
                pass

    def _process(self, document_id: str) -> None:
        created_images = []
        try:
            document = self.store.set_document_state(document_id, "extracting")
            content = self.store.original_path(document_id).read_bytes()
            extracted = extract_docx(content, document["filename"])
            old_images = {fragment["image_name"] for fragment in self.store.list_fragments(document_id) if fragment["image_name"]}
            image_names = {}
            for media_path, image_bytes in extracted.images.items():
                suffix = PurePosixPath(media_path).suffix.lower()
                image_name = f"{document_id}-{uuid.uuid4().hex[:12]}{suffix}"
                target = self.store.images_dir / image_name
                fd, temporary = tempfile.mkstemp(prefix="image-", dir=self.store.images_dir)
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(image_bytes)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, target)
                    created_images.append(target)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
                image_names[media_path] = image_name
            fragments = []
            for fragment in extracted.fragments:
                item = {key: value for key, value in fragment.items() if key != "media_path"}
                if "media_path" in fragment:
                    item["image_name"] = image_names[fragment["media_path"]]
                fragments.append(item)
            self.store.replace_fragments(document_id, fragments)
            for image_name in old_images - set(image_names.values()):
                (self.store.images_dir / image_name).unlink(missing_ok=True)
            self.store.set_document_state(document_id, "extracted", extracted.warnings)
            self._analyze(document_id)
        except Exception as exc:
            for path in created_images:
                path.unlink(missing_ok=True)
            try:
                self.store.set_document_state(document_id, "failed", error=str(exc))
            except Exception:
                pass
