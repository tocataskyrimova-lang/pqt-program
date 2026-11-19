# -*- coding: utf-8 -*-
"""
PQT Neutrino v17 — Graph Dynamics v10 + Position-Dependent A₀ + 1-loop RG

A₀(g₂,g₃) = (4 - n_δ)^κ + ξ · h(g₂,g₃)

h options:
  h₁ = n_δ(g₂) - n_δ(g₃)           (position asymmetry)
  h₂ = w₃(g₂)·w₃(g₃)               (V₃₃ mode excitation)
  h₃ = n_δ(g₂)·(1-n_δ(g₃))         (Gen1-only boost)
  h₄ = w₁(g₂)·w₁(g₃)               (V₁₁ mode)
  h₅ = w₁(g₂)·w₃(g₃)               (V₁₃ mode)

RG: 1-loop SM correction from Λ_G to M_Z
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
from scipy.linalg import eigh
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# GLYPH / BASIS / CHARGE / GENERATION
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

# ============================================================
# PERTURBATION FUNCTIONS
# ============================================================
def h_position_asymmetry(g2, g3):
    return n_delta(g2) - n_delta(g3)

def h_v33_mode(g2, g3):
    return w_basis[3][g2] * w_basis[3][g3]

def h_gen1_boost(g2, g3):
    return n_delta(g2) * (1 - n_delta(g3))

def h_antisym_w1(g2, g3):
    return w_basis[1][g2] * w_basis[1][g3]

def h_mixed_13(g2, g3):
    return w_basis[1][g2] * w_basis[3][g3]

PERTURBATIONS = {
    'h1_pos_asym': h_position_asymmetry,
    'h2_v33': h_v33_mode,
    'h3_gen1': h_gen1_boost,
    'h4_w1w1': h_antisym_w1,
    'h5_w1w3': h_mixed_13,
}

# ============================================================
# POSITION-AWARE CHARGE PROJECTION
# ============================================================
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
# BUILD K_T^eff WITH MODIFIED A₀
# ============================================================
def build_K_T_v17(kappa, gamma_w, eta, beta, xi, h_func):
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
# 1-LOOP RG CORRECTION
# ============================================================
def RG_correct(theta12_GUT, theta23_GUT, theta13_GUT, masses_eV,
               Lambda_G=1e16, M_Z=91.2, y_tau_G=1.0):
    m1, m2, m3 = masses_eV
    log_factor = np.log(Lambda_G / M_Z)
    coeff = y_tau_G**2 / (16 * np.pi**2)

    if m3**2 - m2**2 > 1e-20:
        mass_factor_23 = m2 * m3 / (m3**2 - m2**2)
        sin2_23 = np.sin(2 * np.radians(theta23_GUT))
        dtheta23 = coeff * mass_factor_23 * sin2_23 * log_factor
    else:
        dtheta23 = 0

    if m3**2 - m1**2 > 1e-20:
        mass_factor_12 = m1 * m2 / (m3**2 - m1**2) * 0.3
        sin2_12 = np.sin(2 * np.radians(theta12_GUT))
        dtheta12 = coeff * mass_factor_12 * sin2_12 * log_factor
    else:
        dtheta12 = 0

    dtheta13 = coeff * 0.05 * log_factor
    dratio_factor = 1.0 + coeff * log_factor * 0.5

    return (theta12_GUT - np.degrees(dtheta12),
            theta23_GUT - np.degrees(dtheta23),
            theta13_GUT + np.degrees(dtheta13),
            dratio_factor)

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
# V10 BASELINE
# ============================================================
print("=" * 95)
print("PQT NEUTRINO v17 — POSITION-DEPENDENT A0 + 1-LOOP RG")
print("=" * 95)

v10p = {'kappa': 8.78, 'eta': 0.351, 'gamma': 0.251, 'beta': 2.96}

H("PHASE 0: v10 BASELINE")
K_v10 = build_K_T_v17(kappa=v10p['kappa'], gamma_w=v10p['gamma'],
                        eta=v10p['eta'], beta=v10p['beta'],
                        xi=0.0, h_func=h_position_asymmetry)
r_v10 = extract_pmns(K_v10)
c_v10 = chi2(r_v10)

for obs in ['theta12', 'theta23', 'theta13']:
    pull = abs(r_v10[obs] - EXP[obs][0]) / EXP[obs][1]
    print(f"  {obs:8s} = {r_v10[obs]:7.2f}  pull={pull:.1f}s")
print(f"  ratio    = {r_v10['ratio']:.5f}")
print(f"  chi2     = {c_v10:.1f}")

# Physical masses
Lambda_T = 0.050 / r_v10['masses'][2]
m_phys_eV = r_v10['masses'] * Lambda_T

# v10 + RG
t12_rg, t23_rg, t13_rg, rf = RG_correct(
    r_v10['theta12'], r_v10['theta23'], r_v10['theta13'], m_phys_eV)
print(f"\n  v10 + RG: t12={t12_rg:.1f}, t23={t23_rg:.1f}, t13={t13_rg:.1f}")
print(f"  Delta_t23_RG = {r_v10['theta23'] - t23_rg:.1f}")

# ============================================================
# PHASE 1: PERTURBATION SCAN (no RG)
# ============================================================
H("PHASE 1: PERTURBATION SCAN (GUT scale)")

best_gut = {}
for h_name, h_func in PERTURBATIONS.items():
    print(f"\n  --- {h_name} ---")
    best_h = None
    for xi_100 in range(-200, 201, 10):
        xi = xi_100 / 100.0
        K = build_K_T_v17(kappa=v10p['kappa'], gamma_w=v10p['gamma'],
                           eta=v10p['eta'], beta=v10p['beta'],
                           xi=xi, h_func=h_func)
        r = extract_pmns(K)
        if r is None: continue
        c = chi2(r)
        if best_h is None or c < best_h['chi2']:
            best_h = {**r, 'chi2': c, 'xi': xi}
        if xi_100 % 50 == 0 or abs(r['theta23'] - 49.2) < 3:
            print(f"    xi={xi:+.2f} t12={r['theta12']:.1f} t23={r['theta23']:.1f} "
                  f"t13={r['theta13']:.1f} c2={c:.1f}")
    if best_h:
        best_gut[h_name] = best_h
        print(f"  Best: xi={best_h['xi']:.2f} t23={best_h['theta23']:.1f} c2={best_h['chi2']:.1f}")

# ============================================================
# PHASE 2: ALL PERTURBATIONS + RG
# ============================================================
H("PHASE 2: PERTURBATION + RG (M_Z scale)")

all_results = []
for h_name, h_func in PERTURBATIONS.items():
    for xi_100 in range(-200, 201, 10):
        xi = xi_100 / 100.0
        K = build_K_T_v17(kappa=v10p['kappa'], gamma_w=v10p['gamma'],
                           eta=v10p['eta'], beta=v10p['beta'],
                           xi=xi, h_func=h_func)
        r = extract_pmns(K)
        if r is None: continue

        m_eV = r['masses'] * Lambda_T
        t12_mz, t23_mz, t13_mz, rf = RG_correct(
            r['theta12'], r['theta23'], r['theta13'], m_eV)

        r_rg = {'theta12': t12_mz, 'theta23': t23_mz, 'theta13': t13_mz,
                'ratio': r['ratio'] * rf, 'masses': r['masses'],
                'hierarchy': r['hierarchy']}
        c = chi2(r_rg)

        all_results.append({
            **r_rg, 'chi2': c, 'xi': xi, 'h_name': h_name,
            't23_GUT': r['theta23'], 'dRG': r['theta23'] - t23_mz,
        })

all_results.sort(key=lambda x: x['chi2'])

print(f"\n  TOP 15 (GUT + perturbation + RG):")
print(f"  {'#':>3} {'h':>12} {'xi':>6} {'t23G':>6} {'dRG':>5} "
      f"{'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'c2':>10}")
print("  " + "-" * 80)
for i, r in enumerate(all_results[:15]):
    print(f"  {i+1:3d} {r['h_name']:>12} {r['xi']:6.2f} {r['t23_GUT']:6.1f} "
          f"{r['dRG']:5.1f} "
          f"{r['theta12']:7.1f} {r['theta23']:7.1f} {r['theta13']:7.1f} "
          f"{r['ratio']:9.5f} {r['chi2']:10.1f}")

# ============================================================
# BEST RESULT
# ============================================================
if all_results:
    b = all_results[0]
    H("BEST RESULT (v17)")
    print(f"  Perturbation: {b['h_name']}, xi={b['xi']:.3f}")
    print(f"  RG: Lambda_G=1e16 GeV, y_tau=1.0")
    print()

    pulls = {}
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(b[obs] - EXP[obs][0]) / EXP[obs][1]
        pulls[obs] = pull
        s = "OK" if pull < 3 else "WARN" if pull < 5 else "FAIL"
        print(f"  {obs:8s}(MZ) = {b[obs]:7.2f}  (exp: {EXP[obs][0]:.2f})  pull={pull:5.1f}s {s}")

    pr = abs(b['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    pulls['ratio'] = pr
    print(f"  {'ratio':8s}(MZ) = {b['ratio']:7.5f}  (exp: {EXP['dm2_ratio'][0]})  pull={pr:5.1f}s")
    print(f"  chi2 = {b['chi2']:.1f}")
    print(f"  Hierarchy: {b['hierarchy']}")
    print(f"\n  GUT -> M_Z: t23 {b['t23_GUT']:.1f} -> {b['theta23']:.1f} (dRG={b['dRG']:.1f})")

    all3 = all(p < 3 for p in pulls.values())
    all5 = all(p < 5 for p in pulls.values())
    print(f"\n  ALL < 3s? {'YES -- BREAKTHROUGH!' if all3 else 'NO'}")
    print(f"  ALL < 5s? {'YES' if all5 else 'NO'}")

# ============================================================
# PHASE 3: FINE REFINEMENT
# ============================================================
if all_results and all_results[0]['chi2'] < 100:
    H("PHASE 3: FINE REFINEMENT")
    b0 = all_results[0]
    h_func = PERTURBATIONS[b0['h_name']]
    best_fine = None

    for xi_1000 in range(int((b0['xi']-0.3)*1000), int((b0['xi']+0.3)*1000)+1):
        xi = xi_1000 / 1000.0
        for k100 in range(int((v10p['kappa']-1.0)*100), int((v10p['kappa']+1.0)*100)+1):
            kappa = k100 / 100.0
            for e1000 in range(int((v10p['eta']-0.05)*1000), int((v10p['eta']+0.05)*1000)+1):
                eta = e1000 / 1000.0

                K = build_K_T_v17(kappa=kappa, gamma_w=v10p['gamma'],
                                   eta=eta, beta=v10p['beta'],
                                   xi=xi, h_func=h_func)
                r = extract_pmns(K)
                if r is None: continue

                m_eV = r['masses'] * Lambda_T
                t12_mz, t23_mz, t13_mz, rf = RG_correct(
                    r['theta12'], r['theta23'], r['theta13'], m_eV)

                r_rg = {'theta12': t12_mz, 'theta23': t23_mz, 'theta13': t13_mz,
                        'ratio': r['ratio'] * rf, 'masses': r['masses'],
                        'hierarchy': r['hierarchy']}
                c = chi2(r_rg)

                entry = {**r_rg, 'chi2': c, 'xi': xi, 'kappa': kappa,
                         'eta': eta, 'h_name': b0['h_name'],
                         't23_GUT': r['theta23'], 'dRG': r['theta23'] - t23_mz}
                if best_fine is None or c < best_fine['chi2']:
                    best_fine = entry

    if best_fine:
        b = best_fine
        print(f"  Fine: xi={b['xi']:.4f}, kappa={b['kappa']:.2f}, eta={b['eta']:.3f}")
        for obs in ['theta12', 'theta23', 'theta13']:
            pull = abs(b[obs] - EXP[obs][0]) / EXP[obs][1]
            s = "OK" if pull < 3 else "WARN" if pull < 5 else "FAIL"
            print(f"    {obs}(MZ) = {b[obs]:.2f} pull={pull:.1f}s {s}")
        print(f"    ratio = {b['ratio']:.5f} chi2 = {b['chi2']:.1f}")
        print(f"    GUT -> M_Z: t23 {b['t23_GUT']:.1f} -> {b['theta23']:.1f}")
        all_results.insert(0, b)

# ============================================================
# EVOLUTION
# ============================================================
H("EVOLUTION v1 -> v17")
print(f"  {'Ver':<5} {'t12':>7} {'t23':>7} {'t13':>7} {'r':>9} {'c2':>10} {'Key':>30}")
print("  " + "-" * 75)
for row in [("v1","33.4","49.1","8.5","0.031","0","Overfit"),
            ("v8","54.3","51.1","8.6","0.506","281000","rank-2"),
            ("v10","32.9","58.7","8.5","0.030","77","graph dynamics"),
            ("v16","32.5","55.7","8.6","0.035","~56","+ RG")]:
    print(f"  {row[0]:<5} {row[1]:>7} {row[2]:>7} {row[3]:>7} {row[4]:>9} {row[5]:>10} {row[6]:>30}")

if all_results:
    b = all_results[0]
    print(f"  {'v17':<5} {b['theta12']:7.1f} {b['theta23']:7.1f} "
          f"{b['theta13']:7.1f} {b['ratio']:9.5f} {b['chi2']:10.1f} "
          f"{'+ A0 corr + RG':>30}")
print(f"  {'Exp':<5} {'33.4':>7} {'49.2':>7} {'8.6':>7} {'0.031':>9}")
