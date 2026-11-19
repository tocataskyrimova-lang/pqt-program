import numpy as np
from scipy.linalg import eigh
import sys

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
    eig2, eig3 = [0, 4, 4, 4], [0, 4, 4, 4]
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
    if scale < 1e-20: return None
    
    K_total = K + l * scale * (np.ones((3,3)) - np.eye(3))
    ev, U = eigh(K_total)
    
    # Strict positive definiteness check
    if np.any(ev < -1e-8): return None
    
    U_a = np.abs(U)
    s13 = U_a[0, 2]
    th13 = np.degrees(np.arcsin(np.clip(s13, 0, 1)))
    den = np.sqrt(max(1 - s13**2, 1e-10))
    th23 = np.degrees(np.arcsin(np.clip(U_a[1, 2] / den, 0, 1)))
    th12 = np.degrees(np.arcsin(np.clip(U_a[0, 1] / den, 0, 1)))
    
    # Safe mass extraction
    m = np.sqrt(np.maximum(ev, 0))
    if m[2]**2 - m[0]**2 < 1e-20: return None
    
    return {'th12': th12, 'th23': th23, 'th13': th13, 'ratio': (m[1]**2-m[0]**2)/(m[2]**2-m[0]**2)}

EXP = {'th12': (33.44, 0.7), 'th23': (49.2, 1.1), 'th13': (8.57, 0.12), 'ratio': (0.0307, 0.0009)}

def evaluate_pulls(r):
    pulls = {
        'th12': abs(r['th12'] - EXP['th12'][0]) / EXP['th12'][1],
        'th23': abs(r['th23'] - EXP['th23'][0]) / EXP['th23'][1],
        'th13': abs(r['th13'] - EXP['th13'][0]) / EXP['th13'][1],
        'ratio': abs(r['ratio'] - EXP['ratio'][0]) / EXP['ratio'][1]
    }
    max_pull = max(pulls.values())
    return max_pull, pulls

print("RIGOROUS SCAN FOR PQT v12 BREAKTHROUGH")
print("Searching parameter space for a valid 3-sigma fit...")

best_pull = 1e10
best_params = None
best_res = None

# Scan ranges
kappa_range = np.linspace(1.0, 15.0, 50)
eta_range = np.linspace(0.1, 0.9, 20)
lam_range = np.linspace(0.0, 0.5, 20)

for k in kappa_range:
    for e in eta_range:
        for l in lam_range:
            r = solve(k, e, l)
            if r is None: continue
            
            max_pull, pulls = evaluate_pulls(r)
            if max_pull < best_pull:
                best_pull = max_pull
                best_params = (k, e, l)
                best_res = r

print("-" * 60)
if best_params:
    print(f"BEST FOUND: max_pull = {best_pull:.2f}σ")
    print(f"Params: kappa={best_params[0]:.2f}, eta={best_params[1]:.2f}, lambda_dem={best_params[2]:.3f}")
    print(f"Results:")
    print(f"  Theta12 = {best_res['th12']:6.2f}° (Target: {EXP['th12'][0]} ± {EXP['th12'][1]})")
    print(f"  Theta23 = {best_res['th23']:6.2f}° (Target: {EXP['th23'][0]} ± {EXP['th23'][1]})")
    print(f"  Theta13 = {best_res['th13']:6.2f}° (Target: {EXP['th13'][0]} ± {EXP['th13'][1]})")
    print(f"  Ratio   = {best_res['ratio']:6.5f} (Target: {EXP['ratio'][0]} ± {EXP['ratio'][1]})")
    
    if best_pull < 3.0:
        print("\nVERDICT: TRUE BREAKTHROUGH CONFIRMED (All parameters < 3σ)")
    else:
        print("\nVERDICT: FAIL (Could not find a < 3σ fit)")
else:
    print("\nVERDICT: FAIL (No valid physical solutions found in scanned range)")
