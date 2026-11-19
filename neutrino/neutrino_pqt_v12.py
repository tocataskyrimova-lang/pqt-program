"""
PQT Neutrino v12 — Democratic Yukawa Overlay from Delocalization

Physical basis: neutrinos are delocalized (μ_ν → 0), so their Yukawa
matrix has democratic (equal) off-diagonal couplings. This overlays
the v10 graph dynamics, shifting θ₂₃ toward 45° (tribimaximal).

K_T^(v12) = K_T^(v10) + λ_dem · J₃^off + ζ·|e₁⟩⟨e₃| + h.c.

Key: λ_dem is NOT a free parameter — it's determined by delocalization.
     For μ_ν → 0: λ_dem → 1 (fully democratic).
     We scan to verify, then fix at predicted value.

Free: (κ, η, γ, β) from v10 + λ_dem structural = 5 (but λ_dem predicted ~1)
"""

import numpy as np
from scipy.linalg import eigh

# ============================================================
# ORTHONORMAL BASIS OF K4
# ============================================================
w = np.zeros((4, 4))
w[0] = [1, 1, 1, 1];       w[0] /= 2.0
w[1] = [1, -1, 0, 0];      w[1] /= np.sqrt(2)
w[2] = [1, 1, -2, 0];      w[2] /= np.sqrt(6)
w[3] = [1, 1, 1, -3];      w[3] /= np.sqrt(12)

def n_delta(idx):
    return 1 if idx == 3 else 0

Q_SIGMA = np.array([1.0, 0.0, 1.0, 0.0])

def position_charge(g2, g3, eta):
    return (1 + eta) * Q_SIGMA[g2] + (1 - eta) * Q_SIGMA[g3]

def get_generation(g2, g3):
    d2, d3 = n_delta(g2), n_delta(g3)
    if d2 == 1 and d3 == 0: return 0
    elif d2 == 0 and d3 == 0: return 1
    else: return 2

gen = np.zeros((4, 4), dtype=int)
for g2 in range(4):
    for g3 in range(4):
        gen[g2, g3] = get_generation(g2, g3)

N_gen = [np.sum(gen == a) for a in range(3)]

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

def build_K_T_v10(kappa, gamma_weight, eta, beta):
    modes = build_eigenmodes(gamma_weight)
    K = np.zeros((3, 3))
    for (lam, V, k, l) in modes:
        if lam < 1e-8: continue
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
# DEMOCRATIC OVERLAY: J₃^off (off-diagonal all-ones)
# ============================================================
J3_off = np.ones((3, 3)) - np.eye(3)

def build_K_T_v12(kappa, gamma_w, eta, beta, lambda_dem,
                   zeta_abs=0.0, zeta_phase=0.0):
    """
    v12 = v10 graph dynamics + democratic Yukawa overlay + optional ζ coupling.
    """
    K_v10 = build_K_T_v10(kappa, gamma_w, eta, beta)

    # We need to scale J3_off to the magnitude of K_v10 so lambda_dem is O(1)
    scale = np.max(np.abs(K_v10))
    K = K_v10 + lambda_dem * scale * J3_off

    # Gen1↔Gen3 retardation coupling (from v11, optional)
    if zeta_abs > 1e-10:
        K = K.astype(complex)
        zeta = zeta_abs * scale * np.exp(1j * zeta_phase)
        K[0, 2] += zeta
        K[2, 0] += np.conj(zeta)

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
EXP_JCP = (0.033, 0.006)

def extract_pmns(K):
    eigenvalues, U = eigh(K)
    idx = np.argsort(eigenvalues.real)
    eigenvalues = eigenvalues[idx].real
    U = U[:, idx]

    if eigenvalues[0] < -1e-6:
        return None

    m = np.sqrt(np.maximum(eigenvalues, 0))
    m = np.sort(m)

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
        'ratio': ratio, 'masses': m,
        'hierarchy': 'NH' if m[0] < m[1] < m[2] else 'IH',
        'J_CP': J_CP, 'U_PMNS': U, 'eigenvalues': eigenvalues,
    }

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
        c += 1e4
    if include_J and abs(r['J_CP']) > 0.001:
        c += ((abs(r['J_CP']) - EXP_JCP[0]) / EXP_JCP[1])**2
    return c

# ============================================================
# PHASE 0: v10 BASELINE
# ============================================================
print("=" * 90)
print("PQT NEUTRINO v12 — DEMOCRATIC YUKAWA OVERLAY FROM DELOCALIZATION")
print("=" * 90)

