# Build summary — QLP iteration (2026-11-07)

| Item | Value |
|---|---|
| Lean | `leanprover/lean4:v4.18.0` (4.18.0, commit 11ccbced7964) |
| Lake | 5.0.0-11ccbce |
| Mathlib | offline snapshot `../mathlib-v4.18.0` @ tag v4.18.0 |
| Command | `MATHLIB_NO_CACHE_ON_UPDATE=1 lake build` |
| Result | exit 0, 1215 targets, `Build completed successfully` |
| Errors | 0 |
| Warnings | 5 (4 × ProofWidgets JS-stub hash, 1 × style linter `RMap.lean:70`) |
| `#print axioms` | 60 directives |
| Theorems with no axioms | 3 |
| Axiom set | `propext`, `Classical.choice`, `Quot.sound`, `Lean.ofReduceBool` |
| `sorryAx` | 0 occurrences |
| Kernel project | `lake build` in `QCatFormal-Kernel` exit 0 |
| New Mathlib module built | `Mathlib.LinearAlgebra.Finsupp.LSum` (857-module closure) |

Logs: `qcat_qlp_build.log`, `qcat_kernel_qlp.log`, `qcat_finsupp_build.log`.
