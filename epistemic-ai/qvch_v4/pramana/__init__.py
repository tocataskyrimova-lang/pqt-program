"""Pramāṇa — evidence classification, the four laws, and conflict arbitration."""

from qvch_v4.pramana.conflicts import ClaimConflict, arbitrate, is_blocking
from qvch_v4.pramana.pramana import (
    PramanaAssessment,
    classify_pramana,
    law1_anumana_cannot_override_pratyaksha,
    law2_sabda_constrains_not_rewrites,
    law3_conflicting_pratyaksha_is_quarantined,
    law4_blocking_conflict_forbids_f,
)

__all__ = [
    "PramanaAssessment",
    "classify_pramana",
    "law1_anumana_cannot_override_pratyaksha",
    "law2_sabda_constrains_not_rewrites",
    "law3_conflicting_pratyaksha_is_quarantined",
    "law4_blocking_conflict_forbids_f",
    "ClaimConflict",
    "arbitrate",
    "is_blocking",
]
