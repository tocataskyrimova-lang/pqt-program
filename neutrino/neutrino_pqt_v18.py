# -*- coding: utf-8 -*-
"""
PQT Neutrino v18 — Joint (κ, ξ) Scan + 1-loop RG

Diagnosis: κ=8.78 makes perturbations negligible.
Solution: scan κ jointly with ξ so perturbations have O(1) effect.
Accept worse GUT-scale angles; rely on RG to partially restore them.
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
from scipy.linalg import eigh
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CORE SETUP
# ============================================================
Q_SIGMA = np.array([1.0, 0.0, 1.0, 0.0])

def n_delta(idx):
    return 1 if idx == 3 else 0

def get_generation(g2, g3):
    d2, d3 = n_delta(g2), n_delta(g3)
    if d2 == 1 and d3 == 0: return 0
    elif d2 == 0 and d3 == 0: return 1
    else: return 2

gen = np.zeros((4, 4), dtype=int)
for g2 in range(4):
    for g3 in range(4):
        gen[g2, g3] = get_generation(g2, g3)

w_basis = np.zeros((4, 4))
w_basis[0] = [1, 1, 1, 1];       w_basis[0] /= 2.0
w_basis[1] = [1, -1, 0, 0];      w_basis[1] /= np.sqrt(2)
w_basis[2] = [1, 1, -2, 0];      w_basis[2] /= np.sqrt(6)
w_basis[3] = [1, 1, 1, -3];      w_basis[3] /= np.sqrt(12)

def position_charge(g2, g3, eta):
    return (1 + eta) * Q_SIGMA[g2] + (1 - eta) * Q_SIGMA[g3]

def project_mode_eta(V, eta):
    proj = np.zeros(3)
    V_2d = V.reshape(4, 4)
    for g2 in range(4):
        for g3 in range(4):
            a = gen[g2, g3]
            q = position_charge(g2, g3, eta)
            proj[a] += q * V_2d[g2, g3]
    return proj

# ============================================================
# PERTURBATION FUNCTIONS
# ============================================================
def h_position_asymmetry(g2, g3):
    return n_delta(g2) - n_delta(g3)

def h_v33_mode(g2, g3):
    return w_basis[3][g2] * w_basis[3][g3]

def h_gen1_boost(g2, g3):
    return n_delta(g2) * (1 - n_delta(g3))

# ============================================================
# BUILD K_T
# ============================================================
def build_K_T(kappa, gamma_w, eta, beta, xi, h_func):
    eig_pos2 = [0, 4, 4, 4]
    eig_pos3 = [0, 4*(1+gamma_w), 4*(1+gamma_w), 4*(1+gamma_w)]

    modes = []
    for k in range(4):
        for l in range(4):
            V = np.outer(w_basis[k], w_basis[l]).flatten()
            lam = eig_pos2[k] + eig_pos3[l]
            modes.append((lam, V, k, l))

    K = np.zeros((3, 3))
    for (lam, V, k, l) in modes:
        if lam < 1e-8: continue
        c_kl = 0.0
        for g2 in range(4):
            for g3 in range(4):
                s = n_delta(g2) + n_delta(g3)
                a0_val = (4 - s)**kappa + xi * h_func(g2, g3)
                c_kl += a0_val * w_basis[k][g2] * w_basis[l][g3]
        proj = project_mode_eta(V, eta)
        weight = lam**(2*beta - 1) * c_kl**2
        K += weight * np.outer(proj, proj)
    return K

# ============================================================
# RG CORRECTION
# ============================================================
def RG_correct(r, Lambda_G=1e16, M_Z=91.2, y_tau=1.0):
    m = r['masses']
    m1, m2, m3 = m[0], m[1], m[2]
    log_factor = np.log(Lambda_G / M_Z)
    coeff = y_tau**2 / (16 * np.pi**2)

    if m3**2 - m2**2 > 1e-10:
        mf23 = m2 * m3 / (m3**2 - m2**2)
        dt23 = coeff * mf23 * np.sin(2 * np.radians(r['theta23'])) * log_factor
    else:
        dt23 = 0

    if m3**2 - m1**2 > 1e-10:
        mf12 = m1 * m2 / (m3**2 - m1**2) * 0.3
        dt12 = coeff * mf12 * np.sin(2 * np.radians(r['theta12'])) * log_factor
    else:
        dt12 = 0

    dt13 = coeff * 0.05 * log_factor
    rf = 1.0 + coeff * log_factor * 0.5

    return {
        'theta12': r['theta12'] - np.degrees(dt12),
        'theta23': r['theta23'] - np.degrees(dt23),
        'theta13': r['theta13'] + np.degrees(dt13),
        'ratio': r['ratio'] * rf,
        'masses': r['masses'],
        'hierarchy': r['hierarchy'],
        'delta_RG_t23': np.degrees(dt23),
    }

# ============================================================
# PMNS EXTRACTION
# ============================================================
EXP = {
    'theta12': (33.44, 0.7),
    'theta23': (49.2, 1.1),
    'theta13': (8.57, 0.12),
    'dm2_ratio': (0.0307, 0.0009),
}

def extract_pmns(K):
    eigenvalues, U = eigh(K)
    idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[idx].real
    U = U[:, idx].real
    if eigenvalues[0] < -1e-6: return None
    m = np.sqrt(np.maximum(eigenvalues, 0))
    m = np.sort(m)

    s13 = abs(U[0, 2])
    theta13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    s23 = abs(U[1, 2]) / den
    theta23 = np.degrees(np.arcsin(np.clip(s23, 0, 1)))
    s12 = abs(U[0, 1]) / den
    theta12 = np.degrees(np.arcsin(np.clip(s12, 0, 1)))

    dm21 = m[1]**2 - m[0]**2
    dm31 = m[2]**2 - m[0]**2
    ratio = dm21 / dm31 if dm31 > 0 else 0

    return {
        'theta12': theta12, 'theta23': theta23, 'theta13': theta13,
        'ratio': ratio, 'masses': m,
        'hierarchy': 'NH' if m[0] < m[1] < m[2] else 'IH',
        'eigenvalues': eigenvalues, 'U': U,
    }

def chi2(r):
    if r is None: return 1e10
    c = 0
    for obs in ['theta12', 'theta23', 'theta13']:
        c += ((r[obs] - EXP[obs][0]) / EXP[obs][1])**2
    if r['ratio'] > 0:
        c += ((r['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1])**2
    else:
        c += 1e4
    if r['hierarchy'] != 'NH': c += 1e3
    return c

H = lambda s: print(f"\n{s:=^95}")

# ============================================================
# PHASE 0: DIAGNOSTIC
# ============================================================
print("=" * 95)
print("PQT NEUTRINO v18 — JOINT (kappa, xi) SCAN + RG")
print("=" * 95)

H("DIAGNOSTIC: perturbation magnitude vs kappa")
print(f"  {'kappa':>6} {'|c_base|':>12} {'|c_pert|':>12} {'ratio':>12} {'visible?':>10}")
print("-" * 58)

for kp10 in [5, 10, 20, 30, 50, 88, 100, 200]:
    kappa = kp10 / 10.0
    c_base = 0; c_pert = 0
    for g2 in range(4):
        for g3 in range(4):
            s = n_delta(g2) + n_delta(g3)
            c_base += (4-s)**kappa * w_basis[0][g2] * w_basis[3][g3]
            c_pert += h_position_asymmetry(g2, g3) * w_basis[0][g2] * w_basis[3][g3]
    ratio = abs(c_pert / c_base) if abs(c_base) > 1e-20 else float('inf')
    vis = "YES" if ratio > 0.01 else "no"
    print(f"  {kappa:6.1f} {abs(c_base):12.1f} {abs(c_pert):12.4f} {ratio:12.6f} {vis:>10}")

# ============================================================
# PHASE 1: theta23 vs kappa (no perturbation, no RG)
# ============================================================
H("PHASE 1: theta23 vs kappa (baseline, no perturbation)")
print(f"  {'kappa':>6} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'c2':>10}")
print("-" * 55)

for kp10 in range(5, 201, 20):
    kappa = kp10 / 10.0
    K = build_K_T(kappa, 0.251, 0.351, 2.96, 0.0, h_position_asymmetry)
    r = extract_pmns(K)
    if r is None: continue
    print(f"  {kappa:6.1f} {r['theta12']:7.1f} {r['theta23']:7.1f} "
          f"{r['theta13']:7.1f} {r['ratio']:9.5f} {chi2(r):10.1f}")

# ============================================================
# PHASE 2: JOINT (kappa, xi, eta) SCAN + RG
# ============================================================
H("PHASE 2: JOINT (kappa, xi, eta) SCAN + RG")

h_func = h_position_asymmetry
best = None
results = []

for kp10 in range(5, 201, 5):      # kappa: 0.5 to 20.0
    kappa = kp10 / 10.0
    for xi10 in range(-100, 101, 5):  # xi: -10 to 10
        xi = xi10 / 10.0
        for eta10 in range(20, 51, 5):  # eta: 0.20 to 0.50
            eta = eta10 / 100.0

            K = build_K_T(kappa, 0.251, eta, 2.96, xi, h_func)
            r = extract_pmns(K)
            if r is None: continue

            r_rg = RG_correct(r)
            c = chi2(r_rg)

            entry = {**r_rg, 'chi2': c, 'kappa': kappa, 'xi': xi, 'eta': eta,
                     't12_GUT': r['theta12'], 't23_GUT': r['theta23'],
                     't13_GUT': r['theta13']}

            if best is None or c < best['chi2']:
                best = entry
            if c < 500:
                results.append(entry)

results.sort(key=lambda x: x['chi2'])

print(f"\n  TOP 20:")
print(f"  {'#':>3} {'kp':>5} {'xi':>6} {'eta':>5} {'t23G':>6} {'dRG':>5} "
      f"{'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'c2':>10}")
print("  " + "-" * 80)
for i, r in enumerate(results[:20]):
    print(f"  {i+1:3d} {r['kappa']:5.1f} {r['xi']:6.1f} {r['eta']:5.2f} "
          f"{r['t23_GUT']:6.1f} {r['delta_RG_t23']:5.1f} "
          f"{r['theta12']:7.1f} {r['theta23']:7.1f} {r['theta13']:7.1f} "
          f"{r['ratio']:9.5f} {r['chi2']:10.1f}")

# ============================================================
# BEST RESULT
# ============================================================
if best:
    b = best
    H("BEST RESULT (v18)")
    print(f"  kappa={b['kappa']:.1f}, xi={b['xi']:.1f}, eta={b['eta']:.2f}")
    print(f"  gamma=0.251, beta=2.96 (fixed)")
    print()

    pulls = {}
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(b[obs] - EXP[obs][0]) / EXP[obs][1]
        pulls[obs] = pull
        s = "OK" if pull < 3 else "WARN" if pull < 5 else "FAIL"
        print(f"  {obs:8s}(MZ) = {b[obs]:7.2f}  (exp: {EXP[obs][0]:.2f})  pull={pull:5.1f}s {s}")

    pr = abs(b['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    pulls['ratio'] = pr
    print(f"  {'ratio':8s}(MZ) = {b['ratio']:7.5f}  pull={pr:5.1f}s")
    print(f"  chi2 = {b['chi2']:.1f}")

    print(f"\n  GUT -> M_Z:")
    print(f"    t12: {b['t12_GUT']:.1f} -> {b['theta12']:.1f}")
    print(f"    t23: {b['t23_GUT']:.1f} -> {b['theta23']:.1f} (dRG={b['delta_RG_t23']:.1f})")
    print(f"    t13: {b['t13_GUT']:.1f} -> {b['theta13']:.1f}")

    all3 = all(p < 3 for p in pulls.values())
    all5 = all(p < 5 for p in pulls.values())
    print(f"\n  ALL < 3s? {'YES!' if all3 else 'NO'}")
    print(f"  ALL < 5s? {'YES' if all5 else 'NO'}")

# ============================================================
# PHASE 3: SCAN RG PARAMETERS
# ============================================================
if best and best['chi2'] < 100:
    H("PHASE 3: SCAN RG PARAMETERS")

    K_best = build_K_T(best['kappa'], 0.251, best['eta'], 2.96,
                         best['xi'], h_func)
    r_best = extract_pmns(K_best)

    best_rg = None
    for yt10 in range(5, 20):
        ytau = yt10 / 10.0
        for logLG10 in range(130, 171, 5):
            LG = 10**(logLG10 / 10.0)
            r_rg = RG_correct(r_best, Lambda_G=LG, y_tau=ytau)
            c = chi2(r_rg)
            if best_rg is None or c < best_rg['chi2']:
                best_rg = {**r_rg, 'chi2': c, 'ytau': ytau, 'LG': LG}

    if best_rg:
        print(f"  Best RG: y_tau={best_rg['ytau']:.1f}, Lambda_G={best_rg['LG']:.1e}")
        for obs in ['theta12', 'theta23', 'theta13']:
            pull = abs(best_rg[obs] - EXP[obs][0]) / EXP[obs][1]
            s = "OK" if pull < 3 else "WARN" if pull < 5 else "FAIL"
            print(f"    {obs} = {best_rg[obs]:.2f} pull={pull:.1f}s {s}")
        print(f"    chi2 = {best_rg['chi2']:.1f}")
        if best_rg['chi2'] < best['chi2']:
            best = best_rg

# ============================================================
# EVOLUTION
# ============================================================
H("COMPLETE EVOLUTION")
print(f"  {'Ver':<5} {'t12':>7} {'t23':>7} {'t13':>7} {'r':>9} {'c2':>10} {'Key':>25}")
print("  " + "-" * 70)
for row in [("v1","33.4","49.1","8.5","0.031","0","Overfit"),
            ("v10","32.9","58.7","8.5","0.030","77","graph dynamics"),
            ("v16","32.5","55.7","8.6","0.035","56","+ RG"),
            ("v17","32.5","55.7","8.6","0.035","56","+ A0 (no effect)")]:
    print(f"  {row[0]:<5} {row[1]:>7} {row[2]:>7} {row[3]:>7} {row[4]:>9} {row[5]:>10} {row[6]:>25}")
if best:
    print(f"  {'v18':<5} {best['theta12']:7.1f} {best['theta23']:7.1f} "
          f"{best['theta13']:7.1f} {best['ratio']:9.5f} {best['chi2']:10.1f} "
          f"{'joint kp,xi+RG':>25}")
print(f"  {'Exp':<5} {'33.4':>7} {'49.2':>7} {'8.6':>7} {'0.031':>9}")
