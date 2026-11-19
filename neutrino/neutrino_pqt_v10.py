"""
PQT Neutrino v10 — Position-aware charge: q_η(g2,g3) = (1+η)·q_σ(g2) + (1-η)·q_σ(g3)
Key: η≠0 separates Gen1(δ@pos2) from Gen3(δ@pos3) in charge space
     → resolves θ₂₃ ↔ θ₁₂ trade-off from v9
Free: κ, η, γ, β = 4 params on 5 observables → 1 DoF
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

# σ-pure charge: q_σ(α)=1, q_σ(β)=0, q_σ(γ)=1, q_σ(δ)=0
Q_SIGMA = np.array([1.0, 0.0, 1.0, 0.0])

# Generation (frozen swap)
gen = np.zeros((4,4),dtype=int)
for g2 in range(4):
    for g3 in range(4):
        d2,d3=nd(g2),nd(g3)
        if d2==1 and d3==0: gen[g2,g3]=0
        elif d2==0 and d3==0: gen[g2,g3]=1
        else: gen[g2,g3]=2

# ============================================================
# POSITION-AWARE CHARGE
# ============================================================
def pos_charge(g2, g3, eta):
    return (1+eta)*Q_SIGMA[g2] + (1-eta)*Q_SIGMA[g3]

# Diagnostic
print("="*80)
print("POSITION-AWARE CHARGE DIAGNOSTIC")
print("="*80)
for eta in [0.0, 0.2, 0.5, 0.8, 1.0]:
    avg=[0,0,0]; cnt=[0,0,0]
    for g2 in range(4):
        for g3 in range(4):
            a=gen[g2,g3]; avg[a]+=pos_charge(g2,g3,eta); cnt[a]+=1
    avg=[avg[i]/cnt[i] for i in range(3)]
    print(f"  eta={eta:.1f}: Gen1={avg[0]:.3f} Gen2={avg[1]:.3f} Gen3={avg[2]:.3f}"
          f"  |Gen1-Gen3|={abs(avg[0]-avg[2]):.3f}")

# ============================================================
# BUILD K_T^eff (eigenmode decomposition + position charge)
# ============================================================
def build_KT(kappa, gamma_w, eta, beta):
    # Eigenvalues of weighted K4□K4
    eig2 = [0, 4, 4, 4]
    eig3 = [0, 4*(1+gamma_w), 4*(1+gamma_w), 4*(1+gamma_w)]
    
    K = np.zeros((3,3))
    for k in range(4):
        for l in range(4):
            lam = eig2[k] + eig3[l]
            if lam < 1e-8: continue
            
            # Initial condition coefficient
            c_kl = 0.0
            for g2 in range(4):
                for g3 in range(4):
                    s = nd(g2)+nd(g3)
                    c_kl += (4-s)**kappa * w[k][g2] * w[l][g3]
            
            # Charge-weighted projection
            proj = np.zeros(3)
            for g2 in range(4):
                for g3 in range(4):
                    a = gen[g2,g3]
                    q = pos_charge(g2, g3, eta)
                    proj[a] += q * w[k][g2] * w[l][g3]
            
            # Spectral weight
            wt = lam**(2*beta - 1) * c_kl**2
            K += wt * np.outer(proj, proj)
    
    mx = np.max(np.abs(K))
    if mx > 0: K /= mx
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

# ============================================================
# PHASE 1: Verify eta effect on theta_23
# ============================================================
print("\n"+"="*80)
print("PHASE 1: eta SWEEP (kappa=2, gamma=0, beta=1.5)")
print("="*80)
print(f"{'eta':>6} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'rank':>4} {'chi2':>10}")
print("-"*60)
for ei in range(0, 21):
    eta=ei/10.0
    K=build_KT(2.0, 0.0, eta, 1.5)
    r=pmns(K)
    if r:
        rk=np.linalg.matrix_rank(K, tol=1e-8)
        print(f"{eta:6.2f} {r['t12']:7.1f} {r['t23']:7.1f} {r['t13']:7.1f} "
              f"{r['ratio']:9.5f} {rk:4d} {chi2(r):10.1f}")

# ============================================================
# PHASE 2: Coarse 4D grid scan
# ============================================================
print("\n"+"="*80)
print("PHASE 2: COARSE 4D GRID SCAN")
print("="*80)

best = {'chi2':1e10}
count = 0

for ki in range(5, 51, 5):       # kappa: 0.5 to 5.0
    kappa = ki/10.0
    for ei in range(0, 20):       # eta: 0.0 to 1.9
        eta = ei/10.0
        for gi in range(-10, 21, 2): # gamma: -1.0 to 2.0
            gamma = gi/10.0
            for bi in range(2, 41, 2): # beta: 0.2 to 4.0
                beta = bi/10.0
                count += 1
                try:
                    K = build_KT(kappa, gamma, eta, beta)
                    r = pmns(K)
                except: continue
                if r is None: continue
                c = chi2(r)
                if c < best['chi2']:
                    best = {**r, 'chi2':c, 'kappa':kappa, 'eta':eta,
                            'gamma':gamma, 'beta':beta}

print(f"Scanned {count} points")
if best['chi2']<1e9:
    print(f"Best: k={best['kappa']:.1f} eta={best['eta']:.1f} "
          f"g={best['gamma']:.1f} b={best['beta']:.1f}")
    print(f"  t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f} "
          f"ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")

# ============================================================
# PHASE 3: Fine grid around best
# ============================================================
print("\n"+"="*80)
print("PHASE 3: FINE GRID REFINEMENT")
print("="*80)

if best['chi2']<1e9:
    kc,ec,gc,bc = best['kappa'],best['eta'],best['gamma'],best['beta']
    for ki in range(max(1,int((kc-1)*20)), int((kc+1)*20)+1):
        kappa=ki/20.0
        for ei in range(max(0,int((ec-0.5)*20)), int((ec+0.5)*20)+1):
            eta=ei/20.0
            for gi in range(int((gc-0.5)*20), int((gc+0.5)*20)+1):
                gamma=gi/20.0
                for bi in range(max(1,int((bc-0.5)*20)), int((bc+0.5)*20)+1):
                    beta=bi/20.0
                    if beta<0.05: continue
                    try:
                        K=build_KT(kappa,gamma,eta,beta)
                        r=pmns(K)
                    except: continue
                    if r is None: continue
                    c=chi2(r)
                    if c<best['chi2']:
                        best={**r,'chi2':c,'kappa':kappa,'eta':eta,
                              'gamma':gamma,'beta':beta}

    print(f"Best fine: k={best['kappa']:.2f} eta={best['eta']:.2f} "
          f"g={best['gamma']:.2f} b={best['beta']:.2f}")
    print(f"  t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f} "
          f"ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")

# ============================================================
# PHASE 4: Differential evolution
# ============================================================
print("\n"+"="*80)
print("PHASE 4: DIFFERENTIAL EVOLUTION")
print("="*80)

def objective(p):
    kappa,eta,gamma,beta=p
    if beta<0.05 or kappa<0.1: return 1e10
    try:
        K=build_KT(kappa,gamma,eta,beta)
        r=pmns(K)
        return chi2(r)
    except: return 1e10

res=differential_evolution(objective, [(0.1,10),(0,2),(-2,5),(0.05,5)],
                            seed=42, maxiter=1000, tol=1e-12, popsize=40,
                            mutation=(0.5,1.5))
ko,eo,go,bo=res.x
K_o=build_KT(ko,go,eo,bo); r_o=pmns(K_o); c_o=chi2(r_o) if r_o else 1e10
print(f"DE: k={ko:.4f} eta={eo:.4f} g={go:.4f} b={bo:.4f}")
if r_o:
    print(f"  t12={r_o['t12']:.3f} t23={r_o['t23']:.3f} t13={r_o['t13']:.3f} "
          f"ratio={r_o['ratio']:.6f} chi2={c_o:.2f}")
    if c_o<best['chi2']:
        best={**r_o,'chi2':c_o,'kappa':ko,'eta':eo,'gamma':go,'beta':bo}

# Also try with wider bounds
res2=differential_evolution(objective, [(0.1,20),(0,3),(-3,10),(0.05,10)],
                             seed=123, maxiter=1000, tol=1e-12, popsize=40)
ko2,eo2,go2,bo2=res2.x
K_o2=build_KT(ko2,go2,eo2,bo2); r_o2=pmns(K_o2); c_o2=chi2(r_o2) if r_o2 else 1e10
print(f"DE2: k={ko2:.4f} eta={eo2:.4f} g={go2:.4f} b={bo2:.4f}")
if r_o2:
    print(f"  t12={r_o2['t12']:.3f} t23={r_o2['t23']:.3f} t13={r_o2['t13']:.3f} "
          f"ratio={r_o2['ratio']:.6f} chi2={c_o2:.2f}")
    if c_o2<best['chi2']:
        best={**r_o2,'chi2':c_o2,'kappa':ko2,'eta':eo2,'gamma':go2,'beta':bo2}

# ============================================================
# FINAL RESULTS
# ============================================================
b=best
print("\n"+"="*80)
print("FINAL BEST RESULT")
print("="*80)
print(f"\n  kappa = {b['kappa']:.4f}")
print(f"  eta   = {b['eta']:.4f}")
print(f"  gamma = {b['gamma']:.4f}")
print(f"  beta  = {b['beta']:.4f}")

K_f=build_KT(b['kappa'],b['gamma'],b['eta'],b['beta'])
rk=np.linalg.matrix_rank(K_f,tol=1e-8)
print(f"  rank  = {rk}")
print(f"\n  K_T =")
print(np.array2string(K_f, precision=4, suppress_small=True))
print(f"  Eigenvalues: {b['ev']}")

print(f"\n{'Observable':>12} {'PQT':>10} {'Exp':>10} {'+/-':>7} {'Pull':>8}")
print("-"*55)
for obs,key,ev,es in [('theta12','t12',33.44,0.7),('theta23','t23',49.2,1.1),
                       ('theta13','t13',8.57,0.12)]:
    pv=b[key]; print(f"  {obs:>10} {pv:10.3f} {ev:10.3f} {es:7.3f} {abs(pv-ev)/es:8.2f}s")
pv=b['ratio']
print(f"  {'ratio':>10} {pv:10.5f} {0.0307:10.5f} {0.0009:7.5f} {abs(pv-0.0307)/0.0009:8.1f}s")
print(f"\n  chi2 = {b['chi2']:.2f}")
print(f"  chi2/DoF = {b['chi2']/1:.2f} (DoF=5-4=1)")

if b['m'][2]>0:
    sc=0.050/b['m'][2]; me=b['m']*sc
    print(f"\n  Masses: m1={me[0]*1e3:.3f} m2={me[1]*1e3:.3f} m3={me[2]*1e3:.3f} meV")
    print(f"  Sum = {sum(me)*1e3:.1f} meV {'OK' if sum(me)*1e3<120 else 'BAD'}")

print(f"\n  U_PMNS:")
print(np.array2string(b['U'], precision=4, suppress_small=True))

# ============================================================
# SENSITIVITY: each parameter independently
# ============================================================
print(f"\n{'SENSITIVITY ANALYSIS':=^80}")
params = [('kappa',b['kappa']),('eta',b['eta']),('gamma',b['gamma']),('beta',b['beta'])]
for pname, pval in params:
    print(f"\n  --- {pname} sensitivity (others fixed) ---")
    print(f"  {'val':>8} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'chi2':>10}")
    for di in range(-10, 11, 2):
        delta = di/50.0 * max(abs(pval), 0.5)
        pv = pval + delta
        if pname=='kappa': K=build_KT(pv,b['gamma'],b['eta'],b['beta'])
        elif pname=='eta': K=build_KT(b['kappa'],b['gamma'],pv,b['beta'])
        elif pname=='gamma': K=build_KT(b['kappa'],pv,b['eta'],b['beta'])
        else: K=build_KT(b['kappa'],b['gamma'],b['eta'],pv)
        r=pmns(K)
        if r:
            c=chi2(r)
            mk = " <--" if abs(di)<1 else ""
            print(f"  {pv:8.3f} {r['t12']:7.1f} {r['t23']:7.1f} {r['t13']:7.1f} "
                  f"{r['ratio']:9.5f} {c:10.1f}{mk}")

# ============================================================
# EVOLUTION TABLE
# ============================================================
print(f"\n{'EVOLUTION v1 -> v10':=^80}")
print(f"{'Ver':<8} {'Free':>4} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'chi2':>10}")
print("-"*65)
for v,f,t12,t23,t13,rat,c2 in [
    ("v1",9,33.41,49.10,8.54,0.0307,0),
    ("v2",2,37.91,56.32,4.11,0.0246,349),
    ("v6",0,54.54,49.03,5.67,0.5063,280719),
    ("v7",1,54.24,51.34,8.88,0.5333,312795),
    ("v8",1,54.27,51.15,8.62,0.5063,280719),
    ("v9",4,35.19,77.64,8.39,0.0343,693),
]:
    print(f"{v:<8} {f:4d} {t12:7.1f} {t23:7.1f} {t13:7.1f} {rat:9.4f} {c2:10.0f}")

print(f"{'v10':<8} {4:4d} {b['t12']:7.1f} {b['t23']:7.1f} {b['t13']:7.1f} "
      f"{b['ratio']:9.5f} {b['chi2']:10.1f}")
print("-"*65)
print(f"{'Exp':<8} {'--':>4} {33.44:7.1f} {49.2:7.1f} {8.57:7.1f} {0.0307:9.4f}")
