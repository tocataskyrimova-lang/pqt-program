# QVCH v4.1 — Security Model

Enforces the central law **"LLM confidence is not evidence"** and the ten
principal constraints (главные ограничения) from the brief.

## 1. Sovereignty: the LLM never approves (Q1)

- `Studio.ingest_observation()` derives the `verdict` **system-side** from
  pipeline validity (`forbidden_fields_detected → QUARANTINE`, else
  `APPROVE`). It never reads a client flag.
- `_guard_no_client_approval()` refuses `approved` / `safe_to_commit` /
  `verdict` / `approved_by` kwargs and raises `ValueError`.
- `ReductionVerifier` computes the reduction score by a single deterministic
  formula; the LLM supplies inputs (slots, evidence weights) but **never**
  the score. `can_crystallize()` enforces every gate.
- `ManasService.decide()` is the **only** production factory of a
  `ManasDecisionEnvelope`. A hand-built ("forged") envelope fails
  signature verification.

## 2. Decision Envelope Gate (Q2)

`Gateway.verify_with_signer()` rejects, independently:
- **forged** (wrong signature);
- **expired** (envelope `expires_at ≤ now`);
- **mismatched** `target_hash` / `draft_hash` / `sanitized_payload_hash`
  (changed write plan);
- **mismatched** `route`;
- **policy-version** mismatch;
- **replay** — `InMemoryConsumptionLedger` / SQL
  (`UNIQUE(decision_id)`, `UNIQUE(nonce)`) allow only the first valid
  attempt to consume; a replay is rejected without altering memory.

For F routes (`F`, `F_candidate`, `CRYSTAL`) the Gateway additionally
requires a non-null `reduction_proof_hash` **and** `ctx.has_reduction_proof`.

## 3. Proof-of-Reduction required for F (Q3, Q4)

- A `FORM`/`CRYSTAL` cannot be created without a verified Reduction
  Certificate (enforced in §2).
- `can_crystallize()` forbids **direct N→F** (`resolved_weight > 0`
  is required; a chain that resolves nothing is rejected).
- Residual unknowns force a **scoped** `F_candidate` (`allow_scoped=True`);
  a global `FACT` requires full resolution (`residual_unknown_slots` empty).

## 4. SQL authorizer boundary (Q7, Q8, constraint #6)

`QvchStore.set_authorizer()` is a native SQLite authorizer (not regex):
`SELECT` always allowed; `INSERT` only into protected tables inside an
authorized `write_scope` (`BEGIN IMMEDIATE`) transaction; `UPDATE`/`DELETE`/
`DROP`/`ALTER` denied (raise `sqlite3.DatabaseError`). History tables are
also `append-only` by trigger. A revision's `content_hash` is UNIQUE and
immutable; a change creates a **new** revision + state event.

## 5. Secrets and sensitive material (Q5, constraint #7)

- `safety.scan()` detects secrets; `sanitize_payload()` replaces them with
  opaque markers; materiality is set to `SECRET_REF`.
- The signing key stays in the `DecisionSigner` — never written to the DB,
  logs, or source.
- Raw legacy `WritePlan` payloads and hidden chain-of-thought are **not**
  persisted (constraint #7).
- `ProbeExecutor._build_env()` passes **only** an explicit allowlist of
  environment variables to the probe subprocess — secret variables are never
  propagated into the probe process.

## 6. Node 15 probe authorization (constraint #5)

A probe is executed by `ProbeExecutor` **only** with a valid
`AUTHORIZE_TEST` envelope bound to `plan.plan_hash()` and not expired;
otherwise it returns a `success=False` receipt and records an
`PROBE_EXECUTION_FORBIDDEN` audit event. Probes run with `shell=False`
on an argv list (no shell string evaluation).

## 7. Crystal application (Q11, Q12, Q13)

- An `Applicability Gate` decision is **required** before a crystal is
  applied; the bound usage outcome references the exact revision + gate.
- A failed **mandatory** probe → `QUARANTINE` (no `APPLY`).
- A `STALE` / `REVOKED` / `QUARANTINED` / `ARCHIVED` / `ABANDONED` /
  `REFUTED` / `SUPERSEDED` crystal loses the auto-apply right
  (`Vinasha.is_blocked`).
- Spanda applies **downward** transitions automatically (only reduces
  influence); **upward** (re-activation) requires a valid
  `AUTHORIZE_STATE_TRANSITION` envelope. On degradation, Vinasha opens a
  new N via `DERIVED_FROM` and never deletes history.

## 8. Forbidden (constraint #3, #9, #10)

No A2A Exchange / NARC / blockchain / external vector DB / new experimental
functionality. No `eval` / `exec` / arbitrary pickle / shell strings.
No fabricated evidence to pass a gate. No `TODO` / `pass` / placeholder module
in the critical path. Completion is claimed only after a working E2E and SQL
evidence — never on the presence of class names alone.

## 9. What is NOT a guarantee (residual)

See `docs/RESIDUAL_RISKS.md`. Highlights: the deterministic rerun match in
the reconciliation report is `False` for uuid-bearing legacy rows (counts are
still idempotent and FK/integrity clean); probe commands are trusted argv
(run in an isolated environment); reduction weights/evidence are supplied by the
caller, so caller-side honesty of inputs is assumed (the verifier is
deterministic, not adversarial to its own inputs).
