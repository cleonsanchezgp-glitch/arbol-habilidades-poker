"""Local embedding refresh; lexical entries are committed by the store."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .local_model import LocalModel
from .storage import Store


class RetrievalIndexer:
    def __init__(self, store: Store, model: LocalModel):
        self.store = store
        self.model = model
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="retrieval-index")
        self.schedule()

    def close(self) -> None:
        self.pool.shutdown(wait=True, cancel_futures=True)

    def schedule(self) -> None:
        if getattr(self.model, "embedding_name", ""):
            self.pool.submit(self.refresh)

    def refresh(self) -> dict:
        """Embed current pending entries without holding a database write lock during inference."""
        name = getattr(self.model, "embedding_name", "")
        if not name:
            return self.store.index_status()
        while True:
            pending = self.store.pending_embeddings(name, 50)
            if not pending:
                break
            for entry in pending:
                try:
                    vector = self.model.embed(entry["content"])
                except Exception as exc:
                    self.store.save_embedding(entry["id"], entry["content"], name, None, str(exc)[:300])
                else:
                    self.store.save_embedding(entry["id"], entry["content"], name, vector)
        return self.store.index_status(name)
