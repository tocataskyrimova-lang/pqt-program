# Process Quantum Theory (PQT) Research Program

[![CI Smoke](https://github.com/tocataskyrimova-lang/pqt-program/actions/workflows/ci-smoke.yml/badge.svg)](https://github.com/tocataskyrimova-lang/pqt-program/actions/workflows/ci-smoke.yml)
[![Version](https://img.shields.io/badge/version-v0.9--baseline-blue.svg)](https://github.com/tocataskyrimova-lang/pqt-program/releases/tag/v0.9-baseline)
[![Lean 4](https://img.shields.io/badge/Lean_4-v4.18.0-orange.svg)](https://leanprover.github.io/)

---

## 1. Academic & Epistemic Positioning

**Process Quantum Theory (PQT)** is an exploratory formal pre-theory and computational/algebraic research program.

> [!IMPORTANT]
> **Scope & Boundaries:** PQT is **NOT** a proven "Theory of Everything" (ToE), nor does it claim to be a first-principles derivation of the Standard Model of particle physics or General Relativity. Rather, it investigates whether non-local memory kernels, braided category semantics, and discrete algebraic structures can resolve specific persistent tensions in quantum foundation models, effective quantum gravity, and flavor physics.

### Epistemic Status Scale
All results, claims, and code artifacts across this repository are tagged under a rigorous epistemic taxonomy:
* `DERIVED_UNDER_ASSUMPTIONS`: Mathematically proven within an explicitly stated axiomatic or algebraic system (e.g. Lean 4 theorem, algebraic identity).
* `PASS_EXECUTION`: Computationally verified by deterministic unit tests, numerical convergence benchmarks, or multi-seed scans.
* `COUNTEREXAMPLE`: Formal or numerical refutation of an unproven conjecture or heuristic proxy (e.g. Sylvester counterexample refuting determinant health heuristics).
* `CANONICAL_HYPOTHESIS`: Formally stated working conjecture accepted as a baseline assumption for higher-tier constructions.
* `NOT_CANONIZED`: Exploratory heuristic, speculative model branch, or unverified phenomenological ansatz.

---

## 2. Repository Layout & Track Architecture

The repository unifies six core modular research tracks:

```
pqt-program/
├── eft-pqt-qg/              # Track A: Non-local Effective Field Theory & Quantum Gravity Benchmarks
│   ├── pqt_qg/              # 3-field (phi, r, s) potential, Coleman-Weinberg, & memory kernels
│   ├── outputs/             # MicroScan, Cooperative Atlas, and Field Bound Stress data/reports
│   └── patches/             # Staged patches (PROPOSED_nonlocal_memory_health.patch for PR #1)
├── formal-lean/             # Track C: Machine-Checked Formal Verification in Lean 4 (v4.18.0)
│   ├── QCatFormal/          # Categorical foundations and functorial bridges
│   ├── QCatFormal-Kernel/   # Self-contained zero-dependency formal core
│   ├── QCat-BraidCore/      # Braided monoidal categories and Yang-Baxter coherence
│   └── QCat-CatBridge/      # Categorical dictionary and bridge theorems
├── pheno-collider/          # Track B: Collider Pheno (VBF / Higgs / 4-lepton Channel)
│   ├── benchmarks/          # v2.0 background closure, v2.2b forensics, historical v2.3, gate records
│   ├── feynrules/           # FeynRules model definitions (.fr) & UFO export scripts (.wls)
│   ├── ufo/                 # Combined SM+PQT UFO Python package (PQT_MemorySector_massbasis)
│   └── tests/               # Deterministic UFO model & historical v2.3 benchmark pytest suites
├── neutrino/                # Neutrino Mass Matrix, PMNS Angles, and RG Evolution
│   ├── neutrino_pqt_v*.py   # Mass-basis operators, seesaw textures, and parameter scans
│   ├── pqt_neutrino_rg_*.py # One-loop renormalization group equations for neutrino parameters
│   └── *.md                 # Formalization docs, audit manifests, and results summaries
├── epistemic-ai/            # Epistemic AI & Autonomous Governance
│   └── qvch/                # Quantum Verification & Consensus Harness (QVCH v3/v4)
└── audits/                  # Cryptographic Audits, Checksums, and Historical Manifests
    ├── repro_freeze_2026_10_25_meta/ # Frozen audit bundle manifest and offline verification
    ├── spectral_audit_2026_11/       # Exact eigvalsh vs det proxy A/B comparison audit
    └── IMPORT_MANIFEST_SHA256.json   # Full cryptographic provenance of baseline import
```

---

## 3. Sibling Repositories & Cross-Project Verification

* **Sibling Repository:** [`tocataskyrimova-lang/PQT-QCAT`](https://github.com/tocataskyrimova-lang/PQT-QCAT)  
  Hosts the M1–M4 categorical proofs and the LIFE-002 biological/cognitive substrate verification track.

---

## 4. Known Status & Open Items

1. **`eft-pqt-qg` Spectral Patch (PR #1):**  
   **Merged upstream (`feat/eft-spectral-eigvalsh`):** Replaced legacy determinant heuristic (`min(det, inv_iota)`) with exact global spectral positivity (`np.linalg.eigvalsh`). Multi-seed A/B audit confirmed 0 false-positive tachyonic cells and 100% agreement with positive-definite control benchmarks.
2. **UFO & FeynRules Model Import (PR #2 — Merged Upstream):**  
   Tree-level FeynRules `.fr` specifications, WolframScript export scripts, and the combined SM+PQT mass-basis UFO Python package (`PQT_MemorySector_massbasis`) merged into `main`. Validated with deterministic 5-test pytest suite (`test_ufo_massbasis.py`) and passing CI smoke workflows.
3. **Collider `v2.3` Cut Stability Gate & Historical Archive (PR #3):**  
   Historical 144-point collider scan archived under `pheno-collider/benchmarks/historical_v23/` with status `ARCHIVED_BACKGROUND_STARVATION`. Analysis confirms nominal significance peak ($Z_{3000} = 598.4$) is driven entirely by near-zero background ($B_{3000} = 0.0143$ under $N_{\text{signal, raw}} = 2$). The statistically valid gate remains `BLOCKED_NEEDS_HIGH_STATS_REGEN` until fresh $\ge 50\text{k}$–$100\text{k}$ event-level kinematics are generated; table interpolation remains strictly forbidden.
4. **Formal Lean Mathlib Integration:**  
   `QCatFormal`, `QCat-BraidCore`, and `QCat-CatBridge` reference an offline snapshot of Mathlib v4.18.0 via `path = "../mathlib-v4.18.0"`. See [`formal-lean/README.md`](formal-lean/README.md) for instructions on setting up or redirecting this dependency.

---

## 5. License & Citations

This software and formalization package are distributed under the Apache License 2.0. See individual package manifests for specific copyright notices and contributor logs.