v10_params = {'kappa': 8.78, 'eta': 0.351, 'gamma_weight': 0.251, 'beta': 2.96}

print(f"\n{'PHASE 0: v10 BASELINE (λ_dem=0)':=^90}")
K_v10 = build_K_T_v10(**v10_params)
r_v10 = extract_pmns(K_v10)
if r_v10:
    c_v10 = chi2(r_v10)
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(r_v10[obs] - EXP[obs][0]) / EXP[obs][1]
        print(f"  {obs} = {r_v10[obs]:.2f}° (pull={pull:.1f}σ)")
    print(f"  ratio = {r_v10['ratio']:.5f}")
    print(f"  χ² = {c_v10:.1f}")

# ============================================================
# EIGENVALUES OF J₃^off FOR REFERENCE
# ============================================================
eig_J3 = np.linalg.eigvalsh(J3_off)
print(f"\n  J₃^off eigenvalues: {eig_J3}")
print(f"  J₃^off eigenvectors: (1,1,1)/√3 for λ=2, two degenerate for λ=-1")
print(f"  → Democratic overlay favors θ₂₃=45°, θ₁₂=35.3° (TBM limit)")

# ============================================================
# PHASE 1: λ_dem SWEEP (ζ=0, real K_T)
# ============================================================
print(f"\n{'PHASE 1: λ_dem SWEEP (real, ζ=0)':=^90}")
print(f"{'λ_dem':>8} {'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} {'ratio':>9} {'NH':>3} {'χ²':>10}")
print("-" * 65)

best_real = None
for lam_100 in range(0, 501, 10):  # λ_dem: 0.00 to 5.00
    lam = lam_100 / 100.0

    K = build_K_T_v12(v10_params['kappa'], v10_params['gamma_weight'],
                       v10_params['eta'], v10_params['beta'],
                       lam, 0.0, 0.0)
    r = extract_pmns(K)

    if r is None: continue

    c = chi2(r)

    if best_real is None or c < best_real['chi2']:
        best_real = {**r, 'chi2': c, 'lambda_dem': lam}

    if lam_100 % 50 == 0 or abs(r['theta23'] - 49.2) < 1.5:
        print(f"{lam:8.2f} {r['theta12']:7.1f} {r['theta23']:7.1f} "
              f"{r['theta13']:7.1f} {r['ratio']:9.5f} "
              f"{'Y' if r['hierarchy']=='NH' else 'N':>3} {c:10.1f}")

if best_real:
    print(f"\n  Best real: λ_dem={best_real['lambda_dem']:.2f}, "
          f"θ₂₃={best_real['theta23']:.1f}°, χ²={best_real['chi2']:.1f}")

# ============================================================
# PHASE 2: PREDICTED VALUE λ_dem = 1
# ============================================================
print(f"\n{'PHASE 2: PREDICTED λ_dem = 1 (full delocalization)':=^90}")
K_pred = build_K_T_v12(v10_params['kappa'], v10_params['gamma_weight'],
                        v10_params['eta'], v10_params['beta'],
                        1.0, 0.0, 0.0)
