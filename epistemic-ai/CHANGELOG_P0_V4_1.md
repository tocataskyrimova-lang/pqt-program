# CHANGELOG — P0 v4.1

## [P0-V4.1] — 2026-07-20 — Sovereignty-complete (P0_V4_1_COMPLETE)

Implemented the QVCH v4.1 package **beside** legacy `qvch_v3`, per
`BRIEF_QVCH_P0_V4_1_CODEX.md`. Legacy code and DB are never modified in
place. All P0-0…P0-J phases, Studio/CLI, the E2E cycle, and the Q1–Q17
qualification gates are implemented and verified by tests (159 passed,
1 skipped).

### New package `qvch_v4/`
- `forge` — QNUF-Forge v2.2: raw text → `StructuredDraft` with
  `noumenon_slots` (unknowns) and forbidden self-assertion detection.
- `cvl` — hard-claim extraction (EXTRACTED / GENERATED_HYPOTHESIS /
  NORMATIVE / OBSERVATION_REQUEST) with materiality + anchors.
- `pramana` — PRATYAKSA / ANUMANA / SABDA evidence classification + conflicts.
- `reduction` — Proof-of-Reduction: `ReductionVerifier.reduce()` /
  `can_crystallize()`; deterministic score; direct N→F rejected; residual
  unknowns force scoped `F_candidate`.
- `manas` — MANAS `ManasService.decide()` (sole envelope factory) +
  `Gateway.verify_with_signer()` (signature/expiry/hash/replay; F routes
  require a reduction proof) + `InMemoryConsumptionLedger`.
- `storage` — `QvchStore` (native `set_authorizer()` SQL boundary,
  `BEGIN IMMEDIATE`, `PRAGMA foreign_keys=ON`) + `Repository` (only
  production write path) + `schema` (v4.1 DDL, append-only tables,
  seeded state-transition rules).
- `retrieval` — epistemic retrieval separating semantic relevance from
  epistemic confidence; FTS5 + deterministic fallback; refuted atoms never
  returned as truth.
- `applicability` — Applicability Gate (preconditions + anti-conditions +
  mandatory Node 15 probes) + typed matcher.
- `probes` — `ProbePlan` / `ProbeReceipt` / `ProbeExecutor` (argv list,
  `shell=False`, env allowlist only, AUTHORIZE_TEST-gated).
- `spanda` — frozen-policy viability score; downward auto-transitions;
  upward requires `AUTHORIZE_STATE_TRANSITION`.
- `vinasha` — loss-of-influence; blocks degraded/non-applicable crystals;
  opens a new N via `DERIVED_FROM`; never deletes history.
- `safety` — materiality + recursive sanitization (secrets → opaque
  `SECRET_REF`).
- `policy.frozen` — versioned frozen Spanda/Vinasha policies.
- `studio` — thin operational API; refuses client approval flags; no
  command bypasses MANAS/Gateway.
- `cli` — `init`, `migrate`, `reconcile`, `ingest`, `retrieve`,
  `maintain`.

### New artifacts
- `scripts/e2e_v4_demo.py` — full N→U→F→use→degrade→new N cycle (14
  brief steps, asserted).
- `tests/test_v4_{a,b,c,d,e,f,g,h,i,j,studio,e2e}.py` — 104 v4 tests.
- `docs/QVCH_V4_ARCHITECTURE.md`, `QVCH_V4_SCHEMA.md`,
  `QVCH_V4_SECURITY_MODEL.md`, `QVCH_V4_STATE_MACHINES.md`,
  `MIGRATION_V3_TO_V4.md`, `TEST_REPORT_P0_V4_1.md`, `RESIDUAL_RISKS.md`.

### Bug fixes (during build)
- `reconcile` CLI no longer crashes on a non-UTF-8 Windows console
  (encoding-safe print; the markdown arrow `→` is preserved for the
  report).
- Spanda transitions use `dataclasses.replace` (frozen dataclasses, Py3.14).
- `_persist_probe` passes the receipt dict (not raw hash kwargs).
- Applicability Gate uses `PreconditionContext.build(os_platform=...)`.

### Constraint compliance
All ten главные ограничения preserved: legacy untouched until migration
reconciliation; new `qvch_v4` package; no A2A/NARC/blockchain/vector-DB;
LLM/Studio never self-approve; Node 15 requires `AUTHORIZE_TEST`; Gateway
requires `AUTHORIZE_WRITE` bound to a canonical `ProposedWritePlan`;
no secrets/keys/CoT/raw-legacy-payload persisted; no fabricated evidence or
mock-for-green; no `TODO`/`pass`/placeholder in critical path; completion
claimed only after working E2E + SQL evidence.
