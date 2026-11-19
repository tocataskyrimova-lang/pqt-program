# QVCH v4.1 — State Machines

Lifecycle transitions are **versioned, seeded** data (`STATE_TRANSITION_SEED`
in `qvch_v4/storage/schema.py`) and enforced by the `atom_state_check`
BEFORE UPDATE trigger. A forbidden transition raises
`sqlite3.IntegrityError` and rolls back. There is no ad-hoc transition
logic in the engines — they ask `Repository.allowed_transition()` and the
trigger is the final authority.

## NOUMENON (N)

```
OPEN ──▶ PARTIALLY_REDUCED ──▶ RESOLVED ──▶ DORMANT ──▶ REOPENED ──▶ PARTIALLY_REDUCED
  │                         │
  └──▶ ABANDONED ◀────────┘
```

N holds the open unknowns. It moves toward `PARTIALLY_REDUCED` as the
ReductionVerifier closes hard slots, `RESOLVED` when fully reduced, and may
return to `DORMANT` / `REOPENED` (re-opened by a Vinasha degradation of a
downstream crystal, which links a new N `DERIVED_FROM` the degraded atom).

## HYPOTHESIS / UNDERSTANDING (U)

```
PROPOSED ──▶ QUARANTINED ──▶ PROPOSED
    │
    └──▶ AUTHORIZED_FOR_TEST ──▶ TESTING ──┬──▶ PARTIALLY_SUPPORTED ──┬──▶ SUPPORTED ──▶ SUPERSEDED
                                                 │                        │
                                                 └──▶ REFUTED ───────────┘──▶ SUPERSEDED ──▶ PROPOSED
```

U branches are **preserved as competing hypotheses** (scientific honesty):
a wrong branch reaches `REFUTED` and is never silently deleted — it stays
retrievable (its epistemic confidence is crushed by contradiction pressure,
never returned as truth). A supported branch (`SUPPORTED`) is the one a
reduction may cite.

## FORM (F / Crystal)

```
CANDIDATE ──▶ VALIDATED ──▶ ACTIVE ──▶ WATCH ──▶ STALE ──▶ QUARANTINED
   │                                  ▲           │              │
   │                                  └───────────┘              ├─▶ ARCHIVED
   └──▶ QUARANTINED ◀──────────────────────────────────┘           │
                                                                     └─▶ REVOKED
```

Key points:
- `ACTIVE → WATCH` on environment drift; `WATCH → STALE` on continued
  degradation.
- `ACTIVE → QUARANTINED` is a **valid single step**; `ACTIVE → STALE`
  is **not** (there is no seeded rule). Spanda therefore drives a degraded
  crystal to `QUARANTINED` in one step, or `WATCH` then `STALE`.
- `QUARANTINED → STALE → ACTIVE` (recovery) is only via a valid
  `AUTHORIZE_STATE_TRANSITION` MANAS envelope.

## Downward vs upward (Spanda)

- **Downward** (rank decreases: `ACTIVE`→`WATCH`→`STALE`→`QUARANTINED`)
  reduces influence and is applied **automatically** by Spanda.
- **Upward** (re-activation) is **never** automatic — it requires a valid
  `AUTHORIZE_STATE_TRANSITION` envelope verified against
  `sha256_hex(atom_id + revision_id + to_state)`.

## Loss-of-influence (Vinasha)

States that lose the auto-apply right (frozen `VinashaPolicy.non_applicable_states`):
`STALE`, `REVOKED`, `QUARANTINED`, `ARCHIVED`, `ABANDONED`,
`REFUTED`, `SUPERSEDED`. When a FORM crystal reaches one of these via
Spanda, Vinasha **blocks** automatic application and opens a new N
(`DERIVED_FROM`) asking *why the previously-valid revision lost
applicability*. The old content and full causal history (revisions, state
events, gate decisions, probes, usages) are **never** deleted.

## Links (memory_links)

`DERIVED_FROM`, `TESTED_BY`, `SUPPORTS`, `CONTRADICTS`, `REFUTES`,
`RESOLVES`, `SPECIALIZES`, `SUPERSEDES`, `LOCATES`. Notably
`F RESOLVES N` (the crystal is bound to the noumenon it reduces) and
`new N DERIVED_FROM degraded atom` (Vinasha's re-opening).
