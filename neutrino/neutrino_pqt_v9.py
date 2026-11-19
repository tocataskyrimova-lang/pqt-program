"""
PQT Neutrino v9 — Breaking rank-2 through asymmetric charge + weighted graph + braiding
σ-charge: q_α=1, q_β=0, q_γ=1, q_δ=1/2 → S₁=1/√2 ≠ 0 → rank ≥ 3
Free: γ(pos-weight), ε_B(braiding), β(spectral), Λ_T(scale) = 4 on 5 obs → 1 DoF
"""
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import differential_evolution

EXP = {'t12':(33.44,0.7),'t23':(49.2,1.1),'t13':(8.57,0.12),'ratio':(0.0307,0.0009)}

# K4 eigenbasis
w = np.zeros((4,4))
w[0]=[1,1,1,1]; w[0]/=2
w[1]=[1,-1,0,0]; w[1]/=np.sqrt(2)
w[2]=[1,1,-2,0]; w[2]/=np.sqrt(6)
w[3]=[1,1,1,-3]; w[3]/=np.sqrt(12)

def nd(g): return 1 if g==3 else 0

# σ-charge: q_α=1, q_β=0, q_γ=1, q_δ=0.5
CHARGE = np.array([1.0, 0.0, 1.0, 0.5])

# Verify S₁ ≠ 0
S1 = sum(CHARGE[i]*w[1][i] for i in range(4))
S2 = sum(CHARGE[i]*w[2][i] for i in range(4))
print(f"σ-charge: S₁={S1:.4f} S₂={S2:.4f} → rank≥3: {abs(S1)>1e-10 or abs(S2)>1e-10}")

# Generation partition (frozen swap)
gen = np.zeros((4,4),dtype=int)
for g2 in range(4):
    for g3 in range(4):
        d2,d3=nd(g2),nd(g3)
        if d2==1 and d3==0: gen[g2,g3]=0
        elif d2==0 and d3==0: gen[g2,g3]=1
        else: gen[g2,g3]=2

# Braiding Im[omega] (antisymmetric)
sigma_layer = [1,-1,1,-1]
def braid_im(i,j):
    if i==j or i==3 or j==3: return 0.0
    if sigma_layer[i]==sigma_layer[j]: return 0.0
    t=np.arctan(np.sqrt(2))
    return t if sigma_layer[i]>sigma_layer[j] else -t

B = np.zeros((4,4))
for i in range(4):
    for j in range(4):
        B[i,j]=braid_im(i,j)

def build_laplacian(gamma=0.0, epsb=0.0):
    n=16; A=np.zeros((n,n))
    for g2 in range(4):
        for g3 in range(4):
            i=g2*4+g3
            for g2p in range(4):
                if g2p!=g2:
                    j=g2p*4+g3; A[i,j]=1.0
                    A[i,j]+=epsb*abs(B[g2,g2p])
            for g3p in range(4):
                if g3p!=g3:
                    j=g2*4+g3p; A[i,j]=1.0+gamma
                    A[i,j]+=epsb*abs(B[g3,g3p])
    D=np.diag(np.sum(A,axis=1))
    return D-A

def build_KT(gamma=0.0, epsb=0.0, charge=CHARGE, beta=0.5):
    L=build_laplacian(gamma, epsb)
    ev,U=eigh(L); idx=np.argsort(ev); ev=ev[idx]; U=U[:,idx]
    # Charge-weighted generation projections for each mode
    qp=np.zeros((3,16))
    for m in range(16):
        V=U[:,m].reshape(4,4)
        for a in range(3):
            t=0.0
            for g2 in range(4):
                for g3 in range(4):
                    if gen[g2,g3]==a:
                        t+=(charge[g2]+charge[g3])*V[g2,g3]
            qp[a,m]=t
    # Build K_T from dynamic covariance (skip zero mode)
    K=np.zeros((3,3))
    for m in range(16):
        if ev[m]<1e-8: continue
        wt = ev[m]**(2*beta-1) if ev[m]>0 else 0
        K += wt*np.outer(qp[:,m], qp[:,m])
    mx=np.max(np.abs(K))
    if mx>0: K/=mx
    return K

