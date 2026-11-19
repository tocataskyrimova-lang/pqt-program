import numpy as np
import sys
from pathlib import Path
sys.path.append(r'C:\AGI\PQT\MAIN\PQT_FORMALIZATION_PACKAGE')
from neutrino_pqt_v11 import build_K_T_v11, extract_pmns_complex

print("Measuring th23 sensitivity to Gen1-Gen3 coupling...")
for z in [0, 1, 5, 10, 20, 50, 100, 500]:
    K = build_K_T_v11(8.78, 0.251, 0.351, 2.96, z, 0)
    r = extract_pmns_complex(K)
    print(f"|ζ|={z:3d} -> θ₂₃={r['theta23']:5.2f} θ₁₂={r['theta12']:5.2f} θ₁₃={r['theta13']:5.2f}")
