"""QVCH v4 applicability subsystem (brief 13)."""

from qvch_v4.applicability.gate import (
    VERDICT_APPLY,
    VERDICT_CAUTIOUS_APPLY,
    VERDICT_ESCALATE,
    VERDICT_QUARANTINE,
    VERDICT_REJECT,
    ApplicabilityGate,
    GateDecision,
)
from qvch_v4.applicability.matcher import (
    PreconditionContext,
    evaluate_anti_conditions,
    evaluate_preconditions,
    semver_satisfies,
)

__all__ = [
    "ApplicabilityGate",
    "GateDecision",
    "VERDICT_APPLY",
    "VERDICT_CAUTIOUS_APPLY",
    "VERDICT_ESCALATE",
    "VERDICT_QUARANTINE",
    "VERDICT_REJECT",
    "PreconditionContext",
    "evaluate_preconditions",
    "evaluate_anti_conditions",
    "semver_satisfies",
]