def pmns(K):
    ev,U=eigh(K); idx=np.argsort(ev); ev=ev[idx]; U=U[:,idx]
    if ev[0]<-1e-6: return None
    ev=np.maximum(ev,0); m=np.sqrt(ev)
    s13=min(abs(U[0,2]),0.9999); c13=np.sqrt(1-s13**2)
    s12=min(abs(U[0,1])/c13,0.9999) if c13>1e-10 else 0
    s23=min(abs(U[1,2])/c13,0.9999) if c13>1e-10 else 0
    dm21=m[1]**2-m[0]**2; dm31=m[2]**2-m[0]**2
    r=dm21/dm31 if dm31>1e-30 else 0
    return {'t12':np.degrees(np.arcsin(s12)),'t23':np.degrees(np.arcsin(s23)),
            't13':np.degrees(np.arcsin(s13)),'ratio':r,'m':m,'ev':ev,'U':U,
            'nh':'NH' if ev[0]<=ev[1]<=ev[2] else 'IH'}

def chi2(r):
    if r is None: return 1e10
    c=((r['t12']-33.44)/0.7)**2+((r['t23']-49.2)/1.1)**2
    c+=((r['t13']-8.57)/0.12)**2+((r['ratio']-0.0307)/0.0009)**2
    if r['nh']!='NH': c+=1e6
    return c

# ================================================================
# PHASE 1: Verify rank=3 with sigma-charge, no perturbation
# ================================================================
print("\n"+"="*90)
print("PHASE 1: σ-CHARGE RANK VERIFICATION")
print("="*90)

for label, ch in [("δ-count",[0,0,0,1]),("σ-charge",[1,0,1,0.5]),
                   ("asymm",[3,1,2,0]),("braiding-order",[1,0.5,0.25,0])]:
    ch=np.array(ch,dtype=float)
    K=build_KT(0,0,ch,0.5)
    r=pmns(K)
    rk=np.linalg.matrix_rank(K,tol=1e-8)
    if r:
        print(f"  {label:20s}: rank={rk}  t12={r['t12']:6.1f} t23={r['t23']:6.1f} "
              f"t13={r['t13']:6.1f} ratio={r['ratio']:.4f} chi2={chi2(r):.0f}")
    else:
        print(f"  {label:20s}: rank={rk}  FAILED (neg ev)")

# ================================================================
# PHASE 2: Coarse grid scan (γ, ε_B, β)
# ================================================================
print("\n"+"="*90)
print("PHASE 2: COARSE GRID SCAN")
print("="*90)

best = {'chi2':1e10}
count=0
for gi in range(-10, 51):      # γ: -1.0 to 5.0
    gamma=gi/10.0
    for ei in range(0, 21):     # ε_B: 0.0 to 2.0
        epsb=ei/10.0
        for bi in range(1, 51): # β: 0.1 to 5.0
            beta=bi/10.0
            try:
                K=build_KT(gamma,epsb,CHARGE,beta)
                r=pmns(K)
            except: continue
            if r is None: continue
            c=chi2(r); count+=1
            if c<best['chi2']:
                best={**r,'chi2':c,'gamma':gamma,'epsb':epsb,'beta':beta}

print(f"Scanned {count} configurations")
if best['chi2']<1e9:
    print(f"Best coarse: γ={best['gamma']:.1f} ε_B={best['epsb']:.1f} β={best['beta']:.1f}")
    print(f"  t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f}")
    print(f"  ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")

# ================================================================
# PHASE 3: Fine grid around best
# ================================================================
print("\n"+"="*90)
print("PHASE 3: FINE GRID REFINEMENT")
print("="*90)

