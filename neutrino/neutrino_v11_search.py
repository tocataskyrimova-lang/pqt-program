import numpy as np
import sys
from pathlib import Path
sys.path.append(r'C:\AGI\PQT\MAIN\PQT_FORMALIZATION_PACKAGE')
from neutrino_pqt_v11 import build_K_T_v11, extract_pmns_complex, chi2

def broad_search():
    print("Starting broad search for PQT v11 breakthrough...")
    best_overall = None
    
    # Try extremely large zeta to see if it even can move theta23
    for z_abs in [10, 50, 100, 500]:
        for z_phi in [0, np.pi/2, np.pi, 1.5*np.pi]:
            K = build_K_T_v11(8.78, 0.251, 0.351, 2.96, z_abs, z_phi)
            r = extract_pmns_complex(K)
            if r:
                print(f"|ζ|={z_abs:3d} φ={z_phi:4.2f} -> θ₂₃={r['theta23']:5.1f} θ₁₂={r['theta12']:5.1f} χ²={chi2(r):.1f}")

    # Random search
    np.random.seed(137)
    for _ in range(1000):
        kappa = np.random.uniform(7.0, 11.0)
        eta = np.random.uniform(0.1, 0.5)
        zeta_abs = np.random.uniform(0, 150)
        zeta_phase = np.random.uniform(0, 2*np.pi)
        
        K = build_K_T_v11(kappa, 0.251, eta, 2.96, zeta_abs, zeta_phase)
        r = extract_pmns_complex(K)
        if r is None: continue
        
        c = chi2(r)
        if best_overall is None or c < best_overall['chi2']:
            best_overall = {**r, 'chi2': c, 'kappa': kappa, 'eta': eta, 'zeta_abs': zeta_abs, 'zeta_phase': zeta_phase}
            if r['theta23'] < 52.0:
                print(f"!!! DISCOVERY: χ²={c:.1f} θ₂₃={r['theta23']:.1f} at |ζ|={zeta_abs:.1f}")

    if best_overall:
        print("\nBEST DISCOVERED:")
        print(f"  χ²={best_overall['chi2']:.1f}")
        print(f"  θ₁₂={best_overall['theta12']:.2f}, θ₂₃={best_overall['theta23']:.2f}, θ₁₃={best_overall['theta13']:.2f}")
        print(f"  κ={best_overall['kappa']:.2f}, η={best_overall['eta']:.3f}, |ζ|={best_overall['zeta_abs']:.1f}")

if __name__ == "__main__":
    broad_search()
