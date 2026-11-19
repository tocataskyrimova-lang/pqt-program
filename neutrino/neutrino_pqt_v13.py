"""
PQT Neutrino v13 — Topological Mutation (C4 □ K4)

Based on the hypothesis that K4 □ K4 is too rigid.
Replacing the G2 dimension with C4 (Cycle graph).

K4 spectrum: [0, 4, 4, 4]
C4 spectrum: [0, 2, 2, 4] (Laplacian)
"""

import numpy as np
from scipy.linalg import eigh

# ============================================================
# BASIS VECTORS
# ============================================================

# K4 Basis (Simplex)
w_K4 = np.zeros((4, 4))
w_K4[0] = [1, 1, 1, 1]; w_K4[0] /= 2.0
w_K4[1] = [1, -1, 0, 0]; w_K4[1] /= np.sqrt(2)
w_K4[2] = [1, 1, -2, 0]; w_K4[2] /= np.sqrt(6)
w_K4[3] = [1, 1, 1, -3]; w_K4[3] /= np.sqrt(12)

# C4 Basis (Cycle/Square)
w_C4 = np.zeros((4, 4))
w_C4[0] = [1, 1, 1, 1];   w_C4[0] /= 2.0  # DC mode (lambda=0)
w_C4[1] = [1, 0, -1, 0];  w_C4[1] /= np.sqrt(2) # cos mode (lambda=2)
w_C4[2] = [0, 1, 0, -1];  w_C4[2] /= np.sqrt(2) # sin mode (lambda=2)
w_C4[3] = [1, -1, 1, -1]; w_C4[3] /= 2.0 # checkerboard (lambda=4)

# ============================================================
# PHYSICS GLOBALS
# ============================================================
def n_delta(idx): return 1 if idx == 3 else 0
Q_SIGMA = np.array([1.0, 0.0, 1.0, 0.0])

def position_charge(g2, g3, eta):
    return (1 + eta) * Q_SIGMA[g2] + (1 - eta) * Q_SIGMA[g3]

def get_generation(g2, g3):
    d2, d3 = n_delta(g2), n_delta(g3)
    if d2 == 1 and d3 == 0: return 0  # Gen1
    elif d2 == 0 and d3 == 0: return 1 # Gen2
    else: return 2                   # Gen3

gen = np.zeros((4, 4), dtype=int)
for g2 in range(4):
    for g3 in range(4):
        gen[g2, g3] = get_generation(g2, g3)

# ============================================================
# BUILD K_T v13 (C4 □ K4)
# ============================================================
def build_K_T_v13(kappa, gamma_w, eta, beta):
    # C4 Laplacian eigenvalues (dim 2)
    eig_pos2 = [0, 2, 2, 4]
    # K4 weighted Laplacian eigenvalues (dim 3)
    eig_pos3 = [0, 4*(1+gamma_w), 4*(1+gamma_w), 4*(1+gamma_w)]
    
    K = np.zeros((3, 3))
    for k in range(4): # C4 dimension
        for l in range(4): # K4 dimension
            lam = eig_pos2[k] + eig_pos3[l]
            if lam < 1e-8: continue
            
            # Basis product
            V_2d = np.outer(w_C4[k], w_K4[l])
            
            # Project to generation space
            proj = np.zeros(3)
            for g2 in range(4):
                for g3 in range(4):
                    a = gen[g2, g3]
                    q = position_charge(g2, g3, eta)
                    proj[a] += q * V_2d[g2, g3]
            
            # Interaction strength c_kl
            c_kl = 0.0
            for g2 in range(4):
                for g3 in range(4):
                    s = n_delta(g2) + n_delta(g3)
                    # Note: w_C4 and w_K4 both used here
                    c_kl += (4 - s)**kappa * w_C4[k][g2] * w_K4[l][g3]
            
            weight = lam**(2*beta-1) * c_kl**2
            K += weight * np.outer(proj, proj)
    return K