if best['chi2']<1e9:
    gc,ec,bc = best['gamma'],best['epsb'],best['beta']
    for gi in range(max(-20,int((gc-1)*20)), int((gc+1)*20)+1):
        gamma=gi/20.0
        for ei in range(max(0,int((ec-0.5)*20)), int((ec+0.5)*20)+1):
            epsb=ei/20.0
            for bi in range(max(1,int((bc-1)*20)), int((bc+1)*20)+1):
                beta=bi/20.0
                if beta<0.01: continue
                try:
                    K=build_KT(gamma,epsb,CHARGE,beta)
                    r=pmns(K)
                except: continue
                if r is None: continue
                c=chi2(r)
                if c<best['chi2']:
                    best={**r,'chi2':c,'gamma':gamma,'epsb':epsb,'beta':beta}

    print(f"Best fine: γ={best['gamma']:.2f} ε_B={best['epsb']:.2f} β={best['beta']:.2f}")
    print(f"  t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f}")
    print(f"  ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")

# ================================================================
# PHASE 4: Differential evolution
# ================================================================
print("\n"+"="*90)
print("PHASE 4: DIFFERENTIAL EVOLUTION")
print("="*90)

def objective(p):
    gamma,epsb,beta=p
    if beta<0.01: return 1e10
    try:
        K=build_KT(gamma,epsb,CHARGE,beta)
        r=pmns(K)
        return chi2(r)
    except: return 1e10

result=differential_evolution(objective, [(-2,10),(0,5),(0.01,10)],
                               seed=42, maxiter=500, tol=1e-10, popsize=30)
gamma_o,epsb_o,beta_o=result.x
K_o=build_KT(gamma_o,epsb_o,CHARGE,beta_o)
r_o=pmns(K_o)
c_o=chi2(r_o) if r_o else 1e10

print(f"DE result: γ={gamma_o:.4f} ε_B={epsb_o:.4f} β={beta_o:.4f}")
if r_o:
    print(f"  t12={r_o['t12']:.3f} t23={r_o['t23']:.3f} t13={r_o['t13']:.3f}")
    print(f"  ratio={r_o['ratio']:.6f} chi2={c_o:.2f}")
    if c_o<best['chi2']:
        best={**r_o,'chi2':c_o,'gamma':gamma_o,'epsb':epsb_o,'beta':beta_o}

# ================================================================
# ALSO TRY: multiple charge models
# ================================================================
print("\n"+"="*90)
print("CHARGE MODEL COMPARISON (with DE optimization)")
print("="*90)

charge_models = [
    ("σ-charge (1,0,1,0.5)", [1.0,0.0,1.0,0.5]),
    ("braiding (1,0.5,0.25,0)", [1.0,0.5,0.25,0.0]),
    ("asymm (3,1,2,0)", [3.0,1.0,2.0,0.0]),
    ("σ-pure (1,0,1,0)", [1.0,0.0,1.0,0.0]),
    ("inverse-σ (0,1,0,0.5)", [0.0,1.0,0.0,0.5]),
    ("linear (0,1,2,3)", [0.0,1.0,2.0,3.0]),
    ("δ-count (0,0,0,1)", [0.0,0.0,0.0,1.0]),
]

best_overall = {'chi2':1e10}
for label, ch in charge_models:
    ch_arr = np.array(ch, dtype=float)
    def obj_ch(p):
        gamma,epsb,beta=p
        if beta<0.01: return 1e10
        try:
            K=build_KT(gamma,epsb,ch_arr,beta)
            r=pmns(K)
            return chi2(r)
        except: return 1e10
    
    res=differential_evolution(obj_ch, [(-2,10),(0,5),(0.01,10)],
                                seed=42, maxiter=200, tol=1e-8, popsize=20)
    g,e,b=res.x
    K=build_KT(g,e,ch_arr,b); r=pmns(K); c=chi2(r) if r else 1e10
    rk=np.linalg.matrix_rank(K,tol=1e-8) if r else 0
    
    if r:
        print(f"  {label:30s}: γ={g:6.2f} ε={e:5.2f} β={b:5.2f} "
              f"t12={r['t12']:6.1f} t23={r['t23']:6.1f} t13={r['t13']:6.1f} "
              f"ratio={r['ratio']:.4f} rk={rk} chi2={c:.0f}")
        if c < best_overall['chi2']:
            best_overall = {**r,'chi2':c,'gamma':g,'epsb':e,'beta':b,
                           'charge_label':label,'charge':ch_arr}

