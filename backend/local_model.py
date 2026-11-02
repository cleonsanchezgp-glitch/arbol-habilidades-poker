"""Loopback-only adapter for an Ollama-compatible local generation endpoint."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .storage import StoreError


class ModelUnavailable(StoreError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        raise ModelUnavailable("Local model endpoint attempted a redirect")


class LocalModel:
    def __init__(self, name: str | None = None, base_url: str | None = None):
        self.name = name if name is not None else os.environ.get("POKER_ROOTS_MODEL", "").strip()
        self.base_url = (base_url or os.environ.get("POKER_ROOTS_OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        parsed = urlsplit(self.base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise StoreError("Local model URL must be an HTTP loopback address")

    @property
    def configured(self) -> bool:
        return bool(self.name)

    def generate_json(self, system: str, prompt: str) -> dict:
        if not self.name:
            raise ModelUnavailable("Set POKER_ROOTS_MODEL to an installed local model and restart the API")
        payload = json.dumps({"model": self.name, "system": system, "prompt": prompt,
                              "format": "json", "stream": False}, ensure_ascii=False).encode("utf-8")
        request = Request(self.base_url + "/api/generate", payload, {"Content-Type": "application/json"}, method="POST")
        try:
            with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=180) as response:
                result = json.load(response)
        except HTTPError as exc:
            with exc:
                detail = exc.read(500).decode("utf-8", "replace")
            raise ModelUnavailable(f"Local model returned HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ModelUnavailable("Local model is unavailable; check that its service and selected model are running") from exc
        except (ValueError, UnicodeError) as exc:
            raise StoreError("Local model returned an invalid API response") from exc
        if not isinstance(result, dict) or not isinstance(result.get("response"), str):
            raise StoreError("Local model response is missing generated text")
        try:
            generated = json.loads(result["response"])
        except json.JSONDecodeError as exc:
            raise StoreError("Local model did not return valid structured JSON") from exc
        if not isinstance(generated, dict):
            raise StoreError("Local model result must be a JSON object")
        return generated
