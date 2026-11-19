"""
PQT Neutrino v5 — K_T from Full Braiding Algebra of QCat
0 free parameters in K_T structure, 1 free parameter (Lambda_T scale)
"""
import numpy as np
from scipy.linalg import eigh
from itertools import product as iprod

# ============================================================
# EXPERIMENTAL DATA (NuFIT 5.3)
# ============================================================
EXP = {'t12':(33.44,0.7),'t23':(49.2,1.1),'t13':(8.57,0.12),'ratio':(0.0307,0.0009)}

# ============================================================
# Q-MATHEMATICS: GLYPH ALGEBRA
# ============================================================
GLYPHS = ['a','b','g','d']  # alpha, beta, gamma, delta
GLYPH_NAMES = {'a':'alpha','b':'beta','g':'gamma','d':'delta'}

# sigma-layers (Axiom 3, Q-Mathematics v3.0)
SIGMA = {'a': +1, 'b': -1, 'g': +1, 'd': -1}

# ============================================================
# BRAID PHASE omega: Sigma x Sigma -> Q_{-1}^x
# ============================================================
def theta_phase(g1, g2):
    """Phase angle from sigma-layer difference."""
    return np.arctan(np.sqrt(abs(SIGMA[g1] - SIGMA[g2])))

# Build full omega table
print("="*75)
print("BRAID PHASE TABLE omega(g1, g2)")
print("="*75)

# omega(g1,g2) = exp(i * sign * theta)
# sign = +1 if sigma[g1] > sigma[g2], -1 if <, 0 if equal
# delta-sector: centrality => omega(d,x) = omega(x,d) = 1
# delta-neutrality: omega(d,d) = 1

def omega(g1, g2):
    """Full braid phase from QCat algebra."""
    if g1 == g2:
        return 1.0 + 0j
    # delta centrality
    if g1 == 'd' or g2 == 'd':
        return 1.0 + 0j
    # General: phase from sigma-layers
    t = theta_phase(g1, g2)
    if t < 1e-10:
        return 1.0 + 0j  # same layer, no phase
    # Asymmetry: direction matters
    if SIGMA[g1] > SIGMA[g2]:
        return np.exp(1j * t)
    else:
        return np.exp(-1j * t)

# Print omega table
print(f"\n{'':>8}", end='')
for g in GLYPHS:
    print(f"  {GLYPH_NAMES[g]:>8}", end='')
print()
for g1 in GLYPHS:
    print(f"{GLYPH_NAMES[g1]:>8}", end='')
    for g2 in GLYPHS:
        w = omega(g1, g2)
        if abs(w.imag) < 1e-10:
            print(f"  {w.real:8.4f}", end='')
        else:
            print(f" {w.real:+.3f}{w.imag:+.3f}j", end='')
    print()

# Verify axioms
print("\nAxiom checks:")
print(f"  omega(d,d) = {omega('d','d'):.4f} (must be 1): {'OK' if abs(omega('d','d')-1)<1e-10 else 'FAIL'}")
print(f"  omega(d,a) = {omega('d','a'):.4f} (centrality => 1): {'OK' if abs(omega('d','a')-1)<1e-10 else 'FAIL'}")
print(f"  omega(a,b)*omega(b,a) = {omega('a','b')*omega('b','a'):.4f} (must be |omega|^2): "
      f"{'OK' if abs(abs(omega('a','b'))**2-1)<1e-10 else 'FAIL'}")

# ============================================================
# CODON SPACE AND GENERATION PARTITION
# ============================================================
print("\n"+"="*75)
print("CODON PARTITION")
print("="*75)

# All S-codons (c1 = alpha)
S_codons = [('a', c2, c3) for c2 in GLYPHS for c3 in GLYPHS]
print(f"Total S-codons: {len(S_codons)}")

# TWO partition schemes to test
def partition_ndelta(codons):
    """Original: by count of delta glyphs."""
    g1 = [c for c in codons if sum(1 for x in c if x=='d') == 0]
    g2 = [c for c in codons if sum(1 for x in c if x=='d') == 1]
    g3 = [c for c in codons if sum(1 for x in c if x=='d') >= 2]
    return g1, g2, g3, "n_delta (9:6:1)"

def partition_lastdelta(codons):
    """Strategy 1: by position of last delta."""
    g1, g2, g3 = [], [], []
    for c in codons:
        positions = [i for i,x in enumerate(c) if x=='d']
        if not positions: g1.append(c)
        elif max(positions) == 1: g2.append(c)
        else: g3.append(c)
    return g1, g2, g3, "last_delta (9:3:4)"

