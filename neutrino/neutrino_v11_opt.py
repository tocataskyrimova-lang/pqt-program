import numpy as np
import sys
from pathlib import Path
from scipy.optimize import minimize
sys.path.append(r'C:\AGI\PQT\MAIN\PQT_FORMALIZATION_PACKAGE')
from neutrino_pqt_v11 import build_K_T_v11, extract_pmns_complex, chi2

def optimize_v11():
    print("Optimizing PQT v11 parameters...")
    
    # x = [kappa, eta, gamma, beta, zeta_abs, zeta_phase]
    x0 = [8.78, 0.351, 0.251, 2.96, 0.1, 0.0]
    
    def objective(x):
        k, e, g, b, z_a, z_p = x
        if k < 0 or e < 0 or e > 1 or g < 0 or b < 0 or z_a < 0:
            return 1e10
        K = build_K_T_v11(k, g, e, b, z_a, z_p)
        r = extract_pmns_complex(K)
        return chi2(r, include_J=True)

    res = minimize(objective, x0, method='Nelder-Mead', options={'maxiter': 200})
    
    print("\nOptimization Result:")
    print(res)
    
    best_x = res.x
    K = build_K_T_v11(*best_x)
    r = extract_pmns_complex(K)
    if r:
        print("\nFinal Metrics:")
        print(f"  th12={r['theta12']:.2f}, th23={r['theta23']:.2f}, th13={r['theta13']:.2f}")
        print(f"  ratio={r['dm2_ratio']:.5f}, J_CP={r['J_CP']:.5f}, chi2={chi2(r):.1f}")
        print(f"  Params: k={best_x[0]:.2f}, e={best_x[1]:.3f}, g={best_x[2]:.3f}, b={best_x[3]:.2f}, z={best_x[4]:.2f}, p={best_x[5]:.2f}")

if __name__ == "__main__":
    optimize_v11()
