"""Independent secret detection (defense-in-depth second scan).

This module is *detection only*. It never mutates its input; it reports every
location that looks like a secret so a caller can forbid a commit when a secret
survives sanitization.

The detector is deliberately conservative about value shapes:
  * sensitive *keys* (e.g. ``api_key``) flag their value regardless of shape;
  * *known* token prefixes (sk-, gh_, AKIA, ya29., xox[baprs]-) are matched,
    but a bare 64-hex content hash (sha256 fingerprints) is NOT treated as a
    secret, so legitimate ``quote_hash`` / ``fingerprint`` fields stay clean.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from qvch_v4.contracts.canonical import sha256_hex

# Keys whose *value* is treated as a secret unconditionally.
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "pwd",
    "token",
    "api_key",
    "apikey",
    "api-key",
    "secret",
    "secret_key",
    "secretkey",
    "private_key",
    "privatekey",
    "cookie",
    "cookies",
    "authorization",
    "auth",
    "credentials",
    "credential",
    "access_key",
    "accesskey",
    "client_secret",
    "session_token",
}

# Known token shapes (prefixed). No generic long-alphanumeric rule — that would
# false-positive on legitimate sha256 fingerprints.
_TOKEN_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bya29\.[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
]

_PEM_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_CONNSTR_RE = re.compile(r"[a-zA-Z][\w+.\-]*://[^/\s:@]+:[^/\s:@]+@")
_BEARER_RE = re.compile(r"(?i)\b(?:bearer|basic)\s+[A-Za-z0-9._\-+/=]{8,}")
# KEY=VALUE lines where KEY is sensitive.
_ENV_RE = re.compile(r"(?im)^\s*([\w.]+)\s*=\s*(\S+)\s*$")

_MAX_DEPTH = 16
_MAX_JSON_LEN = 1 << 20  # 1 MiB inline JSON ceiling


@dataclass(frozen=True)
class SecretFinding:
    """A located secret. ``fingerprint`` is a hash of the offending value;
    the value itself is never returned or stored."""

    kind: str  # sensitive_key | pem_private_key | connection_string | bearer_auth | token_pattern | env_pair
    path: str  # dotted/list/::json path to the value
    fingerprint: str  # sha256 of the offending value slice


def _norm_key(k: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def scan_value(text: str, path: str, findings: list[SecretFinding]) -> None:
    if not isinstance(text, str) or not text:
        return
    if _PEM_RE.search(text):
        findings.append(SecretFinding("pem_private_key", path, sha256_hex(text[:512])))
        return
    if _CONNSTR_RE.search(text):
        findings.append(SecretFinding("connection_string", path, sha256_hex(text[:512])))
    if _BEARER_RE.search(text):
        findings.append(SecretFinding("bearer_auth", path, sha256_hex(text[:512])))
    for m in _ENV_RE.finditer(text):
        if _norm_key(m.group(1)) in SENSITIVE_KEYS:
            findings.append(SecretFinding("env_pair", path, sha256_hex(m.group(2))))
    for pat in _TOKEN_PATTERNS:
        m = pat.search(text)
        if m:
            findings.append(SecretFinding("token_pattern", path, sha256_hex(m.group(0))))
            break


def _scan(obj: Any, path: str, depth: int, findings: list[SecretFinding]) -> None:
    if depth > _MAX_DEPTH:
        # Circuit breaker: a depth-bomb we cannot fully inspect is treated as
        # untrusted. Flagging it makes the caller refuse the commit rather than
        # risk a silently-missed secret.
        findings.append(
            SecretFinding("depth_exceeded", path, sha256_hex(str(path) or "root"))
        )
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else str(k)
            if _norm_key(k) in SENSITIVE_KEYS and isinstance(v, str) and v:
                findings.append(
                    SecretFinding("sensitive_key", child, sha256_hex(v))
                )
            _scan(v, child, depth + 1, findings)
    elif isinstance(obj, (list, tuple, set)):
        for i, v in enumerate(obj):
            _scan(v, f"{path}[{i}]", depth + 1, findings)
    elif isinstance(obj, str):
        scan_value(obj, path, findings)
        stripped = obj.lstrip()
        if (stripped.startswith("{") or stripped.startswith("[")) and len(obj) <= _MAX_JSON_LEN:
            try:
                _scan(json.loads(obj), path + "::json", depth + 1, findings)
            except (ValueError, TypeError):
                pass


def scan(obj: Any) -> list[SecretFinding]:
    """Return every secret location found in ``obj`` (non-mutating)."""
    findings: list[SecretFinding] = []
    _scan(obj, "", 0, findings)
    return findings


def has_secret(obj: Any) -> bool:
    return bool(scan(obj))