# ============================================================
# PMNS & ANALYTICS
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
    m = np.sqrt(np.maximum(eigenvalues[idx], 0))
    U = U[:, idx]
    U_abs = np.abs(U)
    
    s13 = U_abs[0, 2]
    theta13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    theta23 = np.degrees(np.arcsin(np.clip(U_abs[1, 2] / den, 0, 1)))
    theta12 = np.degrees(np.arcsin(np.clip(U_abs[0, 1] / den, 0, 1)))
    
    dm21 = m[1]**2 - m[0]**2
    dm31 = m[2]**2 - m[0]**2
    ratio = dm21 / dm31 if dm31 > 0 else 0
    
    return {'theta12': theta12, 'theta23': theta23, 'theta13': theta13, 'ratio': ratio, 'masses': m}

def chi2(r):
    if r is None: return 1e10
    c = 0
    for obs in ['theta12', 'theta23', 'theta13']:
        c += ((r[obs] - EXP[obs][0]) / EXP[obs][1])**2
    c += ((r['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1])**2
    return c

# ============================================================
# SCAN
# ============================================================
print("=" * 90)
print("PQT NEUTRINO v13 — TOPOLOGICAL MUTATION (C4 □ K4)")
print("=" * 90)

best = None
results = []

# Coarse Scan
for kappa in [6.0, 7.0, 8.0, 9.0, 10.0]:
    for eta in np.linspace(0.1, 0.5, 9):
        for gamma in [0.2, 0.25, 0.3]:
            for beta in [2.5, 3.0, 3.5]:
                K = build_K_T_v13(kappa, gamma, eta, beta)
                r = extract_pmns(K)
                c = chi2(r)
                entry = {**r, 'chi2': c, 'kappa': kappa, 'eta': eta, 'gamma': gamma, 'beta': beta}
                if best is None or c < best['chi2']:
                    best = entry
                results.append(entry)

results.sort(key=lambda x: x['chi2'])

print(f"\n{'TOP 15 RESULTS (C4 □ K4)':=^90}")
print(f"{'#':>3} {'κ':>5} {'η':>5} {'γ':>5} {'β':>5} {'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} {'ratio':>9} {'χ²':>10}")
print("-" * 90)

for i, r in enumerate(results[:15]):
    print(f"{i+1:3d} {r['kappa']:5.1f} {r['eta']:5.2f} {r['gamma']:5.2f} {r['beta']:5.2f} "
          f"{r['theta12']:7.1f} {r['theta23']:7.1f} {r['theta13']:7.1f} "
          f"{r['ratio']:9.5f} {r['chi2']:10.1f}")

if best:
    print(f"\n{'BEST RESULT (v13)':=^90}")
    print(f"  κ={best['kappa']:.2f}, η={best['eta']:.2f}, γ={best['gamma']:.2f}, β={best['beta']:.2f}")
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(best[obs] - EXP[obs][0]) / EXP[obs][1]
        print(f"  {obs:10s} = {best[obs]:8.2f}° (exp: {EXP[obs][0]:8.2f}°) pull={pull:4.1f}σ")
    pull_r = abs(best['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    print(f"  {'ratio':10s} = {best['ratio']:8.5f} (exp: {EXP['dm2_ratio'][0]:8.4f}) pull={pull_r:4.1f}σ")
    print(f"  χ² = {best['chi2']:.1f}")
    print(f"  Σm_ν = {np.sum(best['masses'])*1000:.1f} meV (at current scale)")

# Comparison
print(f"\n{'EVOLUTION: v10 (K4□K4) vs v13 (C4□K4)':=^90}")
print(f"{'Ver':<6} {'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} {'ratio':>9} {'χ²':>10}")
print("-" * 60)
print(f"{'v10':<6} {'32.9':>7} {'58.7':>7} {'8.5':>7} {'0.030':>9} {'77':>10}")
if best:
    print(f"{'v13':<6} {best['theta12']:7.1f} {best['theta23']:7.1f} {best['theta13']:7.1f} {best['ratio']:9.5f} {best['chi2']:10.1f}")
