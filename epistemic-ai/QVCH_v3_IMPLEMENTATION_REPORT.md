# QVCH_v3 Implementation Report

Date: 2026-05-21
Root: `C:\AGI\QVCH_v3`

## Summary

Implemented a clean-start MVP of QVCH_v3 as a cognitive memory system, not a continuation of `qvch_dist_v2`.

Central invariant:

```text
LLM confidence is not evidence.
```

The implementation establishes a conservative local-only pipeline:

```text
RawExperience
→ NormalizedEvent
→ StructuredDraft
→ MANAS Review
→ Safety Review
→ Validation
→ WritePlan
→ MemoryWriteGateway
→ SQLite persistence
→ Retrieval / Probe / Monitor
```

SQLite is treated only as persistence substrate. Memory intake is routed through `MemoryWriteGateway.commit(WritePlan)`.

## Implemented Components

### Package Structure

Created package:

```text
C:\AGI\QVCH_v3\qvch_v3
```

Main subsystems:

- `contracts` — dataclass/JSON-compatible cognitive contracts.
- `core` — normalization, deterministic structuring, write-plan builders, Noumenon lifecycle helpers.
- `manas` — conservative MANAS review and validation logic.
- `safety` — deterministic secret scanning/redaction.
- `storage` — SQLite schema, DB wrapper, write gateway.
- `retrieval` — status-aware retrieval and memory probe.
- `monitor` — basic health reporting.

### Core Contracts

Implemented first-class contracts for:

- `RawExperience`
- `NormalizedEvent`
- `StructuredDraft`
- `MemoryAtomDraft`
- `ManasReview`
- `SafetyReview`
- `EvidenceRef`
- `ValidationResult`
- `WritePlan`
- `WriteReceipt`
- `NoumenonRecord`
- `NoumenonTransition`
- `NResolutionLink`
- `RepairPair`
- `SkillCandidate`
- `CrystalRecord`
- `RetrievalResult`
- `MemoryProbeResult`

### Living Noumenon Lifecycle

Implemented Noumenon as a dynamic object, not just a storage row.

Supported lifecycle states:

```text
N_open
→ revisited
→ guidance_received
→ partially_resolved
→ resolved_to_F_candidate
→ promoted_to_F
→ crystallized
→ retired
```

Implemented helper interfaces:

- `open_noumenon_backlog()`
- `revisit_noumenon()`
- `receive_guidance()`
- `partially_resolve_noumenon()`
- `resolve_noumenon()`
- `transition_noumenon()`

### Repair Pair Lineage

Implemented first-class repair lineage:

```text
bad answer
→ correction / critique
→ improved answer
→ repair pair candidate
```

A `RepairPair` stores:

- bad answer;
- failure reason;
- correction source;
- corrected answer;
- validation status;
- evidence refs;
- linked Noumenon ids;
- linked SkillCandidate id.

Repair pairs are retrievable and can resolve Noumena.

### Skill Emergence Tracking

Implemented `SkillCandidate` as a first-class object created from repeated successful repairs.

Rules encoded in tests:

- one success is not a reflex;
- repeated repairs can create a skill candidate;
- skill candidate does not become cognitive reflex without future validation.

### Write Gateway Discipline

Implemented `MemoryWriteGateway` as the only persistence boundary.

Gateway accepts only `WritePlan`, not raw text.

Gateway verifies:

- normalized event exists;
- MANAS review exists and is approved;
- safety review exists and passed;
- atomization exists for N/U/F/crystal routes;
- route is explicit;
- crystal requires non-LLM evidence;
- secret redaction is applied when needed;
- audit row is written for committed and rejected plans.

### SQLite Schema v0

Implemented schema tables:

- `memory_events`
- `memory_atoms`
- `noumena`
- `noumenon_transitions`
- `hypotheses`
- `repair_pairs`
- `skill_candidates`
- `crystals`
- `evidence_refs`
- `write_plans`
- `write_audit`
- `probe_runs`
- `monitor_events`

### Retrieval / Probe / Monitor

Implemented:

- status-aware retrieval returning epistemic status and lineage;
- memory probe that validates actual retrievability, not just write success;
- basic monitor health report for counts of events, atoms, open N, repair pairs, skills, crystals, and probe failures.

## Documentation Added

Created docs:

- `docs/ARCHITECTURE.md`
- `docs/GLOSSARY.md`
- `docs/NO_DIRECT_DB_WRITE.md`
- `docs/DONOR_POLICY.md`

Also created project `README.md` and `pytest.ini`.

## Tests

Implemented MVP test suite:

```text
C:\AGI\QVCH_v3\tests\test_mvp.py
```

Coverage includes all requested MVP scenarios:

1. Raw input cannot be written directly to DB.
2. Unknown creates `N_open`.
3. Revisited unknown creates `revisited` transition.
4. Guidance updates N to `guidance_received`.
5. Partial answer creates `partially_resolved`, not F.
6. Valid evidence can resolve N to F candidate.
7. Crystal can link back to resolved N.
8. Bad answer + correction creates `RepairPair`.
9. RepairPair can resolve an N.
10. Repeated similar RepairPairs create `SkillCandidate`.
11. SkillCandidate does not become reflex without validation.
12. Secret inside repair/correction is redacted.
13. LLM confidence alone cannot promote F or crystal.
14. Retrieval returns epistemic status and lineage.
15. Memory Probe verifies usability, not just write success.

Latest verification:

```text
15 passed in 1.54s
```

Command used:

```powershell
cd C:\AGI\QVCH_v3
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider
```

## Donor Policy Status

`C:\AGI\PQT-transformers\qvch_dist_v2` was not imported as runtime.

It remains donor-only. QVCH_v3 is a clean project with newly created code and contracts.

## Archive

ZIP archive produced separately as:

```text
C:\AGI\QVCH_v3_clean_mvp_2026-05-21.zip
```

## Update 2026-05-21 — Gateway Hardening Pass

Implemented requested hardening items:

1. `MemoryWriteGateway.commit()` is now wrapped in an atomic SQLite transaction. On runtime failure, event/write-plan/object writes are rolled back and only a failed audit record remains.
2. RepairPair secret redaction now applies to all text fields: `bad_answer`, `failure_reason`, `correction_source`, and `corrected_answer`.
3. Direct SQL bypass protection added in `QVCHDatabase.execute()` for protected memory tables. Public writes to core memory tables require authorized internal APIs such as the gateway or lifecycle helpers.
4. Added `support_count` to `memory_atoms` and `atom_evidence` links. Duplicate F candidates no longer create atom spam; they accumulate distinct non-LLM evidence.
5. Added minimal conflict detector for storage-location claims. Conflicting F candidates/crystals are blocked before persistence.
6. Added end-to-end demo script:

```powershell
python C:\AGI\QVCH_v3\scripts\e2e_demo.py
```

Demo path:

```text
raw text → normalized event → write plan → gateway commit → retrieval → memory probe
```

Current verification:

```text
21 passed in 1.72s
```
