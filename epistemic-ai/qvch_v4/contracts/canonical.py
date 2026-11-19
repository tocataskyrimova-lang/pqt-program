"""Deterministic canonicalization and hashing.

All canonical hashes in v4 are `sha256:<hex>` over the lexicographically sorted,
ASCII-stable JSON of a payload. This is the single source of truth for hash
bindings in the MANAS Decision Envelope, write plans, revisions and receipts.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Stable JSON: sorted keys, no insignificant whitespace, UTF-8 safe."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def hash_json(value: Any) -> str:
    """Canonical hash of any JSON-serializable payload."""
    return sha256_hex(canonical_json(value))


def hash_text(text: str) -> str:
    return sha256_hex(text or "")


def verify_canonical(payload: Any, expected_hash: str) -> bool:
    return hash_json(payload) == expected_hash
