# QVCH v4.1 — Architecture

QVCH v4.1 is a new `qvch_v4` package built **beside** the legacy
`qvch_v3` package. Legacy code and the legacy database are **never** modified
in place (constraint #1). v4 shares SQLite as a *persistence substrate only*;
all memory writes pass through the sovereign write path.

## Central law

> **LLM/Rajas proposes. QNUF-Forge structures. CVL extracts hard claims and
> evidence. Pramāṇa classifies evidence and conflicts. ReductionVerifier proves
> reduction of N. MANAS authorizes one exact transaction. QVCH stores
> immutable causal history. Applicability Gate authorizes local use. Node 15
> executes probes and actions. Spanda measures viability. Vinasha removes the
> right to influence.**

The LLM never sets the final truth, the reduction score, or an `APPROVE`
verdict.

## Component map

| Layer | Module | Responsibility |
|--------|--------|----------------|
| Structure | `qvch_v4.forge` (QNUF-Forge v2.2) | Turns raw observation text into a `StructuredDraft`; raises `noumenon_slots` for unknowns; flags forbidden self-assertion fields. |
| Extraction | `qvch_v4.cvl` | Extracts hard claims (EXTRACTED / GENERATED_HYPOTHESIS / NORMATIVE / OBSERVATION_REQUEST) with materiality + anchors. |
| Evidence | `qvch_v4.pramana` | Classifies evidence as PRATYAKSA / ANUMANA / SABDA; detects conflicts. |
| Reduction | `qvch_v4.reduction` (Proof-of-Reduction) | Server-side deterministic authority. `ReductionVerifier.reduce()` / `can_crystallize()`. |
| Sovereignty | `qvch_v4.manas` (MANAS) | `ManasService.decide()` mints a `ManasDecisionEnvelope`; `Gateway.verify_with_signer()` verifies signature/expiry/hash/replay and requires a reduction proof for F routes. |
| Storage | `qvch_v4.storage` (QvchStore + Repository) | SQL-first SQLite v4.1; `set_authorizer()` SQL boundary; append-only history tables; the **only** production write path. |
| Retrieval | `qvch_v4.retrieval` | Epistemic retrieval: separates semantic relevance from epistemic confidence; never returns a refuted atom as truth. |
| Applicability | `qvch_v4.applicability` (Applicability Gate + Node 15) | Static preconditions + anti-conditions + mandatory Node 15 probes before a crystal may be applied locally. |
| Viability | `qvch_v4.spanda` (Spanda) | Computes a frozen-policy viability score; moves FORM crystals downward automatically, upward only under `AUTHORIZE_STATE_TRANSITION`. |
| Loss of influence | `qvch_v4.vinasha` (Vinasha) | Blocks auto-application of degraded/non-applicable crystals; opens a new N via `DERIVED_FROM` on degradation; never deletes history. |
| Safety | `qvch_v4.safety` | Materiality classification + recursive sanitization; secrets → opaque `SECRET_REF` markers. |
| Policy | `qvch_v4.policy.frozen` | Versioned **frozen** Spanda/Vinasha policies (no scattered literals). |
| Orchestration | `qvch_v4.studio` + `qvch_v4.cli` | Thin operational surface. Refuses client approval flags. No command bypasses MANAS/Gateway. |

## Write path (every protected write)

```
observation text
   -> QNUF-Forge.forge()           StructuredDraft (noumenon_slots = unknowns)
   -> CVL.extract()                   hard claims + anchors
   -> Pramāṇa.classify()            PRATYAKSA/ANUMANA/SABDA + conflicts
   -> ReductionVerifier (for F)       ReductionCertificate (server-side score)
   -> ManasService.decide()          ManasDecisionEnvelope (AUTHORIZE_WRITE / _TEST / _STATE_TRANSITION)
   -> Gateway.verify_with_signer()    signature + expiry + target_hash + replay + (F) reduction proof
   -> Repository.write_atom()          immutable atom + revision + state event (append-only)
```

A crystal is **applied locally** only after the Applicability Gate passes
(preconditions + anti-conditions + mandatory Node 15 probes under a valid
`AUTHORIZE_TEST`). Usage outcome is bound to the exact revision + gate decision.

## What is deliberately NOT in v4 (constraint #3)

No A2A Exchange, no NARC, no blockchain, no external vector DB, no new
experimental functionality. Retrieval uses SQLite FTS5 with a deterministic
token-overlap fallback — no external service.

## Run surface

- Library: `from qvch_v4.studio import Studio`
- CLI: `python -m qvch_v4.cli {init,migrate,reconcile,ingest,retrieve,maintain}`
- E2E demo: `python scripts/e2e_v4_demo.py`
