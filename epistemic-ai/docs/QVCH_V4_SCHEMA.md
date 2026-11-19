# QVCH v4.1 — SQL Schema

SQL-first, deterministic SQLite substrate. Source: `qvch_v4/storage/schema.py`.
Every real relation has an FK; history tables are **append-only** (UPDATE/DELETE
forbidden by trigger *and* by the connection authorizer). Writes go through the
`Repository` — never a raw SQL string.

## Tables (PK / FK / UNIQUE / CHECK)

| Table | PK | Key FKs | UNIQUE | Notable CHECK |
|-------|----|----------|---------|----------------|
| `schema_migrations` | version | — | — | — |
| `memory_sessions` | session_id | → memory_sessions (session) | — | — |
| `memory_events` | event_id | session_id | content_hash | — |
| `epistemic_lineages` | lineage_id | — | — | — |
| `memory_atoms` | atom_id | lineage_id → epistemic_lineages | — | `atom_kind`, `materiality_class`, `current_state` |
| `atom_revisions` | revision_id | atom_id → memory_atoms (RESTRICT) | `content_hash`; (atom_id, revision_number) | `state` |
| `atom_state_events` | event_id | atom_id → memory_atoms (RESTRICT) | — | — |
| `memory_links` | link_id | from_atom_id, to_atom_id → memory_atoms (RESTRICT) | — | `link_type` |
| `evidence_refs` | evidence_id | — | content_hash | source_type, llm_confidence |
| `evidence_bundles` | bundle_id | — | content_hash | — |
| `evidence_bundle_items` | item_id | bundle_id CASCADE, evidence_id RESTRICT | (bundle_id, evidence_id) | — |
| `structured_drafts` | draft_id | — | canonical_hash | `json_valid(payload_json)` |
| `claims` | claim_id | draft_id CASCADE | — | claim_type, materiality_class |
| `claim_evidence` | (claim_id, evidence_id) | both RESTRICT | PK | — |
| `claim_conflicts` | conflict_id | — | — | status |
| `pramana_reports` | report_id | claim_id CASCADE | canonical_hash | pramana_type |
| `reduction_proofs` | proof_id | lineage_id, noumenon_atom_id | proof_hash | — |
| `reduction_slots` | slot_id | proof_id CASCADE | — | resolved IN (0,1) |
| `manas_decisions` | decision_id | — | canonical_hash | purpose, verdict, route |
| `decision_consumptions` | consumption_id | — | decision_id, nonce | — |
| `write_attempts` | attempt_id | — | — | — |
| `artifact_locators` | locator_id | — | immutable_content_hash | materiality_class |
| `applicability_contracts` | contract_id | atom_id, revision_id CASCADE | (atom_id, revision_id) | — |
| `applicability_probes` | probe_id | contract_id CASCADE | — | — |
| `retrieval_runs` | run_id | — | — | — |
| `retrieval_hits` | hit_id | run_id CASCADE, atom_id, revision_id | — | outcome |
| `gate_decisions` | gate_id | atom_id, revision_id, contract_id | — | verdict |
| `probe_runs` | probe_run_id | atom_id | — | — |
| `usage_outcomes` | outcome_id | atom_id, revision_id, gate_id | — | outcome |
| `maintenance_events` | event_id | atom_id CASCADE | — | — |
| `audit_events` | event_id | — | — | — |
| `migration_issues` | issue_id | — | — | severity |

## Append-only boundary

`APPEND_ONLY_TABLES` = all `*_revisions`, `*_state_events`, `*_links`,
`*_refs`, `*_bundles`, `*_reports`, `*_proofs`, `*_slots`, `*_decisions`,
`*_consumptions`, `*_attempts`, `*_drafts`, `*_claims`, `*_events`,
`*_runs`, `*_hits`, `*_gate_decisions`, `*_probe_runs`, `*_usage_outcomes`,
`*_maintenance_events`, `*_audit_events`, `*_migration_issues`.

`PROTECTED_TABLES` = append-only set ∪ {`memory_sessions`,
`epistemic_lineages`, `memory_atoms`, `applicability_contracts`,
`applicability_probes`, `artifact_locators`, `state_transition_rules`,
`schema_migrations`}.

`QvchStore.set_authorizer()` implements the SQL boundary **natively** (not
regex): `SELECT` is always permitted; `INSERT` is permitted only into
protected tables inside an authorized `write_scope` transaction; `UPDATE`/`DELETE`/
`DROP`/`ALTER` are denied (raising `sqlite3.DatabaseError`). This makes the
boundary verifiable by SQL, not by string matching (P0-F / Q7,Q8).

## State-transition seed (brief 10.4)

Enforced by the `atom_state_check` BEFORE UPDATE trigger; a forbidden
transition raises `sqlite3.IntegrityError` and rolls back.

```
NOUMENON   OPEN -> PARTIALLY_REDUCED -> RESOLVED -> DORMANT -> REOPENED -> ABANDONED
HYPOTHESIS PROPOSED -> QUARANTINED/AUTHORIZED_FOR_TEST -> TESTING
            TESTING -> PARTIALLY_SUPPORTED/SUPPORTED/REFUTED
            PARTIALLY_SUPPORTED -> SUPPORTED/REFUTED
            SUPPORTED/REFUTED -> SUPERSEDED -> PROPOSED
FORM        CANDIDATE -> VALIDATED -> ACTIVE -> WATCH -> STALE -> QUARANTINED
            -> ARCHIVED/REVOKED ; ACTIVE -> QUARANTINED ; WATCH -> ACTIVE
            ; STALE -> ACTIVE/QUARANTINED
```

Note: `ACTIVE -> STALE` and `ACTIVE -> QUARANTINED` are valid; `ACTIVE ->
STALE` is **not** a single direct step (the gateway therefore drives a
degraded crystal to `QUARANTINED` in one step, or `WATCH` then `STALE`).

## Hashes

`sha256_hex(data) = "sha256:" + hexdigest` (never re-prepend).
`canonical_json(v) = json.dumps(v, ensure_ascii=False, sort_keys=True,
separators=(",",":"))`. `hash_json(v) = sha256_hex(canonical_json(v))`.
`content_hash` is UNIQUE across `atom_revisions` / `evidence_refs` and is the
immutable binding the Gateway verifies (`observed_target_hash`).
