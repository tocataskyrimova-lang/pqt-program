# BRIEF QVCH P0-V4.1-R3
## Final Trust Anchor, Atomic Ingest and Form-Proof Closure

**Executor:** Claude Code / Codex  
**Input:** `QVCH_v3(3).zip` and the independent R2 audit  
**Scope:** final closure of already-declared P0/R2 invariants only  
**Forbidden:** P1 features, UI expansion beyond v4 cutover, A2A, NARC, vector DB, unrelated refactor

## 0. Final command

Preserve the valid R1/R2 work. Close the remaining *classes* of bypass demonstrated by `test_qvch_v4_1_r3_regressions.py`.

Do not patch only the literal test inputs. The implementation must establish one anchored trust root, one all-surface safe ingest transaction, an unconditional F-proof law, server-computed SQL reduction and a non-public maintenance authority.

Completion requires all ten external R3 regressions to pass unmodified, plus all existing tests and a revised production-only E2E.

---

## 1. Pin the runtime trust root

The trust root must not be selectable per `Studio` or `Repository` instance.

Replace:

```text
Studio(store, keyring=caller_keyring)
Repository(store, keyring=caller_keyring)
```

with a composition-root-owned runtime:

```text
QvchRuntime(
    store,
    authority_client,
    verifier,
    maintenance_authority_client,
    policy_registry,
)
```

Requirements:

- public callers cannot inject signing-capable verification material;
- `Studio` receives a `ManasAuthorityClient`, not a signer or keyring;
- `Repository` receives an internal verifier handle from `QvchRuntime` only;
- no public property exposes a private signing key;
- remove `LocalManasAuthority.signer` from public API;
- remove every public Studio `signer` parameter;
- CLI obtains the authority client from the composition root and never reads a signer;
- E2E never reads signer material.

### Cryptographic requirement

Production verification should use asymmetric signatures:

```text
authority owns Ed25519 private key
runtime Gateway owns public verification key only
```

HMAC may remain only in an explicitly named isolated test/dev adapter. A component holding an HMAC verification secret can also sign and is not a sovereign verifier.

---

## 2. Remove arbitrary privileged mutation callbacks

`Repository.authorized_write(..., mutate)` must not be callable by ordinary runtime code with an arbitrary callback and live connection.

Implement an internal typed coordinator:

```text
WriteCoordinator.execute(AuthorizedWriteIntent)
```

Allowed sealed intent variants include only:

- `CreateNoumenonIntent`;
- `CreateHypothesisIntent`;
- `CreateFormIntent`;
- `TransitionAtomIntent`;
- `CreateLinkIntent`;
- `PersistReductionIntent`;
- `DeclareApplicabilityIntent`;
- `RecordProbeIntent`;
- `MaintenanceDegradationIntent`.

Requirements:

- intent is canonical and hash-bound before MANAS decision;
- operation, target, route and expected SQL mutation are fixed by the intent type;
- no caller function receives the SQL connection;
- no public `_emit_*` path is used by application callers;
- verifier and write coordinator are created only by the runtime composition root;
- a caller-created signer/keyring/authority cannot authorize the store.

---

## 3. Make ingest safe before persistence and fully atomic

Current order is forbidden:

```text
persist raw draft/claims
→ sanitize
→ authorize atom
```

Required order:

```text
raw source remains ephemeral
→ recursive sanitize
→ independent second scan
→ materiality classification
→ Forge/anchor validation over a safe source representation
→ canonical safe draft/claims/evidence/write intent
→ MANAS decision
→ one SQL transaction
```

The single transaction must include:

- sanitized memory event/source descriptor;
- StructuredDraft;
- claims;
- lineage;
- evidence bundle/references;
- MANAS decision;
- decision consumption;
- atom + revision + state event;
- write attempt/audit.

If any step fails, all rows roll back.

### Hard secret gate

For the adversarial secret corpus, after success or failure:

```text
secret literal in any TEXT/BLOB SQL value = 0
secret literal in SQLite file bytes       = 0
```

Tests must scan every table/column, not only atom revisions and evidence refs.

Anchor quotations containing secrets must persist only a redacted marker and non-reversible fingerprint.

---

