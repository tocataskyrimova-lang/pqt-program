"""
PQT Neutrino v20 — C₄□K₄ Topology

Replaces one K₄ factor with C₄ (cyclic graph on 4 vertices).
C₄ Laplacian eigenvalues: {0, 2, 2, 4} vs K₄: {0, 4, 4, 4}

Options:
  Topology A: C₄□K₄ (C₄ at pos-2, K₄ at pos-3)
  Topology B: K₄□C₄ (K₄ at pos-2, C₄ at pos-3)

PQT motivation: C₄ represents cyclic (5'→3') codon reading,
K₄ represents maximal mixing (all-to-all).
"""

import numpy as np
from scipy.linalg import eigh
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# GLYPH STRUCTURE
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

# ============================================================
# GRAPH EIGENVECTORS
# ============================================================
# K₄ (complete graph): eigenvalues {0, 4, 4, 4}
K4_eigenvalues = [0, 4, 4, 4]
K4_basis = np.zeros((4, 4))
K4_basis[0] = [1, 1, 1, 1];       K4_basis[0] /= 2.0
K4_basis[1] = [1, -1, 0, 0];      K4_basis[1] /= np.sqrt(2)
K4_basis[2] = [1, 1, -2, 0];      K4_basis[2] /= np.sqrt(6)
K4_basis[3] = [1, 1, 1, -3];      K4_basis[3] /= np.sqrt(12)

# C₄ (cycle graph 0-1-2-3-0): Laplacian eigenvalues {0, 2, 2, 4}
C4_eigenvalues = [0, 2, 2, 4]
C4_basis = np.zeros((4, 4))
C4_basis[0] = [1, 1, 1, 1];       C4_basis[0] /= 2.0
C4_basis[1] = [1, 0, -1, 0];      C4_basis[1] /= np.sqrt(2)
C4_basis[2] = [0, 1, 0, -1];      C4_basis[2] /= np.sqrt(2)
C4_basis[3] = [1, -1, 1, -1];     C4_basis[3] /= 2.0

# ============================================================
# POSITION-AWARE CHARGE
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
# BUILD K_T FOR ARBITRARY TOPOLOGY
# ============================================================
def build_K_T(kappa, gamma_w, eta, beta,
              basis_2, eig_2, basis_3, eig_3):
    """
    Build K_T^eff for product graph G₂□G₃.

    basis_2, eig_2: eigenvectors and eigenvalues of pos-2 graph
    basis_3, eig_3: eigenvectors and eigenvalues of pos-3 graph

    Pos-3 eigenvalues get weight (1+γ).
    """
    # Weighted eigenvalues for pos-3
    eig_3_w = [e * (1 + gamma_w) for e in eig_3]

    modes = []
    for k in range(4):
        for l in range(4):
            V = np.outer(basis_2[k], basis_3[l]).flatten()
            lam = eig_2[k] + eig_3_w[l]
            modes.append((lam, V, k, l))

    K = np.zeros((3, 3))
    for (lam, V, k, l) in modes:
        if abs(lam) < 1e-8: continue

        c_kl = 0.0
        for g2 in range(4):
            for g3 in range(4):
                s = n_delta(g2) + n_delta(g3)
                a0_val = (4 - s)**kappa
                c_kl += a0_val * basis_2[k][g2] * basis_3[l][g3]

        proj = project_mode_eta(V, eta)
        weight = abs(lam)**(2*beta - 1) * c_kl**2
        K += weight * np.outer(proj, proj)

    return K

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

# ============================================================
# TOPOLOGIES
# ============================================================
TOPOS = {
    'K4xK4': {
        'name': 'K₄□K₄ (v10 baseline)',
        'basis_2': K4_basis, 'eig_2': K4_eigenvalues,
        'basis_3': K4_basis, 'eig_3': K4_eigenvalues,
    },
    'C4xK4': {
        'name': 'C₄□K₄ (C₄ at pos-2)',
        'basis_2': C4_basis, 'eig_2': C4_eigenvalues,
        'basis_3': K4_basis, 'eig_3': K4_eigenvalues,
    },
    'K4xC4': {
        'name': 'K₄□C₄ (C₄ at pos-3)',
        'basis_2': K4_basis, 'eig_2': K4_eigenvalues,
        'basis_3': C4_basis, 'eig_3': C4_eigenvalues,
    },
    'C4xC4': {
        'name': 'C₄□C₄ (both cyclic)',
        'basis_2': C4_basis, 'eig_2': C4_eigenvalues,
        'basis_3': C4_basis, 'eig_3': C4_eigenvalues,
    },
}

