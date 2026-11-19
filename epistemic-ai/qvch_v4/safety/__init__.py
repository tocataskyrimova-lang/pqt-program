"""Recursive safety: secret scanning, payload sanitization, materiality.

These utilities enforce brief constraint #7 (never store secrets, signing keys,
raw credentials, hidden chain-of-thought, or full legacy WritePlan payloads)
and #8 (no mocked evidence). The scanner is *detection only*; the sanitizer
produces an opaque secret_ref locator and the canonical hash used downstream.
"""

from qvch_v4.safety.materiality import classify_materiality
from qvch_v4.safety.sanitizer import (
    SanitizedResult,
    sanitize_and_hash,
    sanitize_payload,
)
from qvch_v4.safety.secret_scanner import (
    SecretFinding,
    has_secret,
    scan,
)

__all__ = [
    "SecretFinding",
    "scan",
    "has_secret",
    "sanitize_payload",
    "sanitize_and_hash",
    "SanitizedResult",
    "classify_materiality",
]
