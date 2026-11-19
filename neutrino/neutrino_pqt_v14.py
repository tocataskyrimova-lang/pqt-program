# -*- coding: utf-8 -*-
"""
PQT Neutrino v14 — TBM with Controlled Breaking via Asymmetric Metric

Physical basis:
  Democratic metric (d_ij = 1) → exact TBM (v13)
  Asymmetric metric (d_13 = 1+δ) → broken TBM → θ_13 ≠ 0

  δ > 0: Gen1↔Gen3 transition is "harder" (memory bypass)
  μ_ν > 0: finite delocalization allows metric to "show through"

  Key: breaking ∝ μ_ν · δ (both needed)

Charged leptons: anisotropic metric (v10, fixed)
Neutrinos: partially broken democratic metric (new)
PMNS = U_ℓ† · U_ν
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
from scipy.linalg import eigh
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# METRICS
# ============================================================
def D_neutrino(delta):
    """Partially broken democratic metric for neutrinos.
    δ = 0: democratic (TBM)
    δ > 0: Gen1↔Gen3 harder (TBM breaking)
    """
    return np.array([[0, 1, 1 + delta],
                     [1, 0, 1],
                     [1 + delta, 1, 0]], dtype=float)

D_ell = np.array([[0, 1, 3],
                  [1, 0, 2],
                  [3, 2, 0]], dtype=float)

# ============================================================
# YUKAWA MATRIX CONSTRUCTION
# ============================================================
def build_Y(diag_y, mu, lam, phases, D):
    """
    Y_ij = delta_ij * y_i + lam * exp(-mu * D_ij + i * phi_ij)
    PSD guaranteed when mu >= 0, lam >= 0, y_i > 0.
    """
    Y = np.diag(diag_y) + lam * np.exp(-mu * D + 1j * phases)
    return Y

# ============================================================
# PMNS EXTRACTION
# ============================================================
def extract_pmns(Y_ell, Y_nu):
    """Extract PMNS from Y_ell and Y_nu diagonalization."""
    # Neutrino sector
    M_nu = Y_nu.conj().T @ Y_nu
    eigs_nu, U_nu = eigh(M_nu)
    eigs_nu = eigs_nu.real
    m_nu = np.sqrt(np.maximum(eigs_nu, 0))

    # Charged lepton sector
    M_ell = Y_ell.conj().T @ Y_ell
    eigs_ell, U_ell = eigh(M_ell)
    eigs_ell = eigs_ell.real
    m_ell = np.sqrt(np.maximum(eigs_ell, 0))

    # PSD check
    if eigs_nu[0] < -1e-6 or eigs_ell[0] < -1e-6:
        return None

    # Column assignment for IO (model prediction):
    # (1,1,1)/sqrt(3) has largest eigenvalue -> m2 (heaviest in IO)
    # m1: larger |U_e| among remaining (TBM: |U_e1|=1/sqrt(2))
    # m3: smaller |U_e| among remaining (TBM: |U_e3|=0)
    U_abs_e = np.abs(U_nu[0, :])
    idx_m2 = np.argmax(eigs_nu)
    remaining = [i for i in range(3) if i != idx_m2]
    if U_abs_e[remaining[0]] > U_abs_e[remaining[1]]:
        idx_m1, idx_m3 = remaining[0], remaining[1]
    else:
        idx_m1, idx_m3 = remaining[1], remaining[0]

    idx_nu = [idx_m1, idx_m2, idx_m3]
    U_nu = U_nu[:, idx_nu]
    m_nu = m_nu[idx_nu]
    eigs_nu = eigs_nu[idx_nu]

    idx_ell = np.argsort(m_ell)
    m_ell = m_ell[idx_ell]
    U_ell = U_ell[:, idx_ell]

    # PMNS matrix
    V = U_ell.conj().T @ U_nu
    V_abs = np.abs(V)

    # PMNS angles
    s13 = V_abs[0, 2]
    theta13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    s23 = V_abs[1, 2] / den
    theta23 = np.degrees(np.arcsin(np.clip(s23, 0, 1)))
    s12 = V_abs[0, 1] / den
    theta12 = np.degrees(np.arcsin(np.clip(s12, 0, 1)))

    # Mass ratios (IO-compatible)
    dm21 = m_nu[1]**2 - m_nu[0]**2
    dm31 = m_nu[2]**2 - m_nu[0]**2
    ratio = dm21 / abs(dm31) if abs(dm31) > 1e-20 else 0

    # Jarlskog
    J_CP = np.imag(V[0,0] * V[1,1] * np.conj(V[0,1]) * np.conj(V[1,0]))

    return {
        'theta12': theta12, 'theta23': theta23, 'theta13': theta13,
        'ratio': ratio, 'masses': m_nu, 'm_ell': m_ell,
        'hierarchy': 'NH' if m_nu[0] < m_nu[1] < m_nu[2] else 'IH',
        'J_CP': J_CP, 'V_PMNS': V, 'U_nu': U_nu, 'U_ell': U_ell,
        'min_eig_nu': eigs_nu[0], 'min_eig_ell': eigs_ell[0],
        'V_abs': V_abs,
    }

# ============================================================
# EXPERIMENTAL VALUES
# ============================================================
EXP = {
    'theta12': (33.44, 0.7),
    'theta23': (49.2, 1.1),
    'theta13': (8.57, 0.12),
    'dm2_ratio': (0.0307, 0.0009),
}
EXP_JCP = (0.033, 0.006)

def chi2(r, include_J=False):
    if r is None: return 1e10
    c = 0
    for obs in ['theta12', 'theta23', 'theta13']:
        c += ((r[obs] - EXP[obs][0]) / EXP[obs][1])**2
    if r['ratio'] > 0:
        c += ((r['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1])**2
    else:
        c += 1e4
    if r['hierarchy'] != 'NH':
        c += 1e3
    if include_J and abs(r['J_CP']) > 0.001:
        c += ((abs(r['J_CP']) - EXP_JCP[0]) / EXP_JCP[1])**2
    return c

# ============================================================
# CHARGED LEPTON SECTOR (fixed)
# ============================================================
ELL_MU = 40.0       # exp(-40) ~ 4e-18, effectively kills off-diagonal
ELL_LAM = 1.0       # O(1) coupling, suppressed by exp(-40)
ELL_DIAG = np.array([1e-14, 1e-8, 1e-2])  # physical hierarchy
ELL_PHASES = np.zeros((3, 3))

Y_ell = build_Y(ELL_DIAG, ELL_MU, ELL_LAM, ELL_PHASES, D_ell)

# Verify U_ell ~ diagonal
M_ell_check = Y_ell.conj().T @ Y_ell
_, U_ell_check = eigh(M_ell_check)
print("Charged lepton |U_ell| (should be ~diagonal):")
print(np.array2string(np.abs(U_ell_check), precision=4, suppress_small=True))

# ============================================================
H = lambda s: print(f"\n{s:=^90}")

# ============================================================
# PHASE 0: v13 BASELINE
# ============================================================
H("PHASE 0: v13 TBM LIMIT (delta=0, mu=0)")
phases_0 = np.zeros((3, 3))
Y_nu_tbm = build_Y(np.ones(3), 0.0, 1.0, phases_0, D_neutrino(0))
r_tbm = extract_pmns(Y_ell, Y_nu_tbm)
if r_tbm:
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(r_tbm[obs] - EXP[obs][0]) / EXP[obs][1]
        print(f"  {obs:8s} = {r_tbm[obs]:7.2f}  pull={pull:5.1f}s")
    print(f"  ratio    = {r_tbm['ratio']:.5f}")
    print(f"  chi2     = {chi2(r_tbm):.1f}")

# ============================================================
# PHASE 1: delta SWEEP
# ============================================================
H("PHASE 1: delta-SWEEP (mu=0.1, lam=1.0, no phases)")
print(f"{'delta':>7} {'th12':>7} {'th23':>7} {'th13':>7} {'ratio':>9} "
      f"{'NH':>3} {'chi2':>10}")
print("-" * 60)

best_d = None
for d100 in range(0, 501):
    delta = d100 / 100.0
    Y_nu = build_Y(np.ones(3), 0.1, 1.0, phases_0, D_neutrino(delta))
    r = extract_pmns(Y_ell, Y_nu)
    if r is None: continue
    c = chi2(r)
    if best_d is None or c < best_d['chi2']:
        best_d = {**r, 'chi2': c, 'delta': delta}
    if d100 % 50 == 0 or abs(r['theta13'] - 8.57) < 1.0:
        print(f"{delta:7.2f} {r['theta12']:7.1f} {r['theta23']:7.1f} "
              f"{r['theta13']:7.1f} {r['ratio']:9.5f} "
              f"{'Y' if r['hierarchy']=='NH' else 'N':>3} {c:10.1f}")

if best_d:
    print(f"\n  Best delta={best_d['delta']:.2f} th13={best_d['theta13']:.1f} chi2={best_d['chi2']:.1f}")

# ============================================================
# PHASE 2: mu x delta MAP
# ============================================================
H("PHASE 2: mu x delta MAP (no phases, lam=1)")
print(f"{'mu':>6} {'delta':>6} {'th12':>7} {'th23':>7} {'th13':>7} {'chi2':>10}")
print("-" * 55)

for mu10 in range(0, 31):
    mu = mu10 / 10.0
    for d10 in range(0, 31):
        delta = d10 / 10.0
        Y_nu = build_Y(np.ones(3), mu, 1.0, phases_0, D_neutrino(delta))
        r = extract_pmns(Y_ell, Y_nu)
        if r is None: continue
        if abs(r['theta13'] - 8.57) < 2.0 or (mu10 % 10 == 0 and d10 % 10 == 0):
            print(f"{mu:6.1f} {delta:6.1f} {r['theta12']:7.1f} {r['theta23']:7.1f} "
                  f"{r['theta13']:7.1f} {chi2(r):10.1f}")

# ============================================================
# PHASE 3: FULL SCAN
# ============================================================
H("PHASE 3: FULL SCAN (mu, lam, delta, phi12, phi23)")

best = None
results = []

for mu10 in range(1, 31):
    mu = mu10 / 10.0
    for lam10 in range(5, 31):
        lam = lam10 / 10.0
        for d10 in range(1, 51):
            delta = d10 / 10.0
            for p12 in range(0, 21, 2):
                phi12 = p12 * np.pi / 10.0
                for p23 in range(0, 21, 2):
                    phi23 = p23 * np.pi / 10.0

                    phases = np.array([[0, phi12, 0],
                                       [-phi12, 0, phi23],
                                       [0, -phi23, 0]])

                    Y_nu = build_Y(np.ones(3), mu, lam, phases,
                                    D_neutrino(delta))
                    r = extract_pmns(Y_ell, Y_nu)
                    if r is None: continue

                    c = chi2(r)
                    entry = {**r, 'chi2': c, 'mu': mu, 'lam': lam,
                             'delta': delta, 'phi12': phi12, 'phi23': phi23}
                    if best is None or c < best['chi2']:
                        best = entry
                    results.append(entry)

results.sort(key=lambda x: x['chi2'])

print(f"\n  TOP 15:")
print(f"  {'#':>3} {'mu':>5} {'lam':>5} {'dlt':>5} {'ph12':>5} {'ph23':>5} "
      f"{'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'J':>8} {'c2':>10}")
print("  " + "-" * 85)
for i, r in enumerate(results[:15]):
    print(f"  {i+1:3d} {r['mu']:5.2f} {r['lam']:5.1f} {r['delta']:5.2f} "
          f"{r['phi12']:5.2f} {r['phi23']:5.2f} "
          f"{r['theta12']:7.1f} {r['theta23']:7.1f} {r['theta13']:7.1f} "
          f"{r['ratio']:9.5f} {r['J_CP']:8.5f} {r['chi2']:10.1f}")

# ============================================================
# BEST RESULT
# ============================================================
if best:
    H("BEST RESULT (v14)")
    print(f"  Neutrino sector:")
    print(f"    mu     = {best['mu']:.3f}")
    print(f"    lam    = {best['lam']:.1f}")
    print(f"    delta  = {best['delta']:.3f}")
    print(f"    phi12  = {best['phi12']:.3f} ({np.degrees(best['phi12']):.1f} deg)")
    print(f"    phi23  = {best['phi23']:.3f} ({np.degrees(best['phi23']):.1f} deg)")
    print()

    pulls = {}
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(best[obs] - EXP[obs][0]) / EXP[obs][1]
        pulls[obs] = pull
        status = "OK" if pull < 3 else "WARN" if pull < 5 else "FAIL"
        print(f"  {obs:8s} = {best[obs]:7.2f}  (exp: {EXP[obs][0]:.2f} +/- "
              f"{EXP[obs][1]:.2f})  pull={pull:5.1f}s {status}")

    pull_r = abs(best['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    pulls['ratio'] = pull_r
    print(f"  {'ratio':8s} = {best['ratio']:7.5f}  (exp: {EXP['dm2_ratio'][0]})  "
          f"pull={pull_r:5.1f}s")
    print(f"  {'J_CP':8s} = {best['J_CP']:7.5f}  (exp: {EXP_JCP[0]})")
    print(f"  chi2 = {best['chi2']:.1f}")
    print(f"  Masses (nu): {best['masses']}")
    print(f"  Masses (ell): {best['m_ell']}")
    print(f"  PSD nu: {best['min_eig_nu']:.6f}")
    print(f"  PSD ell: {best['min_eig_ell']:.6f}")
    print(f"  Hierarchy: {best['hierarchy']}")

    all_lt3 = all(p < 3 for p in pulls.values())
    all_lt5 = all(p < 5 for p in pulls.values())
    print(f"\n  ALL ANGLES < 3s? {'YES -- BREAKTHROUGH!' if all_lt3 else 'NO'}")
    print(f"  ALL ANGLES < 5s? {'YES' if all_lt5 else 'NO'}")

    # PMNS matrix
    print(f"\n  |U_PMNS|:")
    V = best['V_abs']
    labels = ['e', 'mu', 'tau']
    for i in range(3):
        row = "  ".join(f"{V[i,j]:.4f}" for j in range(3))
        print(f"    {labels[i]}   {row}")

# ============================================================
# PHASE 4: FINE REFINEMENT
# ============================================================
if best and best['chi2'] < 100:
    H("PHASE 4: FINE REFINEMENT")

    best_fine = None
    for mu100 in range(max(1, int((best['mu']-0.2)*100)),
                        int((best['mu']+0.2)*100)+1):
        mu = mu100 / 100.0
        for lam100 in range(max(1, int((best['lam']-0.3)*100)),
                             int((best['lam']+0.3)*100)+1):
            lam = lam100 / 100.0
            for d100 in range(max(1, int((best['delta']-0.3)*100)),
                               int((best['delta']+0.3)*100)+1):
                delta = d100 / 100.0
                for p12_10 in range(max(0, int((best['phi12']-0.3)*10/np.pi)*10),
                                     int((best['phi12']+0.3)*10/np.pi)*10+1):
                    phi12 = p12_10 * np.pi / 100.0
                    for p23_10 in range(max(0, int((best['phi23']-0.3)*10/np.pi)*10),
                                         int((best['phi23']+0.3)*10/np.pi)*10+1):
                        phi23 = p23_10 * np.pi / 100.0

                        phases = np.array([[0, phi12, 0],
                                           [-phi12, 0, phi23],
                                           [0, -phi23, 0]])
                        Y_nu = build_Y(np.ones(3), mu, lam, phases,
                                        D_neutrino(delta))
                        r = extract_pmns(Y_ell, Y_nu)
                        if r is None: continue
                        c = chi2(r)
                        entry = {**r, 'chi2': c, 'mu': mu, 'lam': lam,
                                 'delta': delta, 'phi12': phi12, 'phi23': phi23}
                        if best_fine is None or c < best_fine['chi2']:
                            best_fine = entry

    if best_fine:
        print(f"  Fine: mu={best_fine['mu']:.3f} lam={best_fine['lam']:.2f} "
              f"delta={best_fine['delta']:.3f}")
        for obs in ['theta12', 'theta23', 'theta13']:
            pull = abs(best_fine[obs] - EXP[obs][0]) / EXP[obs][1]
            status = "OK" if pull < 3 else "WARN" if pull < 5 else "FAIL"
            print(f"    {obs} = {best_fine[obs]:.2f} pull={pull:.1f}s {status}")
        print(f"    ratio = {best_fine['ratio']:.5f}")
        print(f"    chi2 = {best_fine['chi2']:.1f}")
        best = best_fine

# ============================================================
# EVOLUTION
# ============================================================
H("EVOLUTION v8 -> v14")
print(f"  {'Ver':<5} {'t12':>7} {'t23':>7} {'t13':>7} {'r':>9} {'J':>8} {'c2':>10} {'Key':>25}")
print("  " + "-" * 80)
for row in [("v8","54.3","51.1","8.6","0.506","0","281000","rank-2 theorem"),
            ("v9","35.2","77.6","8.4","0.034","0","693","rank-3 sigma-charge"),
            ("v10","32.9","58.7","8.5","0.030","0","77","position-aware eta"),
            ("v13","35.2","45.0","0.0","1.0","0","5000+","democratic TBM")]:
    print(f"  {row[0]:<5} {row[1]:>7} {row[2]:>7} {row[3]:>7} {row[4]:>9} {row[5]:>8} {row[6]:>10} {row[7]:>25}")
if best:
    print(f"  {'v14':<5} {best['theta12']:7.1f} {best['theta23']:7.1f} "
          f"{best['theta13']:7.1f} {best['ratio']:9.5f} {best['J_CP']:8.5f} "
          f"{best['chi2']:10.1f} {'broken TBM delta':>25}")
print(f"  {'Exp':<5} {'33.4':>7} {'49.2':>7} {'8.6':>7} {'0.031':>9} {'0.033':>8}")
