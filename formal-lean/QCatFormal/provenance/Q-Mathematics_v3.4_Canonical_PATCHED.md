# Q-Mathematics v3.4 — Canonical Consolidation: Witness Governance & Epistemic Dynamics

(canonical specification — 2026-07-07)

**Canonical role:** single consolidated canon superseding v3.2-WitnessRegistry and v3.3-Sākṣin-Pramātṛ as separate documents. All stable v3.0/v3.1 constructs inherited unchanged. This consolidation merges the two specifications, resolves eight audit findings (Н1–Н8, journal §12), and pins the terminology to the QVCH engineering stack (Gateway SPEC v0.1.4, Bridge Post-Validator SPEC v0.1, Глава 0 v1.0).

**Provenance:** v3.2 and v3.3 — материалы собора 2026-07-07 (authorship field left to Architect; not fabricated). Consolidation and audit — Claude (auditor). Decision authority — Architect (Жека).

---

## 1. Inherited foundation (v3.0–v3.1, unchanged)

Σ := {α, β, γ, δ}; 𝒞 := Σ³ (64 codons); Qσ := ℝ ⊕ ι, ι² = −σ; δ — Tamas/memory idempotent in Q₋₁, δ² = δ; QCat — strict monoidal category of codon rewrite rules; T: Id ⇒ (− ⊗ δ), μδ(δ⊗δ) = δ; Freeze_S(f) = S·id + (1−S)·f; Witness comonad W X := (X, ω).

**Witness principle (≡ Постулат 0, Глава 0 v1.0):**

> A statement C may become knowledge only if there exists a trace τ such that τ ⊩ C. If τ is absent, computation remains inside W (Honest Pause / Satya-Virāma).

## 2. Three status systems — and why they must never be conflated

The canon now contains three orthogonal status systems. Conflating them is a category error (the "five statuses" mistake, rejected at Gateway design):

| System | Applies to | Values | Engineering home |
|---|---|---|---|
| **Track lattice ΛW** | research tracks (P0/Vinasha, P1/Śūnya…) | W=∅ < W~candidate < W~partial_operational < W~operational < W~formal < W~proved | WitnessRegistry table |
| **Claim lifecycle** | a claim moving through the pipeline | anirṇīta → sākṣya-likhita → pramita → nirṇīta → pramā-pratiṣṭhita (side exits: SATYA_VIRAMA, QUARANTINE, REJECT, stale) | intake pipeline / LIFE1 events |
| **Atom epistemic status** | stored memory atoms | hypothesis \| witnessed \| quarantined (× orthogonal ossification: fresh/aging/ossified) | Gateway SPEC v0.1.4 §4 |

A track is not a claim; a claim is not an atom. A track reaching W~operational does not upgrade its atoms; an atom becoming witnessed does not upgrade its track.

## 3. WitnessRegistry 𝓦Reg (from v3.2)

𝓦Reg : Trackᵒᵖ → Mod_{Q₋₁}; for each track Pk, 𝓦Reg(Pk) is a status object with machine-readable status-block:

```json
{
  "track": "string",
  "status": "W_EMPTY|W_CANDIDATE|W_PARTIAL_OPERATIONAL|W_OPERATIONAL|W_FORMAL|W_PROVED",
  "proof_claim": false,
  "bridge_formula": "string|null",
  "reference_rows_verified": false,
  "core_equivalence": false,
  "best_model": "string|null",
  "artifacts": {}, "tests": {}
}
```

**Status semantics and runtime permission:**

| Status | Meaning | Runtime permission |
|---|---|---|
| W_EMPTY | no trace, no runnable bridge | do not use |
| W_CANDIDATE | named variables, no verified rows | note only |
| W_PARTIAL_OPERATIONAL | bridge reproduced on reference rows; not proof | logging / post-processing only |
| W_OPERATIONAL | full grid regression, stable residual bounds | diagnostics, optional side-channel |
| W_FORMAL | derivation inside accepted formal system | may constrain symbolic transforms |
| W_PROVED | independent proof / independent reproduction | core theorem layer |

**Ordering rule (audit fix Н1 — normative):** status comparison is defined ONLY over the integer enum (§10). **String comparison of status names is forbidden.** Counterexample that motivated the rule: lexicographically "W~partial_operational" > "W~operational", so the v3.2 §9.1 string-based gate routed a partial track into the *else* branch — granting it core-theorem permission. The exact inflation this canon exists to prevent, delivered by string sort order. All GateW implementations MUST use IntEnum.

