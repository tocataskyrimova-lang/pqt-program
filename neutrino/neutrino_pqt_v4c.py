"""PQT Neutrino v4c — Definitive scan, normalized K_T"""
import numpy as np
from scipy.linalg import eigh, eig

EXP = {'t12':(33.44,0.7),'t23':(49.2,1.1),'t13':(8.57,0.12),'ratio':(0.0307,0.0009)}
P12=np.pi/4; P23=np.pi/4; P13=np.arctan(np.sqrt(2))

def pmns(K):
    M=(K+K.conj().T)/2; ev,U=eigh(M.real)
    idx=np.argsort(ev); ev=ev[idx]; U=U[:,idx]
    if any(e<=0 for e in ev): return None
    s13=min(abs(U[0,2]),0.999); c13=np.sqrt(1-s13**2)
    s12=min(abs(U[0,1])/c13,0.999) if c13>1e-10 else 0
    s23=min(abs(U[1,2])/c13,0.999) if c13>1e-10 else 0
    dm21=ev[1]**2-ev[0]**2; dm31=ev[2]**2-ev[0]**2
    r=dm21/dm31 if dm31>1e-30 else 0
    return {'t12':np.degrees(np.arcsin(s12)),'t23':np.degrees(np.arcsin(s23)),
            't13':np.degrees(np.arcsin(s13)),'ratio':r,'m':ev,'nh':ev[0]<ev[1]<ev[2]}

def c2(r):
    if r is None or not r['nh']: return 1e10
    return sum(((r[k]-EXP[k][0])/EXP[k][1])**2 for k in ['t12','t23','t13','ratio'])

def scan(N, eps, label, krange=np.arange(0.1,12,0.005)):
    """Scan kappa for given partition N and eps structure."""
    best={'chi2':1e10}
    for kappa in krange:
        # Exponential weight: w(gen_i) = N_i * exp(-kappa*(2-gen_level_i))
        # Simple power law on codon counts
        k = np.array(N,dtype=float)**kappa
        kn = k / sum(k)  # NORMALIZE to [0,1]
        K = np.diag(kn.astype(complex))
        for i,j,e,p in eps:
            v = e * np.sqrt(kn[i]*kn[j]) * np.exp(1j*p)
            K[i,j]=v; K[j,i]=v.conj()
        r=pmns(K)
        ch=c2(r)
        if ch<best['chi2']:
            best={**r,'chi2':ch,'kappa':kappa,'label':label,'K':K}
    return best

print("="*75)
print("PQT NEUTRINO v4c — DEFINITIVE SCAN")
print("All K_T normalized, geometric off-diagonal scaling")
print("="*75)

configs = [
    # Original v3 partition
    ("v3: 9:6:1, eps13=1/9",  [9,6,1], [(0,1,1/3,P12),(0,2,1/9,P13),(1,2,1.0,P23)]),
    # Strategy 1: position-based partition
    ("S1: 9:3:4, eps=1/3,1/4,1/4", [9,3,4], [(0,1,1/3,P12),(0,2,1/4,P13),(1,2,1/4,P23)]),
    # Strategy 1 variant: different eps
    ("S1v: 9:3:4, eps=1/3,1/3,1/3", [9,3,4], [(0,1,1/3,P12),(0,2,1/3,P13),(1,2,1/3,P23)]),
    # Symmetric-ish partition
    ("S4: 7:5:4, eps=1/3,1/4,1/4", [7,5,4], [(0,1,1/3,P12),(0,2,1/4,P13),(1,2,1/4,P23)]),
    # Equal partition (control)
    ("CTL: 5:5:5, eps=1/3,1/9,1", [5,5,5], [(0,1,1/3,P12),(0,2,1/9,P13),(1,2,1.0,P23)]),
    # Inverted count: Gen3 has MORE codons (heavy has most memory)
    ("S5: 4:3:9, eps=1/4,1/3,1/4", [4,3,9], [(0,1,1/4,P12),(0,2,1/3,P13),(1,2,1/4,P23)]),
    # From full codon space including Q-modes
    ("S6: 9:6:4, eps=1/3,1/4,2/3", [9,6,4], [(0,1,1/3,P12),(0,2,1/4,P13),(1,2,2/3,P23)]),
    # Near-democratic
    ("S7: 6:5:5, eps=1/3,1/4,1/3", [6,5,5], [(0,1,1/3,P12),(0,2,1/4,P13),(1,2,1/3,P23)]),
]

