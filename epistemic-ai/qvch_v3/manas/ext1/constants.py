from __future__ import annotations

BANNER = "DRY_NO_HYPOTHESIS_CLAIM"
CLAIM_BOUNDARY = (
    "EXT1-DRY verifies pipeline hermeticity only. It does not test whether PQT "
    "predicts real future bad writes. EXT1_PASS/PARTIAL/FAIL are forbidden until "
    "forward PILOT/HOLDOUT on new episodes."
)
C_ALIAS_NOTE = "EXT1 C alias is C_R, not Kernel C redefinition"
C_ALIAS_REPORT_NOTE = (
    "EXT1 C observable is an adapter alias for C_R and does not modify PQT Kernel semantics."
)
SYNTHETIC_PREFIX = "SYNTHETIC_MACHINERY_CHECK_"
SYNTHETIC_DISCLAIMER = "measures the detector, not PQT"

TERMINAL_W0_BREACH = "EXT1_DRY_W0_BREACH"
TERMINAL_SELF_CONFIRM = "EXT1_SELF_CONFIRM"
TERMINAL_LEAKAGE = "EXT1_DRY_LEAKAGE"
TERMINAL_ENCODER_LAUNDER = "EXT1_DRY_ENCODER_LAUNDER"
TERMINAL_CIRCULAR_LABEL = "EXT1_DRY_CIRCULAR_LABEL"
TERMINAL_LABEL_FAILED = "EXT1_DRY_LABEL_EXTRACTION_FAILED"
TERMINAL_SURROGATE_FAILED = "EXT1_DRY_SURROGATE_FAILED"
TERMINAL_NO_DATA = "EXT1_DRY_NO_WITNESS_DATA"
TERMINAL_LABEL_UNAVAILABLE = "EXT1_DRY_INCONCLUSIVE_LABEL_UNAVAILABLE"
TERMINAL_INCONCLUSIVE = "EXT1_DRY_INCONCLUSIVE"
TERMINAL_HERMETIC = "EXT1_DRY_PIPELINE_HERMETIC"

DATA_NO_DB = "NO_MEMORY_DB"
DATA_EMPTY_DB = "EMPTY_MEMORY_DB"
DATA_NO_EPISODES = "NO_ELIGIBLE_EPISODES"
DATA_AVAILABLE = "HISTORICAL_DATA_AVAILABLE"

LABEL_UNAVAILABLE = "EXT1_DRY_INCONCLUSIVE_LABEL_UNAVAILABLE"
LABEL_AVAILABLE = "STRONG_Y_BAD_WRITE_COMPUTABLE"

MACHINERY_PASS = "SYNTHETIC_MACHINERY_CHECKS_PASS"
MACHINERY_FAIL = "SYNTHETIC_MACHINERY_CHECKS_FAIL"

FORBIDDEN_ENCODER_FIELDS = frozenset(
    {
        "conflict_score",
        "novelty_score",
        "support_count",
        "evidence_quality",
        "llm_confidence",
        "manas_decision",
        "write_decision",
        "accepted",
        "rejected",
        "validation_status",
        "lifecycle_state",
        "y_bad_write",
    }
)

REPORT_BASE = {"banner": BANNER, "claim_boundary": CLAIM_BOUNDARY}