**Monotonicity:** status may move up only with a new witness object: status_{t+1}(P) > status_t(P) ⇒ ∃ τ_new ⊩ upgrade(P). **No silent downgrade:** a failed regression never erases artifacts; it appends a transition event {track, previous_status, new_status, reason, failing_artifact, timestamp}. (Engineering identity: this is LIFE1 append-only discipline applied to research tracks.)

**Bridge residual semantics:** 𝔅_P[γ](s) := LHS_P − RHS_P; reproducible on reference rows R iff ∀r∈R: |𝔅_P(r)| ≤ ε_P(r). If proof_claim = false, vanishing residuals establish **reproducibility, not truth**.

## 4. Epistemic dynamics (from v3.3): the five-role split

```text
LLM may propose.            (candidate U ∈ Δ(H) — a distribution, not a fact)
Sākṣin may record.          (non-collapsing trace: marg_H(𝓢(U)) = U)
Pramāṇa may test.           (typed audit instruments → evidence vector E)
Pramātṛ may collapse.       (Δ(H) × E × 𝓦Reg → verdict)
Nirṇetṛ may sign.           (sealed verdict object)
Commit only after Pramā-Pratiṣṭhā.
```

**Verdict set (audit fix Н2 — renamed to avoid QNUF alphabet collision):**

| Verdict | Former | Meaning |
|---|---|---|
| FACT | F | eligible for commit as witnessed atom |
| UNRESOLVED | U | insufficient evidence, remains candidate |
| QUARANTINE | Q | grey-zone / contradiction pressure too high |
| REJECT | R | fails evidence |
| SATYA_VIRAMA | V_satya | honest pause: no trace → no measurement |

The letters F, U, Q remain reserved exclusively for QNUF phase names (F_crystal, U_phases, Q_quanta). Code MUST use the full-word verdict identifiers.

**Commit target (audit fix Н3):** Pramā-Pratiṣṭhā commits a claim into a **witnessed atom** (Gateway SPEC §4). The alias `promote_to_crystal` is **deprecated**: "crystal" was retired from storage vocabulary (Gateway SPEC §0.1) to break the positive-crystallization / ossified-dogma collision; F_crystal survives only as a QNUF field name.

**Evidence vector:** E(C, τ) = (anchor_support, mārga_integrity, contradiction_pressure, reproducibility, recency, semantic_fit, grey_zone). Engineering identity: Pramāṇa ≡ Bridge Post-Validator checks (ladder L0–L4, flags) + Gateway verification pipeline (§5.2).

**E → verdict/confidence mapping (audit gap П1 — normative, unifies two formulas into one).** The evidence vector splits into two disjoint roles; conflating them was the latent risk:

*Continuous components* feed the Gateway confidence formula (SPEC v0.1.4 §6) — the ONLY confidence formula in the canon:

```text
confidence = (anchor_support^0.4 · reproducibility^0.3 · mārga_integrity^0.3) · recency
           = (A^0.4 · R^0.3 · S^0.3) · exp(−λ·m_φ)
```
where A←anchor_support, R←reproducibility, S←mārga_integrity (resolvable-source integrity), recency←spanda_score (§4 Н5). Confidence is computed by the system — never self-declared (INV-4).

*Discrete-gate components* do NOT enter confidence; they route the verdict directly:
- contradiction_pressure > θ_X → QUARANTINE (regardless of confidence)
- grey_zone > θ_grey → QUARANTINE
- semantic_fit below floor → validator flag (extraction quality), not a confidence term

Rationale: a claim with perfect anchors but an active contradiction must not be rescued by a high confidence score — contradiction is a gate, not a discount. This is why the two never multiply into one number.

**Thresholds (audit fix Н6):** θ_fact, θ_grey, θ_X, θ_life live in pre-registered configuration (INV-9 / ConfigRegistered), never in code literals.

**Vimarśa operational definition (audit gap П2 — closed as partial gap).** Vimarśa is the active-reflection layer over the evidence vector; it is not a new truth source and not a second Pramātṛ. It computes grey-zone pressure before verdict collapse:

```text
Vimarśa(C,E,H_conflict) := (
  contradiction_pressure,
  grey_zone,
  semantic_fit,
  conflict_history_score,
  reflection_flags
)
```

