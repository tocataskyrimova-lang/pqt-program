# QNUF-Forge v2.2 — Prompt/Contract

**Role:** untrusted compiler of LLM output into a structured candidate. QNUF-Forge
structures; it does **not** assign FACT, choose the final route, or authorize a write.

## Input

`RawThoughtOutput`:

```json
{
  "source_text": "<user/observed text; ephemeral, never stored raw>",
  "observed_model_output": "<optional JSON string the model returned>",
  "structured_fields": {
    "claims": [ Claim, ... ],
    "noumenon_slots": [ Slot, ... ],
    "transformations": [ Transformation, ... ]
  },
  "model_id": "string|null"
}
```

## Claim types (minimum)

| type | anchor required | notes |
|---|---|---|
| `EXTRACTED` | **yes (verified)** | Postulate 0: no verified anchor → claim does not exist |
| `GENERATED_HYPOTHESIS` | no | must stay HYPOTHESIS; cannot directly support F |
| `NORMATIVE` | no | requires `normative_source_ref` |
| `OBSERVATION_REQUEST` | no | observation / unknown marker |

## Verbatim anchor

```json
{
  "source_event_id": "evt_...",
  "start_offset": 12,
  "end_offset": 48,
  "quote": "<exact slice>",
  "quote_hash": "sha256:<hex>",
  "redacted": false,
  "fingerprint": "sha256:<hex> | null"
}
```

Verification recomputes `sha256(quote)` from `source_text[start_offset:end_offset]`
and compares to `quote_hash`. For secret spans, `redacted=true`, `quote=null`,
and only `fingerprint = sha256(slice)` survives.

## Forbidden LLM self-assigned fields

The Forge **ignores and records** any of:

```
approved, fact, authoritative_confidence, final_route,
safe_to_commit, manas_decision, decision, verify, verified
```

Their presence never influences the draft; they are reported in
`CanonicalStructuredDraft.forbidden_fields_detected`.

## Output

`CanonicalStructuredDraft` with `canonical_hash = sha256(canonical_json(payload))`.
Deterministic: identical input → identical hash.

## Invariants enforced

1. EXTRACTED without verified anchor → reject (ForgeRejection).
2. Hypothesis without anchor → retained as hypothesis candidate.
3. LLM cannot assign FACT or APPROVE.
4. Canonical hash deterministic.