## 4. Enforce proof for every FORM unconditionally

`FORM` is a proven epistemic type. Therefore:

```text
reduction_proof_hash is mandatory for every CreateFormIntent
```

Rules:

- `FORM/CANDIDATE` without proof is forbidden;
- an unproved candidate is `HYPOTHESIS/PROPOSED`, not FORM;
- remove `requires_proof = bool(reduction_proof_hash)`;
- missing proof always fails;
- proof must belong to the same lineage/root N;
- transitions `CANDIDATE → VALIDATED → ACTIVE` must verify the bound proof remains live and not revoked;
- add relational `form_proof_bindings(form_atom_id, proof_id, decision_id, bound_at)` with FKs and UNIQUE form binding;
- SQL or trigger-level enforcement must prevent an unbound FORM.

---

## 5. MANAS must derive verdict from trusted reports, not purpose

Remove the rule:

```text
known purpose -> APPROVE
```

The authority receives IDs/hashes only and loads trusted decision facts from a read-only `DecisionView`.

Minimum derivation:

### Write N

Approve only when:

- sanitization clean;
- materiality classified;
- Forge/schema valid;
- forbidden fields absent;
- anchors valid for extracted claims;
- canonical write intent matches requested hash.

### Write U

Additionally require:

- source/root lineage exists;
- U is a declared hypothesis/proposal, not extracted FACT;
- initial state is allowed.

### Write F

Additionally require:

- SQL-derived live Reduction Verdict;
- same lineage/root N;
- no blocking conflict;
- proof hash matches server-computed certificate;
- requested FORM scope equals proof scope.

### State transition

Require:

- allowed state-machine edge;
- operation-specific prerequisites;
- F proof remains live for validation/activation.

### Test

Require:

- policy-approved canonical ProbePlan;
- resource/network/environment restrictions.

Missing or conflicting facts produce `QUARANTINE` or `REJECT`, never default APPROVE.

---

## 6. Build the Reduction Certificate from normalized SQL facts

The caller must not submit a `ReductionCertificate` or final score.

Replace:

```text
Studio.record_reduction(caller_certificate, ...)
```

with:

```text
Studio.request_reduction(ReductionRequest(ids only))
```

Normalize at minimum:

- `reduction_supported_u(proof_id, atom_id)`;
- `reduction_evidence_bundles(proof_id, bundle_id)`;
- `reduction_evidence_refs(proof_id, evidence_id)`;
- `reduction_test_receipts(proof_id, probe_run_id, criterion_id)`;
- `reduction_baseline_slots(proof_id, slot_id, weight)`;
- `reduction_resolved_slots(proof_id, slot_id)`;
- `reduction_conflicts(proof_id, conflict_id, blocking)`;
- `reduction_residual_slots(proof_id, slot_id)`.

All relations require real FKs.

Server procedure:

1. load root N and baseline slots;
2. load supported U and verify state/lineage;
3. load support-bearing evidence;
4. load immutable Node 15 receipts and acceptance criteria;
5. load conflicts;
6. derive resolved/residual slots;
7. build `ReductionInput` internally;
8. compute score via `ReductionVerifier`;
9. persist only the server-produced certificate and normalized relations;
10. return proof ID/hash to MANAS.

A caller-supplied altered score/hash must be rejected even when internally content-consistent.

---

## 7. Restrict maintenance authority

`Spanda(store)` and `Vinasha(store)` must not create their own signer/keyring.

They receive a non-exported system maintenance client from `QvchRuntime`.

A degradation plan requires:

- source is `FORM`;
- source state is `STALE` or `QUARANTINED`, never plain ACTIVE;
- persisted failed mandatory probe, gate quarantine, dependency drift or equivalent evidence;
- Spanda assessment hash;
- fixed new-N question template and source revision binding.

Commit atomically as one `MaintenanceDegradationIntent`:

- maintenance decision and consumption;
- maintenance event;
- new N + revision + state event;
- `DERIVED_FROM` link;
- audit.

Ordinary callers cannot invoke a maintenance authority or provide an arbitrary reason as sufficient authorization.

---

## 8. Cut over the actual HTTP Studio

`apps/qvch_studio/server.py` must not remain a writable v3 self-approval surface.