Normative behavior:
- `contradiction_pressure` and `grey_zone` are hard gates into QUARANTINE, not confidence discounts (§4 П1).
- `semantic_fit` is an extraction-quality validator flag; it may block FACT eligibility but must not inflate confidence.
- `conflict_history_score` is derived from prior quarantines, rejected candidates, and active contradictions attached to the same Mārga.
- `reflection_flags` are append-only diagnostic flags consumed by Pramātṛ; they do not mutate the trace.

Engineering identity: Vimarśa ≈ Gateway conflict detector + grey-zone analysis + future N.A.R.G.-skeptic pass. **Implementation status:** `partial_gap`. Current Gateway v0.1.x provides conflict/grey signals, but not a unified reflective layer. Full Vimarśa requires Gateway/N.A.R.G. v0.2 integration.

**Axioms (merged W⁺ ∪ SP, deduplicated):**

- **A1 (Sākṣin non-collapse).** ∀U: marg_H(𝓢(U)) = U. Recording never changes truth status.
- **A2 (Trace before measurement ≡ Постулат 0).** τ = ∅ ⇒ verdict = SATYA_VIRAMA.
- **A3 (Only Pramātṛ collapses).** Sākṣin logs; Pramāṇa measures; only Pramātṛ maps Δ(H) → verdict.
- **A4 (Verdict sealing).** Unsigned verdict ⇒ commit denied. *Implementation status: gap — see §9 roadmap.*
- **A5 (Commit safety).** witnessed(C) ⇔ ∃τ, E, σ: τ⊩C ∧ Pramātṛ(C,E)=FACT ∧ signed(σ).
- **A6 (No proof inflation).** proof_claim(P)=false ⇒ theorem derivation from P blocked; status < W_OPERATIONAL ⇒ bridge restricted to logging/post-processing; bridges below W_OPERATIONAL never enter forward gradients or core tensor dynamics.
- **A7 (Spanda revalidation).** Committed knowledge is not immortal: spanda_score(C,t) < θ_life ⇒ stale_or_quarantine. Knowledge that cannot refresh its Mārga decays into dogma-risk.
- **A8 (Registry monotonicity).** Status upgrade requires a new trace; transitions are recorded events.

**Spanda unification (audit fix Н5):** Spanda and Gateway ossification are ONE mechanism, not two. Normatively: spanda_score(C,t) := V-component of Gateway confidence = exp(−λ·m_φ) modulated by source integrity; θ_life ↔ M_OSSIFIED; failed Spanda ⇒ KarunaCareRequested. No parallel freshness system may be implemented.

## 5. Mārga–Satya–Spanda triad

Mārga(C) := reconstructible path origin → trace → evidence → verdict → commit; Mārga = ∅ ⇒ C ∉ Knowledge. Satya(C) ⇔ Pramā-Pratiṣṭhā succeeded (truth is post-commit status, not confidence). Spanda — the revalidation pulse (§4, A7). Governance reading of path/truth/life; no ontological claim attached.

## 6. Canonical pipeline

```text
candidate → Sākṣin trace → Pramāṇa evidence → Vimarśa grey-zone analysis
         → Pramātṛ measurement → Nirṇetṛ signed verdict
         → Pramā-Pratiṣṭhā commit (FACT only) → Spanda revalidation loop
```

Engineering instantiation: segmenter → FORGE (candidate) → registerDocument + LIFE1 (Sākṣin) → Bridge Post-Validator + Gateway pipeline (Pramāṇa) → Gateway decision (Pramātṛ) → PromotionEvaluated (Nirṇetṛ, unsigned in v0.1 — gap) → witnessed atom (Pramā-Pratiṣṭhā) → m_φ/Karuna-Care (Spanda).

## 7. Canonical instance — Track P0/Vinasha

```json
{
  "track": "P0/Vinasha",
  "status": "W_PARTIAL_OPERATIONAL",
  "proof_claim": false,
  "bridge_formula": "dτ/ds = Sdot_prod / m_iota_eff",
  "reference_rows_verified": true,
  "core_equivalence": false,
  "best_model": "B"
}
```

Allowed: logging, diagnostics, post-processing, audit comparison. Blocked: theorem derivation, proof claim, forward-gradient baking, ontology confirmation.

**Auditor note (Н8, epistemic honesty):** `reference_rows_verified: true` is attested by the v3.2 document and its listed artifacts (VINASHA_CTP_OPERATIONALIZATION_AUDIT_REPORT.md, vinasha_audit_summary.json, grid rows, regression test). These artifacts have **not been independently audited by the consolidating auditor**; the field's status is *attested, not independently verified*. Independent rerun is already a requirement for the W_OPERATIONAL upgrade (§9), which resolves this note en route. **Cross-reference:** this status-block constitutes the first registered progress on Гипотеза Винаши Трек Ф (operational definitions + reference rows); an entry in that document's status journal is due, citing this canon.