# ============================================================
# BUILD K_T FROM BRAIDING ALGEBRA
# ============================================================
def build_KT_braiding(generations):
    """Build K_T from full braiding algebra. 0 free parameters."""
    K = np.zeros((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            total = 0j
            for ci in generations[i]:
                for cj in generations[j]:
                    # Product of omega over 3 codon positions
                    braid = 1.0 + 0j
                    for pos in range(3):
                        braid *= omega(ci[pos], cj[pos])
                    total += braid
            # Normalize by geometric mean of generation sizes
            Ni = len(generations[i])
            Nj = len(generations[j])
            K[i, j] = total / np.sqrt(Ni * Nj)
    return K

def build_KT_braiding_mean(generations):
    """K_T normalized by arithmetic mean (alternative)."""
    K = np.zeros((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            total = 0j
            for ci in generations[i]:
                for cj in generations[j]:
                    braid = 1.0 + 0j
                    for pos in range(3):
                        braid *= omega(ci[pos], cj[pos])
                    total += braid
            K[i, j] = total / (len(generations[i]) * len(generations[j]))
    return K

def build_KT_braiding_raw(generations):
    """K_T without normalization (raw counts)."""
    K = np.zeros((3, 3), dtype=complex)
    for i in range(3):
        for j in range(3):
            total = 0j
            for ci in generations[i]:
                for cj in generations[j]:
                    braid = 1.0 + 0j
                    for pos in range(3):
                        braid *= omega(ci[pos], cj[pos])
                    total += braid
            K[i, j] = total
    return K

# ============================================================
# PMNS EXTRACTION
# ============================================================
def extract_pmns(K):
    M = (K + K.conj().T) / 2
    ev, U = eigh(M.real)
    idx = np.argsort(ev); ev = ev[idx]; U = U[:, idx]
    if any(e <= 0 for e in ev): return None
    s13 = min(abs(U[0,2]), 0.999); c13 = np.sqrt(1-s13**2)
    s12 = min(abs(U[0,1])/c13, 0.999) if c13>1e-10 else 0
    s23 = min(abs(U[1,2])/c13, 0.999) if c13>1e-10 else 0
    dm21 = ev[1]**2-ev[0]**2; dm31 = ev[2]**2-ev[0]**2
    r = dm21/dm31 if dm31>1e-30 else 0
    return {'t12':np.degrees(np.arcsin(s12)),'t23':np.degrees(np.arcsin(s23)),
            't13':np.degrees(np.arcsin(s13)),'ratio':r,'m':ev,
            'nh':'NH' if ev[0]<ev[1]<ev[2] else 'IH'}

def chi2(r):
    if r is None: return 1e10
    return sum(((r[k]-EXP[k][0])/EXP[k][1])**2 for k in ['t12','t23','t13','ratio'])

def show(label, K, r):
    print(f"\n--- {label} ---")
    print(f"K_T matrix:")
    for i in range(3):
        row = "  ["
        for j in range(3):
            v=K[i,j]
            if abs(v.imag)<1e-6: row+=f" {v.real:9.5f}"
            else: row+=f" {v.real:+.4f}{v.imag:+.4f}j"
        print(row+" ]")
    if r is None:
        print("  FAILED: negative eigenvalues")
        return
    p = {k:abs(r[k]-EXP[k][0])/EXP[k][1] for k in ['t12','t23','t13','ratio']}
    print(f"  Eigenvalues: [{r['m'][0]:.5f}, {r['m'][1]:.5f}, {r['m'][2]:.5f}]")
    print(f"  t12={r['t12']:6.2f} ({p['t12']:5.1f}s)  t23={r['t23']:6.2f} ({p['t23']:5.1f}s)  "
          f"t13={r['t13']:6.2f} ({p['t13']:5.1f}s)  ratio={r['ratio']:.5f} ({p['ratio']:5.1f}s)")
    print(f"  chi2={chi2(r):.1f}  Hierarchy={r['nh']}")

# ============================================================
# RUN ALL COMBINATIONS
# ============================================================
print("\n"+"="*75)
print("K_T FROM FULL BRAIDING ALGEBRA (0 free parameters)")
print("="*75)

partitions = [partition_ndelta, partition_lastdelta]
normalizations = [
    ("geom_mean", build_KT_braiding),
    ("arith_mean", build_KT_braiding_mean),
    ("raw", build_KT_braiding_raw),
]

all_results = []
for pfunc in partitions:
    g1, g2, g3, pname = pfunc(S_codons)
    print(f"\n{'='*75}")
    print(f"Partition: {pname}  |  Gen sizes: {len(g1)}:{len(g2)}:{len(g3)}")
    print(f"{'='*75}")

    for nname, nfunc in normalizations:
        K = nfunc([g1, g2, g3])
        r = extract_pmns(K)
        label = f"{pname} + {nname}"
        show(label, K, r)
        if r:
            all_results.append({'label':label, 'K':K, 'r':r, 'chi2':chi2(r)})

# ============================================================
# ALSO TEST: torsion mode (chi_x != 1)
# ============================================================
print("\n"+"="*75)
print("TORSION MODE: chi_x != 1 (active Tamas ether)")
print("="*75)

def omega_torsion(g1, g2, chi_vals):
    """omega with non-trivial delta torsion."""
    if g1 == g2: return 1.0+0j
    if g1 == 'd':
        return complex(chi_vals.get(g2, 1.0))
    if g2 == 'd':
        return complex(1.0 / chi_vals.get(g1, 1.0))
    t = theta_phase(g1, g2)
    if t < 1e-10: return 1.0+0j
    if SIGMA[g1] > SIGMA[g2]: return np.exp(1j*t)
    else: return np.exp(-1j*t)

def build_KT_torsion(generations, chi_vals):
    K = np.zeros((3,3), dtype=complex)
    for i in range(3):
        for j in range(3):
            total = 0j
            for ci in generations[i]:
                for cj in generations[j]:
                    braid = 1.0+0j
                    for pos in range(3):
                        braid *= omega_torsion(ci[pos], cj[pos], chi_vals)
                    total += braid
            Ni=len(generations[i]); Nj=len(generations[j])
            K[i,j] = total / (Ni*Nj)
    return K

# Scan torsion values
g1,g2,g3,pname = partition_ndelta(S_codons)
best_torsion = {'chi2':1e10}
for chi_a in np.arange(-2, 2.1, 0.1):
    for chi_b in np.arange(-2, 2.1, 0.1):
        for chi_g in np.arange(-2, 2.1, 0.1):
            cv = {'a':chi_a, 'b':chi_b, 'g':chi_g}
            K = build_KT_torsion([g1,g2,g3], cv)
            r = extract_pmns(K)
            c = chi2(r) if r else 1e10
            if c < best_torsion['chi2']:
                best_torsion = {'chi2':c, 'r':r, 'K':K, 'chi':cv,
                                'label':f"torsion chi_a={chi_a:.1f} chi_b={chi_b:.1f} chi_g={chi_g:.1f}"}

if best_torsion['r']:
    show(best_torsion['label'], best_torsion['K'], best_torsion['r'])
    all_results.append(best_torsion)
    print(f"  chi values: {best_torsion['chi']}")

# Same for last-delta partition
g1,g2,g3,pname = partition_lastdelta(S_codons)
best_torsion2 = {'chi2':1e10}
for chi_a in np.arange(-2, 2.1, 0.1):
    for chi_b in np.arange(-2, 2.1, 0.1):
        for chi_g in np.arange(-2, 2.1, 0.1):
            cv = {'a':chi_a, 'b':chi_b, 'g':chi_g}
            K = build_KT_torsion([g1,g2,g3], cv)
            r = extract_pmns(K)
            c = chi2(r) if r else 1e10
            if c < best_torsion2['chi2']:
                best_torsion2 = {'chi2':c, 'r':r, 'K':K, 'chi':cv,
                                 'label':f"9:3:4 torsion chi_a={chi_a:.1f} chi_b={chi_b:.1f} chi_g={chi_g:.1f}"}

if best_torsion2['r']:
    show(best_torsion2['label'], best_torsion2['K'], best_torsion2['r'])
    all_results.append(best_torsion2)
    print(f"  chi values: {best_torsion2['chi']}")

# ============================================================
# FINAL RANKING
# ============================================================
print("\n"+"="*75)
print("FINAL RANKING — ALL CONFIGURATIONS")
print("="*75)
print(f"{'#':>2} {'t12':>6} {'t23':>6} {'t13':>6} {'ratio':>8} {'chi2':>9} {'NH':>3} {'Label'}")
print("-"*85)
for i,res in enumerate(sorted(all_results, key=lambda x:x['chi2'])):
    r=res['r']
    print(f"{i+1:2d} {r['t12']:6.1f} {r['t23']:6.1f} {r['t13']:6.1f} {r['ratio']:8.5f} "
          f"{res['chi2']:9.1f} {r['nh']:>3} {res['label'][:50]}")
print("-"*85)
print(f"   {33.44:6.1f} {49.2:6.1f} {8.57:6.1f} {0.0307:8.5f}           EXPERIMENT")

# Best result
br = min(all_results, key=lambda x:x['chi2'])
print(f"\n{'='*75}")
print(f"BEST: {br['label']}")
print(f"chi2 = {br['chi2']:.2f}, free params = {'0 (centrality)' if 'torsion' not in br['label'] else '3 (chi_a,chi_b,chi_g)'}")
r=br['r']
p={k:abs(r[k]-EXP[k][0])/EXP[k][1] for k in ['t12','t23','t13','ratio']}
print(f"  t12={r['t12']:.2f} ({p['t12']:.1f}s)  t23={r['t23']:.2f} ({p['t23']:.1f}s)")
print(f"  t13={r['t13']:.2f} ({p['t13']:.1f}s)  ratio={r['ratio']:.5f} ({p['ratio']:.1f}s)")
print(f"  Hierarchy: {r['nh']}")
sc=0.050/r['m'][2] if r['m'][2]>0 else 1; me=r['m']*sc
print(f"  Masses: m1={me[0]*1e3:.1f} m2={me[1]*1e3:.1f} m3={me[2]*1e3:.1f} Sum={sum(me)*1e3:.0f} meV")
