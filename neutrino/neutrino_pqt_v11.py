"""
PQT Neutrino v11 — Retardation-based Gen1↔Gen3 coupling
Building on v10 (position-aware charge) + direct ζ coupling

Graph: K4 □ K4 (weighted)
Charge: position-aware σ-charge with η-asymmetry
New: ζ·|e₁⟩⟨e₃| + h.c. from retardation dynamics
CP-phase: φ_ζ from split-complex temporal asymmetry

Free params: κ, η, γ, β, |ζ|, φ_ζ = 6
Observables: θ₁₂, θ₂₃, θ₁₃, ratio, J_CP = 5+1
"""

import numpy as np
from scipy.linalg import eigh
from itertools import product

# ============================================================
# ORTHONORMAL BASIS OF K4
# ============================================================
w = np.zeros((4, 4))
w[0] = [1, 1, 1, 1];       w[0] /= 2.0
w[1] = [1, -1, 0, 0];      w[1] /= np.sqrt(2)
w[2] = [1, 1, -2, 0];      w[2] /= np.sqrt(6)
w[3] = [1, 1, 1, -3];      w[3] /= np.sqrt(12)

# ============================================================
# GLYPH INDEXING
# ============================================================
def n_delta(idx):
    return 1 if idx == 3 else 0

# ============================================================
# σ-CHARGE
# ============================================================
Q_SIGMA = np.array([1.0, 0.0, 1.0, 0.0])

def position_charge(g2, g3, eta):
    return (1 + eta) * Q_SIGMA[g2] + (1 - eta) * Q_SIGMA[g3]

# ============================================================
# GENERATION PARTITION
# ============================================================
def get_generation(g2, g3):
    d2, d3 = n_delta(g2), n_delta(g3)
    if d2 == 1 and d3 == 0:
        return 0  # Gen1 (ν_e)
    elif d2 == 0 and d3 == 0:
        return 1  # Gen2 (ν_μ)
    else:
        return 2  # Gen3 (ν_τ)

gen = np.zeros((4, 4), dtype=int)
for g2 in range(4):
    for g3 in range(4):
        gen[g2, g3] = get_generation(g2, g3)

# ============================================================
# EIGENMODES OF WEIGHTED GRAPH
# ============================================================
def build_eigenmodes(gamma_weight):
    eig_pos2 = [0, 4, 4, 4]
    eig_pos3 = [0, 4*(1+gamma_weight), 4*(1+gamma_weight), 4*(1+gamma_weight)]
    modes = []
    for k in range(4):
        for l in range(4):
            V = np.outer(w[k], w[l]).flatten()
            lam = eig_pos2[k] + eig_pos3[l]
            modes.append((lam, V, k, l))
    return modes

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
# BUILD K_T^v10
# ============================================================
def build_K_T_v10(kappa, gamma_weight, eta, beta):
    modes = build_eigenmodes(gamma_weight)
    K = np.zeros((3, 3))
    for (lam, V, k, l) in modes:
        if lam < 1e-8:
            continue
        c_kl = 0.0
        for g2 in range(4):
            for g3 in range(4):
                s = n_delta(g2) + n_delta(g3)
                c_kl += (4 - s)**kappa * w[k][g2] * w[l][g3]
        proj = project_mode_eta(V, eta)
        weight = lam**(2*beta - 1) * c_kl**2
        K += weight * np.outer(proj, proj)
    return K

# ============================================================
# BUILD K_T^v11
# ============================================================
def build_K_T_v11(kappa, gamma_weight, eta, beta, zeta_abs, zeta_phase):
    """
    v11: adds direct Gen1↔Gen3 coupling from retardation.
    We normalize K_v10 to a scale where max element is 10.0
    to allow zeta (0-3) to be a significant perturbation.
    """
    K_v10 = build_K_T_v10(kappa, gamma_weight, eta, beta)
    
    # Structural normalization
    norm = np.max(np.abs(K_v10))
    K_norm = (K_v10 / norm) * 10.0

    # Hermitian Gen1-Gen3 coupling
    K_v11 = K_norm.astype(complex)
    zeta = zeta_abs * np.exp(1j * zeta_phase)
    K_v11[0, 2] += zeta          
    K_v11[2, 0] += np.conj(zeta) 

    return K_v11

# ============================================================
# PMNS EXTRACTION
# ============================================================
EXP = {
    'theta12': (33.44, 0.7),
    'theta23': (49.2, 1.1),
    'theta13': (8.57, 0.12),
    'dm2_ratio': (0.0307, 0.0009),
}
EXP_JCP = (0.033, 0.006)

def extract_pmns_complex(K):
    eigenvalues, U = eigh(K)
    idx = np.argsort(eigenvalues.real)
    eigenvalues = eigenvalues[idx].real
    U = U[:, idx]
    if eigenvalues[0] < -1e-6: return None
    m = np.sqrt(np.maximum(eigenvalues, 0))
    U_abs = np.abs(U)
    s13 = U_abs[0, 2]
    theta13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    s23 = U_abs[1, 2] / den
    theta23 = np.degrees(np.arcsin(np.clip(s23, 0, 1)))
    s12 = U_abs[0, 1] / den
    theta12 = np.degrees(np.arcsin(np.clip(s12, 0, 1)))
    dm21 = m[1]**2 - m[0]**2
    dm31 = m[2]**2 - m[0]**2
    ratio = dm21 / dm31 if dm31 > 0 else 0
    J_CP = np.imag(U[0,0] * U[1,1] * np.conj(U[0,1]) * np.conj(U[1,0]))
    return {
        'theta12': theta12, 'theta23': theta23, 'theta13': theta13,
        'dm2_ratio': ratio, 'masses': m,
        'hierarchy': 'NH' if m[0] < m[1] < m[2] else 'IH',
        'J_CP': J_CP, 'U_PMNS': U,
    }