# ============================================================
# MAIN
# ============================================================
print("=" * 95)
print("PQT NEUTRINO v20 — TOPOLOGY SCAN (C₄□K₄)")
print("=" * 95)

# ============================================================
# PHASE 0: EIGENSTRUCTURE COMPARISON
# ============================================================
print(f"\n{'PHASE 0: EIGENSTRUCTURE':=^95}")

for name, topo in TOPOS.items():
    eig_2 = topo['eig_2']
    eig_3_w = [e * 1.251 for e in topo['eig_3']]  # γ=0.251

    # All product eigenvalues
    all_eigs = sorted([eig_2[k] + eig_3_w[l]
                       for k in range(4) for l in range(4)], reverse=True)

    print(f"\n  {topo['name']}:")
    print(f"    G₂ eigenvalues: {eig_2}")
    print(f"    G₃ eigenvalues (×1.251): {[f'{e:.1f}' for e in eig_3_w]}")
    print(f"    Product eigenvalues (top 5): {[f'{e:.1f}' for e in all_eigs[:5]]}")
    print(f"    Non-zero modes: {sum(1 for e in all_eigs if abs(e) > 1e-8)}")

# ============================================================
# PHASE 1: SCAN ALL TOPOLOGIES
# ============================================================
print(f"\n{'PHASE 1: TOPOLOGY SCAN (κ=8.78, β=2.96, γ=0.251)':=^95}")

for topo_name, topo in TOPOS.items():
    print(f"\n  --- {topo['name']} ---")
    print(f"  {'η':>6} {'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} {'ratio':>9} {'χ²':>10}")
    print(f"  {'-'*55}")

    best_t = None
    for eta_100 in range(0, 51, 2):
        eta = eta_100 / 100.0

        K = build_K_T(8.78, 0.251, eta, 2.96,
                       topo['basis_2'], topo['eig_2'],
                       topo['basis_3'], topo['eig_3'])
        r = extract_pmns(K)
        if r is None: continue

        c = chi2(r)
        if best_t is None or c < best_t['chi2']:
            best_t = {**r, 'chi2': c, 'eta': eta}

        if eta_100 % 10 == 0:
            print(f"  {eta:6.2f} {r['theta12']:7.1f} {r['theta23']:7.1f} "
                  f"{r['theta13']:7.1f} {r['ratio']:9.5f} {c:10.1f}")

    if best_t:
        print(f"  Best: η={best_t['eta']:.2f}, θ₂₃={best_t['theta23']:.1f}°, "
              f"χ²={best_t['chi2']:.1f}")

# ============================================================
# PHASE 2: FULL PARAMETER SCAN FOR BEST TOPOLOGY
# ============================================================
print(f"\n{'PHASE 2: FULL SCAN (ALL TOPOLOGIES)':=^95}")

all_results = []

for topo_name, topo in TOPOS.items():
    for kappa_10 in range(30, 120, 10):  # κ: 3.0 to 12.0
        kappa = kappa_10 / 10.0

        for beta_10 in range(15, 50, 5):  # β: 1.5 to 5.0
            beta = beta_10 / 10.0

            for eta_100 in range(5, 51, 10):  # η: 0.05 to 0.50
                eta = eta_100 / 100.0

                for gamma_10 in range(0, 40, 10):  # γ: 0.0 to 0.4
                    gamma = gamma_10 / 100.0

                    K = build_K_T(kappa, gamma, eta, beta,
                                   topo['basis_2'], topo['eig_2'],
                                   topo['basis_3'], topo['eig_3'])
                    r = extract_pmns(K)
                    if r is None: continue

                    c = chi2(r)

                    if c < 300:
                        all_results.append({
                            **r, 'chi2': c,
                            'topo': topo_name,
                            'kappa': kappa, 'beta': beta,
                            'eta': eta, 'gamma': gamma,
                        })

all_results.sort(key=lambda x: x['chi2'])

# ============================================================
# TOP 30 RESULTS
# ============================================================
print(f"\n{'TOP 30 RESULTS ACROSS ALL TOPOLOGIES':=^95}")
print(f"{'#':>3} {'Topo':>7} {'κ':>5} {'β':>4} {'η':>5} {'γ':>5} "
      f"{'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} {'ratio':>9} {'χ²':>10}")
print("-" * 85)

for i, r in enumerate(all_results[:30]):
    print(f"{i+1:3d} {r['topo']:>7} {r['kappa']:5.1f} {r['beta']:4.1f} "
          f"{r['eta']:5.2f} {r['gamma']:5.2f} "
          f"{r['theta12']:7.1f} {r['theta23']:7.1f} {r['theta13']:7.1f} "
          f"{r['ratio']:9.5f} {r['chi2']:10.1f}")

