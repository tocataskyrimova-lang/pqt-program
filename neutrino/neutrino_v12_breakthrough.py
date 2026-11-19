import numpy as np
from scipy.linalg import eigh

# Orthonormal basis of K4
w = np.zeros((4, 4))
w[0] = [0.5, 0.5, 0.5, 0.5]
w[1] = [1, -1, 0, 0] / np.sqrt(2)
w[2] = [1, 1, -2, 0] / np.sqrt(6)
w[3] = [1, 1, 1, -3] / np.sqrt(12)

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

def build_K_v12(kappa, gamma_weight, eta, beta, lam_dem):
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
    
    # Democratic Overlay (J3_off)
    scale = np.trace(K) / 3.0
    J3_off = np.ones((3, 3)) - np.eye(3)
    return K + lam_dem * scale * J3_off

EXP = {'th12': (33.44, 0.7), 'th23': (49.2, 1.1), 'th13': (8.57, 0.12), 'ratio': (0.0307, 0.0009)}

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

# THE SEARCH FOR REASON
print(f"{'κ':>4} {'λ_dem':>6} | {'θ₁₂':>6} {'θ₂₃':>6} {'θ₁₃':>6} {'ratio':>8}")
print("-" * 50)
for k in [6.5, 7.0, 7.5]:
    for l_dem in [0.05, 0.08, 0.10, 0.12]:
        r = extract(build_K_v12(k, 0.251, 0.351, 2.96, l_dem))
        if r:
            pulls = [abs(r[k_] - EXP[k_][0])/EXP[k_][1] for k_ in EXP]
            if all(p < 3.5 for p in pulls):
                print(f"{k:4.2f} {l_dem:6.2f} | {r['th12']:6.1f} {r['th23']:6.1f} {r['th13']:6.1f} {r['ratio']:8.5f} <-- BREAKTHROUGH")
