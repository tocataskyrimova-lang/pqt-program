"""Immutable evidence references (brief 7.1).

Evidence is a *reference*, not a free-text opinion. Every EvidenceRef is
content-addressed and idempotent: equal inputs yield an identical evidence_id
and canonical hash, so the same observation is never duplicated and can always
be hash-verified downstream.

``llm_confidence`` is permitted ONLY as diagnostic metadata. It is carried on
the record but is explicitly non-support-bearing: see ``is_support_bearing`` and
the ReductionVerifier gate (brief 8 / Gate P0-D) which rejects evidence bundles
that consist solely of LLM confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json, sha256_hex


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    source_type: str  # enums.EvidenceSourceType value
    locator: dict[str, Any]
    content_hash: str  # sha256 of the referenced artifact / payload
    canonical_payload: dict[str, Any]
    llm_confidence: float | None = None  # DIAGNOSTIC ONLY — never support

    def to_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "locator": self.locator,
            "content_hash": self.content_hash,
            "canonical_payload": self.canonical_payload,
            "llm_confidence": self.llm_confidence,
        }

    def canonical_hash(self) -> str:
        return hash_json(self.to_payload())

    @property
    def is_diagnostic_only(self) -> bool:
        """True when this record carries only an LLM confidence annotation."""
        return self.llm_confidence is not None


def build_evidence(
    source_type: str,
    locator: dict[str, Any],
    content: str,
    *,
    content_hash: str | None = None,
    canonical_payload: dict[str, Any] | None = None,
    llm_confidence: float | None = None,
) -> EvidenceRef:
    """Construct an immutable, content-addressed evidence reference.

    ``content`` is the raw artifact being referenced (a probe result, a log
    slice, a canonical text, ...). It is hashed, never stored verbatim in a way
    that would let a later stage re-interpret it as an opinion.
    """
    try:
        enums.EvidenceSourceType(source_type)
    except ValueError as exc:
        raise ValueError(f"unknown evidence source_type: {source_type!r}") from exc

    h = content_hash or sha256_hex(content)
    canonical_payload = canonical_payload if canonical_payload is not None else {
        "source_type": source_type,
        "content_hash": h,
    }
    # Deterministic, idempotent id derived from the immutable parts.
    seed = sha256_hex(f"{source_type}|{h}|{hash_json(locator)}")
    return EvidenceRef(
        evidence_id=f"ev_{seed[7:23]}",
        source_type=source_type,
        locator=dict(locator),
        content_hash=h,
        canonical_payload=dict(canonical_payload),
        llm_confidence=llm_confidence,
    )


def is_support_bearing(ev: EvidenceRef) -> bool:
    """An LLM-confidence annotation never increases support (brief 7.1)."""
    return not ev.is_diagnostic_only


__all__ = ["EvidenceRef", "build_evidence", "is_support_bearing"]
