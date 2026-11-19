"""Frozen lifecycle policy objects (brief 14, "Frozen Policy").

These are declared ``frozen`` so the coefficients are immutable once loaded —
the Spanda/Vinasha engines read every weight and threshold from an instance,
never from a literal sprinkled through the logic. A new policy *version* is a
new object, which is how tuning is versioned and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SpandaPolicy:
    """Coefficients for the Spanda viability score (brief 14.1).

    The score is a weighted blend of five positive signals minus two pressure
    terms, clamped to [0, 1]. Thresholds then map the score onto the FORM
    lifecycle states ACTIVE → WATCH → STALE → QUARANTINED.
    """

    version: str = "spanda/1.0"

    # Positive weights (sum to 0.80).
    w_applicability_health: float = 0.30
    w_probe_success_rate: float = 0.15
    w_successful_usage_rate: float = 0.15
    w_evidence_freshness: float = 0.10
    w_dependency_compatibility: float = 0.10

    # Negative magnitudes (subtracted, then clamped). Sum to 0.20.
    w_contradiction_pressure: float = 0.10
    w_observed_failure_rate: float = 0.10

    # Thresholds on the final score ∈ [0, 1].
    watch_below: float = 0.60
    stale_below: float = 0.40
    quarantine_below: float = 0.20

    # Evidence younger than this many days counts as "fresh".
    freshness_window_days: int = 30

    def to_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "w_applicability_health": self.w_applicability_health,
            "w_probe_success_rate": self.w_probe_success_rate,
            "w_successful_usage_rate": self.w_successful_usage_rate,
            "w_evidence_freshness": self.w_evidence_freshness,
            "w_dependency_compatibility": self.w_dependency_compatibility,
            "w_contradiction_pressure": self.w_contradiction_pressure,
            "w_observed_failure_rate": self.w_observed_failure_rate,
            "watch_below": self.watch_below,
            "stale_below": self.stale_below,
            "quarantine_below": self.quarantine_below,
        }

    @classmethod
    def default(cls) -> "SpandaPolicy":
        return cls()


@dataclass(frozen=True)
class VinashaPolicy:
    """Parameters governing Vinasha loss-of-influence handling (brief 14.2).

    Vinasha never deletes causal history. When a previously valid crystal
    degrades it (a) loses the right to auto-apply and (b) a new N is opened
    asking *why* it lost applicability, linked by DERIVED_FROM.
    """

    version: str = "vinasha/1.0"

    # A revision in any of these states must NOT be auto-applied. They retain
    # their content and full causal history for audit; they simply cannot
    # influence new decisions automatically.
    non_applicable_states: tuple[str, ...] = (
        "STALE", "REVOKED", "QUARANTINED", "ARCHIVED",
        "ABANDONED", "REFUTED", "SUPERSEDED",
    )

    # FORM lifecycle rank — used by Spanda to tell a degrading (downward)
    # transition from a re-activating (upward) one. Upward transitions must be
    # authorised by a MANAS decision; downward transitions are automatic.
    state_rank: dict[str, int] = field(default_factory=lambda: {
        "ARCHIVED": 0, "REVOKED": 0, "QUARANTINED": 1,
        "STALE": 2, "WATCH": 3, "ACTIVE": 4,
    })

    degradation_link_type: str = "DERIVED_FROM"
    new_n_question: str = (
        "Why did this previously valid revision lose applicability?"
    )

    def to_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "non_applicable_states": list(self.non_applicable_states),
            "state_rank": dict(self.state_rank),
            "degradation_link_type": self.degradation_link_type,
            "new_n_question": self.new_n_question,
        }

    @classmethod
    def default(cls) -> "VinashaPolicy":
        return cls()


__all__ = ["SpandaPolicy", "VinashaPolicy"]
