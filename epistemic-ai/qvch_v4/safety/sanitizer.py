"""Recursive payload sanitization (brief 6.1).

Pipeline (brief 6.1):

    sanitize → canonical serialize → second independent scan → hash

If the second scan still finds a secret, the result is ``clean=False`` and the
caller must forbid the commit. We never store the secret, only an opaque
``secret_ref`` locator carrying a non-reversible fingerprint.

Recursion is bounded by depth and inline-JSON size so a hostile payload cannot
cause unbounded traversal.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, is_dataclass
from typing import Any

from qvch_v4.contracts.canonical import canonical_json, sha256_hex
from qvch_v4.safety.secret_scanner import (
    SENSITIVE_KEYS,
    _ENV_RE,
    _PEM_RE,
    _BEARER_RE,
    _CONNSTR_RE,
    scan,
    SecretFinding,
)

_MAX_DEPTH = 16
_MAX_JSON_LEN = 1 << 20

_REDACTED_MARKER = "<REDACTED_SECRET:sha256:{fp}>"


@dataclass(frozen=True)
class SanitizedResult:
    sanitized: Any
    canonical_hash: str
    # False => a secret survived sanitization; commit MUST be forbidden.
    clean: bool
    first_findings: tuple[SecretFinding, ...]  # detections in raw input
    second_findings: tuple[SecretFinding, ...]  # detections in serialized output


def _norm_key(k: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def _secret_locator(key_name: str, value: str) -> dict:
    return {
        "locator_type": "secret_ref",
        "provider": "environment",
        "reference": key_name,
        "fingerprint": sha256_hex(value),
        "never_embed": True,
    }


def _redact_string(text: str) -> str:
    return _REDACTED_MARKER.format(fp=sha256_hex(text))


def _string_is_secret(text: str) -> bool:
    if not isinstance(text, str) or not text:
        return False
    return bool(
        _PEM_RE.search(text)
        or _CONNSTR_RE.search(text)
        or _BEARER_RE.search(text)
        or any(p.search(text) for p in (
            re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
            re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
            re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
            re.compile(r"\bya29\.[A-Za-z0-9_-]{20,}\b"),
        ))
        or any(
            _norm_key(m.group(1)) in SENSITIVE_KEYS
            for m in _ENV_RE.finditer(text)
        )
    )


def _sanitize(obj: Any, depth: int) -> Any:
    if depth > _MAX_DEPTH:
        # Circuit breaker: we will not faithfully reproduce a hostile
        # depth-bomb. Collapse the untrustworthy subtree to an opaque marker so
        # no secret text can survive into the canonical output.
        return _REDACTED_MARKER.format(fp=sha256_hex(repr(obj)[:4096]))

    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            nk = _norm_key(k)
            if nk in SENSITIVE_KEYS and v is not None:
                if isinstance(v, str):
                    out[k] = _secret_locator(str(k), v)
                else:
                    out[k] = _secret_locator(str(k), canonical_json(v)[:512])
            else:
                out[k] = _sanitize(v, depth + 1)
        return out

    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(v, depth + 1) for v in obj]

    if is_dataclass(obj) and not isinstance(obj, type):
        payload = obj.to_payload() if hasattr(obj, "to_payload") else obj.__dict__
        return _sanitize(payload, depth)

    if isinstance(obj, str):
        if _string_is_secret(obj):
            return _redact_string(obj)
        stripped = obj.lstrip()
        if (stripped.startswith("{") or stripped.startswith("[")) and len(obj) <= _MAX_JSON_LEN:
            try:
                return _sanitize(json.loads(obj), depth + 1)
            except (ValueError, TypeError):
                return obj
        return obj

    return obj


def sanitize_payload(raw: Any, *, max_depth: int = _MAX_DEPTH) -> Any:
    """Recursively sanitize ``raw``; secrets become opaque locators/markers."""
    return _sanitize(raw, 0 if max_depth < 0 else 0)


def sanitize_and_hash(raw: Any, *, max_depth: int = _MAX_DEPTH) -> SanitizedResult:
    """sanitize → canonical serialize → second independent scan → hash.

    The second scan runs over the canonical serialized output so it independently
    re-examines the full structure (including nested JSON). If it still finds a
    secret, ``clean`` is ``False``. The canonical hash is over the sanitized form.
    """
    first = tuple(scan(raw))
    sanitized = _sanitize(raw, 0 if max_depth < 0 else 0)
    canonical = canonical_json(sanitized)
    second = tuple(scan(canonical))
    return SanitizedResult(
        sanitized=sanitized,
        canonical_hash=sha256_hex(canonical),
        clean=not second,
        first_findings=first,
        second_findings=second,
    )
