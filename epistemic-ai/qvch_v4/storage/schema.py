"""QVCH v4.1 SQL schema (brief 10).

SQL-first, deterministic SQLite substrate. All ids are opaque UUID strings,
times are UTC ISO-8601, hashes are ``sha256:<hex>``. Every relation that is
real has an FK; history tables are append-only (UPDATE/DELETE forbidden by
trigger *and* by the connection authorizer); writes go through the repository,
never a raw SQL string.
"""

from __future__ import annotations

# --- Allowed value vocabularies (mirror qvch_v4.contracts.enums) -------------
ATOM_KINDS = "'NOUMENON','HYPOTHESIS','FORM','REPAIR','SKILL','LOCATOR','CAPSULE'"
MATERIALITY = "'SEMANTIC','LITERAL_ARTIFACT','SKILL_TRACE','SECRET_REF','MIXED'"
VERDICTS = "'APPROVE','QUARANTINE','REJECT'"
ROUTES = "'Q','N','U','F_candidate','F','CRYSTAL','REPAIR','SKILL','REJECT','QUARANTINE'"
PURPOSES = "'AUTHORIZE_TEST','AUTHORIZE_WRITE','AUTHORIZE_STATE_TRANSITION'"
EVIDENCE_SOURCES = (
    "'NODE15_EXECUTION','TEST_LOG','ARTIFACT_HASH','SOURCE_ANCHOR',"
    "'POLICY_CANON','EXTERNAL_SIGNED_RECEIPT','INFERENCE'"
)
PRAMANA = "'PRATYAKSA','ANUMANA','SABDA'"
CONFLICT_STATUS = (
    "'OPEN','RESOLVED_BY_PRATYAKSA','CONSTRAINED_BY_SABDA',"
    "'RESOLVED_BY_REFORMULATION','QUARANTINED','IRREDUCIBLE'"
)
LINK_TYPES = (
    "'DERIVED_FROM','TESTED_BY','SUPPORTS','CONTRADICTS','REFUTES','RESOLVES',"
    "'SPECIALIZES','SUPERSEDES','LOCATES'"
)
APPLICABILITY = "'APPLY','CAUTIOUS_APPLY','ESCALATE','QUARANTINE','REJECT'"
USAGE = "'SUCCESS','PARTIAL_SUCCESS','FAILURE','ABORTED','CONTEXT_MISMATCH','UNEXPECTED_SIDE_EFFECT'"
SEVERITY = "'INFO','WARNING','ERROR','CRITICAL'"

N_STATES = "'OPEN','PARTIALLY_REDUCED','RESOLVED','DORMANT','ABANDONED','REOPENED'"
U_STATES = (
    "'PROPOSED','QUARANTINED','AUTHORIZED_FOR_TEST','TESTING','PARTIALLY_SUPPORTED',"
    "'SUPPORTED','REFUTED','SUPERSEDED'"
)
F_STATES = (
    "'CANDIDATE','VALIDATED','ACTIVE','WATCH','STALE','QUARANTINED','ARCHIVED','REVOKED'"
)

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL,
    content_hash TEXT
);

CREATE TABLE IF NOT EXISTS memory_sessions (
    session_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    source TEXT,
    meta_json TEXT
);

CREATE TABLE IF NOT EXISTS memory_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES memory_sessions(session_id),
    event_type TEXT,
    occurred_at TEXT NOT NULL,
    sanitized_json TEXT,
    content_hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS epistemic_lineages (
    lineage_id TEXT PRIMARY KEY,
    root_noumenon_id TEXT,
    status TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_atoms (
    atom_id TEXT PRIMARY KEY,
    lineage_id TEXT NOT NULL REFERENCES epistemic_lineages(lineage_id),
    atom_kind TEXT NOT NULL CHECK (atom_kind IN (%s)),
    materiality_class TEXT CHECK (materiality_class IN (%s)),
    current_state TEXT NOT NULL,
    current_revision_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS atom_revisions (
    revision_id TEXT PRIMARY KEY,
    atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id) ON DELETE RESTRICT,
    revision_number INTEGER NOT NULL,
    state TEXT NOT NULL,
    canonical_payload_json TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    UNIQUE (atom_id, revision_number)
);

CREATE TABLE IF NOT EXISTS atom_state_events (
    event_id TEXT PRIMARY KEY,
    atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id) ON DELETE RESTRICT,
    from_state TEXT,
    to_state TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    decision_id TEXT,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS memory_links (
    link_id TEXT PRIMARY KEY,
    from_atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id) ON DELETE RESTRICT,
    to_atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id) ON DELETE RESTRICT,
    link_type TEXT NOT NULL CHECK (link_type IN (%s)),
    strength REAL,
    created_at TEXT NOT NULL,
    provenance TEXT
);

