"""CVL — Claim extraction and evidence binding (brief 5 / 7).

CVL takes a validated Forge draft and extracts *hard* claims, binding each
EXTRACTED claim to its immutable verbatim anchor as ``SOURCE_ANCHOR`` evidence.
Hypotheses are carried through as candidates but are never promoted to fact by
CVL — that promotion is the sovereign MANAS envelope's job, gated by a valid
ReductionCertificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json
from qvch_v4.cvl.evidence_builder import EvidenceRef, build_evidence


@dataclass(frozen=True)
class ExtractedClaim:
    claim_id: str
    claim_type: str
    subject: str
    predicate: str
    value: str
    materiality_class: str | None
    evidence_ids: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type,
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "materiality_class": self.materiality_class,
            "evidence_ids": list(self.evidence_ids),
        }

    def canonical_hash(self) -> str:
        return hash_json(self.to_payload())


def extract(draft) -> tuple[ExtractedClaim, ...]:
    """Extract hard claims from a CanonicalStructuredDraft, binding evidence."""
    out: list[ExtractedClaim] = []
    for c in draft.claims:
        evidence_ids: tuple[str, ...] = ()
        if c.claim_type == enums.ClaimType.EXTRACTED.value and c.anchor is not None:
            # The verified verbatim anchor IS the immutable SOURCE_ANCHOR evidence.
            content = c.anchor.quote or (c.anchor.fingerprint or "")
            ev: EvidenceRef = build_evidence(
                source_type=enums.EvidenceSourceType.SOURCE_ANCHOR.value,
                locator={
                    "source_event_id": c.anchor.source_event_id,
                    "start_offset": c.anchor.start_offset,
                    "end_offset": c.anchor.end_offset,
                    "quote_hash": c.anchor.quote_hash,
                },
                content=content,
            )
            evidence_ids = (ev.evidence_id,)
        out.append(
            ExtractedClaim(
                claim_id=c.claim_id,
                claim_type=c.claim_type,
                subject=c.subject,
                predicate=c.predicate,
                value=c.value,
                materiality_class=c.materiality_class,
                evidence_ids=evidence_ids,
            )
        )
    return tuple(out)


__all__ = ["ExtractedClaim", "extract"]