results = []
for label, N, eps in configs:
    r = scan(N, eps, label)
    results.append(r)
    p = {k:abs(r[k]-EXP[k][0])/EXP[k][1] for k in ['t12','t23','t13','ratio']}
    mp = max(p.values())
    print(f"\n{label}")
    print(f"  kappa={r['kappa']:.3f}  chi2={r['chi2']:.1f}")
    print(f"  t12={r['t12']:.1f}({p['t12']:.1f}s) t23={r['t23']:.1f}({p['t23']:.1f}s) "
          f"t13={r['t13']:.1f}({p['t13']:.1f}s) ratio={r['ratio']:.5f}({p['ratio']:.1f}s)")
    sc=0.050/r['m'][2] if r['m'][2]>0 else 1; me=r['m']*sc
    print(f"  m1={me[0]*1e3:.1f} m2={me[1]*1e3:.1f} m3=50.0 Sum={sum(me)*1e3:.0f} meV")

# Sort and display
print("\n"+"="*75)
print("RANKING BY CHI2")
print("="*75)
print(f"{'#':>2} {'Config':<35} {'t12':>6} {'t23':>6} {'t13':>6} {'ratio':>8} {'chi2':>9}")
print("-"*75)
for i,r in enumerate(sorted(results, key=lambda x:x['chi2'])):
    print(f"{i+1:2d} {r['label']:<35} {r['t12']:6.1f} {r['t23']:6.1f} {r['t13']:6.1f} {r['ratio']:8.5f} {r['chi2']:9.1f}")
print("-"*75)
print(f"   {'Experiment':<35} {33.44:6.1f} {49.2:6.1f} {8.57:6.1f} {0.0307:8.5f}")

# Best result analysis
br = min(results, key=lambda x:x['chi2'])
print(f"\n{'='*75}")
print(f"BEST: {br['label']}")
print(f"{'='*75}")
p = {k:abs(br[k]-EXP[k][0])/EXP[k][1] for k in ['t12','t23','t13','ratio']}
print(f"  kappa = {br['kappa']:.4f}")
print(f"  chi2 = {br['chi2']:.2f}, chi2/DoF = {br['chi2']/2:.2f}")
print(f"  max pull = {max(p.values()):.1f} sigma")
for k in ['t12','t23','t13','ratio']:
    print(f"  {k:>6}: PQT={br[k]:8.3f}  exp={EXP[k][0]:8.3f}+/-{EXP[k][1]:.3f}  pull={p[k]:.1f}s")
K = br['K']
print(f"\n  K_T matrix:")
for i in range(3):
    row = "    ["
    for j in range(3):
        v=K[i,j]
        if abs(v.imag)<1e-10: row+=f" {v.real:9.6f}"
        else: row+=f" {v.real:+.5f}{v.imag:+.5f}j"
    print(row+" ]")

# Check: does ANY partition give theta13 in 3-sigma?
print(f"\n{'='*75}")
print("THETA_13 DIAGNOSTIC: Can ANY partition reach 8.57 +/- 0.36?")
print(f"{'='*75}")
for r in sorted(results, key=lambda x:abs(x['t13']-8.57)):
    gap = abs(r['t13']-8.57)/0.12
    ok = "YES" if gap < 3 else "no"
    print(f"  {r['label']:<35} t13={r['t13']:6.2f}  gap={gap:6.1f}s  3s? {ok}")
