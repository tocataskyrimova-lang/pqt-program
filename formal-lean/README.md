# Formal Lean 4 Certification Track (Track C)

This directory hosts machine-checked proofs and categorical foundations for Process Quantum Theory using **Lean 4** (`leanprover/lean4:v4.18.0`).

---

## Subprojects Overview

1. **`QCatFormal-Kernel/`**  
   * **Role:** Zero-dependency formal core. Contains fundamental categorical structures, objects, morphisms, and basic coherence without external Mathlib requirements.
   * **Status:** Cleanly compiles on vanilla Lean 4.18.0 with no external dependencies.
2. **`QCatFormal/`**  
   * **Role:** Categorical foundations, monoidal categories, and semantic bridges.
   * **Status:** Depends on Mathlib v4.18.0.
3. **`QCat-BraidCore/`**  
   * **Role:** Braided monoidal categories, Yang-Baxter equation coherence, hexagon axioms, and knot-theoretic state spaces.
   * **Status:** Depends on Mathlib v4.18.0.
4. **`QCat-CatBridge/`**  
   * **Role:** Functorial dictionary translating operational PQT concepts into certified categorical structures.
   * **Status:** Depends on Mathlib v4.18.0.

---

## Mathlib v4.18.0 Dependency & Hardcoded Paths

In `lakefile.toml` for `QCatFormal`, `QCat-BraidCore`, and `QCat-CatBridge`, the Mathlib dependency is configured as:

```toml
[[require]]
name = "mathlib"
path = "../mathlib-v4.18.0"
```

### Why this path is used:
In the offline audit environment (`REPRO_FREEZE_2026-10-25`), Mathlib v4.18.0 was vendored locally alongside the Lean projects to ensure deterministic, network-free compilation without depending on volatile remote Git tags.

### How to build on a new machine:
If you are compiling outside this offline directory structure, choose one of two options:

#### Option A: Clone Mathlib v4.18.0 locally
Clone `mathlib4` into a sibling directory relative to your project folder:
```bash
git clone --branch v4.18.0 https://github.com/leanprover-community/mathlib4.git ../mathlib-v4.18.0
```

#### Option B: Switch `lakefile.toml` to Git dependency
Replace the `path` requirement in `lakefile.toml` with the standard remote Git requirement:
```toml
[[require]]
name = "mathlib"
git = "https://github.com/leanprover-community/mathlib4.git"
rev = "v4.18.0"
```
Then run:
```bash
lake update
lake build
```