# ============================================================
# BEST RESULT
# ============================================================
if all_results:
    b = all_results[0]
    print(f"\n{'BEST RESULT (v20)':=^95}")
    print(f"  Topology: {TOPOS[b['topo']]['name']}")
    print(f"  κ = {b['kappa']:.1f}, β = {b['beta']:.1f}, "
          f"η = {b['eta']:.2f}, γ = {b['gamma']:.2f}")
    print()

    pulls = {}
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(b[obs] - EXP[obs][0]) / EXP[obs][1]
        pulls[obs] = pull
        status = "✅" if pull < 3 else "⚠️" if pull < 5 else "❌"
        print(f"  {obs:8s} = {b[obs]:7.2f}°  (exp: {EXP[obs][0]:.2f}° ± "
              f"{EXP[obs][1]:.2f}°)  pull={pull:5.1f}σ {status}")

    pull_r = abs(b['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    pulls['ratio'] = pull_r
    print(f"  {'ratio':8s} = {b['ratio']:7.5f}  (exp: {EXP['dm2_ratio'][0]})  "
          f"pull={pull_r:5.1f}σ")
    print(f"  χ² = {b['chi2']:.1f}")
    print(f"  Masses: {b['masses']}")
    print(f"  Hierarchy: {b['hierarchy']}")

    all_lt3 = all(p < 3 for p in pulls.values())
    print(f"\n  ALL < 3σ? {'YES — BREAKTHROUGH!' if all_lt3 else 'NO'}")

    # Compare with v10
    print(f"\n  vs v10 (K₄□K₄, χ²=77):")
    print(f"    θ₂₃: 58.7° → {b['theta23']:.1f}° "
          f"(Δ = {b['theta23'] - 58.7:+.1f}°)")
    print(f"    χ²:   77   → {b['chi2']:.1f}")

# ============================================================
# PER-TOPOLOGY SUMMARY
# ============================================================
print(f"\n{'PER-TOPOLOGY BEST RESULTS':=^95}")
print(f"{'Topology':<15} {'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} {'ratio':>9} {'χ²':>10}")
print("-" * 60)

for topo_name in TOPOS:
    topo_results = [r for r in all_results if r['topo'] == topo_name]
    if topo_results:
        b = topo_results[0]
        print(f"{topo_name:<15} {b['theta12']:7.1f} {b['theta23']:7.1f} "
              f"{b['theta13']:7.1f} {b['ratio']:9.5f} {b['chi2']:10.1f}")
    else:
        print(f"{topo_name:<15} {'(no valid results)':>40}")

# ============================================================
# COMPARISON: v1 → v20
# ============================================================
print(f"\n{'COMPLETE EVOLUTION':=^95}")
print(f"{'Ver':<6} {'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} {'ratio':>9} {'χ²':>10} {'Key':>30}")
print("-" * 95)
print(f"{'v1':<6} {'33.4':>7} {'49.1':>7} {'8.5':>7} {'0.031':>9} {'0':>10} {'Overfit':>30}")
print(f"{'v8':<6} {'54.3':>7} {'51.1':>7} {'8.6':>7} {'0.506':>9} {'281k':>10} {'rank-2':>30}")
print(f"{'v10':<6} {'32.9':>7} {'58.7':>7} {'8.5':>7} {'0.030':>9} {'77':>10} {'K₄□K₄':>30}")

if all_results:
    b = all_results[0]
    print(f"{'v20':<6} {b['theta12']:7.1f} {b['theta23']:7.1f} "
          f"{b['theta13']:7.1f} {b['ratio']:9.5f} {b['chi2']:10.1f} "
          f"{b['topo']:>30}")

print(f"{'Exp':<6} {'33.4':>7} {'49.2':>7} {'8.6':>7} {'0.031':>9}")

# ============================================================
# MASS PREDICTIONS
# ============================================================
if all_results and all_results[0]['chi2'] < 200:
    b = all_results[0]
    print(f"\n{'MASS PREDICTIONS (v20)':=^95}")
    m = b['masses']
    Lambda_T = 0.050 / m[2] if m[2] > 0 else 1
    m_ev = m * Lambda_T
    print(f"  m₁ = {m_ev[0]*1e3:.2f} мэВ")
    print(f"  m₂ = {m_ev[1]*1e3:.2f} мэВ")
    print(f"  m₃ = {m_ev[2]*1e3:.2f} мэВ")
    print(f"  Σm_ν = {sum(m_ev)*1e3:.1f} мэВ")
    print(f"  Hierarchy: {b['hierarchy']}")
