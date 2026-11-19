"""
PQT Neutrino v1 — METHODOLOGICAL AUDIT
Answers the critical question: prediction or fit?
"""
import numpy as np
from scipy.optimize import minimize
from scipy.linalg import eigh

# Experimental data (PDG 2024 / NuFIT 5.3)
Dm21_sq_exp = 7.53e-5   # eV^2
Dm31_sq_exp = 2.453e-3  # eV^2
theta12_exp = np.radians(33.41)
theta23_exp = np.radians(49.1)
theta13_exp = np.radians(8.54)

# ============================================================
# QUESTION 1: HOW MANY FREE PARAMETERS?
# ============================================================
print("=" * 70)
print("QUESTION 1: Parameter count — prediction or fit?")
print("=" * 70)

print("""
K_T ansatz: 3x3 Hermitian matrix with off-diagonal phases
Parameters:
  k1, k2, k3         — 3 diagonal elements
  eps_12, eps_13, eps_23 — 3 off-diagonal magnitudes  
  phi_12, phi_13, phi_23 — 3 phases

TOTAL FREE PARAMETERS: 9

Observables being fitted:
  theta_12, theta_23, theta_13 — 3 angles
  Ratio Dm21^2/Dm31^2          — 1 ratio
  (Overall mass scale set by Lambda_T — not fitted here)

OBSERVABLES FITTED: 4

VERDICT: 9 parameters > 4 observables = OVERFITTING
The 10^-25 "accuracy" is numerical optimizer precision, NOT physical prediction.
This is a PARAMETERIZATION, not a PREDICTION of angles/splittings.
""")

# ============================================================
# QUESTION 2: WHAT IS GENUINELY PREDICTED?
# ============================================================
print("=" * 70)
print("QUESTION 2: What survives as genuine prediction?")
print("=" * 70)

def build_KT(params):
    k1, k2, k3, eps_12, eps_13, eps_23, phi_12, phi_13, phi_23 = params
    KT = np.zeros((3, 3), dtype=complex)
    KT[0, 0] = k1; KT[1, 1] = k2; KT[2, 2] = k3
    KT[0, 1] = eps_12 * np.exp(1j * phi_12)
    KT[1, 0] = eps_12 * np.exp(-1j * phi_12)
    KT[0, 2] = eps_13 * np.exp(1j * phi_13)
    KT[2, 0] = eps_13 * np.exp(-1j * phi_13)
    KT[1, 2] = eps_23 * np.exp(1j * phi_23)
    KT[2, 1] = eps_23 * np.exp(-1j * phi_23)
    return KT

def extract_physics(params):
    KT = build_KT(params)
    M_herm = (KT + KT.conj().T) / 2
    eigenvalues, U = eigh(M_herm.real)
    idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[idx]
    U = U[:, idx]
    # Scale to physical masses
    dm31 = eigenvalues[2]**2 - eigenvalues[0]**2
    if dm31 > 0:
        scale = np.sqrt(Dm31_sq_exp / dm31)
    else:
        scale = 1.0
    masses = eigenvalues * scale
    dm21 = masses[1]**2 - masses[0]**2
    dm31_phys = masses[2]**2 - masses[0]**2
    m_sum = np.sum(np.abs(masses))
    ordering = "NORMAL" if masses[2] > masses[1] > masses[0] > 0 else "OTHER"
    return masses, dm21, dm31_phys, m_sum, ordering, U

def loss_function(params):
    KT = build_KT(params)
    M_herm = (KT + KT.conj().T) / 2
    eigenvalues, U = eigh(M_herm.real)
    idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[idx]
    U = U[:, idx]
    dm21_sq = eigenvalues[1]**2 - eigenvalues[0]**2
    dm31_sq = eigenvalues[2]**2 - eigenvalues[0]**2
    ratio_exp = Dm21_sq_exp / Dm31_sq_exp
    ratio_model = dm21_sq / dm31_sq if abs(dm31_sq) > 1e-30 else 1e10
    s13 = np.abs(U[0, 2])
    c13 = np.sqrt(max(1 - s13**2, 0))
    t13 = np.arcsin(np.clip(s13, 0, 1))
    s12 = np.abs(U[0, 1]) / c13 if c13 > 1e-10 else 0
    s23 = np.abs(U[1, 2]) / c13 if c13 > 1e-10 else 0
    t12 = np.arcsin(np.clip(s12, 0, 1))
    t23 = np.arcsin(np.clip(s23, 0, 1))
    loss = 100 * (ratio_model - ratio_exp)**2
    loss += (t12 - theta12_exp)**2
    loss += (t23 - theta23_exp)**2
    loss += 10 * (t13 - theta13_exp)**2
    for ev in eigenvalues:
        if ev < 0: loss += 100
    return loss

