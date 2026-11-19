"""Deterministic-first materiality classification (brief 6.3, 2.5).

Materiality answers *how* a remembered fact must be treated:

    SEMANTIC        — meaning is remembered.
    LITERAL_ARTIFACT— retrieved exactly by locator + verified hash.
    SKILL_TRACE     — trusted only through an execution receipt.
    SECRET_REF      — stored only as an opaque locator; never as content.
    MIXED           — more than one marker is present.

Deterministic detection is authoritative. An LLM/Planner MAY *suggest* a class
but cannot force a different one: a suggestion is honored only when it agrees
with (or does not contradict) the deterministic signal.
"""

from __future__ import annotations

import re
from typing import Any

from qvch_v4.contracts import enums

_SECRET_KEYS = {
    "password", "passwd", "pwd", "token", "api_key", "apikey", "secret",
    "secret_key", "private_key", "cookie", "authorization", "credentials",
    "access_key", "client_secret", "session_token",
}
_LITERAL_KEYS = {
    "exactlocator", "immutablecontenthash", "retrievalrecipe",
    "semanticcapsule", "revision", "commit", "contenthash",
}
_SKILL_KEYS = {
    "executionreceipt", "proberesult", "receipt", "exitcode", "node15",
    "probeexitcode", "executionid",
}
_PEM_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_LOCATOR_RE = re.compile(r'"locator_type"\s*:\s*"secret_ref"')


def _norm_key(k: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def _gather(payload: Any, acc: set[str], depth: int) -> None:
    if depth > 16:
        return
    if isinstance(payload, dict):
        for k, v in payload.items():
            nk = _norm_key(k)
            if nk in _SECRET_KEYS:
                acc.add("secret")
            if isinstance(v, dict) and v.get("locator_type") == "secret_ref":
                acc.add("secret")
            if nk in _LITERAL_KEYS:
                acc.add("literal")
            if nk in _SKILL_KEYS:
                acc.add("skill")
            _gather(v, acc, depth + 1)
    elif isinstance(payload, (list, tuple, set)):
        for x in payload:
            _gather(x, acc, depth + 1)
    elif isinstance(payload, str):
        if _PEM_RE.search(payload):
            acc.add("secret")
        if _LOCATOR_RE.search(payload):
            acc.add("secret")


def _detect(payload: Any) -> str | None:
    acc: set[str] = set()
    _gather(payload, acc, 0)
    if not acc:
        return None
    if "secret" in acc and len(acc) > 1:
        return enums.MaterialityClass.MIXED.value
    if "secret" in acc:
        return enums.MaterialityClass.SECRET_REF.value
    if "literal" in acc and "skill" in acc:
        return enums.MaterialityClass.MIXED.value
    if "literal" in acc:
        return enums.MaterialityClass.LITERAL_ARTIFACT.value
    if "skill" in acc:
        return enums.MaterialityClass.SKILL_TRACE.value
    return None


def classify_materiality(payload: Any, *, suggested: str | None = None) -> str:
    """Return a materiality class.

    Deterministic detection is authoritative (brief 6.3 "deterministic-first").
    An LLM/Planner MAY *propose* a class via ``suggested``, but that proposal is
    non-binding: it can never change the deterministic result, and when no
    deterministic signal is present the safe default ``SEMANTIC`` is returned.
    This guarantees the LLM cannot relabel a secret as benign or upgrade
    materiality on its own authority.
    """
    detected = _detect(payload)
    if detected is not None:
        return detected
    return enums.MaterialityClass.SEMANTIC.value
