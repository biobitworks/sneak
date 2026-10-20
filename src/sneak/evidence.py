"""Append-only local evidence store. Successors never rewrite predecessors."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .contracts import EvidenceRef
from .merkle import canonical


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(payload)).hexdigest()


class EvidenceStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._index_path = self.root / "index.jsonl"
        if not self._index_path.exists():
            self._index_path.write_text("")

    def append_receipt(
        self,
        kind: str,
        payload: dict[str, Any],
        parent_id: Optional[str] = None,
        provider: str = "sneak.local",
    ) -> EvidenceRef:
        receipt_id = f"{kind}-{uuid.uuid4().hex[:12]}"
        body = {
            "id": receipt_id,
            "kind": kind,
            "parent_id": parent_id,
            "payload": payload,
            "observed_at": utc_now(),
        }
        artifact_digest = digest_payload(body)
        body["artifact_digest"] = artifact_digest
        rel = f"{kind}/{receipt_id}.json"
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as fh:
            json.dump(body, fh, indent=2, sort_keys=True)
            fh.write("\n")
        with self._index_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": receipt_id, "path": rel, "digest": artifact_digest}) + "\n")
        return EvidenceRef(
            provider=provider,
            external_id=receipt_id,
            artifact_digest=artifact_digest,
            receipt_path=str(path),
            observed_at=body["observed_at"],
        )

    def read(self, receipt_path: str) -> dict[str, Any]:
        return json.loads(Path(receipt_path).read_text(encoding="utf-8"))