CREATE TABLE IF NOT EXISTS evidence_refs (
    evidence_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (source_type IN (%s)),
    locator_json TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    canonical_payload_json TEXT NOT NULL,
    llm_confidence REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_bundles (
    bundle_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    content_hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS evidence_bundle_items (
    item_id TEXT PRIMARY KEY,
    bundle_id TEXT NOT NULL REFERENCES evidence_bundles(bundle_id) ON DELETE CASCADE,
    evidence_id TEXT NOT NULL REFERENCES evidence_refs(evidence_id) ON DELETE RESTRICT,
    weight REAL,
    UNIQUE (bundle_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS structured_drafts (
    draft_id TEXT PRIMARY KEY,
    source_text_hash TEXT NOT NULL,
    canonical_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json))
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    draft_id TEXT REFERENCES structured_drafts(draft_id) ON DELETE CASCADE,
    claim_type TEXT NOT NULL CHECK (claim_type IN ('EXTRACTED','GENERATED_HYPOTHESIS','NORMATIVE','OBSERVATION_REQUEST')),
    subject TEXT,
    predicate TEXT,
    value TEXT,
    materiality_class TEXT CHECK (materiality_class IN (%s)),
    anchor_json TEXT,
    evidence_refs_json TEXT
);

CREATE TABLE IF NOT EXISTS claim_evidence (
    claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    evidence_id TEXT NOT NULL REFERENCES evidence_refs(evidence_id) ON DELETE RESTRICT,
    PRIMARY KEY (claim_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS claim_conflicts (
    conflict_id TEXT PRIMARY KEY,
    claim_a_id TEXT NOT NULL,
    claim_b_id TEXT NOT NULL,
    conflict_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (%s)),
    evidence_ids_json TEXT,
    resolution_reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pramana_reports (
    report_id TEXT PRIMARY KEY,
    claim_id TEXT REFERENCES claims(claim_id) ON DELETE CASCADE,
    pramana_type TEXT NOT NULL CHECK (pramana_type IN (%s)),
    evidence_ids_json TEXT,
    assessed_outcome TEXT,
    canonical_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reduction_proofs (
    proof_id TEXT PRIMARY KEY,
    lineage_id TEXT NOT NULL REFERENCES epistemic_lineages(lineage_id),
    noumenon_atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id),
    supported_u_atom_ids_json TEXT,
    baseline_unknown_slots_json TEXT,
    acceptance_criteria_json TEXT,
    evidence_bundle_ids_json TEXT,
    passed_tests_json TEXT,
    failed_tests_json TEXT,
    counterexamples_json TEXT,
    resolved_slots_json TEXT,
    residual_unknown_slots_json TEXT,
    contradiction_pressure REAL,
    reduction_score REAL,
    scope TEXT,
    verifier_version TEXT,
    proof_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    slot_reduction REAL,
    evidence_quality REAL,
    scope_coverage REAL,
    has_supporting_evidence INTEGER
);

CREATE TABLE IF NOT EXISTS reduction_slots (
    slot_id TEXT PRIMARY KEY,
    proof_id TEXT NOT NULL REFERENCES reduction_proofs(proof_id) ON DELETE CASCADE,
    lineage_id TEXT REFERENCES epistemic_lineages(lineage_id),
    slot_kind TEXT,
    weight REAL,
    resolved INTEGER CHECK (resolved IN (0,1)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS manas_decisions (
    decision_id TEXT PRIMARY KEY,
    purpose TEXT NOT NULL CHECK (purpose IN (%s)),
    target_id TEXT NOT NULL,
    target_hash TEXT NOT NULL,
    draft_id TEXT,
    draft_hash TEXT,
    sanitized_payload_hash TEXT,
    evidence_bundle_hash TEXT,
    pramana_report_hash TEXT,
    reduction_proof_hash TEXT,
    verdict TEXT NOT NULL CHECK (verdict IN (%s)),
    route TEXT CHECK (route IN (%s)),
    policy_version TEXT NOT NULL,
    service_version TEXT NOT NULL,
    key_id TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    nonce TEXT NOT NULL,
    signature_algorithm TEXT NOT NULL,
    signature TEXT NOT NULL,
    canonical_hash TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS decision_consumptions (
    consumption_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL UNIQUE REFERENCES manas_decisions(decision_id),
    nonce TEXT NOT NULL UNIQUE,
    consumed_at TEXT NOT NULL,
    envelope_hash TEXT
);

CREATE TABLE IF NOT EXISTS write_attempts (
    attempt_id TEXT PRIMARY KEY,
    decision_id TEXT,
    target_hash TEXT,
    verdict TEXT,
    allowed INTEGER,
    reason TEXT,
    attempted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_locators (
    locator_id TEXT PRIMARY KEY,
    materiality_class TEXT CHECK (materiality_class IN (%s)),
    exact_locator TEXT NOT NULL,
    immutable_content_hash TEXT NOT NULL UNIQUE,
    revision TEXT,
    commit_ref TEXT,
    retrieval_recipe_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applicability_contracts (
    contract_id TEXT PRIMARY KEY,
    atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id) ON DELETE CASCADE,
    revision_id TEXT NOT NULL REFERENCES atom_revisions(revision_id) ON DELETE CASCADE,
    scope TEXT,
    precondition_json TEXT NOT NULL,
    anti_condition_json TEXT,
    required_probes_json TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (atom_id, revision_id)
);

CREATE TABLE IF NOT EXISTS applicability_probes (
    probe_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL REFERENCES applicability_contracts(contract_id) ON DELETE CASCADE,
    probe_name TEXT NOT NULL,
    command_hash TEXT,
    env_hash TEXT,
    exit_code INTEGER,
    stdout_hash TEXT,
    stderr_hash TEXT,
    executed_at TEXT NOT NULL,
    receipt_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retrieval_runs (
    run_id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    started_at TEXT NOT NULL,
    strategy TEXT
);

CREATE TABLE IF NOT EXISTS retrieval_hits (
    hit_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES retrieval_runs(run_id) ON DELETE CASCADE,
    atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id),
    revision_id TEXT NOT NULL REFERENCES atom_revisions(revision_id),
    semantic_relevance REAL,
    anchor_support REAL,
    reproducibility REAL,
    applicability REAL,
    freshness REAL,
    contradiction_pressure REAL,
    epistemic_confidence REAL,
    task_utility REAL,
    retrieval_rank REAL,
    components_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gate_decisions (
    gate_id TEXT PRIMARY KEY,
    atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id),
    revision_id TEXT NOT NULL REFERENCES atom_revisions(revision_id),
    contract_id TEXT REFERENCES applicability_contracts(contract_id),
    verdict TEXT NOT NULL CHECK (verdict IN (%s)),
    reason TEXT,
    decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS probe_runs (
    probe_run_id TEXT PRIMARY KEY,
    probe_plan_id TEXT,
    atom_id TEXT REFERENCES memory_atoms(atom_id),
    decision_id TEXT,
    command_hash TEXT,
    env_hash TEXT,
    exit_code INTEGER,
    stdout_hash TEXT,
    stderr_hash TEXT,
    executed_at TEXT NOT NULL,
    receipt_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_outcomes (
    outcome_id TEXT PRIMARY KEY,
    atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id),
    revision_id TEXT NOT NULL REFERENCES atom_revisions(revision_id),
    gate_id TEXT REFERENCES gate_decisions(gate_id),
    outcome TEXT NOT NULL CHECK (outcome IN (%s)),
    context_json TEXT,
    occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS maintenance_events (
    event_id TEXT PRIMARY KEY,
    atom_id TEXT REFERENCES memory_atoms(atom_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    reason TEXT,
    occurred_at TEXT NOT NULL,
    meta_json TEXT
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    actor TEXT,
    action TEXT,
    target TEXT,
    detail_json TEXT,
    occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS migration_issues (
    issue_id TEXT PRIMARY KEY,
    source_ref TEXT,
    issue_type TEXT,
    reason_code TEXT,
    detail_json TEXT,
    severity TEXT CHECK (severity IN (%s)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_transition_rules (
    rule_id TEXT PRIMARY KEY,
    atom_kind TEXT NOT NULL CHECK (atom_kind IN (%s)),
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    UNIQUE (atom_kind, from_state, to_state)
);
""" % (
    ATOM_KINDS,
    MATERIALITY,
    LINK_TYPES,
    EVIDENCE_SOURCES,
    MATERIALITY,
    CONFLICT_STATUS,
    PRAMANA,
    PURPOSES,
    VERDICTS,
    ROUTES,
    MATERIALITY,
    APPLICABILITY,
    USAGE,
    SEVERITY,
    ATOM_KINDS,
)

# Append-only history tables: UPDATE/DELETE are forbidden at all times.
APPEND_ONLY_TABLES = {
    "atom_revisions",
    "atom_state_events",
    "memory_links",
    "evidence_refs",
    "evidence_bundles",
    "evidence_bundle_items",
    "claim_evidence",
    "claim_conflicts",
    "pramana_reports",
    "reduction_proofs",
    "reduction_slots",
    "manas_decisions",
    "decision_consumptions",
    "write_attempts",
    "structured_drafts",
    "claims",
    "memory_events",
    "retrieval_runs",
    "retrieval_hits",
    "gate_decisions",
    "probe_runs",
    "usage_outcomes",
    "maintenance_events",
    "audit_events",
    "migration_issues",
}

# Every table the repository is permitted to write through the authorized path.
PROTECTED_TABLES = APPEND_ONLY_TABLES | {
    "memory_sessions",
    "epistemic_lineages",
    "memory_atoms",
    "applicability_contracts",
    "applicability_probes",
    "artifact_locators",
    "state_transition_rules",
    "schema_migrations",
}

# State transition rules seed (brief 10.4).
STATE_TRANSITION_SEED = [
    # NOUMENON
    ("NOUMENON", "OPEN", "PARTIALLY_REDUCED"),
    ("NOUMENON", "OPEN", "ABANDONED"),
    ("NOUMENON", "PARTIALLY_REDUCED", "RESOLVED"),
    ("NOUMENON", "PARTIALLY_REDUCED", "DORMANT"),
    ("NOUMENON", "PARTIALLY_REDUCED", "ABANDONED"),
    ("NOUMENON", "RESOLVED", "DORMANT"),
    ("NOUMENON", "DORMANT", "REOPENED"),
    ("NOUMENON", "REOPENED", "PARTIALLY_REDUCED"),
    ("NOUMENON", "ABANDONED", "REOPENED"),
    # HYPOTHESIS (U)
    ("HYPOTHESIS", "PROPOSED", "QUARANTINED"),
    ("HYPOTHESIS", "PROPOSED", "AUTHORIZED_FOR_TEST"),
    ("HYPOTHESIS", "QUARANTINED", "PROPOSED"),
    ("HYPOTHESIS", "AUTHORIZED_FOR_TEST", "TESTING"),
    ("HYPOTHESIS", "TESTING", "PARTIALLY_SUPPORTED"),
    ("HYPOTHESIS", "TESTING", "SUPPORTED"),
    ("HYPOTHESIS", "TESTING", "REFUTED"),
    ("HYPOTHESIS", "PARTIALLY_SUPPORTED", "SUPPORTED"),
    ("HYPOTHESIS", "PARTIALLY_SUPPORTED", "REFUTED"),
    ("HYPOTHESIS", "SUPPORTED", "SUPERSEDED"),
    ("HYPOTHESIS", "REFUTED", "SUPERSEDED"),
    ("HYPOTHESIS", "SUPERSEDED", "PROPOSED"),
    # FORM (F)
    ("FORM", "CANDIDATE", "VALIDATED"),
    ("FORM", "VALIDATED", "ACTIVE"),
    ("FORM", "ACTIVE", "WATCH"),
    ("FORM", "WATCH", "STALE"),
    ("FORM", "WATCH", "ACTIVE"),
    ("FORM", "STALE", "QUARANTINED"),
    ("FORM", "STALE", "ACTIVE"),
    ("FORM", "QUARANTINED", "STALE"),
    ("FORM", "QUARANTINED", "ARCHIVED"),
    ("FORM", "QUARANTINED", "REVOKED"),
    ("FORM", "ARCHIVED", "REVOKED"),
    ("FORM", "ACTIVE", "QUARANTINED"),
]

__all__ = [
    "SCHEMA_DDL",
    "APPEND_ONLY_TABLES",
    "PROTECTED_TABLES",
    "STATE_TRANSITION_SEED",
    "ATOM_KINDS",
    "MATERIALITY",
    "VERDICTS",
    "ROUTES",
    "PURPOSES",
    "EVIDENCE_SOURCES",
    "PRAMANA",
    "CONFLICT_STATUS",
    "LINK_TYPES",
    "APPLICABILITY",
    "USAGE",
    "SEVERITY",
    "N_STATES",
    "U_STATES",
    "F_STATES",
]
