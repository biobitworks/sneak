"""Live Cognee Cloud client used as Sneak working-memory data storage."""

from __future__ import annotations

import json
import os
import re
import ipaddress
import urllib.parse
import uuid
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from .secrets import export_to_environ


class CogneeClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        dataset: str = "sneak_working_memory",
    ):
        export_to_environ()
        env_base = os.environ.get("COGNEE_BASE_URL", "")
        env_key = os.environ.get("COGNEE_API_KEY", "")
        self.base_url = (env_base if base_url is None else base_url).rstrip("/")
        if self.base_url:
            parsed = urllib.parse.urlsplit(self.base_url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("Cognee endpoint must be an absolute HTTPS URL or loopback HTTP URL")
            if parsed.scheme == "http":
                host = parsed.hostname or ""
                try:
                    loopback = ipaddress.ip_address(host).is_loopback
                except ValueError:
                    loopback = host == "localhost"
                if not loopback:
                    raise ValueError("Remote Cognee transport requires HTTPS")
        self.api_key = env_key if api_key is None else api_key
        self.dataset = dataset

    @property
    def base(self) -> str:
        """Backward-compatible readonly endpoint identity."""
        return self.base_url

    @property
    def available(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: Any = None,
        raw: Optional[bytes] = None,
        content_type: Optional[str] = None,
        timeout: float = 180.0,
    ) -> tuple[int, Any]:
        headers = {"X-Api-Key": self.api_key, "Accept": "application/json"}
        body = raw
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if content_type:
            headers["Content-Type"] = content_type
        req = urllib.request.Request(
            self.base_url + path, data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_response = resp.read(2 * 1024 * 1024 + 1)
                if len(raw_response) > 2 * 1024 * 1024:
                    raise ValueError("Cognee response exceeds bounded size")
                raw_body = raw_response.decode("utf-8")
                return resp.status, json.loads(raw_body) if raw_body else None
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(err)
            except json.JSONDecodeError:
                parsed = {"error": err[:500]}
            return e.code, parsed

    def health(self) -> dict[str, Any]:
        status, body = self._request("GET", "/health")
        return {"http_status": status, "body": body, "live": status == 200}

    def add_text(self, texts: list[str] | str, dataset: Optional[str] = None) -> dict[str, Any]:
        """Support both Cognee JSON add_text and prior multipart /add contracts.

        A scalar is a text file upload; a list uses Cognee's JSON text-ingest API.
        Remote writes are opt-in at the calling workflow and must contain approved text.
        """
        ds = dataset or self.dataset
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", ds):
            raise ValueError("unsafe Cognee dataset name")
        if isinstance(texts, str):
            if not texts or len(texts.encode("utf-8")) > 1024 * 1024:
                raise ValueError("empty or oversized Cognee text")
            boundary = "sneak-" + uuid.uuid4().hex
            prefix = (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"datasetName\"\r\n\r\n"
                f"{ds}\r\n--{boundary}\r\n"
                "Content-Disposition: form-data; name=\"data\"; filename=\"synthetic-review.txt\"\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n\r\n"
            ).encode("utf-8")
            raw = prefix + texts.encode("utf-8") + f"\r\n--{boundary}--\r\n".encode("ascii")
            status, body = self._request(
                "POST", "/api/v1/add", raw=raw,
                content_type=f"multipart/form-data; boundary={boundary}")
        else:
            if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
                raise ValueError("texts must be a string or list of strings")
            status, body = self._request(
                "POST", "/api/v1/add_text",
                data={"datasetName": ds, "textData": texts})
        return {"http_status": status, "body": body, "ok": status == 200}

    def cognify(self, dataset: Optional[str] = None) -> dict[str, Any]:
        status, body = self._request(
            "POST",
            "/api/v1/cognify",
            data={"datasets": [dataset or self.dataset]},
        )
        return {"http_status": status, "body": body, "ok": status == 200}

    def search(
        self,
        query: str,
        dataset: Optional[str] = None,
        *,
        search_type: str = "CHUNKS",
        top_k: int = 5,
    ) -> dict[str, Any]:
        status, body = self._request(
            "POST",
            "/api/v1/search",
            data={
                "query": query,
                "datasets": [dataset or self.dataset],
                "searchType": search_type,
                "top_k": top_k,
            },
        )
        hits: list[dict[str, Any]] = []
        if status == 200 and isinstance(body, list):
            for row in body:
                for item in row.get("search_result") or []:
                    if isinstance(item, dict):
                        hits.append(
                            {
                                "id": item.get("id"),
                                "text": item.get("text") or item.get("answer"),
                                "dataset": row.get("dataset_name"),
                            }
                        )
                    elif isinstance(item, str):
                        hits.append({"text": item, "dataset": row.get("dataset_name")})
        return {"http_status": status, "body": body, "hits": hits, "ok": status == 200}

    def remember_and_wait(
        self,
        text: str,
        *,
        dataset: Optional[str] = None,
        wait_seconds: float = 60.0,
        query: Optional[str] = None,
    ) -> dict[str, Any]:
        """Write text, cognify, poll until searchable (or timeout)."""
        ds = dataset or self.dataset
        added = self.add_text([text], dataset=ds)
        cognified = self.cognify(dataset=ds)
        q = query or text[:120]
        deadline = time.time() + wait_seconds
        last: dict[str, Any] = {}
        while time.time() < deadline:
            last = self.search(q, dataset=ds, search_type="CHUNKS")
            if last.get("hits"):
                break
            time.sleep(2)
        return {
            "dataset": ds,
            "add": {"http_status": added["http_status"], "ok": added["ok"]},
            "cognify": {"http_status": cognified["http_status"], "ok": cognified["ok"]},
            "search": {
                "http_status": last.get("http_status"),
                "hit_count": len(last.get("hits") or []),
                "hits": last.get("hits") or [],
                "ok": bool(last.get("hits")),
            },
            "observed_outcome": "PASS" if last.get("hits") else "PENDING",
        }
