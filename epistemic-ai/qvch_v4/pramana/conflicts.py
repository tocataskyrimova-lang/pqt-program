"""Claim conflict arbitration (brief 7.3).

Both sides of a conflict are preserved, along with the conflict type, the
supporting evidence, and the explicit resolution reason. Statuses follow the
brief:

  OPEN | RESOLVED_BY_PRATYAKSA | CONSTRAINED_BY_SABDA |
  RESOLVED_BY_REFORMULATION | QUARANTINED | IRREDUCIBLE

Resolution is driven entirely by the four Pramāṇa laws (pramana.py); the LLM
never chooses the outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json, sha256_hex
from qvch_v4.pramana.pramana import (
    PramanaAssessment,
    law1_anumana_cannot_override_pratyaksha,
    law3_conflicting_pratyaksha_is_quarantined,
)

PRATYAKSA = enums.PramanaType.PRATYAKSA.value
ANUMANA = enums.PramanaType.ANUMANA.value
SABDA = enums.PramanaType.SABDA.value

_BLOCKING = {
    enums.ConflictStatus.OPEN.value,
    enums.ConflictStatus.QUARANTINED.value,
    enums.ConflictStatus.IRREDUCIBLE.value,
}


@dataclass(frozen=True)
class ClaimConflict:
    conflict_id: str
    claim_a_id: str
    claim_b_id: str
    conflict_type: str
    status: str  # enums.ConflictStatus value
    evidence_ids: tuple[str, ...]
    resolution_reason: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "claim_a_id": self.claim_a_id,
            "claim_b_id": self.claim_b_id,
            "conflict_type": self.conflict_type,
            "status": self.status,
            "evidence_ids": list(self.evidence_ids),
            "resolution_reason": self.resolution_reason,
        }

    def canonical_hash(self) -> str:
        return hash_json(self.to_payload())

    @property
    def is_blocking(self) -> bool:
        return self.status in _BLOCKING


def _conflict_id(a_id: str, b_id: str, ctype: str) -> str:
    ordered = "|".join(sorted([a_id, b_id]))
    return f"cf_{sha256_hex(f'{ordered}|{ctype}')[7:23]}"


def arbitrate(
    claim_a_id: str,
    claim_b_id: str,
    assess_a: PramanaAssessment,
    assess_b: PramanaAssessment,
    *,
    evidence_ids: tuple[str, ...] = (),
) -> ClaimConflict:
    """Apply the Pramāṇa laws to a pair of assessments and return a conflict."""
    ta, tb = assess_a.pramana_type, assess_b.pramana_type
    pair = {ta, tb}

    # Law 1 — Anumāna cannot override an observed Pratyakṣa result.
    if ANUMANA in pair and PRATYAKSA in pair:
        anu = assess_a if ta == ANUMANA else assess_b
        pra = assess_b if ta == ANUMANA else assess_a
        ctype = "ANUMANA_VS_PRATYAKSA"
        if not law1_anumana_cannot_override_pratyaksha(pra.outcome, anu.outcome):
            return ClaimConflict(
                conflict_id=_conflict_id(claim_a_id, claim_b_id, ctype),
                claim_a_id=claim_a_id,
                claim_b_id=claim_b_id,
                conflict_type=ctype,
                status=enums.ConflictStatus.RESOLVED_BY_PRATYAKSA.value,
                evidence_ids=evidence_ids,
                resolution_reason=(
                    "anumana cannot override the observed pratyaksha result (Law 1)"
                ),
            )
        return ClaimConflict(
            conflict_id=_conflict_id(claim_a_id, claim_b_id, ctype),
            claim_a_id=claim_a_id,
            claim_b_id=claim_b_id,
            conflict_type=ctype,
            status=enums.ConflictStatus.OPEN.value,
            evidence_ids=evidence_ids,
            resolution_reason="anumana consistent with observation",
        )

    # Law 2 — Śabda constrains action; the observed truth is unchanged.
    if SABDA in pair and PRATYAKSA in pair:
        ctype = "SABDA_CONSTRAINT"
        return ClaimConflict(
            conflict_id=_conflict_id(claim_a_id, claim_b_id, ctype),
            claim_a_id=claim_a_id,
            claim_b_id=claim_b_id,
            conflict_type=ctype,
            status=enums.ConflictStatus.CONSTRAINED_BY_SABDA.value,
            evidence_ids=evidence_ids,
            resolution_reason=(
                "sabda constrains the permitted action; observed truth unchanged (Law 2)"
            ),
        )

    # Law 3 — two Pratyakṣa that disagree are quarantined, not voted on.
    if pair == {PRATYAKSA, PRATYAKSA}:
        ctype = "PRATYAKSA_VS_PRATYAKSA"
        if law3_conflicting_pratyaksha_is_quarantined(assess_a.outcome, assess_b.outcome):
            return ClaimConflict(
                conflict_id=_conflict_id(claim_a_id, claim_b_id, ctype),
                claim_a_id=claim_a_id,
                claim_b_id=claim_b_id,
                conflict_type=ctype,
                status=enums.ConflictStatus.QUARANTINED.value,
                evidence_ids=evidence_ids,
                resolution_reason=(
                    "two pratyaksha disagree; quarantine and re-check environment (Law 3)"
                ),
            )
        return ClaimConflict(
            conflict_id=_conflict_id(claim_a_id, claim_b_id, ctype),
            claim_a_id=claim_a_id,
            claim_b_id=claim_b_id,
            conflict_type=ctype,
            status=enums.ConflictStatus.OPEN.value,
            evidence_ids=evidence_ids,
            resolution_reason="pratyaksha observations consistent",
        )

    # SABDA vs ANUMANA, or any non-adversarial pairing: no Pramāṇa conflict.
    return ClaimConflict(
        conflict_id=_conflict_id(claim_a_id, claim_b_id, "NO_CONFLICT"),
        claim_a_id=claim_a_id,
        claim_b_id=claim_b_id,
        conflict_type="NO_CONFLICT",
        status=enums.ConflictStatus.OPEN.value,
        evidence_ids=evidence_ids,
        resolution_reason="no pramana conflict detected",
    )


def is_blocking(status: str) -> bool:
    return status in _BLOCKING


__all__ = ["ClaimConflict", "arbitrate", "is_blocking"]
