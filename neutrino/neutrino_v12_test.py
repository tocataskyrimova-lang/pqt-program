import numpy as np
import sys
from pathlib import Path
sys.path.append(r'C:\AGI\PQT\MAIN\PQT_FORMALIZATION_PACKAGE')
from neutrino_pqt_v12 import build_K_T_v12, extract_pmns, chi2

def test_tbm_limit():
    print("Testing TBM limit (very large lambda_dem)...")
    K = build_K_T_v12(8.78, 0.251, 0.351, 2.96, 1e6)
    r = extract_pmns(K)
    print(f"  θ₁₂={r['theta12']:.2f}°, θ₂₃={r['theta23']:.2f}°, θ₁₃={r['theta13']:.2f}°")
    
    print("\nTesting sweep of lambda_dem up to 100 to find the sweet spot...")
    for lam in [0, 0.1, 0.5, 1, 5, 10, 50, 100]:
        K = build_K_T_v12(8.78, 0.251, 0.351, 2.96, lam)
        r = extract_pmns(K)
        if r:
            print(f"λ={lam:5.1f} -> θ₂₃={r['theta23']:5.2f} θ₁₂={r['theta12']:5.2f} θ₁₃={r['theta13']:5.2f} ratio={r['ratio']:6.4f}")

if __name__ == "__main__":
    test_tbm_limit()
