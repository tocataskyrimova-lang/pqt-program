# -*- coding: utf-8 -*-
"""
PQT Neutrino v15 — TBM from Democratic Metric + Charged Lepton Corrections

Physical structure:
  U_nu (democratic metric + hierarchy y3 >> y1,y2) → exact TBM
  U_ell (anisotropic metric, moderate mu_e) → small rotation corrections
  PMNS = U_ell† · U_nu
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
D_dem = np.array([[0, 1, 1],
                  [1, 0, 1],
                  [1, 1, 0]], dtype=float)

D_aniso = np.array([[0, 1, 3],
                    [1, 0, 2],
                    [3, 2, 0]], dtype=float)

# ============================================================
# YUKAWA CONSTRUCTION
# ============================================================
def build_Y(diag_y, mu, lam, phases, D):
    return np.diag(diag_y) + lam * np.exp(-mu * D + 1j * phases)

def antisym_phase(p12, p23, p13=0):
    return np.array([[0, p12, p13],
                     [-p12, 0, p23],
                     [-p13, -p23, 0]])

# ============================================================
# PMNS EXTRACTION
# ============================================================
def extract_pmns(Y_ell, Y_nu):
    M_nu = Y_nu.conj().T @ Y_nu
    en, Un = eigh(M_nu)
    en = en.real
    mn = np.sqrt(np.maximum(en, 0))

    M_ell = Y_ell.conj().T @ Y_ell
    ee, Ue = eigh(M_ell)
    ee = ee.real
    me = np.sqrt(np.maximum(ee, 0))

    if en[0] < -1e-6 or ee[0] < -1e-6:
        return None

    # Sort ascending
    idx_n = np.argsort(mn); mn = mn[idx_n]; Un = Un[:, idx_n]; en = en[idx_n]
    idx_e = np.argsort(me); me = me[idx_e]; Ue = Ue[:, idx_e]

    V = Ue.conj().T @ Un
    Va = np.abs(V)

    s13 = Va[0, 2]
    t13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    t23 = np.degrees(np.arcsin(np.clip(Va[1, 2] / den, 0, 1)))
    t12 = np.degrees(np.arcsin(np.clip(Va[0, 1] / den, 0, 1)))

    dm21 = mn[1]**2 - mn[0]**2
    dm31 = mn[2]**2 - mn[0]**2
    ratio = dm21 / abs(dm31) if abs(dm31) > 1e-20 else 0

    J = np.imag(V[0,0] * V[1,1] * np.conj(V[0,1]) * np.conj(V[1,0]))

    # TBM overlap
    tbm = np.array([1, 1, 1]) / np.sqrt(3)
    tbm_ov = [abs(np.dot(Un[:, i].conj(), tbm))**2 for i in range(3)]

    nh = 'NH' if mn[0] < mn[1] < mn[2] else 'IH'

    return {
        'theta12': t12, 'theta23': t23, 'theta13': t13,
        'ratio': ratio, 'masses': mn, 'm_ell': me,
        'hierarchy': nh, 'J_CP': J, 'V_PMNS': V, 'V_abs': Va,
        'U_nu': Un, 'U_ell': Ue, 'tbm_overlap': tbm_ov,
        'min_eig_nu': en[0], 'min_eig_ell': ee[0],
    }

# ============================================================
# EXPERIMENTAL
# ============================================================
EXP = {
    'theta12': (33.44, 0.7),
    'theta23': (49.2, 1.1),
    'theta13': (8.57, 0.12),
    'dm2_ratio': (0.0307, 0.0009),
}
EXP_JCP = (0.033, 0.006)

def chi2(r):
    if r is None: return 1e10
    c = 0
    for o in ['theta12', 'theta23', 'theta13']:
        c += ((r[o] - EXP[o][0]) / EXP[o][1])**2
    if r['ratio'] > 0:
        c += ((r['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1])**2
    else:
        c += 1e4
    if r['hierarchy'] != 'NH':
        c += 10  # mild penalty
    return c

# ============================================================
H = lambda s: print(f"\n{s:=^95}")

# ============================================================
# PHASE 0: PURE TBM with y3 >> y1,y2
# ============================================================
print("=" * 95)
print("PQT NEUTRINO v15 — TBM + CHARGED LEPTON CORRECTIONS")
print("=" * 95)

H("PHASE 0: PURE TBM (U_ell = I)")

# y3 >> y1,y2 ensures (1,1,1)/sqrt(3) is m2
diag_nu = np.array([1.0, 1.0, 10.0])
Y_nu_tbm = build_Y(diag_nu, 0.0, 1.0, np.zeros((3,3)), D_dem)
Y_ell_I = np.eye(3, dtype=complex)

r_tbm = extract_pmns(Y_ell_I, Y_nu_tbm)
if r_tbm:
    print(f"  TBM overlap on m2: {r_tbm['tbm_overlap'][1]:.3f}")
    print(f"  Masses: {r_tbm['masses']}")
    for o in ['theta12', 'theta23', 'theta13']:
        tgt = 35.26 if o == 'theta12' else 45.0 if o == 'theta23' else 0.0
        print(f"  {o:8s} = {r_tbm[o]:7.2f}  (TBM: {tgt:.1f})")

# ============================================================
# PHASE 1: NEUTRINO PARAMETER SCAN — find best TBM
# ============================================================
H("PHASE 1: NEUTRINO PARAMETER SCAN")

print(f"{'y1':>5} {'y2':>5} {'y3':>5} {'mu':>5} {'lam':>5} "
      f"{'t12':>7} {'t23':>7} {'t13':>7} {'TBM_m2':>7} {'c2_tbm':>8}")
print("-" * 70)

best_nu = None
for y1_10 in [5, 10, 15, 20, 30]:
    y1 = y1_10 / 10.0
    for y2_10 in [5, 10, 15, 20, 30]:
        y2 = y2_10 / 10.0
        for y3_10 in range(20, 301, 10):
            y3 = y3_10 / 10.0
            for mu10 in range(0, 11):
                mu = mu10 / 10.0
                for lam10 in [5, 10, 15, 20, 25, 30]:
                    lam = lam10 / 10.0

                    Y_nu = build_Y(np.array([y1, y2, y3]), mu, lam,
                                    np.zeros((3,3)), D_dem)
                    r = extract_pmns(Y_ell_I, Y_nu)
                    if r is None: continue

                    # TBM quality
                    tbm_c2 = ((r['theta12'] - 35.26)/0.5)**2 + \
                             ((r['theta23'] - 45.0)/0.5)**2 + \
                             (r['theta13']/0.3)**2
                    tbm_m2 = r['tbm_overlap'][1]

                    if tbm_m2 > 0.8 and (best_nu is None or
                        (tbm_c2 < best_nu['tbm_c2'] and r['ratio'] > 0)):
                        best_nu = {**r, 'tbm_c2': tbm_c2,
                                   'y1': y1, 'y2': y2, 'y3': y3,
                                   'mu': mu, 'lam': lam}

                    if tbm_m2 > 0.95 and tbm_c2 < 1:
                        print(f"{y1:5.1f} {y2:5.1f} {y3:5.1f} {mu:5.1f} {lam:5.1f} "
                              f"{r['theta12']:7.2f} {r['theta23']:7.2f} {r['theta13']:7.2f} "
                              f"{tbm_m2:7.3f} {tbm_c2:8.2f}")

if best_nu:
    print(f"\n  Best neutrino: y=({best_nu['y1']:.1f},{best_nu['y2']:.1f},{best_nu['y3']:.1f}), "
          f"mu={best_nu['mu']:.1f}, lam={best_nu['lam']:.1f}")
    print(f"  TBM overlap: {[f'{x:.3f}' for x in best_nu['tbm_overlap']]}")
    print(f"  Angles: t12={best_nu['theta12']:.2f} t23={best_nu['theta23']:.2f} "
          f"t13={best_nu['theta13']:.2f}")
    print(f"  ratio={best_nu['ratio']:.5f} nh={best_nu['hierarchy']}")

# ============================================================
# PHASE 2: CHARGED LEPTON CORRECTION
# ============================================================
H("PHASE 2: CHARGED LEPTON CORRECTION SCAN")

# Use best neutrino or default
if best_nu:
    y_n = np.array([best_nu['y1'], best_nu['y2'], best_nu['y3']])
    mu_n = best_nu['mu']
    lam_n = best_nu['lam']
else:
    y_n = np.array([1.0, 1.0, 10.0])
    mu_n = 0.0
    lam_n = 1.0

Y_nu_fixed = build_Y(y_n, mu_n, lam_n, np.zeros((3,3)), D_dem)

# Physical charged lepton masses (GeV)
y_e_phys = np.array([0.511e-3, 105.7e-3, 1777e-3])

print(f"  Neutrino: y=({y_n[0]:.1f},{y_n[1]:.1f},{y_n[2]:.1f}), mu={mu_n}, lam={lam_n}")
print(f"  Charged leptons: y=({y_e_phys[0]:.4f},{y_e_phys[1]:.3f},{y_e_phys[2]:.1f})")
print()
print(f"{'mu_e':>6} {'lam_e':>6} {'p12':>5} {'p23':>5} {'p13':>5} "
      f"{'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'J':>8} {'c2':>10}")
print("-" * 85)

best = None
results = []

# Scan: mu_e 3-15, lam_e 0.1-5.0, phases coarse
for mu_e10 in range(30, 151, 5):
    mu_e = mu_e10 / 10.0
    for lam_e10 in range(1, 51, 2):
        lam_e = lam_e10 / 10.0
        for p12 in range(0, 21, 3):
            phi12 = p12 * np.pi / 10.0
            for p23 in range(0, 21, 3):
                phi23 = p23 * np.pi / 10.0
                for p13 in range(0, 21, 3):
                    phi13 = p13 * np.pi / 10.0

                    ph = antisym_phase(phi12, phi23, phi13)
                    Y_ell = build_Y(y_e_phys, mu_e, lam_e, ph, D_aniso)
                    r = extract_pmns(Y_ell, Y_nu_fixed)
                    if r is None: continue

                    c = chi2(r)
                    entry = {**r, 'chi2': c, 'mu_e': mu_e, 'lam_e': lam_e,
                             'phi12': phi12, 'phi23': phi23, 'phi13': phi13}
                    if best is None or c < best['chi2']:
                        best = entry
                    results.append(entry)

results.sort(key=lambda x: x['chi2'])

print(f"\n  TOP 15:")
print(f"  {'#':>3} {'mu_e':>6} {'lam':>5} {'p12':>5} {'p23':>5} {'p13':>5} "
      f"{'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'J':>8} {'c2':>10}")
print("  " + "-" * 80)
for i, r in enumerate(results[:15]):
    print(f"  {i+1:3d} {r['mu_e']:6.1f} {r['lam_e']:5.1f} "
          f"{r['phi12']:5.2f} {r['phi23']:5.2f} {r['phi13']:5.2f} "
          f"{r['theta12']:7.1f} {r['theta23']:7.1f} {r['theta13']:7.1f} "
          f"{r['ratio']:9.5f} {r['J_CP']:8.5f} {r['chi2']:10.1f}")

# ============================================================
# BEST RESULT
# ============================================================
if best:
    H("BEST RESULT (v15)")
    print(f"  Neutrino: y=({y_n[0]:.1f},{y_n[1]:.1f},{y_n[2]:.1f})")
    print(f"  Charged lepton: mu_e={best['mu_e']:.1f}, lam_e={best['lam_e']:.1f}")
    print(f"    phi12={best['phi12']:.2f} ({np.degrees(best['phi12']):.0f} deg)")
    print(f"    phi23={best['phi23']:.2f} ({np.degrees(best['phi23']):.0f} deg)")
    print(f"    phi13={best['phi13']:.2f} ({np.degrees(best['phi13']):.0f} deg)")
    print()

    pulls = {}
    for o in ['theta12', 'theta23', 'theta13']:
        p = abs(best[o] - EXP[o][0]) / EXP[o][1]
        pulls[o] = p
        s = "OK" if p < 3 else "WARN" if p < 5 else "FAIL"
        print(f"  {o:8s} = {best[o]:7.2f}  (exp: {EXP[o][0]:.2f} +/- {EXP[o][1]:.2f})  "
              f"pull={p:5.1f}s {s}")

    pr = abs(best['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    pulls['ratio'] = pr
    print(f"  {'ratio':8s} = {best['ratio']:7.5f}  (exp: {EXP['dm2_ratio'][0]})  pull={pr:5.1f}s")
    print(f"  {'J_CP':8s} = {best['J_CP']:7.5f}  (exp: {EXP_JCP[0]})")
    print(f"  chi2 = {best['chi2']:.1f}")
    print(f"  Masses (nu): {best['masses']}")
    print(f"  Masses (ell): {best['m_ell']}")
    print(f"  TBM overlap: {[f'{x:.3f}' for x in best['tbm_overlap']]}")
    print(f"  Hierarchy: {best['hierarchy']}")

    all3 = all(p < 3 for p in pulls.values())
    all5 = all(p < 5 for p in pulls.values())
    print(f"\n  ALL < 3s? {'YES -- BREAKTHROUGH!' if all3 else 'NO'}")
    print(f"  ALL < 5s? {'YES' if all5 else 'NO'}")

    print(f"\n  |U_PMNS|:")
    V = best['V_abs']
    for i, l in enumerate(['e', 'mu', 'tau']):
        row = "  ".join(f"{V[i,j]:.4f}" for j in range(3))
        print(f"    {l}   {row}")

    print(f"\n  TBM vs v15 vs Exp:")
    for o in ['theta12', 'theta23', 'theta13']:
        tgt = 35.26 if o == 'theta12' else 45.0 if o == 'theta23' else 0.0
        print(f"    {o}: TBM={tgt:.1f}, v15={best[o]:.1f}, Exp={EXP[o][0]:.1f}")

# ============================================================
# PHASE 3: FINE REFINEMENT
# ============================================================
if best and best['chi2'] < 500:
    H("PHASE 3: FINE REFINEMENT")
    best_f = None
    for mu_e100 in range(max(10, int((best['mu_e']-1)*100)),
                          int((best['mu_e']+1)*100)+1):
        mu_e = mu_e100 / 100.0
        for lam_e100 in range(max(1, int((best['lam_e']-0.5)*100)),
                               int((best['lam_e']+0.5)*100)+1):
            lam_e = lam_e100 / 100.0
            for p12_100 in range(int((best['phi12']-0.3)*100/np.pi)*10,
                                  int((best['phi12']+0.3)*100/np.pi)*10+1):
                phi12 = p12_100 * np.pi / 1000.0
                for p23_100 in range(int((best['phi23']-0.3)*100/np.pi)*10,
                                      int((best['phi23']+0.3)*100/np.pi)*10+1):
                    phi23 = p23_100 * np.pi / 1000.0
                    for p13_100 in range(int((best['phi13']-0.3)*100/np.pi)*10,
                                          int((best['phi13']+0.3)*100/np.pi)*10+1):
                        phi13 = p13_100 * np.pi / 1000.0

                        ph = antisym_phase(phi12, phi23, phi13)
                        Y_ell = build_Y(y_e_phys, mu_e, lam_e, ph, D_aniso)
                        r = extract_pmns(Y_ell, Y_nu_fixed)
                        if r is None: continue
                        c = chi2(r)
                        entry = {**r, 'chi2': c, 'mu_e': mu_e, 'lam_e': lam_e,
                                 'phi12': phi12, 'phi23': phi23, 'phi13': phi13}
                        if best_f is None or c < best_f['chi2']:
                            best_f = entry

    if best_f and best_f['chi2'] < best['chi2']:
        print(f"  Fine: mu_e={best_f['mu_e']:.2f} lam_e={best_f['lam_e']:.2f}")
        for o in ['theta12', 'theta23', 'theta13']:
            p = abs(best_f[o] - EXP[o][0]) / EXP[o][1]
            s = "OK" if p < 3 else "WARN" if p < 5 else "FAIL"
            print(f"    {o} = {best_f[o]:.2f} pull={p:.1f}s {s}")
        print(f"    ratio = {best_f['ratio']:.5f} chi2 = {best_f['chi2']:.1f}")
        best = best_f

# ============================================================
# PHASE 4: ROBUSTNESS
# ============================================================
H("PHASE 4: ROBUSTNESS (multiple TBM points)")
if best:
    configs = [
        (1.0, 1.0, 5.0, 0.0, 1.0),
        (1.0, 1.0, 10.0, 0.0, 1.0),
        (1.0, 1.0, 20.0, 0.0, 1.0),
        (0.5, 0.5, 10.0, 0.0, 1.0),
        (2.0, 2.0, 10.0, 0.0, 1.0),
    ]
    ph_best = antisym_phase(best['phi12'], best['phi23'], best['phi13'])
    Y_ell_best = build_Y(y_e_phys, best['mu_e'], best['lam_e'], ph_best, D_aniso)
    for y1, y2, y3, mu, lam in configs:
        Y_nu_t = build_Y(np.array([y1, y2, y3]), mu, lam, np.zeros((3,3)), D_dem)
        r_t = extract_pmns(Y_ell_best, Y_nu_t)
        if r_t:
            print(f"  y=({y1},{y2},{y3}) mu={mu} lam={lam}: "
                  f"t12={r_t['theta12']:.1f} t23={r_t['theta23']:.1f} "
                  f"t13={r_t['theta13']:.1f} c2={chi2(r_t):.1f}")

# ============================================================
# EVOLUTION
# ============================================================
H("EVOLUTION v8 -> v15")
print(f"  {'Ver':<5} {'t12':>7} {'t23':>7} {'t13':>7} {'r':>9} {'J':>8} {'c2':>10} {'Key':>30}")
print("  " + "-" * 85)
rows = [("v8","54.3","51.1","8.6","0.506","0","281000","rank-2 theorem"),
        ("v10","32.9","58.7","8.5","0.030","0","77","graph dynamics"),
        ("v13","35.2","45.0","0.0","1.0","0","5000+","democratic TBM"),
        ("v14","41.4","54.6","6.1","0.061","0","1721","asymmetric metric")]
for row in rows:
    print(f"  {row[0]:<5} {row[1]:>7} {row[2]:>7} {row[3]:>7} {row[4]:>9} {row[5]:>8} {row[6]:>10} {row[7]:>30}")
if best:
    print(f"  {'v15':<5} {best['theta12']:7.1f} {best['theta23']:7.1f} "
          f"{best['theta13']:7.1f} {best['ratio']:9.5f} {best['J_CP']:8.5f} "
          f"{best['chi2']:10.1f} {'TBM + U_ell corr':>30}")
print(f"  {'Exp':<5} {'33.4':>7} {'49.2':>7} {'8.6':>7} {'0.031':>9} {'0.033':>8}")
