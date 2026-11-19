# Migration v3 → v4.1

Shadow migration: legacy `qvch_v3` (and its database) is **never** modified
in place (constraint #1). The migration is **read-only** over the legacy DB
and **append-only** into a fresh v4 DB, gated by reconciliation.

## Flow

```
seed_legacy_db(legacy)          # test fixture; real runs read an existing v3 DB
run_migration(legacy, v4)
   -> shadow-read v3 rows
   -> map v3 concepts -> v4 atoms/revisions/lineages
   -> redact sensitive / unmappable rows
   -> write through Repository (validated envelopes not required for migration,
      but every row passes the SQL authorizer boundary)
   -> ReconciliationReport (counts, FK, integrity, deterministic rerun)
```

## Mapping (demonstrated by the fixture)

The legacy fixture (`seed_legacy_db`) produces, in v3:

```
atom_evidence: 3   crystals: 1   evidence_refs: 3   hypotheses: 1
memory_atoms: 3   memory_events: 3   monitor_events: 1   noumena: 1
noumenon_transitions: 1   probe_runs: 1   repair_pairs: 1
skill_candidates: 1   write_audit: 1   write_plans: 1
```

Mapped into v4 (fresh v4 DB):

```
memory_atoms: 6   atom_revisions: 6   epistemic_lineages: 6
memory_events: 3   audit_events: 4   atom_state_events: 2
migration_issues: 0
mapped: 12   unmapped: 0   redacted: 0   critical_issues: 0
```

(Atom counts exceed raw v3 atom rows because each v4 atom carries its own
revision; `atom_revisions` == `memory_atoms`.)

## Reconciliation gates (Q16)

- `mapped > 0`, `unmapped == 0`, `critical_issues == 0`.
- `fk_ok == True` (every FK in the v4 DB resolves).
- `integrity_ok == True` (schema/append-only invariants hold).
- `can_cutover()` is `True` only when the above hold.
- **Idempotent rerun**: re-running `run_migration` over the same
  `legacy`/`v4` pair yields the same `mapped` count with no duplicate
  atoms (`deterministic_rerun_match` reports the row-level metric; see
  residual risks re: uuid-bearing legacy rows).

## Redaction (constraint #7)

Sensitive / unmappable legacy rows are **redacted**, not copied raw. Raw
legacy `WritePlan` payloads and hidden chain-of-thought are not persisted
into v4. The migration report fixture stores only non-sensitive content.

## CLI

```powershell
python -m qvch_v4.cli migrate   --from legacy_v3.db --to v4.db
python -m qvch_v4.cli reconcile --from legacy_v3.db --to v4.db
# reconcile prints the markdown report and `can_cutover=True`
```

## Cutover rule

Do **not** perform a downstream cutover while `can_cutover()` is `False`
or while `critical_issues > 0`. A blocked reconciliation is surfaced with
exact counts, not masked.
