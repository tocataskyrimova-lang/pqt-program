import numpy as np
from scipy.linalg import eigh

w = np.array([[0.5, 0.5, 0.5, 0.5], [1, -1, 0, 0]/np.sqrt(2), [1, 1, -2, 0]/np.sqrt(6), [1, 1, 1, -3]/np.sqrt(12)])
Q_SIGMA = np.array([1.0, 0.0, 1.0, 0.0])
def n_delta(idx): return 1 if idx == 3 else 0
def position_charge(g2, g3, eta): return (1 + eta) * Q_SIGMA[g2] + (1 - eta) * Q_SIGMA[g3]
def get_gen(g2, g3):
    d2, d3 = n_delta(g2), n_delta(g3)
    if d2 == 1 and d3 == 0: return 0
    elif d2 == 0 and d3 == 0: return 1
    else: return 2
gen = np.zeros((4, 4), dtype=int)
for g2 in range(4):
    for g3 in range(4): gen[g2, g3] = get_gen(g2, g3)

def run_v12(kappa, eta, l_dem, zeta=0):
    K = np.zeros((3, 3))
    eig_pos2, eig_pos3 = [0, 4, 4, 4], [0, 4.1, 4.1, 4.1]
    for k in range(4):
        for l in range(4):
            lam = eig_pos2[k] + eig_pos3[l]
            if lam < 1e-8: continue
            V_2d = np.outer(w[k], w[l])
            proj = np.zeros(3)
            for g2 in range(4):
                for g3 in range(4): proj[gen[g2,g3]] += position_charge(g2, g3, eta) * V_2d[g2, g3]
            c_kl = 0.0
            for g2 in range(4):
                for g3 in range(4): c_kl += (4 - (n_delta(g2)+n_delta(g3)))**kappa * w[k][g2] * w[l][g3]
            K += (lam**4.92) * (c_kl**2) * np.outer(proj, proj)
    scale = np.max(np.abs(K))
    K_total = K + l_dem * scale * (np.ones((3,3)) - np.eye(3))
    if zeta > 0:
        K_total = K_total.astype(complex)
        K_total[0,2] += zeta * scale * 1j; K_total[2,0] -= zeta * scale * 1j
    ev, U = eigh(K_total)
    if np.any(ev < 0): return None
    U_abs = np.abs(U)
    s13 = U_abs[0, 2]
    th13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    th23 = np.degrees(np.arcsin(np.clip(U_abs[1, 2] / den, 0, 1)))
    th12 = np.degrees(np.arcsin(np.clip(U_abs[0, 1] / den, 0, 1)))
    m = np.sqrt(ev)
    return {'th12': th12, 'th23': th23, 'th13': th13, 'ratio': (m[1]**2-m[0]**2)/(m[2]**2-m[0]**2)}

EXP = {'th12': 33.44, 'th23': 49.2, 'th13': 8.57, 'ratio': 0.0307}

print(f"{'λ_dem':>5} {'ζ':>4} | {'θ₁₂':>5} {'θ₂₃':>5} {'θ₁₃':>5} {'ratio':>7}")
print("-" * 45)
# Scan around delocalized eta=0.2
for l in [0.05, 0.10, 0.15]:
    for z in [0.0, 0.02]:
        r = run_v12(8.78, 0.22, l, z)
        if r:
            print(f"{l:5.2f} {z:4.2f} | {r['th12']:5.1f} {r['th23']:5.1f} {r['th13']:5.1f} {r['ratio']:7.4f}")
