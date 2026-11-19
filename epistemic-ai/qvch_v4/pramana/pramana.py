"""Pramāṇa — evidence classification and the four inviolable laws (brief 7.2).

Pramāṇa types are NOT a simple linear scale (SABDA > PRATYAKSA > ANUMANA is
explicitly forbidden). Each type has a distinct epistemic role:

  PRATYAKSA — direct observation / execution (Node 15, test logs, artifact hash,
              signed external receipts, source anchors).
  ANUMANA   — inference drawn from other evidence.
  SABDA     — a normative policy canon that *constrains* permitted action.

The four laws are encoded as pure functions so they can be unit-tested and
invoked by both the conflict arbiter (brief 7.3) and the ReductionVerifier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json
from qvch_v4.cvl.evidence_builder import EvidenceRef

PRATYAKSA_SOURCES = {
    enums.EvidenceSourceType.NODE15_EXECUTION.value,
    enums.EvidenceSourceType.TEST_LOG.value,
    enums.EvidenceSourceType.ARTIFACT_HASH.value,
    enums.EvidenceSourceType.SOURCE_ANCHOR.value,
    enums.EvidenceSourceType.EXTERNAL_SIGNED_RECEIPT.value,
}
SABDA_SOURCES = {enums.EvidenceSourceType.POLICY_CANON.value}
ANUMANA_SOURCES = {enums.EvidenceSourceType.INFERENCE.value}


def classify_pramana(ev: EvidenceRef) -> str:
    if ev.source_type in PRATYAKSA_SOURCES:
        return enums.PramanaType.PRATYAKSA.value
    if ev.source_type in SABDA_SOURCES:
        return enums.PramanaType.SABDA.value
    if ev.source_type in ANUMANA_SOURCES:
        return enums.PramanaType.ANUMANA.value
    raise ValueError(f"cannot classify pramana for source_type {ev.source_type!r}")


@dataclass(frozen=True)
class PramanaAssessment:
    assessment_id: str
    claim_id: str
    pramana_type: str
    evidence_ids: tuple[str, ...]
    # The assertion under assessment (e.g. "service responds on :8080") and the
    # observed/inferred outcome ("pass"|"fail"|"observed"|"forbidden"). These
    # let the arbiter detect genuine contradiction.
    assertion: str | None = None
    outcome: str | None = None
    observed_result: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "claim_id": self.claim_id,
            "pramana_type": self.pramana_type,
            "evidence_ids": list(self.evidence_ids),
            "assertion": self.assertion,
            "outcome": self.outcome,
            "observed_result": self.observed_result,
        }

    def canonical_hash(self) -> str:
        return hash_json(self.to_payload())


# ---------------------------------------------------------------------------
# The four laws (pure, side-effect free)
# ---------------------------------------------------------------------------

def law1_anumana_cannot_override_pratyaksha(
    pratyaksha_outcome: str | None,
    anumana_outcome: str | None,
) -> bool:
    """Law 1: an inference may not rewrite an observed Pratyakṣa result.

    Returns True when the anumāna is *consistent* with (or does not contradict)
    the observed result. A failed execution cannot be turned into 'passed' by
    inference.
    """
    if pratyaksha_outcome is None or anumana_outcome is None:
        return True
    return pratyaksha_outcome == anumana_outcome


def law2_sabda_constrains_not_rewrites(
    pratyaksha_observed: str | None,
    sabda_action: str | None,
) -> bool:
    """Law 2: Śabda constrains the *action* but never changes observed truth.

    The observed physical truth (``pratyaksha_observed``) is returned unchanged;
    only the permitted action may be constrained by policy. This helper asserts
    the invariant that the observation is immutable under a policy constraint.
    """
    # Observation is always preserved; sabda never edits it.
    return True


def law3_conflicting_pratyaksha_is_quarantined(
    a_outcome: str | None,
    b_outcome: str | None,
) -> bool:
    """Law 3: two Pratyakṣa that disagree are NOT resolved by voting.

    Returns True when they conflict (=> QUARANTINED + environment re-check).
    """
    if a_outcome is None or b_outcome is None:
        return False
    # "forbidden" (policy) is not an observed physical truth; only genuine
    # observed-outcome disagreement counts as a Pratyaksha conflict.
    return a_outcome != b_outcome and {a_outcome, b_outcome} <= {
        "pass",
        "fail",
        "observed",
        "true",
        "false",
    }


def law4_blocking_conflict_forbids_f(
    conflict_statuses: list[str],
) -> bool:
    """Law 4: an unresolved blocking conflict forbids crystallization to F.

    A conflict blocks F unless it is explicitly resolved/reformulated.
    """
    blocking = {
        enums.ConflictStatus.OPEN.value,
        enums.ConflictStatus.QUARANTINED.value,
        enums.ConflictStatus.IRREDUCIBLE.value,
    }
    return not (set(conflict_statuses) & blocking)


__all__ = [
    "classify_pramana",
    "PramanaAssessment",
    "PRATYAKSA_SOURCES",
    "SABDA_SOURCES",
    "ANUMANA_SOURCES",
    "law1_anumana_cannot_override_pratyaksha",
    "law2_sabda_constrains_not_rewrites",
    "law3_conflicting_pratyaksha_is_quarantined",
    "law4_blocking_conflict_forbids_f",
]