# Run many fits and collect ALL solutions
print("\nRunning 1000 random fits to explore solution landscape...")
solutions = []
np.random.seed(12345)
for trial in range(1000):
    k_scale = np.random.uniform(0.01, 2.0)
    x0 = [
        k_scale * np.random.uniform(0.01, 1.0),
        k_scale * np.random.uniform(0.1, 1.0),
        k_scale * np.random.uniform(0.1, 1.5),
        k_scale * np.random.uniform(0.01, 0.5),
        k_scale * np.random.uniform(0.001, 0.3),
        k_scale * np.random.uniform(0.01, 0.5),
        np.random.uniform(-np.pi, np.pi),
        np.random.uniform(-np.pi, np.pi),
        np.random.uniform(-np.pi, np.pi),
    ]
    result = minimize(loss_function, x0, method='Nelder-Mead',
                      options={'maxiter': 5000, 'xatol': 1e-10, 'fatol': 1e-12})
    if result.fun < 1e-6:  # good fit
        masses, dm21, dm31, m_sum, ordering, U = extract_physics(result.x)
        if all(m > 0 for m in masses):
            solutions.append({
                'params': result.x,
                'loss': result.fun,
                'masses': masses * 1e3,  # meV
                'm_sum': m_sum * 1e3,  # meV
                'ordering': ordering,
                'dm21': dm21,
                'dm31': dm31,
            })

print(f"Good solutions found: {len(solutions)} / 1000")

# ============================================================
# ANALYZE: IS MASS ORDERING ROBUST?
# ============================================================
print("\n" + "=" * 70)
print("ROBUSTNESS CHECK: Is normal hierarchy a robust prediction?")
print("=" * 70)

orderings = [s['ordering'] for s in solutions]
n_normal = orderings.count("NORMAL")
n_other = orderings.count("OTHER")
print(f"\n  Normal hierarchy: {n_normal} / {len(solutions)} ({100*n_normal/len(solutions):.1f}%)")
print(f"  Other:            {n_other} / {len(solutions)} ({100*n_other/len(solutions):.1f}%)")

# Mass sum distribution
m_sums = [s['m_sum'] for s in solutions]
print(f"\n  Sum of masses (meV):")
print(f"    min:    {min(m_sums):.2f}")
print(f"    max:    {max(m_sums):.2f}")
print(f"    mean:   {np.mean(m_sums):.2f}")
print(f"    median: {np.median(m_sums):.2f}")
print(f"    std:    {np.std(m_sums):.2f}")

# Individual mass distributions
m1s = [s['masses'][0] for s in solutions]
m2s = [s['masses'][1] for s in solutions]
m3s = [s['masses'][2] for s in solutions]
print(f"\n  m1 (meV): {np.mean(m1s):.2f} +/- {np.std(m1s):.2f}  range [{min(m1s):.2f}, {max(m1s):.2f}]")
print(f"  m2 (meV): {np.mean(m2s):.2f} +/- {np.std(m2s):.2f}  range [{min(m2s):.2f}, {max(m2s):.2f}]")
print(f"  m3 (meV): {np.mean(m3s):.2f} +/- {np.std(m3s):.2f}  range [{min(m3s):.2f}, {max(m3s):.2f}]")

# ============================================================
# QUESTION 3: WHAT WOULD A GENUINE PREDICTION REQUIRE?
# ============================================================
print("\n" + "=" * 70)
print("QUESTION 3: Genuine prediction requirements")
print("=" * 70)