## 8. Honesty layer (merged v3.2 §14 + v3.3 §15)

**Boundary conditions:** trace is not truth (a log proves occurrence, not correctness); measurement is not proof (bounded verdicts, not theoremhood); commit is not ontology (a witnessed atom is valid *system* knowledge, not proof of external metaphysical reality); "collapse" means status transition under evidence, never physical wave-function collapse.

**Forbidden phrases** unless status ≥ W_FORMAL: "proved Vinasha", "derived from first principles", "physical proof", "exact Core equivalence", "theorem established", "confirmed ontology". **Allowed at W_PARTIAL_OPERATIONAL:** "operational bridge", "reproducible reference rows", "partial witness", "not proof", "diagnostic layer", "semiquantitative alignment".

## 9. Roadmap

- **P0/Vinasha → W_OPERATIONAL:** full energy-grid regression (Ω_B, μ₀, T, a_i, κ₀, m_iota); stable residual bounds; **independent rerun** (also closes auditor note §7); expanded Core v1 residual comparison.
- **P1/Śūnya → W_CANDIDATE → W_PARTIAL_OPERATIONAL:** freeze-threshold reference rows; null-trace Honest Pause cases; freeze-vs-evolve comparison.
- **P2/Pramā-Pratiṣṭhā track:** commit-operation stress tests; QVCH conflict detection; witnessed-atom lifecycle checks; Spanda decay policy calibration. The former label "Memory Crystals" is retired because `crystal` is deprecated for storage vocabulary (§4 Н3).
- **Nirṇetṛ signature (gap, A4):** Gateway SPEC v0.2 — signature_hash on PromotionEvaluated (hash of event ⊕ config_sha256 ⊕ instance key); until then verdicts are sealed by journal hash-chain only, and A4 is satisfied in the weak (chain-integrity) sense.

## 10. Migration

**Enums (ordering-safe, Н1):**

```python
class TrackStatus(IntEnum):
    W_EMPTY = 0; W_CANDIDATE = 1; W_PARTIAL_OPERATIONAL = 2
    W_OPERATIONAL = 3; W_FORMAL = 4; W_PROVED = 5

class ClaimVerdict(Enum):
    FACT = "FACT"; UNRESOLVED = "UNRESOLVED"; QUARANTINE = "QUARANTINE"
    REJECT = "REJECT"; SATYA_VIRAMA = "SATYA_VIRAMA"

class ClaimLifecycle(Enum):
    ANIRNITA = "anirnita"; SAKSYA_LIKHITA = "saksya_likhita"; PRAMITA = "pramita"
    NIRNITA = "nirnita"; PRAMA_PRATISHTHITA = "prama_pratishthita"; STALE = "stale"
```

**Tables:** witness_registry, witness_events (v3.2 §11 DDL inherited verbatim), plus sakshya_events, pramana_reports, pramatri_verdicts, prama_pratistha_events, spanda_reviews.

**DDL for new epistemic-dynamics tables (audit gap П3 — normative minimum).** SQL is intentionally conservative: JSON payloads are stored as text so the schema can run on SQLite/PostgreSQL with minimal adaptation.