Choose one:

1. migrate it to `qvch_v4.studio` and `QvchRuntime`; or
2. move it to an explicitly named `legacy_read_only` path and disable commit endpoints; or
3. remove it from production/run scripts.

Hard gate:

```text
no writable shipped UI imports qvch_v3 ManasReview
no writable shipped UI constructs approved=True / positional True review
```

---

## 9. Public API cleanup

Remove `signer` from every public Studio mutation signature.

Remove public access to:

- signing keys;
- signing-capable keyring values;
- arbitrary `authorized_write` callbacks;
- maintenance signer/authority construction;
- runtime `_write_scope` and `_emit_*` use outside storage internals.

Compatibility belongs in an external adapter that cannot perform protected writes, not in the sovereign API.

---

## 10. Packaging and reproducibility

Ship:

- `BREAF/R3_CLOSURE_REPORT.md`;
- `pyproject.toml` with exact test requirements;
- all R1, corrected R2 and R3 regression files;
- exact self-contained test count;
- external-substrate count separately;
- wheel rebuilt from the same source tree;
- source/wheel hash manifest.

Do not claim tests not present in the archive.

---

## 11. Mandatory tests

Include and pass unmodified:

```text
test_qvch_v4_1_r3_regressions.py
```

Also retain all previous R1/R2 tests after correcting only the previously acknowledged contradictory Vinasha fixture setup.

Add tests for:

- no raw secret in any table/column or file bytes after success/failure;
- failed ingest leaves zero rows;
- FORM insert without relational proof binding fails at SQL layer;
- activation after proof revocation/quarantine fails;
- alternate Repository/Studio trust root rejected;
- arbitrary mutation callback is impossible through public API;
- caller cannot instantiate maintenance authority;
- production HTTP Studio uses v4 sovereign runtime;
- authority missing one trusted report returns QUARANTINE;
- forged score with valid U/evidence is recomputed/rejected.

---

## 12. Revised production E2E

The E2E must use only the public `QvchRuntime` / Studio API.

It must not contain:

- `DecisionSigner`;
- `.signer` / `._signer`;
- caller keyring construction;
- `Repository.authorized_write`;
- `_emit_*`;
- `_write_scope`;
- migration fixture writes in the production scenario.

Add explicit demonstrations:

1. alternate caller trust root cannot be installed;
2. failed ingest leaves no rows and no secret bytes;
3. FORM without proof fails;
4. inflated caller score cannot be submitted;
5. maintenance on ACTIVE FORM fails;
6. valid degradation creates N+link atomically;
7. actual HTTP/CLI write route reaches v4 runtime.

---

## 13. Final gates

```text
R3-Q1  runtime caller cannot choose trust root
R3-Q2  caller cannot submit arbitrary privileged mutation callback
R3-Q3  every FORM has relational SQL proof binding
R3-Q4  missing proof can never create/activate FORM
R3-Q5  ingest sanitizes before persistence
R3-Q6  failed ingest leaves zero rows
R3-Q7  no secret survives in any SQL/file surface
R3-Q8  MANAS does not approve from purpose alone
R3-Q9  reduction score/certificate are server-built from SQL
R3-Q10 maintenance is evidence-gated and non-public
R3-Q11 actual writable Studio is v4 sovereign path
R3-Q12 public mutation APIs contain no signer
R3-Q13 all prior valid R1/R2 gates remain green
R3-Q14 archive test claims are fully reproducible
R3-Q15 production E2E contains no key/capability/storage bypass
```

Any single failure blocks completion.

---

## 14. Final report

Return:

1. exact status;
2. files changed;
3. runtime trust-boundary diagram;
4. public API diff;
5. typed WriteIntent matrix;
6. atomic ingest transaction trace;
7. normalized proof DDL and SQL derivation trace;
8. maintenance authorization trace;
9. v3 HTTP Studio disposition/cutover;
10. R1/R2/R3 test results with exact commands;
11. self-contained vs external test counts;
12. wheel/source hash manifest;
13. residual risks.

Do not call R3 complete while any ordinary in-process caller can choose a signing key, create a verifier that trusts it, pass an arbitrary mutation callback, create FORM without proof, or persist raw input before sanitization.
