"""
PQT Neutrino — Structural Angle Audit
Checking if theta23 = 58.7 deg is a fundamental constant of the K4 □ K4 graph.
"""

import numpy as np
from scipy.linalg import eigh

# Basis
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

def build_K_T_v10(kappa, gamma_w, eta, beta):
    eig_pos2 = [0, 4, 4, 4]
    eig_pos3 = [0, 4*(1+gamma_w), 4*(1+gamma_w), 4*(1+gamma_w)]
    K = np.zeros((3, 3))
    for k in range(4):
        for l in range(4):
            lam = eig_pos2[k] + eig_pos3[l]
            if lam < 1e-8: continue
            V_2d = np.outer(w[k], w[l])
            proj = np.zeros(3)
            for g2 in range(4):
                for g3 in range(4):
                    proj[gen[g2, g3]] += position_charge(g2, g3, eta) * V_2d[g2, g3]
            c_kl = 0.0
            for g2 in range(4):
                for g3 in range(4):
                    s = n_delta(g2) + n_delta(g3)
                    c_kl += (4 - s)**kappa * w[k][g2] * w[l][g3]
            K += (lam**(2*beta-1)) * (c_kl**2) * np.outer(proj, proj)
    return K

def extract_pmns(K):
    ev, U = eigh(K)
    U_abs = np.abs(U[:, np.argsort(ev)])
    s13 = U_abs[0, 2]
    den = np.sqrt(max(1 - s13**2, 1e-10))
    th23 = np.degrees(np.arcsin(np.clip(U_abs[1, 2] / den, 0, 1)))
    return th23

print("=" * 60)
print("TEST: θ₂₃ vs η (Structural Constant Check)")
print("-" * 60)
print(f"{'η':>6} | {'θ₂₃':>8}")
print("-" * 20)

# Scan eta with high precision
for eta in [0.0, 0.1, 0.2, 0.3, 0.351, 0.4, 0.5, 0.7, 0.9]:
    th23 = extract_pmns(build_K_T_v10(8.78, 0.251, eta, 2.96))
    print(f"{eta:6.3f} | {th23:8.2f}°")

print("-" * 60)
# Check arccos connections
angle = 58.74
print(f"Target angle: {angle}°")
for n in range(1, 10):
    val = np.degrees(np.arccos(1/n))
    print(f"arccos(1/{n}) = {val:8.2f}° | diff = {abs(angle-val):5.2f}°")

val_tbm = np.degrees(np.arctan(np.sqrt(2)))
print(f"arctan(sqrt(2)) = {val_tbm:8.2f}° (TBM limit)")
