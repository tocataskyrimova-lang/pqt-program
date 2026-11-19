"""
PQT Neutrino v6b — Generation relabeling check
Does swapping Gen2 <-> Gen3 fix the angle assignment?
"""
import numpy as np
from scipy.linalg import eigh

EXP = {'t12':(33.44,0.7),'t23':(49.2,1.1),'t13':(8.57,0.12),'ratio':(0.0307,0.0009)}

# K_T^dyn from v6 (kappa=1)
K_orig = np.array([
    [ 5.0625, -1.6875, -3.375],
    [-1.6875,  2.8125, -1.125],
    [-3.375,  -1.125,   4.500]
])

def extract(K, label):
    ev, U = eigh(K)
    idx = np.argsort(ev); ev = ev[idx]; U = U[:, idx]
    ev = np.maximum(ev, 0)
    m = np.sqrt(ev)
    
    s13 = min(abs(U[0,2]), 0.9999); c13 = np.sqrt(1-s13**2)
    s12 = min(abs(U[0,1])/c13, 0.9999) if c13>1e-10 else 0
    s23 = min(abs(U[1,2])/c13, 0.9999) if c13>1e-10 else 0
    t13 = np.degrees(np.arcsin(s13))
    t12 = np.degrees(np.arcsin(s12))
    t23 = np.degrees(np.arcsin(s23))
    
    dm21 = ev[1]-ev[0]; dm31 = ev[2]-ev[0]
    ratio = dm21/dm31 if dm31>1e-30 else 0
    
    c2 = ((t12-EXP['t12'][0])/EXP['t12'][1])**2
    c2 += ((t23-EXP['t23'][0])/EXP['t23'][1])**2
    c2 += ((t13-EXP['t13'][0])/EXP['t13'][1])**2
    c2 += ((ratio-EXP['ratio'][0])/EXP['ratio'][1])**2
    
    p12 = abs(t12-EXP['t12'][0])/EXP['t12'][1]
    p23 = abs(t23-EXP['t23'][0])/EXP['t23'][1]
    p13 = abs(t13-EXP['t13'][0])/EXP['t13'][1]
    pr = abs(ratio-EXP['ratio'][0])/EXP['ratio'][1]
    
    print(f"\n=== {label} ===")
    print(f"K_T =\n{np.array2string(K, precision=4)}")
    print(f"Eigenvalues: {ev}")
    print(f"PMNS matrix:\n{np.array2string(U, precision=4)}")
    print(f"t12={t12:.2f} ({p12:.1f}s)  t23={t23:.2f} ({p23:.1f}s)  t13={t13:.2f} ({p13:.1f}s)")
    print(f"ratio={ratio:.5f} ({pr:.1f}s)  chi2={c2:.1f}")
    print(f"Masses: m1={m[0]*50/m[2]:.1f} m2={m[1]*50/m[2]:.1f} m3=50.0 meV")
    return c2

# Original: Gen1=9(no-d), Gen2=3(d@2), Gen3=4(d@3)
extract(K_orig, "ORIGINAL: Gen1(9) Gen2(3) Gen3(4)")

# Permutation 1: swap Gen2 <-> Gen3 (swap rows/cols 1,2)
P23 = np.array([[1,0,0],[0,0,1],[0,1,0]])
K_swap23 = P23 @ K_orig @ P23.T
extract(K_swap23, "SWAP Gen2<->Gen3: Gen1(9) Gen2(4) Gen3(3)")

# Permutation 2: swap Gen1 <-> Gen3 (swap rows/cols 0,2)
P13 = np.array([[0,0,1],[0,1,0],[1,0,0]])
K_swap13 = P13 @ K_orig @ P13.T
extract(K_swap13, "SWAP Gen1<->Gen3: Gen1(4) Gen2(3) Gen3(9)")

# Permutation 3: cyclic Gen1->Gen2->Gen3->Gen1
Pcyc = np.array([[0,1,0],[0,0,1],[1,0,0]])
K_cyc = Pcyc @ K_orig @ Pcyc.T
extract(K_cyc, "CYCLIC: Gen1(3) Gen2(4) Gen3(9)")

# Permutation 4: reverse cyclic
Pcyc2 = np.array([[0,0,1],[1,0,0],[0,1,0]])
K_cyc2 = Pcyc2 @ K_orig @ Pcyc2.T
extract(K_cyc2, "REV-CYCLIC: Gen1(4) Gen2(9) Gen3(3)")

# Permutation 5: swap Gen1 <-> Gen2
P12 = np.array([[0,1,0],[1,0,0],[0,0,1]])
K_swap12 = P12 @ K_orig @ P12.T
extract(K_swap12, "SWAP Gen1<->Gen2: Gen1(3) Gen2(9) Gen3(4)")

# Summary
print("\n" + "="*75)
print("SUMMARY: ALL PERMUTATIONS")
print("="*75)
print(f"{'Label':<35} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'chi2':>9}")
print("-"*75)
perms = [
    ("Original (9,3,4)", K_orig),
    ("Swap Gen2<->Gen3 (9,4,3)", K_swap23),
    ("Swap Gen1<->Gen3 (4,3,9)", K_swap13),
    ("Cyclic (3,4,9)", K_cyc),
    ("Rev-cyclic (4,9,3)", K_cyc2),
    ("Swap Gen1<->Gen2 (3,9,4)", K_swap12),
]
for label, K in perms:
    ev, U = eigh(K)
    idx = np.argsort(ev); ev = ev[idx]; U = U[:, idx]
    ev = np.maximum(ev, 0)
    s13 = min(abs(U[0,2]),0.9999); c13=np.sqrt(1-s13**2)
    s12 = min(abs(U[0,1])/c13,0.9999) if c13>1e-10 else 0
    s23 = min(abs(U[1,2])/c13,0.9999) if c13>1e-10 else 0
    t13=np.degrees(np.arcsin(s13)); t12=np.degrees(np.arcsin(s12)); t23=np.degrees(np.arcsin(s23))
    dm21=ev[1]-ev[0]; dm31=ev[2]-ev[0]; ratio=dm21/dm31 if dm31>1e-30 else 0
    c2=((t12-33.44)/0.7)**2+((t23-49.2)/1.1)**2+((t13-8.57)/0.12)**2+((ratio-0.0307)/0.0009)**2
    print(f"{label:<35} {t12:7.2f} {t23:7.2f} {t13:7.02f} {ratio:9.5f} {c2:9.1f}")
print("-"*75)
print(f"{'Experiment':<35} {33.44:7.2f} {49.2:7.02f} {8.57:7.02f} {0.0307:9.5f}")
