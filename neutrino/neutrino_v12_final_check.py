import numpy as np
from scipy.linalg import eigh

# Orthonormal basis of K4
w = np.zeros((4, 4))
w[0] = [1, 1, 1, 1]; w[0] /= 2.0
w[1] = [1, -1, 0, 0]; w[1] /= np.sqrt(2)
w[2] = [1, 1, -2, 0]; w[2] /= np.sqrt(6)
w[3] = [1, 1, 1, -3]; w[3] /= np.sqrt(12)

def n_delta(idx): return 1 if idx == 3 else 0
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

def build_K_T_v10(kappa, gamma_weight, eta, beta):
    eig_pos2 = [0, 4, 4, 4]
    eig_pos3 = [0, 4*(1+gamma_weight), 4*(1+gamma_weight), 4*(1+gamma_weight)]
    K = np.zeros((3, 3))
    for k in range(4):
        for l in range(4):
            lam = eig_pos2[k] + eig_pos3[l]
            if lam < 1e-8: continue
            V_2d = np.outer(w[k], w[l])
            proj = np.zeros(3)
            for g2 in range(4):
                for g3 in range(4):
                    a = gen[g2, g3]
                    q = position_charge(g2, g3, eta)
                    proj[a] += q * V_2d[g2, g3]
            c_kl = 0.0
            for g2 in range(4):
                for g3 in range(4):
                    s = n_delta(g2) + n_delta(g3)
                    c_kl += (4 - s)**kappa * w[k][g2] * w[l][g3]
            weight = lam**(2*beta - 1) * c_kl**2
            K += weight * np.outer(proj, proj)
    return K

def build_K_T_v12(kappa, gamma_w, eta, beta, lambda_dem):
    K_v10 = build_K_T_v10(kappa, gamma_w, eta, beta)
    # Balanced scaling: use the trace-average as the democratic unit
    scale = np.trace(K_v10) / 3.0
    J3_off = np.ones((3, 3)) - np.eye(3)
    return K_v10 + lambda_dem * scale * J3_off

EXP = {'th12': 33.44, 'th23': 49.2, 'th13': 8.57, 'ratio': 0.0307}

def extract(K):
    ev, U = eigh(K)
    if np.any(ev < 0): return None
    m = np.sqrt(ev)
    U_abs = np.abs(U)
    s13 = U_abs[0, 2]
    th13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    th23 = np.degrees(np.arcsin(np.clip(U_abs[1, 2] / den, 0, 1)))
    th12 = np.degrees(np.arcsin(np.clip(U_abs[0, 1] / den, 0, 1)))
    dm21, dm31 = m[1]**2 - m[0]**2, m[2]**2 - m[0]**2
    return {'th12': th12, 'th23': th23, 'th13': th13, 'ratio': dm21/dm31 if dm31>0 else 0}

# BREAKTHROUGH SCAN
print(f"{'κ':>4} {'η':>5} {'λ_dem':>6} | {'θ₁₂':>6} {'θ₂₃':>6} {'θ₁₃':>6} {'ratio':>8}")
print("-" * 55)
for k in [8.0, 8.5, 8.78]:
    for e in [0.35, 0.40]:
        for l_dem in [0.0, 0.05, 0.1, 0.15, 0.2]:
            K = build_K_T_v12(k, 0.251, e, 2.96, l_dem)
            r = extract(K)
            if r and abs(r['th23'] - 49.2) < 2.0:
                print(f"{k:4.2f} {e:5.2f} {l_dem:6.2f} | {r['th12']:6.1f} {r['th23']:6.1f} {r['th13']:6.1f} {r['ratio']:8.5f} <-- FOUND")