def chi2(result, include_J=False):
    if result is None: return 1e10
    c = 0
    for obs in ['theta12', 'theta23', 'theta13']:
        c += ((result[obs] - EXP[obs][0]) / EXP[obs][1])**2
    if result['dm2_ratio'] > 0:
        c += ((result['dm2_ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1])**2
    else: c += 1e4
    if result['hierarchy'] != 'NH': c += 1e4
    if include_J and abs(result['J_CP']) > 0.001:
        c += ((abs(result['J_CP']) - EXP_JCP[0]) / EXP_JCP[1])**2
    return c

# ============================================================
# EXECUTION
# ============================================================
print("=" * 90)
print("PQT NEUTRINO v11 — RETARDATION-BASED Gen1↔Gen3 COUPLING")
print("=" * 90)

v10_params = {'kappa': 8.78, 'eta': 0.351, 'gamma_weight': 0.251, 'beta': 2.96}

# PHASE 0
print(f"\n{'PHASE 0: v10 BASELINE (ζ=0)':=^90}")
K_v10 = build_K_T_v10(**v10_params)
r_v10 = extract_pmns_complex(K_v10)
if r_v10:
    print(f"  θ₁₂={r_v10['theta12']:.2f}°, θ₂₃={r_v10['theta23']:.2f}°, θ₁₃={r_v10['theta13']:.2f}°")
    print(f"  dm2_ratio={r_v10['dm2_ratio']:.5f}, J_CP={r_v10['J_CP']:.5f}, χ²={chi2(r_v10):.1f}")

# PHASE 1 & 2: SCAN
best_zeta = None
for zeta_100 in range(0, 301, 5):
    zeta_abs = zeta_100 / 100.0
    for phase_10 in range(0, 21, 2):
        phi = phase_10 * np.pi / 10.0
        K = build_K_T_v11(v10_params['kappa'], v10_params['gamma_weight'], 
                           v10_params['eta'], v10_params['beta'], zeta_abs, phi)
        r = extract_pmns_complex(K)
        if r is None: continue
        c = chi2(r)
        if best_zeta is None or c < best_zeta['chi2']:
            best_zeta = {**r, 'chi2': c, 'zeta_abs': zeta_abs, 'zeta_phase': phi}

if best_zeta:
    print(f"\n{'BEST FIXED RESULT (v11)':=^90}")
    print(f"  |ζ| = {best_zeta['zeta_abs']:.3f}, φ_ζ = {best_zeta['zeta_phase']:.3f} rad ({np.degrees(best_zeta['zeta_phase']):.1f}°)")
    print(f"  θ₁₂ = {best_zeta['theta12']:.2f}°, θ₂₃ = {best_zeta['theta23']:.2f}°, θ₁₃ = {best_zeta['theta13']:.2f}°")
    print(f"  dm2_ratio = {best_zeta['dm2_ratio']:.5f}, J_CP = {best_zeta['J_CP']:.5f}, χ² = {best_zeta['chi2']:.1f}")

# PHASE 6: FULL SCAN
print(f"\n{'PHASE 6: REDUCED FULL SCAN (κ, η, |ζ|, φ_ζ)':=^90}")
best_full = None
gamma_fix = 0.251
beta_fix = 2.96

for kappa_10 in range(50, 151, 10):
    kappa = kappa_10 / 10.0
    for eta_100 in range(20, 60, 5):
        eta = eta_100 / 100.0
        for zeta_100 in range(0, 201, 20):
            zeta_abs = zeta_100 / 100.0
            for phase_10 in range(0, 21, 4):
                phi = phase_10 * np.pi / 10.0
                K = build_K_T_v11(kappa, gamma_fix, eta, beta_fix, zeta_abs, phi)
                r = extract_pmns_complex(K)
                if r is None: continue
                c = chi2(r)
                if best_full is None or c < best_full['chi2']:
                    best_full = {**r, 'chi2': c, 'kappa': kappa, 'eta': eta, 'zeta_abs': zeta_abs, 'zeta_phase': phi}

if best_full:
    print(f"\n{'BEST FULL RESULT':=^90}")
    print(f"  κ={best_full['kappa']:.2f}, η={best_full['eta']:.3f}, |ζ|={best_full['zeta_abs']:.3f}, φ={best_full['zeta_phase']:.2f}")
    for obs, (exp_val, exp_err) in EXP.items():
        pull = abs(best_full[obs] - exp_val) / exp_err
        print(f"  {obs:10s} = {best_full[obs]:8.2f}° (exp: {exp_val:8.2f}°) pull={pull:4.1f}σ")
    print(f"  J_CP       = {best_full['J_CP']:8.5f} (exp: {EXP_JCP[0]:8.5f})")
    print(f"  χ² = {best_full['chi2']:.1f}")
    all_good = all(abs(best_full[obs] - EXP[obs][0]) < 3*EXP[obs][1] for obs in EXP)
    print(f"\n  ALL ANGLES < 3σ? {'YES — BREAKTHROUGH!' if all_good else 'NO'}")
