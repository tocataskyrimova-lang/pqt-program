# Test Report — P0 v4.1

## Summary

| Suite | Files | Tests | Result |
|-------|-------|-------|--------|
| v4 unit/integration/adversarial | `test_v4_{a,b,c,d,e,f,g,h,i,j,studio,e2e}.py` (12) | 104 | 104 passed |
| Legacy regression (Q15) | `test_ext1_dry.py`, `test_life1_stage2.py`, `test_mvp.py`, `test_qvch_studio.py` | 56 | 55 passed, 1 skipped |
| **Total** | | **160** | **159 passed, 1 skipped** |

The 1 skipped is a pre-existing PQT-core drift test (skipped via the
portability guard, not a failure). No v4 test is skipped.

Run command:
```powershell
PYTHONPATH=(Get-Location).Path python -m pytest tests/ -q
# -> 159 passed, 1 skipped
```

## v4 per-file matrix

| File | Phase | Tests | Covers |
|------|-------|-------|---------|
| `test_v4_a.py` | P0-A QNUF-Forge v2.2 | 9 | StructuredDraft; noumenon slots; canonical hash deterministic (Q7) |
| `test_v4_b.py` | P0-B Safety | 10 | Materiality; recursive sanitization; secret → opaque `SECRET_REF` locator+hash (Q5, Q6) |
| `test_v4_c.py` | P0-C CVL/Pramāṇa | 9 | Claim extraction; PRATYAKSA/ANUMANA/SABDA; conflicts |
| `test_v4_d.py` | P0-D Proof-of-Reduction | 10 | `ReductionVerifier.reduce`/`can_crystallize`; scoped `F_candidate`; direct N→F rejected (Q3, Q4) |
| `test_v4_e.py` | P0-E MANAS Envelope | 11 | **Adversarial**: forged / expired / reused-nonce / mismatched draft·payload·route rejected (Q2) |
| `test_v4_f.py` | P0-F SQL boundary | 13 | **Adversarial**: direct INSERT/UPDATE/DELETE/REPLACE/DDL blocked; forbidden state transition rolls back (Q7, Q8, Q4) |
| `test_v4_g.py` | P0-G Migration | 9 | 12 mapped / 0 unmapped / 0 critical; idempotent rerun; reconciliation serialization (Q16) |
| `test_v4_h.py` | P0-H Retrieval | 9 | FTS5+fallback; refuted atom not truth; contradiction visible; relevance ≠ confidence; lineage/status returned (Q9, Q10) |
| `test_v4_i.py` | P0-I Applicability Gate + Node 15 | 8 | Happy path APPLY; mismatched precondition → CAUTIOUS; probe without AUTHORIZE_TEST not executed; mandatory failed probe → QUARANTINE; anti-condition; usage bound to revision (Q11, Q12) |
| `test_v4_j.py` | P0-J Spanda + Vinasha | 7 | Healthy stays ACTIVE; degradation → QUARANTINED; Vinasha new N + blocks; history preserved; upward needs MANAS; frozen policy; blocked states (Q13, Q14) |
| `test_v4_studio.py` | Studio/CLI | 8 | CLI init/ingest/retrieve/maintain; ingest via AUTHORIZE_WRITE; secret sanitized; analyze read-only; client approval flags refused (Q1, Q5) |
| `test_v4_e2e.py` | E2E | 1 | Full N→U branches→F→use→degrade→new N cycle via `scripts/e2e_v4_demo.py` (Q17) |

## Qualification gate → test trace (Q1–Q17)

| Gate | Verified by |
|------|-------------|
| Q1 LLM/Studio/Planner cannot self-approve | `test_v4_studio.py::test_studio_refuses_client_approval_flags`; `test_v4_d.py` (score not LLM-set); `test_v4_e.py` (forged envelope rejected) |
| Q2 forged/expired/mismatched/replayed rejected | `test_v4_e.py` (5 tests) |
| Q3 F impossible without verified Reduction Certificate | `test_v4_d.py`; enforced in `Gateway` (F routes require `reduction_proof_hash`+`has_reduction_proof`) |
| Q4 direct N→F / forbidden transitions impossible | `test_v4_d.py` (direct N→F rejected); `test_v4_f.py::test_forbidden_state_transition_rolls_back` |
| Q5 secret in no column/audit/receipt | `test_v4_studio.py::test_ingest_secret_is_sanitized`; `test_v4_b.py` |
| Q6 literal artifact by locator+hash | `test_v4_b.py::test_materiality_literal_artifact`; `test_v4_h.py::test_literal_artifact_returned_as_locator_and_hash` |
| Q7 each atom owns its canonical content | `test_v4_a.py::test_canonical_hash_deterministic`; schema `atom_revisions.canonical_payload_json` |
| Q8 revision immutable; change → new revision | `test_v4_f.py::test_direct_update_blocked`/`test_direct_replace_blocked` (append-only trigger) |
| Q9 retrieval distinguishes relevance vs epistemic confidence | `test_v4_h.py::test_no_evidence_confidence_not_one`/`test_scoring_formulas_match_spec` |
| Q10 evidence/contradictions/lineage/status returned explicitly | `test_v4_h.py` (contradiction visible; states distinguishable; locator+hash) |
| Q11 crystal not applied without Applicability Gate | `test_v4_i.py`; `test_v4_studio.py::test_cli_ingest_and_retrieve` (apply path) |
| Q12 failed mandatory probe blocks APPLY | `test_v4_i.py::test_mandatory_failed_probe_blocks_apply` |
| Q13 stale/revoked crystal loses influence automatically | `test_v4_j.py::test_vinasha_blocked_states`/`test_spanda_degradation_moves_to_quarantine` |
| Q14 Vinasha preserves history + opens new N on degradation | `test_v4_j.py::test_vinasha_preserves_history`/`test_vinasha_creates_new_n_and_blocks` |
| Q15 all legacy + v4 tests pass | 159 passed, 1 skipped (full `tests/`) |
| Q16 migration idempotent, integrity/FK clean | `test_v4_g.py` (idempotent rerun; `can_cutover()`; `fk_ok`/`integrity_ok`) |
| Q17 E2E full cycle | `test_v4_e2e.py` (asserts all 14 brief steps) |

## Adversarial coverage (explicit)

The v4 suite deliberately includes negative tests for every sovereignty claim:
forged/expired/replayed/mismatched decision envelopes (Q2), direct SQL
writes of every major kind (Q7/Q8), direct N→F (Q3/Q4), secret leakage
into any TEXT column (Q5), and mandatory-probe bypass (Q12). These are
real assertions, not mocks (constraint #8).