print("""
For PQT neutrino to be a PREDICTION (not a fit), one of these must hold:

OPTION A: K_T from first principles (0 free parameters)
  - Derive K_T entirely from hexad structure + Q-Mathematics
  - Each matrix element computed from codon algebra
  - No fitting to neutrino data at all
  - Status: NOT DONE. K_T is parameterized, not derived.

OPTION B: K_T with constraints (< 4 free parameters)  
  - PQT symmetries reduce 9 parameters to <= 3
  - Fit fewer parameters than observables
  - Remaining observables are genuine predictions
  - Status: NOT DONE. Currently 9 free params > 4 observables.

OPTION C: Structural predictions independent of K_T details
  - Properties that hold for ANY K_T consistent with PQT
  - These are genuine predictions even with 9 parameters
  - Examples checked below...
""")

# Check structural predictions
print("STRUCTURAL PREDICTIONS (valid regardless of K_T parameterization):")
print()

# 1. m_nu = 0 from Yukawa
print("1. m_nu^Yukawa = 0 (from hexad gauge structure)")
print("   This is STRUCTURAL — does not depend on K_T.")
print("   Status: GENUINE PREDICTION of PQT framework.")
print()

# 2. Seesaw-analog scale
print("2. Tamas-seesaw: m_nu ~ Lambda_EW^2 / m_iota")
print("   Predicts m_iota ~ 10^15 GeV IF m_nu ~ 0.05 eV")
print("   This constrains the Tamas mass scale.")
print("   Status: GENUINE structural prediction (order-of-magnitude).")
print()

# 3. Normal hierarchy robustness
print(f"3. Normal hierarchy: {100*n_normal/len(solutions):.0f}% of solutions")
if n_normal / len(solutions) > 0.95:
    print("   ROBUST across solution space -> GENUINE prediction")
elif n_normal / len(solutions) > 0.50:
    print("   MAJORITY but not robust -> WEAK prediction")
else:
    print("   NOT robust -> NOT a prediction")
print()

# 4. Sum of masses range
below_planck = sum(1 for s in m_sums if s < 120)
print(f"4. Sum m_nu < 0.12 eV: {100*below_planck/len(solutions):.0f}% of solutions")
print(f"   Range: [{min(m_sums):.1f}, {max(m_sums):.1f}] meV")
print()

# 5. m1 > 0 (no massless neutrino)
m1_min = min(m1s)
print(f"5. Lightest neutrino mass m1 > 0:")
print(f"   min(m1) = {m1_min:.3f} meV across all solutions")
if m1_min > 0.1:
    print("   PQT excludes m1 = 0 -> GENUINE prediction (testable by KATRIN/Project 8)")
else:
    print("   m1 can be very small -> weak prediction")

# ============================================================
# HONEST SCORECARD
# ============================================================
print("\n" + "=" * 70)
print("HONEST SCORECARD")
print("=" * 70)

print("""
+------------------------------------------+----------+------------------+
| Claim                                    | Type     | Status           |
+------------------------------------------+----------+------------------+
| m_nu = 0 from Yukawa in hexad           | STRUCT.  | GENUINE          |
| Mass from Tamas sector (not Higgs)       | STRUCT.  | GENUINE          |
| Tamas-seesaw scale m_iota ~ 10^15 GeV   | STRUCT.  | GENUINE (order)  |
| Normal mass hierarchy                    | ROBUST?  | See above        |
| Sum m_nu < 0.12 eV                       | RANGE    | See above        |
| m1 > 0 (no massless neutrino)            | RANGE    | See above        |
| theta_12 = 33.41 deg                     | FIT      | NOT prediction   |
| theta_23 = 49.10 deg                     | FIT      | NOT prediction   |
| theta_13 = 8.54 deg                      | FIT      | NOT prediction   |
| Dm21^2/Dm31^2 = 0.0307                   | FIT      | NOT prediction   |
| "Accuracy 10^-25"                        | ARTIFACT | Optimizer noise  |
| delta_CP = 0 deg                         | DEFAULT  | Hermitian approx |
+------------------------------------------+----------+------------------+

BOTTOM LINE:
  PQT neutrino v1 is a PARAMETERIZATION with structural constraints,
  NOT a parameter-free prediction. The 10^-25 accuracy claim is
  misleading — it reflects optimizer convergence, not physical content.

  GENUINE predictions: m_nu=0 from Yukawa, Tamas-seesaw scale,
  possibly normal hierarchy (if robust across solutions).
  
  TO UPGRADE TO PREDICTION: derive K_T from Q-Mathematics codons
  with <= 3 free parameters, or show structural constraints
  that reduce the parameter space below the observable count.
""")
