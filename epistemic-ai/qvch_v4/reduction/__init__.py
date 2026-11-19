"""Proof-of-Reduction: the server-side reduction authority."""

from qvch_v4.reduction.verifier import (
    AcceptanceCriterion,
    BaselineSlot,
    CrystallizationVerdict,
    EvidenceItem,
    ReductionCertificate,
    ReductionInput,
    ReductionVerifier,
    VERIFIER_VERSION,
)

__all__ = [
    "ReductionVerifier",
    "ReductionCertificate",
    "ReductionInput",
    "BaselineSlot",
    "AcceptanceCriterion",
    "EvidenceItem",
    "CrystallizationVerdict",
    "VERIFIER_VERSION",
]
