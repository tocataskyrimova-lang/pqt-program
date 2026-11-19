# Residual Risks (no hiding)

These are limitations that remain after P0 v4.1. None of them relax a
sovereignty or security gate; they are scope/maturity boundaries.

## R1. Deterministic rerun match is `False` for uuid-bearing legacy rows

`ReconciliationReport.deterministic_rerun_match` reports `False` on the
fixture. Root cause: legacy v3 rows contain uuid-generated values, so a
second run does not reproduce byte-identical content hashes even though
**row counts and `mapped` are identical and idempotent** (no duplicate
atoms), and `fk_ok`/`integrity_ok` are `True`. The migration is therefore
idempotent at the structural level; the per-row hash match is a stricter
metric that the legacy data cannot satisfy. **Not** a blocker for Q16
(`can_cutover()` is `True`).

## R2. Probe commands are trusted argv

`ProbeExecutor` runs `plan.command` (an argv list, `shell=False`) in a
subprocess. The *authorization* (AUTHORIZE_TEST envelope, plan-hash
binding, expiry) is enforced; the *correctness* of the probe program
itself is the caller's responsibility and assumed trusted. Probes should
run in an isolated environment. No shell string is ever evaluated
(constraint #3/#19).

## R3. Reduction inputs are caller-supplied

`ReductionVerifier` is deterministic and never lets the LLM set the
score, but the *inputs* (baseline slots, evidence weights, acceptance
criteria, supported-U ids) are supplied by the orchestrating engine. The
verifier therefore guarantees internal consistency and gate enforcement,
not the honesty of upstream evidence classification. Pramāṇa classification
(CVL/evidence) is the upstream control.

## R4. In-memory consumption ledger in the demo

`Gateway.verify_with_signer()` accepts a `ledger` argument. The E2E demo
and unit tests pass `InMemoryConsumptionLedger`; production replay
protection should use the SQL `decision_consumptions` UNIQUE
(`decision_id`,`nonce`) contract (already implemented and append-only).
The in-memory ledger is a reference implementation, not the production
boundary.

## R5. Spanda score tuning

The frozen `SpandaPolicy` weights were tuned so a healthy FORM stays
`ACTIVE` and a clearly degraded FORM reaches `QUARANTINED`/`STALE` within
the seeded state machine. The thresholds are versioned and frozen; they
have not been calibrated against a large production workload. The
`ACTIVE → STALE` step is intentionally two-phase (`ACTIVE → QUARANTINED`
or `ACTIVE → WATCH → STALE`) because no direct rule is seeded.

## R6. Retrieval freshness is heuristic

`freshness_for_state` and Laplace priors (0.5 uninformative) are
deliberate guards against over-confident retrieval, not a learned ranking.
They prioritize "not returning refuted/low-support atoms as truth" over
relevance tuning.

## R7. Legacy scope

Only a representative subset of v3 concepts is mapped (the fixture covers
atoms, evidence, hypotheses, crystals, events, probes, repairs, skills).
Real v3 deployments may carry concepts not in the fixture; unmapped rows
are reported via `migration_issues` and **redacted**, never force-copied.

## R8. No external services (by design)

No vector DB, message broker, blockchain, A2A, or NARC (constraint #3).
Retrieval is FTS5 + deterministic fallback; this bounds scale to what
SQLite FTS5 handles and is intentional for this phase.