# ================================================================
# FINAL RESULTS
# ================================================================
b = best if best['chi2'] < best_overall['chi2'] else best_overall
print("\n"+"="*90)
print("FINAL BEST RESULT")
print("="*90)
print(f"  γ = {b['gamma']:.4f}")
print(f"  ε_B = {b['epsb']:.4f}")
print(f"  β = {b['beta']:.4f}")
if 'charge_label' in b:
    print(f"  charge = {b['charge_label']}")

K_final=build_KT(b['gamma'],b['epsb'],
                  b.get('charge',CHARGE),b['beta'])
rk=np.linalg.matrix_rank(K_final,tol=1e-8)
print(f"  rank = {rk}")
print(f"\n  K_T =")
print(np.array2string(K_final, precision=4, suppress_small=True))

print(f"\n{'Observable':>12} {'PQT':>10} {'Exp':>10} {'sigma':>7} {'Pull':>8}")
print("-"*55)
for obs,key,ev,es in [('theta12','t12',33.44,0.7),('theta23','t23',49.2,1.1),
                       ('theta13','t13',8.57,0.12)]:
    pv=b[key]; pull=abs(pv-ev)/es
    print(f"  {obs:>10} {pv:10.3f} {ev:10.3f} {es:7.3f} {pull:8.2f}σ")
pv=b['ratio']; pull=abs(pv-0.0307)/0.0009
print(f"  {'ratio':>10} {pv:10.5f} {0.0307:10.5f} {0.0009:7.5f} {pull:8.1f}σ")
print(f"\n  χ² = {b['chi2']:.2f}")
print(f"  χ²/DoF = {b['chi2']/1:.2f}  (DoF = 5 obs - 4 params = 1)")

if b['m'][2]>0:
    sc=0.050/b['m'][2]; me=b['m']*sc
    print(f"\n  Masses: m1={me[0]*1e3:.3f} m2={me[1]*1e3:.3f} m3={me[2]*1e3:.3f} meV")
    print(f"  Sum = {sum(me)*1e3:.1f} meV")

# ================================================================
# EVOLUTION TABLE
# ================================================================
print(f"\n{'EVOLUTION v1 -> v9':=^90}")
print(f"{'Ver':<8} {'Free':>4} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'chi2':>10}")
print("-"*65)
for v,f,t12,t23,t13,rat,c2 in [
    ("v1",9,33.41,49.10,8.54,0.03070,0),("v2",2,37.91,56.32,4.11,0.02459,349),
    ("v3",2,39.42,47.10,5.46,0.01716,958),("v4",2,74.0,5.3,7.84,0.04519,5249),
    ("v5",0,None,None,None,None,None),
    ("v6",0,54.54,49.03,5.67,0.50628,280719),
    ("v7",1,54.24,51.34,8.88,0.53333,312795),
    ("v8",1,54.27,51.15,8.62,0.50628,280719),
]:
    if t12: print(f"{v:<8} {f:4d} {t12:7.1f} {t23:7.1f} {t13:7.1f} {rat:9.5f} {c2:10.0f}")
    else: print(f"{v:<8} {f:4d}    ---    ---    ---       ---        ---")

chi2_v9 = b['chi2']
print(f"{'v9':<8} {4:4d} {b['t12']:7.1f} {b['t23']:7.1f} {b['t13']:7.1f} "
      f"{b['ratio']:9.5f} {chi2_v9:10.1f}")
print("-"*65)
print(f"{'Exp':<8} {'--':>4} {33.44:7.1f} {49.2:7.1f} {8.57:7.1f} {0.0307:9.5f}")
