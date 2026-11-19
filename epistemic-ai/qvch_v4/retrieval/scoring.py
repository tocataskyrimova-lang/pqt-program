"""Epistemic retrieval scoring (brief 12.2 / 12.3).

All components are computed server-side and stored with a full component
breakdown in ``retrieval_hits``. The two headline formulas:

    epistemic_confidence = clamp(
        anchor_support * reproducibility * applicability * freshness
        * (1 - contradiction_pressure), 0, 1)

    retrieval_rank = semantic_relevance * epistemic_confidence * task_utility

Invariant (brief 12.3): if an atom has no evidence, its anchor_support is 0,
so epistemic_confidence can never be 1.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def compute_epistemic_confidence(anchor_support: float, reproducibility: float,
                                 applicability: float, freshness: float,
                                 contradiction_pressure: float) -> float:
    return clamp(
        anchor_support * reproducibility * applicability * freshness
        * (1.0 - clamp(contradiction_pressure))
    )


def compute_retrieval_rank(semantic_relevance: float, epistemic_confidence: float,
                           task_utility: float) -> float:
    return clamp(semantic_relevance) * clamp(epistemic_confidence) * clamp(task_utility)


# Freshness by lifecycle state (brief 12.3): compatibility with the current
# environment/revision, not mere text age.
_FRESHNESS_BY_STATE = {
    "ACTIVE": 1.0,
    "VALIDATED": 1.0,
    "CANDIDATE": 0.9,
    "SUPPORTED": 0.9,
    "PARTIALLY_SUPPORTED": 0.7,
    "PARTIALLY_REDUCED": 0.7,
    "RESOLVED": 0.8,
    "OPEN": 0.6,
    "PROPOSED": 0.6,
    "WATCH": 0.5,
    "DORMANT": 0.4,
    "REOPENED": 0.6,
    "AUTHORIZED_FOR_TEST": 0.7,
    "TESTING": 0.7,
    "STALE": 0.2,
    "QUARANTINED": 0.15,
    "ARCHIVED": 0.1,
    "REVOKED": 0.0,
    "REFUTED": 0.1,
    "SUPERSEDED": 0.2,
    "ABANDONED": 0.0,
}


def freshness_for_state(state: str) -> float:
    return _FRESHNESS_BY_STATE.get(state, 0.5)


@dataclass(frozen=True)
class EpistemicRetrievalPacket:
    atom_id: str
    revision_id: str
    atom_kind: str
    epistemic_state: str
    content_capsule_or_locator: Any
    semantic_relevance: float
    anchor_support: float
    reproducibility: float
    applicability: float
    freshness: float
    contradiction_pressure: float
    epistemic_confidence: float
    task_utility: float
    retrieval_rank: float
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    conflicting_candidates: list[str] = field(default_factory=list)
    lineage_id: str | None = None
    scope: str | None = None
    preconditions: list[dict] = field(default_factory=list)
    anti_conditions: list[dict] = field(default_factory=list)
    downgrade_rule: str | None = None
    lifecycle_status: str | None = None
    is_refuted: bool = False
    is_stale: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "revision_id": self.revision_id,
            "atom_kind": self.atom_kind,
            "epistemic_state": self.epistemic_state,
            "content_capsule_or_locator": self.content_capsule_or_locator,
            "semantic_relevance": self.semantic_relevance,
            "anchor_support": self.anchor_support,
            "reproducibility": self.reproducibility,
            "applicability": self.applicability,
            "freshness": self.freshness,
            "contradiction_pressure": self.contradiction_pressure,
            "epistemic_confidence": self.epistemic_confidence,
            "task_utility": self.task_utility,
            "retrieval_rank": self.retrieval_rank,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "conflicting_candidates": self.conflicting_candidates,
            "lineage_id": self.lineage_id,
            "scope": self.scope,
            "preconditions": self.preconditions,
            "anti_conditions": self.anti_conditions,
            "downgrade_rule": self.downgrade_rule,
            "lifecycle_status": self.lifecycle_status,
            "is_refuted": self.is_refuted,
            "is_stale": self.is_stale,
        }


__all__ = [
    "clamp",
    "compute_epistemic_confidence",
    "compute_retrieval_rank",
    "freshness_for_state",
    "EpistemicRetrievalPacket",
]
