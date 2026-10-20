"""Minimal Cognee Cloud/OSS HTTP adapter. Secrets are process-only, never logged."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
import uuid

class CogneeError(RuntimeError):
    pass

class CogneeClient:
    def __init__(self, base_url=None, api_key=None):
        self.base = (base_url or os.environ.get("COGNEE_BASE_URL") or "").rstrip("/")
        self.key = api_key if api_key is not None else os.environ.get("COGNEE_API_KEY")
        if not (self.base.startswith("https://") or self.base.startswith("http://127.0.0.1:") or self.base.startswith("http://localhost:")):
            raise ValueError("Cognee endpoint must use TLS, unless loopback")
    def _request(self, path, body=None, content_type=None):
        headers = {"Accept": "application/json"}
        if self.key: headers["X-Api-Key"] = self.key
        if content_type: headers["Content-Type"] = content_type
        req = urllib.request.Request(self.base + path, data=body, headers=headers,
                                     method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                raw = response.read(262144)
                try: result = json.loads(raw) if raw else None
                except ValueError: result = {"response_type": "non_json"}
                return {"http_status": response.status, "result": result}
        except urllib.error.HTTPError as exc:
            raise CogneeError("Cognee HTTP status " + str(exc.code)) from None
        except urllib.error.URLError:
            raise CogneeError("Cognee transport unavailable") from None
    def health(self):
        return self._request("/health")
    def datasets(self):
        return self._request("/api/v1/datasets")
    def add_text(self, text, dataset):
        boundary = "sneak-" + uuid.uuid4().hex
        def part(name, value):
            return (("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + name +
                     "\"\r\n\r\n" + value + "\r\n").encode("utf-8"))
        payload = (("--" + boundary + "\r\nContent-Disposition: form-data; name=\"data\"; filename=\"synthetic-review.txt\"\r\nContent-Type: text/plain\r\n\r\n").encode() + text.encode("utf-8") + b"\r\n" + part("datasetName", dataset) + ("--" + boundary + "--\r\n").encode())
        return self._request("/api/v1/add", payload, "multipart/form-data; boundary=" + boundary)
    def cognify(self, dataset):
        return self._request("/api/v1/cognify", json.dumps({"datasets":[dataset], "runInBackground":False}).encode(), "application/json")
    def search(self, query, dataset, mode="CHUNKS"):
        return self._request("/api/v1/search", json.dumps({"query":query,"searchType":mode,"datasets":[dataset]}).encode(), "application/json")