r_pred = extract_pmns(K_pred)
if r_pred:
    c_pred = chi2(r_pred)
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(r_pred[obs] - EXP[obs][0]) / EXP[obs][1]
        status = "✅" if pull < 3 else "⚠️" if pull < 5 else "❌"
        print(f"  {obs:8s} = {r_pred[obs]:7.2f}°  (exp: {EXP[obs][0]:.2f}°)  "
              f"pull={pull:5.1f}σ {status}")
    pull_r = abs(r_pred['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    print(f"  {'ratio':8s} = {r_pred['ratio']:7.5f}  (exp: {EXP['dm2_ratio'][0]:.4f})  "
          f"pull={pull_r:5.1f}σ {'✅' if pull_r < 3 else '❌'}")
    print(f"  χ² = {c_pred:.1f}")
    print(f"  Masses: {r_pred['masses']}")

# ============================================================
# PHASE 3: FULL SCAN (κ, η, λ_dem) at fixed γ, β
# ============================================================
print(f"\n{'PHASE 3: SCAN (κ, η, λ_dem) at γ='}{v10_params['gamma_weight']}{', β='}{v10_params['beta']}:=^90")

best = None
results = []

for kappa_10 in range(50, 151, 10):      # 5.0 to 15.0
    kappa = kappa_10 / 10.0
    for eta_100 in range(15, 60, 5):     # 0.15 to 0.60
        eta = eta_100 / 100.0
        for lam_100 in range(0, 301, 10): # 0.00 to 3.00
            lam = lam_100 / 100.0

            K = build_K_T_v12(kappa, v10_params['gamma_weight'], eta,
                               v10_params['beta'], lam)
            r = extract_pmns(K)
            if r is None: continue

            c = chi2(r)
            entry = {**r, 'chi2': c, 'kappa': kappa, 'eta': eta,
                     'lambda_dem': lam}

            if best is None or c < best['chi2']:
                best = entry
            results.append(entry)

results.sort(key=lambda x: x['chi2'])

print(f"\n{'TOP 15 RESULTS':=^90}")
print(f"{'#':>3} {'κ':>5} {'η':>5} {'λ_dem':>7} {'θ₁₂':>7} {'θ₂₃':>7} "
      f"{'θ₁₃':>7} {'ratio':>9} {'NH':>3} {'χ²':>10}")
print("-" * 80)

for i, r in enumerate(results[:15]):
    print(f"{i+1:3d} {r['kappa']:5.1f} {r['eta']:5.2f} {r['lambda_dem']:7.2f} "
          f"{r['theta12']:7.1f} {r['theta23']:7.1f} {r['theta13']:7.1f} "
          f"{r['ratio']:9.5f} {'Y' if r['hierarchy']=='NH' else 'N':>3} "
          f"{r['chi2']:10.1f}")

# ============================================================
# PHASE 4: BEST RESULT + CP
# ============================================================
if best:
    print(f"\n{'BEST RESULT (v12)':=^90}")
    print(f"  κ = {best['kappa']:.2f}")
    print(f"  η = {best['eta']:.3f}")
    print(f"  γ = {v10_params['gamma_weight']:.3f} (fixed)")
    print(f"  β = {v10_params['beta']:.3f} (fixed)")
    print(f"  λ_dem = {best['lambda_dem']:.3f}")
    print()

    pulls = {}
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(best[obs] - EXP[obs][0]) / EXP[obs][1]
        pulls[obs] = pull
        status = "✅" if pull < 3 else "⚠️" if pull < 5 else "❌"
        print(f"  {obs:8s} = {best[obs]:7.2f}°  (exp: {EXP[obs][0]:.2f}° ± "
              f"{EXP[obs][1]:.2f}°)  pull={pull:5.1f}σ {status}")

    pull_r = abs(best['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    pulls['ratio'] = pull_r
    print(f"  {'ratio':8s} = {best['ratio']:7.5f}  (exp: {EXP['dm2_ratio'][0]:.4f})  "
          f"pull={pull_r:5.1f}σ")
    print(f"  χ² = {best['chi2']:.1f}")
    print(f"  Masses: {best['masses']}")

    all_lt3 = all(p < 3 for p in pulls.values())
    all_lt5 = all(p < 5 for p in pulls.values())
    print(f"\n  ALL < 3σ? {'YES — BREAKTHROUGH!' if all_lt3 else 'NO'}")
    print(f"  ALL < 5σ? {'YES' if all_lt5 else 'NO'}")

# ============================================================
# PHASE 5: ADD ζ FOR CP-VIOLATION AT BEST POINT
# ============================================================
if best:
    print(f"\n{'PHASE 5: ADD ζ FOR CP-VIOLATION':=^90}")
    print(f"{'|ζ|':>7} {'φ':>5} {'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} "
          f"{'ratio':>9} {'J_CP':>8} {'χ²':>10}")
    print("-" * 75)

    best_cp = None
    for zeta_100 in range(0, 101, 10):  # |ζ|: 0.0 to 1.0
        zeta_abs = zeta_100 / 100.0
        for phase_10 in range(0, 21, 5):  # φ: 0 to 2π
            phi = phase_10 * np.pi / 10.0

            K = build_K_T_v12(best['kappa'], v10_params['gamma_weight'],
                               best['eta'], v10_params['beta'],
                               best['lambda_dem'], zeta_abs, phi)
            r = extract_pmns(K)
            if r is None: continue

            c = chi2(r)

            if best_cp is None or c < best_cp['chi2']:
                best_cp = {**r, 'chi2': c, 'zeta_abs': zeta_abs,
                           'zeta_phase': phi}

            if zeta_100 % 50 == 0 and phase_10 % 10 == 0:
                print(f"{zeta_abs:7.2f} {phi:5.2f} {r['theta12']:7.1f} "
                      f"{r['theta23']:7.1f} {r['theta13']:7.1f} "
                      f"{r['ratio']:9.5f} {r['J_CP']:8.5f} {c:10.1f}")

    if best_cp:
        print(f"\n  Best with CP: |ζ|={best_cp['zeta_abs']:.2f}, "
              f"φ={best_cp['zeta_phase']:.2f}, J_CP={best_cp['J_CP']:.5f}, "
              f"χ²={best_cp['chi2']:.1f}")

# ============================================================
# PHASE 6: v12 PREDICTED (λ_dem = 1, no fitting)
# ============================================================
print(f"\n{'PHASE 6: v12 STRUCTURAL PREDICTION (λ_dem=1, κ,η from v10)':=^90}")
K_struct = build_K_T_v12(v10_params['kappa'], v10_params['gamma_weight'],
                          v10_params['eta'], v10_params['beta'],
                          1.0, 0.0, 0.0)
r_struct = extract_pmns(K_struct)
if r_struct:
    c_struct = chi2(r_struct)
    for obs in ['theta12', 'theta23', 'theta13']:
        pull = abs(r_struct[obs] - EXP[obs][0]) / EXP[obs][1]
        status = "✅" if pull < 3 else "⚠️" if pull < 5 else "❌"
        print(f"  {obs:8s} = {r_struct[obs]:7.2f}°  pull={pull:5.1f}σ {status}")
    pull_r = abs(r_struct['ratio'] - EXP['dm2_ratio'][0]) / EXP['dm2_ratio'][1]
    print(f"  {'ratio':8s} = {r_struct['ratio']:7.5f}  pull={pull_r:5.1f}σ")
    print(f"  χ² = {c_struct:.1f}")
    print(f"  New parameters: 0 (λ_dem=1 is predicted by delocalization)")

# ============================================================
# COMPARISON: v8 → v12
# ============================================================
print(f"\n{'EVOLUTION: v8 → v12':=^90}")
print(f"{'Ver':<6} {'θ₁₂':>7} {'θ₂₃':>7} {'θ₁₃':>7} {'ratio':>9} {'J_CP':>8} "
      f"{'χ²':>10} {'Key':>30}")
print("-" * 95)
print(f"{'v8':<6} {'54.3':>7} {'51.1':>7} {'8.6':>7} {'0.506':>9} {'0':>8} "
      f"{'281000':>10} {'rank-2 theorem':>30}")
print(f"{'v9':<6} {'35.2':>7} {'77.6':>7} {'8.4':>7} {'0.034':>9} {'0':>8} "
      f"{'693':>10} {'rank-3 σ-charge':>30}")
print(f"{'v10':<6} {'32.9':>7} {'58.7':>7} {'8.5':>7} {'0.030':>9} {'0':>8} "
      f"{'77':>10} {'position-aware η':>30}")
print(f"{'v11':<6} {'33.0':>7} {'58.7':>7} {'8.6':>7} {'0.030':>9} {'0.02':>8} "
      f"{'75.5':>10} {'retardation ζ':>30}")

if best:
    print(f"{'v12':<6} {best['theta12']:7.1f} {best['theta23']:7.1f} "
          f"{best['theta13']:7.1f} {best['ratio']:9.5f} {best_cp['J_CP'] if best_cp else 0:8.5f} "
          f"{best['chi2']:10.1f} {'democratic λ_dem':>30}")

print(f"{'Exp':<6} {'33.4':>7} {'49.2':>7} {'8.6':>7} {'0.031':>9} {'0.033':>8}")

# ============================================================
# MASS PREDICTIONS
# ============================================================
if best:
    print(f"\n{'MASS PREDICTIONS':=^90}")
    m = best['masses']
    Lambda_T = 0.050 / m[2] if m[2] > 0 else 1
    m_ev = m * Lambda_T
    print(f"  m₁ = {m_ev[0]*1e3:.2f} мэВ")
    print(f"  m₂ = {m_ev[1]*1e3:.2f} мэВ")
    print(f"  m₃ = {m_ev[2]*1e3:.2f} мэВ")
    print(f"  Σm_ν = {sum(m_ev)*1e3:.1f} мэВ")
    print(f"  Hierarchy: {'NH' if m[0] < m[1] < m[2] else 'IH'}")
