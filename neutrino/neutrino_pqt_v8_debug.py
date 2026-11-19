"""
PQT Neutrino v8 — Debug: find all non-zero mode projections
"""
import numpy as np
from scipy.linalg import eigh

w = np.zeros((4,4))
w[0]=[1,1,1,1]; w[0]/=2
w[1]=[1,-1,0,0]; w[1]/=np.sqrt(2)
w[2]=[1,1,-2,0]; w[2]/=np.sqrt(6)
w[3]=[1,1,1,-3]; w[3]/=np.sqrt(12)

def nd(g): return 1 if g==3 else 0

# Swapped partition
gen = np.zeros((4,4),dtype=int)
for g2 in range(4):
    for g3 in range(4):
        d2,d3=nd(g2),nd(g3)
        if d2==1 and d3==0: gen[g2,g3]=0
        elif d2==0 and d3==0: gen[g2,g3]=1
        else: gen[g2,g3]=2

Pi = np.zeros((3,16))
for g2 in range(4):
    for g3 in range(4):
        Pi[gen[g2,g3], g2*4+g3] = 1.0

print("ALL 16 eigenmode projections onto generation space:")
print(f"{'Mode':>8} {'lambda':>6} {'p_Gen1':>10} {'p_Gen2':>10} {'p_Gen3':>10} {'|p|':>8}")
print("-"*60)

PiV = {}
for k in range(4):
    for l in range(4):
        lam = (0 if k==0 else 4)+(0 if l==0 else 4)
        V=np.outer(w[k],w[l]).flatten()
        p=Pi@V
        norm=np.linalg.norm(p)
        PiV[(k,l)]=p
        nz = " *" if norm>1e-8 and lam>0 else ""
        print(f"  V_{k}{l}  {lam:6d} {p[0]:10.4f} {p[1]:10.4f} {p[2]:10.4f} {norm:8.4f}{nz}")

# Check h1 perturbation decomposition
print("\n\nPerturbation h1(g2,g3) = (nd(g2)-nd(g3))*(4-nd(g2)-nd(g3)):")
print(f"{'(g2,g3)':>10} {'nd2':>4} {'nd3':>4} {'h1':>6}")
for g2 in range(4):
    for g3 in range(4):
        d2,d3=nd(g2),nd(g3)
        h1=(d2-d3)*(4-d2-d3)
        if abs(h1)>0:
            print(f"  ({g2},{g3})    {d2:4d} {d3:4d} {h1:6.0f}")

print("\n\nDecomposition of h1 into eigenmodes:")
for k in range(4):
    for l in range(4):
        V=np.outer(w[k],w[l])
        c=0.0
        for g2 in range(4):
            for g3 in range(4):
                d2,d3=nd(g2),nd(g3)
                h1=(d2-d3)*(4-d2-d3)
                c+=h1*V[g2,g3]
        if abs(c)>1e-8:
            p=PiV[(k,l)]
            lam=(0 if k==0 else 4)+(0 if l==0 else 4)
            print(f"  h1 . V_{k}{l} = {c:+.4f}  lambda={lam}  PiV=({p[0]:+.4f},{p[1]:+.4f},{p[2]:+.4f})  |PiV|={np.linalg.norm(p):.4f}")

# Also try second perturbation: position-weight
print("\n\nAlternative perturbation h2(g2,g3) = nd(g2)*w3(g2) - nd(g3)*w3(g3):")
# This is asymmetric and may excite different modes
for k in range(4):
    for l in range(4):
        V=np.outer(w[k],w[l])
        c=0.0
        for g2 in range(4):
            for g3 in range(4):
                h2 = nd(g2)*(1 if g2==3 else 0) - nd(g3)*(1 if g3==3 else 0)
                c+=h2*V[g2,g3]
        if abs(c)>1e-8:
            p=PiV[(k,l)]
            lam=(0 if k==0 else 4)+(0 if l==0 else 4)
            print(f"  h2 . V_{k}{l} = {c:+.4f}  lambda={lam}  PiV=({p[0]:+.4f},{p[1]:+.4f},{p[2]:+.4f})")

# Try general asymmetric IC: A0(g2,g3) depends on g2 differently from g3
print("\n\nGeneral asymmetric IC: A0(g2,g3) = alpha^(kappa*(4-nd(g2))) * (4-nd(g3)):")
# This breaks the g2<->g3 symmetry
print("Testing: which modes get excited by position-asymmetric ICs")
for ic_type in ["pos2_weight", "glyph_asymm", "swap_asymm"]:
    A0 = np.zeros((4,4))
    for g2 in range(4):
        for g3 in range(4):
            if ic_type == "pos2_weight":
                # Weight position 2 differently
                A0[g2,g3] = (4-nd(g2)) * (4-2*nd(g3))
            elif ic_type == "glyph_asymm":
                # Different glyphs have different amplitudes
                A0[g2,g3] = (4-nd(g2)-nd(g3)) + 0.5*(g2-g3)
            elif ic_type == "swap_asymm":
                # Explicitly break g2<->g3
                A0[g2,g3] = (4-nd(g2))**2 * (4-nd(g3))
    
    print(f"\n  IC type: {ic_type}")
    active = []
    for k in range(4):
        for l in range(4):
            V=np.outer(w[k],w[l])
            c=np.sum(A0*V)
            if abs(c)>1e-8:
                p=PiV[(k,l)]
                lam=(0 if k==0 else 4)+(0 if l==0 else 4)
                active.append((k,l,c,lam,p))
                print(f"    c_{k}{l} = {c:+8.4f}  lambda={lam}  PiV=({p[0]:+.4f},{p[1]:+.4f},{p[2]:+.4f})")
    
    # Check rank in generation space (excluding zero mode)
    nonzero_projections = [a[4] for a in active if a[3]>0 and np.linalg.norm(a[4])>1e-8]
    if len(nonzero_projections)>=2:
        M=np.column_stack(nonzero_projections)
        print(f"    Rank of projections (excl. zero mode) = {np.linalg.matrix_rank(M, tol=1e-6)}")
