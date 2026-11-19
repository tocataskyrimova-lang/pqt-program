from __future__ import annotations

LIFE1_TABLES = {
    "memory_lifecycle_events",
    "repair_atom_links",
    "repair_crystal_links",
}

CORE_STATE_TABLES = {
    "memory_atoms",
    "noumena",
    "repair_pairs",
    "skill_candidates",
    "crystals",
    "hypotheses",
}

PRODUCTION_DB_PATH = r"C:\AGI\QVCH_v3\memory.db"
SANDBOX_DB_PATH = r"C:\AGI\PQT\qvch_life1_stage2_sandbox_migration_out\memory_sandbox.db"

FINAL_STATUS_VERIFIED = "LIFE1_STAGE2_SANDBOX_MIGRATION_VERIFIED"
STOP_STATUS_PREFIX = "LIFE1_STAGE2_STOP"
BASELINE_UNKNOWN_HISTORY = "BASELINE_SNAPSHOT_UNKNOWN_HISTORY"

ALLOWED_PROVENANCE_SOURCES = {
    "qvch_gateway",
    "qvch_life1",
    "qvch_decision_path",
    "manas_review",
    "manual_sandbox_test",
}

FORBIDDEN_LABEL_PROVENANCE_MARKERS = {
    "pqt",
    "ext1",
    "witness",
    "encoder",
    "synthetic",
    "surrogate",
    "replay_future",
}
