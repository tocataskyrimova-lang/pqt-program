# PQT Executive Summary v1.0

**Prema–Quanta Theory — Research Package Overview**

Date: 2026-05-16

---

## 1. What PQT Is

PQT (Prema–Quanta Theory) is a formal dynamical framework describing a closed cycle of cognitive/physical processes. The system state is characterized by a 13-dimensional vector:

$$
x(t) = \{\phi, C_R, C, R_t, m_\phi, \rho_G; P_L, P_I, \theta, E, q_v, Q, N\}
$$

The core cycle is:

$$
\phi \to C_R \to C \to R_t \to m_\phi \to \rho_G \to \phi
$$

representing impulse → turbulence → form → wear → sediment → focus → new impulse.

Two poles modulate the cycle: **Prema** ($P_L$, coherence) and **Maya** ($P_I$, dissipation), subject to the constraint $P_L + P_I \le 1$.

The framework includes:
- A complete ODE system (12 coupled equations + 1 SDE for phase)
- Six laws of post-Schrödinger logic (Σ-interference, Ŵ-locality, τ-delay, ΔΦ-fluctuation, S-loop, Śūnya)
- An Euler–Lagrange reduction showing the ODE system arises from an effective action with Rayleigh dissipation in the overdamped limit
- A collider-physics implementation as a two-scalar extension of the Standard Model

The EFT layer introduces scalars $S$ (PDG 9000006, light) and $H_2$ (PDG 9000007, heavy) with Higgs-like couplings scaled by mixing angle $\theta$. This is implemented as a FeynRules model and validated through the full collider simulation chain.

---

## 2. What Has Been Validated

### Theory Layer
- ✅ Canonical ODE system fully documented (pqt_canon_v1.0)
- ✅ Euler–Lagrange reduction verified sector-by-sector
- ✅ 7 parameters numerically calibrated
- ✅ Six laws formally stated with mathematical forms

### EFT / Collider Layer
- ✅ FeynRules model files: `PQT_MemorySector_massbasis.fr` + SM extension
- ✅ UFO model: 21 files, validated MG5 import
- ✅ Full collider chain: FeynRules → UFO → MG5 → Pythia8 → Delphes → ROOT → cutflow
- ✅ 14 benchmark versions (v1.x through v31), all passing except v22 (partial — see below)

### Phase Structure
- ✅ Four phases (Prema, Gurutva, Tamas, Mixed) with stable classification
- ✅ 4/4 benchmark points pass at all grid resolutions (n=40, 50, 80)
- ✅ Observable contours on 100×100 grid with 6 acceptance checks (all pass)

### Numerical Results
- ✅ Signal: σ_reco = 0.02387 fb at m200, sin²θ = 10⁻⁴
- ✅ Backgrounds: ZZjj, ttZ, Hjj off-shell all simulated
- ✅ Z₃₀₀₀ = 5.32 in v2.1 exact replay (3000 fb⁻¹)

---

## 3. What Is Unresolved

### ANALYSIS_MISMATCH (Critical)
The v2.2 robustness audit showed an apparent significance collapse compared to v2.1. Forensic analysis (v22b) classified this as **ANALYSIS_MISMATCH**: the v2.1 exact replay produces Z=5.32, but tighter window/VBF cuts in v2.2 eliminate background so aggressively that the significance formula becomes undefined. This is a cut-optimization artifact, not a signal weakness, but requires resolution through consistent cut methodology (v2.3).

### Open Operational Gaps
| Gap | Priority |
|---|---|
| v2.3 consistent cut optimization | High |
| Larger background MC (≥10k events) | High |
| VBF-tail systematic estimate | Medium |
| Control region definitions | Medium |
| Systematic uncertainty bands | Medium |

### Open Theory Gaps
| Gap | Status |
|---|---|
| Formal Lyapunov analysis for stabilization theorem | Proof sketch only |
| Stochastic θ derivation from action | Requires Onsager–Machlup extension |
| Heaviside guards as variational objects | Open |
| Analytical phase boundary equations | Numerically validated, not closed-form |

### Truth Policy Reminder
- No failed experiments have been removed
- No partial results have been relabeled as successes
- The forensic section (Section 10) explicitly documents the ANALYSIS_MISMATCH
- All numerical values are taken verbatim from source files
- No new physics claims are made beyond validated outputs