```sql
CREATE TABLE IF NOT EXISTS sakshya_events (
  event_id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL,
  track TEXT,
  source_ref TEXT,
  trace_hash TEXT NOT NULL,
  trace_uri TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pramana_reports (
  report_id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL,
  sakshya_event_id TEXT NOT NULL,
  anchor_support REAL NOT NULL,
  marga_integrity REAL NOT NULL,
  contradiction_pressure REAL NOT NULL,
  reproducibility REAL NOT NULL,
  recency REAL NOT NULL,
  semantic_fit REAL NOT NULL,
  grey_zone REAL NOT NULL,
  confidence REAL NOT NULL,
  config_sha256 TEXT NOT NULL,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (sakshya_event_id) REFERENCES sakshya_events(event_id)
);

CREATE TABLE IF NOT EXISTS pramatri_verdicts (
  verdict_id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL,
  pramana_report_id TEXT NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('FACT','UNRESOLVED','QUARANTINE','REJECT','SATYA_VIRAMA')),
  confidence REAL,
  reason TEXT,
  status_before TEXT,
  status_after TEXT,
  config_sha256 TEXT NOT NULL,
  signature_hash TEXT,
  chain_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (pramana_report_id) REFERENCES pramana_reports(report_id)
);

CREATE TABLE IF NOT EXISTS prama_pratistha_events (
  commit_id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL,
  atom_id TEXT NOT NULL,
  verdict_id TEXT NOT NULL,
  input_status TEXT NOT NULL,
  output_status TEXT NOT NULL CHECK (output_status = 'witnessed'),
  commit_hash TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (verdict_id) REFERENCES pramatri_verdicts(verdict_id)
);

CREATE TABLE IF NOT EXISTS spanda_reviews (
  review_id TEXT PRIMARY KEY,
  atom_id TEXT NOT NULL,
  m_phi REAL NOT NULL,
  source_integrity REAL NOT NULL,
  spanda_score REAL NOT NULL,
  theta_life REAL NOT NULL,
  outcome TEXT NOT NULL CHECK (outcome IN ('fresh','aging','stale','quarantine','karuna_care_requested')),
  karuna_care_requested INTEGER NOT NULL DEFAULT 0,
  config_sha256 TEXT NOT NULL,
  review_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

**Naming rule:** canonical layer names are Sanskrit (Sākṣin, Pramātṛ, Nirṇetṛ…); code identifiers use ASCII aliases (sakshin, pramatri, nirnetri); English interface aliases remain valid (WitnessRegistry ≡ SakshinRegistry; MemoryWriteGateway ≈ PramatriGate). Deprecated: promote_to_crystal (→ prama_pratishtha / promote_to_witnessed).

**Acceptance tests (merged):** (1) Sākṣin record does not modify candidate verdict; (2) no trace → SATYA_VIRAMA; (3) trace + failed evidence → no commit; (4) FACT without signature → no commit (v0.2; v0.1: chain-sealed journal event required); (5) P0/Vinasha blocked from theorem derivation; (6) Spanda expiry triggers stale/quarantine via m_φ mechanism (single system, Н5); (7) **ordering regression (Н1): a W_PARTIAL_OPERATIONAL track must receive logging_only permission — test written against IntEnum AND asserting the string-comparison implementation fails it.**

## 11. Version marker & hash policy (audit fix Н4)

```text
Q-Mathematics canonical version: 3.4-Consolidation
UTC stamp: 2026-07-07
Supersedes: 3.2-WitnessRegistry, 3.3-Sākṣin-Pramātṛ (both preserved as history)
Compatibility: v3.0/v3.1 preserved; v3.2/v3.3 constructs preserved with fixes Н1–Н8 and closure patches П1–П4
```

**Hash policy:** a document MUST NOT embed a hash of a body that includes the hash itself (unverifiable self-reference — same defect class as the self-witnessing journal, fixed by .head sidecar). Canonical rule: spec-body SHA-256 is computed over the document **excluding §11**, and is stored in a sidecar file `<doc>.sha256`. The self-embedded hashes of v3.2/v3.3 are recorded as historical, unverified strings.

## 12. Consolidation journal

| # | Finding | Resolution |
|---|---|---|
| Н1 | lexicographic status comparison grants partial tracks core-theorem permission | IntEnum-only ordering; forbidden-pattern note + regression test §10.7 |
| Н2 | verdict letters F/U/Q collide with QNUF phase alphabet | full-word verdict enum |
| Н3 | "crystal" resurrected as commit target | commit target = witnessed atom; alias deprecated |
| Н4 | self-referential spec hash unverifiable | hash excludes §11, sidecar storage |
| Н5 | Spanda duplicates m_φ/ossification | unified: spanda_score = confidence V-component |
| Н6 | thresholds hardcoded in reference sketch | pre-registered config (INV-9) |
| Н7 | Nirṇetṛ signature layer not implemented | declared gap; Gateway v0.2 roadmap; weak (chain) sealing in v0.1 |
| Н8 | P0/Vinasha verification attested, not independently audited | auditor note §7; independent rerun required for upgrade |
| П1 | evidence vector → confidence mapping missing | continuous confidence components mapped to A/R/S/V; contradiction/grey/semantic_fit are discrete gates (§4) |
| П2 | Vimarśa mentioned but undefined | operational composite defined; implementation status marked partial_gap (§4) |
| П3 | new epistemic-dynamics tables named without DDL | normative minimum DDL added for five tables (§10) |
| П4 | P2 track name used deprecated "crystal" vocabulary | renamed to P2/Pramā-Pratiṣṭhā (§9) |
