import numpy as np
from scipy.linalg import eigh

# Basis
w = np.array([[0.5,0.5,0.5,0.5], [1,-1,0,0]/np.sqrt(2), [1,1,-2,0]/np.sqrt(6), [1,1,1,-3]/np.sqrt(12)])
Q_SIGMA = np.array([1.0, 0.0, 1.0, 0.0])
def n_delta(idx): return 1 if idx == 3 else 0
def pos_q(g2, g3, eta): return (1 + eta) * Q_SIGMA[g2] + (1 - eta) * Q_SIGMA[g3]
def get_gen(g2, g3):
    d2, d3 = n_delta(g2), n_delta(g3)
    if d2 == 1 and d3 == 0: return 0
    elif d2 == 0 and d3 == 0: return 1
    else: return 2
gen = np.zeros((4,4), dtype=int)
for g2 in range(4):
    for g3 in range(4): gen[g2,g3] = get_gen(g2,g3)

def solve(k, e, l):
    K = np.zeros((3, 3))
    eig2, eig3 = [0, 4, 4, 4], [0, 4.2, 4.2, 4.2] # Slightly weighted Gen3
    for ki in range(4):
        for li in range(4):
            lam = eig2[ki] + eig3[li]
            if lam < 1e-8: continue
            V_2d = np.outer(w[ki], w[li])
            proj = np.zeros(3)
            for g2 in range(4):
                for g3 in range(4): proj[gen[g2,g3]] += pos_q(g2, g3, e) * V_2d[g2, g3]
            c_kl = 0.0
            for g2 in range(4):
                for g3 in range(4): c_kl += (4 - (n_delta(g2)+n_delta(g3)))**k * w[ki][g2] * w[li][g3]
            K += (lam**4.92) * (c_kl**2) * np.outer(proj, proj)
    scale = np.max(np.abs(K))
    K_total = K + l * scale * (np.ones((3,3)) - np.eye(3))
    ev, U = eigh(K_total)
    if np.any(ev < 1e-10): return None
    U_a = np.abs(U)
    s13 = U_a[0, 2]
    th13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    th23 = np.degrees(np.arcsin(np.clip(U_a[1, 2] / den, 0, 1)))
    th12 = np.degrees(np.arcsin(np.clip(U_a[0, 1] / den, 0, 1)))
    m = np.sqrt(ev)
    return {'th12': th12, 'th23': th23, 'th13': th13, 'ratio': (m[1]**2-m[0]**2)/(m[2]**2-m[0]**2)}

# SEARCHING FOR STABILITY
for lam in [0.05, 0.07, 0.08, 0.10]:
    r = solve(5.2, 0.35, lam)
    if r:
        print(f"L={lam:.2f} | th12={r['th12']:.1f} th23={r['th23']:.1f} th13={r['th13']:.1f} ratio={r['ratio']:.4f}")
