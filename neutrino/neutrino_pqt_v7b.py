"""PQT Neutrino v7b — Clean results extraction"""
import numpy as np
from scipy.linalg import eigh

EXP = {'t12':(33.44,0.7),'t23':(49.2,1.1),'t13':(8.57,0.12),'ratio':(0.0307,0.0009)}

w = np.zeros((4,4))
w[0]=[1,1,1,1]; w[0]/=2
w[1]=[1,-1,0,0]; w[1]/=np.sqrt(2)
w[2]=[1,1,-2,0]; w[2]/=np.sqrt(6)
w[3]=[1,1,1,-3]; w[3]/=np.sqrt(12)

def nd(g): return 1 if g==3 else 0

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

PiV = {}
for k in range(4):
    for l in range(4):
        lam = (0 if k==0 else 4)+(0 if l==0 else 4)
        if lam==0: continue
        V=np.outer(w[k],w[l]).flatten(); p=Pi@V
        if np.linalg.norm(p)>1e-10: PiV[(k,l)]=p

def get_c(kappa):
    c={}
    for k in range(4):
        for l in range(4):
            v=0.0
            for g2 in range(4):
                for g3 in range(4):
                    s=nd(g2)+nd(g3); f=(4-s)**kappa if (4-s)>0 else 0
                    v+=f*w[k][g2]*w[l][g3]
            c[(k,l)]=v
    return c

def build_KT(kappa):
    c=get_c(kappa); K=np.zeros((3,3))
    for (k,l),p in PiV.items():
        K += 0.5*c[(k,l)]**2*np.outer(p,p)
    return K

def pmns(K):
    ev,U=eigh(K); idx=np.argsort(ev); ev=ev[idx]; U=U[:,idx]
    if ev[0]<-1e-8: return None
    ev=np.maximum(ev,0); m=np.sqrt(ev)
    s13=min(abs(U[0,2]),0.9999); c13=np.sqrt(1-s13**2)
    s12=min(abs(U[0,1])/c13,0.9999) if c13>1e-10 else 0
    s23=min(abs(U[1,2])/c13,0.9999) if c13>1e-10 else 0
    return {'t12':np.degrees(np.arcsin(s12)),'t23':np.degrees(np.arcsin(s23)),
            't13':np.degrees(np.arcsin(s13)),'ratio':(ev[1]-ev[0])/(ev[2]-ev[0]) if ev[2]-ev[0]>0 else 0,
            'm':m,'ev':ev,'U':U,'nh':'NH' if ev[0]<ev[1]<ev[2] else 'IH'}

def chi2(r):
    return ((r['t12']-33.44)/0.7)**2+((r['t23']-49.2)/1.1)**2+((r['t13']-8.57)/0.12)**2+((r['ratio']-0.0307)/0.0009)**2

print("="*85)
print("PQT NEUTRINO v7 — COMPLETE RESULTS")
print("="*85)
print(f"\n{'kappa':>8} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'chi2':>10} {'rank':>4} {'m1/m3':>8}")
print("-"*75)

best = None
for ki in range(50, 100001):
    kap = ki/1000.0
    K=build_KT(kap); r=pmns(K)
    if r is None: continue
    c=chi2(r); rk=int(np.sum(r['ev']>1e-8*np.max(r['ev'])))
    m1m3=r['m'][0]/r['m'][2] if r['m'][2]>0 else 0
    if best is None or c<best[1]: best=(kap,c,r,rk)
    if ki%2000==0:
        print(f"{kap:8.2f} {r['t12']:7.2f} {r['t23']:7.2f} {r['t13']:7.2f} "
              f"{r['ratio']:9.5f} {c:10.1f} {rk:4d} {m1m3:8.5f}")

# KEY KAPPA VALUES
print(f"\n{'KEY VALUES':=^85}")
print(f"{'kappa':>8} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'chi2':>10}")
print("-"*60)
for kap in [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 10.0, 50.0, 1000.0]:
    K=build_KT(kap); r=pmns(K)
    if r: print(f"{kap:8.1f} {r['t12']:7.2f} {r['t23']:7.2f} {r['t13']:7.2f} "
                f"{r['ratio']:9.5f} {chi2(r):10.1f}")

# ASYMPTOTIC LIMIT
print(f"\n{'ASYMPTOTIC LIMIT (kappa -> inf)':=^85}")
K_inf = build_KT(1000); r_inf = pmns(K_inf)
if r_inf:
    print(f"  t12 = {r_inf['t12']:.4f} deg  (exp: 33.44)")
    print(f"  t23 = {r_inf['t23']:.4f} deg  (exp: 49.20)")
    print(f"  t13 = {r_inf['t13']:.4f} deg  (exp: 8.57)")
    print(f"  ratio = {r_inf['ratio']:.6f}  (exp: 0.0307)")
    print(f"  chi2 = {chi2(r_inf):.1f}")
    p12=abs(r_inf['t12']-33.44)/0.7; p23=abs(r_inf['t23']-49.2)/1.1
    p13=abs(r_inf['t13']-8.57)/0.12; pr=abs(r_inf['ratio']-0.0307)/0.0009
    print(f"\n  Pulls: t12={p12:.1f}s  t23={p23:.1f}s  t13={p13:.1f}s  ratio={pr:.1f}s")
    sc=0.050/r_inf['m'][2] if r_inf['m'][2]>0 else 1
    me=r_inf['m']*sc
    print(f"\n  Masses: m1={me[0]*1e3:.3f} m2={me[1]*1e3:.3f} m3={me[2]*1e3:.3f} meV")
    print(f"  Sum = {sum(me)*1e3:.1f} meV")

# EVOLUTION TABLE
print(f"\n{'EVOLUTION v1 -> v7':=^85}")
print(f"{'Ver':<6} {'Free':>4} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'chi2':>9} {'Key result'}")
print("-"*85)
for v,f,t12,t23,t13,rat,c2,note in [
    ("v1",9,33.41,49.10,8.54,0.03070,0,"Overfit (9>4)"),
    ("v2",2,37.91,56.32,4.11,0.02459,349,"eps13=0"),
    ("v3",2,39.42,47.10,5.46,0.01716,958,"cascade eps13"),
    ("v4",2,74.0,5.3,7.84,0.04519,5249,"partition trade-off"),
    ("v5",0,None,None,None,None,None,"FAILED (neg ev)"),
    ("v6",0,54.54,49.03,5.67,0.50628,280719,"t23=49.0 (0.2s)!"),
]:
    if t12: print(f"{v:<6} {f:4d} {t12:7.1f} {t23:7.1f} {t13:7.1f} {rat:9.5f} {c2:9.0f} {note}")
    else: print(f"{v:<6} {f:4d}    ---    ---    ---       ---       --- {note}")

if r_inf:
    print(f"{'v7-inf':<6} {1:4d} {r_inf['t12']:7.1f} {r_inf['t23']:7.1f} {r_inf['t13']:7.1f} "
          f"{r_inf['ratio']:9.5f} {chi2(r_inf):9.0f} t13=8.88 (2.6s)!")
print("-"*85)
print(f"{'Exp':<6} {'--':>4} {33.44:7.1f} {49.2:7.1f} {8.57:7.1f} {0.0307:9.5f}")
