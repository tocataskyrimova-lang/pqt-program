"""PQT Neutrino v4 — Three strategies for theta_13"""
import numpy as np
from scipy.linalg import eigh, eig
from scipy.optimize import minimize_scalar

EXP = {'theta12':(33.44,0.7),'theta23':(49.2,1.1),'theta13':(8.57,0.12),'ratio':(0.0307,0.0009)}
PHI_12=np.pi/4; PHI_23=np.pi/4; PHI_13=np.arctan(np.sqrt(2))

def angles(U, masses):
    s13=min(abs(U[0,2]),1.0); t13=np.degrees(np.arcsin(s13))
    c13=np.sqrt(max(1-s13**2,1e-30))
    s12=min(abs(U[0,1])/c13,1.0) if c13>1e-10 else 0
    s23=min(abs(U[1,2])/c13,1.0) if c13>1e-10 else 0
    t12=np.degrees(np.arcsin(s12)); t23=np.degrees(np.arcsin(s23))
    m=np.sort(masses); dm21=m[1]**2-m[0]**2; dm31=m[2]**2-m[0]**2
    r=dm21/dm31 if dm31>0 else 0; nh='NH' if m[0]<m[1]<m[2] and min(m)>0 else 'IH'
    return {'t12':t12,'t23':t23,'t13':t13,'ratio':r,'m':m,'nh':nh}

def chi2(r):
    c=((r['t12']-EXP['theta12'][0])/EXP['theta12'][1])**2
    c+=((r['t23']-EXP['theta23'][0])/EXP['theta23'][1])**2
    c+=((r['t13']-EXP['theta13'][0])/EXP['theta13'][1])**2
    c+=((r['ratio']-EXP['ratio'][0])/EXP['ratio'][1])**2 if r['ratio']>0 else 1e4
    if r['nh']!='NH': c+=1e4
    return c

def do_hermitian(K):
    ev,U=eigh((K+K.conj().T)/2); idx=np.argsort(ev); ev=ev[idx]; U=U[:,idx]
    if any(e<=0 for e in ev): return None
    return angles(U, ev)

def do_nonhermitian(K):
    ev,VR=eig(K); idx=np.argsort(np.abs(ev)); ev=ev[idx]; VR=VR[:,idx]
    m=np.abs(ev)
    if any(x<=0 for x in m): return None
    return angles(VR, m)

# === STRATEGY 1: Partition 9:3:4 ===
print("="*75)
print("STRATEGY 1: Partition 9:3:4 (eps13=1/4 from Hamming-1)")
print("="*75)
best1={'chi2':1e10}
for kappa in np.arange(0.05,6.0,0.02):
    k=np.array([9,3,4],dtype=float)**kappa; k/=sum(k)
    K=np.diag(k.astype(complex))
    for i,j,e,p in [(0,1,1/3,PHI_12),(0,2,1/4,PHI_13),(1,2,1/4,PHI_23)]:
        v=e*np.sqrt(k[i]*k[j])*np.exp(1j*p); K[i,j]=v; K[j,i]=v.conj()
    r=do_hermitian(K)
    if r and chi2(r)<best1['chi2']:
        best1={**r,'chi2':chi2(r),'kappa':kappa}
b=best1
print(f"  kappa={b['kappa']:.2f} t12={b['t12']:.1f} t23={b['t23']:.1f} t13={b['t13']:.1f} ratio={b['ratio']:.5f} chi2={b['chi2']:.1f} {b['nh']}")

# === STRATEGY 2: Nonlinear alpha ===
print("\n"+"="*75)
print("STRATEGY 2: Original 9:6:1 + nonlinear alpha")
print("="*75)
best2={'chi2':1e10}
for kappa in np.arange(0.1,5.0,0.05):
    for alpha in np.arange(0.0,2.5,0.05):
        k=np.array([9,6,1],dtype=float)**kappa; k/=sum(k)
        K=np.diag(k.astype(complex))
        for i,j,e,p in [(0,1,1/3,PHI_12),(0,2,1/9,PHI_13),(1,2,1.0,PHI_23)]:
            v=e*(k[i]*k[j])**alpha*np.exp(1j*p); K[i,j]=v; K[j,i]=v.conj()
        r=do_hermitian(K)
        if r and chi2(r)<best2['chi2']:
            best2={**r,'chi2':chi2(r),'kappa':kappa,'alpha':alpha}
b=best2
print(f"  kappa={b['kappa']:.2f} alpha={b['alpha']:.2f} t12={b['t12']:.1f} t23={b['t23']:.1f} t13={b['t13']:.1f} ratio={b['ratio']:.5f} chi2={b['chi2']:.1f} {b['nh']}")

# === STRATEGY 3: Non-Hermitian 9:6:1 ===
print("\n"+"="*75)
print("STRATEGY 3: Non-Hermitian braiding (9:6:1)")
print("="*75)
best3={'chi2':1e10}
delta_b=np.array([[0,1,1],[-1,0,0.2],[-1,-0.2,0]])
eps_mat=np.array([[0,1/3,1/9],[1/3,0,1],[1/9,1,0]])
phi_mat=np.array([[0,PHI_12,PHI_13],[-PHI_12,0,PHI_23],[-PHI_13,-PHI_23,0]])
for kappa in np.arange(0.1,5.0,0.1):
    for lam in np.arange(0.0,0.5,0.01):
        k=np.array([9,6,1],dtype=float)**kappa; k/=sum(k)
        KH=np.diag(k.astype(complex))
        KA=np.zeros((3,3),dtype=complex)
        for i in range(3):
            for j in range(3):
                if i!=j:
                    v=eps_mat[i,j]*np.sqrt(k[i]*k[j])*np.exp(1j*phi_mat[i,j])
                    KH[i,j]=v; KH[j,i]=v.conj() if j>i else KH[j,i]
                    KA[i,j]=eps_mat[i,j]*delta_b[i,j]*np.exp(1j*phi_mat[i,j])
        K=KH+1j*lam*KA
        r=do_nonhermitian(K)
        if r and chi2(r)<best3['chi2']:
            best3={**r,'chi2':chi2(r),'kappa':kappa,'lambda_A':lam}
b=best3
print(f"  kappa={b['kappa']:.2f} lam_A={b.get('lambda_A',0):.3f} t12={b['t12']:.1f} t23={b['t23']:.1f} t13={b['t13']:.1f} ratio={b['ratio']:.5f} chi2={b['chi2']:.1f} {b['nh']}")

# === STRATEGY 1+3: Combined ===
print("\n"+"="*75)
print("STRATEGY 1+3: Partition 9:3:4 + Non-Hermitian")
print("="*75)
best13={'chi2':1e10}
eps13_mat=np.array([[0,1/3,1/4],[1/3,0,1/4],[1/4,1/4,0]])
delta_b13=np.array([[0,1,1],[-1,0,0.33],[-1,-0.33,0]])
for kappa in np.arange(0.05,6.0,0.1):
    for lam in np.arange(0.0,0.5,0.01):
        k=np.array([9,3,4],dtype=float)**kappa; k/=sum(k)
        KH=np.diag(k.astype(complex))
        KA=np.zeros((3,3),dtype=complex)
        for i in range(3):
            for j in range(3):
                if i!=j:
                    v=eps13_mat[i,j]*np.sqrt(k[i]*k[j])*np.exp(1j*phi_mat[i,j])
                    KH[i,j]=v
                    KA[i,j]=eps13_mat[i,j]*delta_b13[i,j]*np.exp(1j*phi_mat[i,j])
        KH=(KH+KH.conj().T)/2
        K=KH+1j*lam*KA
        r=do_nonhermitian(K)
        if r and chi2(r)<best13['chi2']:
            best13={**r,'chi2':chi2(r),'kappa':kappa,'lambda_A':lam}
b=best13
print(f"  kappa={b['kappa']:.2f} lam_A={b.get('lambda_A',0):.3f} t12={b['t12']:.1f} t23={b['t23']:.1f} t13={b['t13']:.1f} ratio={b['ratio']:.5f} chi2={b['chi2']:.1f} {b['nh']}")

# === SUMMARY ===
print("\n"+"="*75)
print("SUMMARY TABLE")
print("="*75)
print(f"{'Strategy':<32} {'t12':>6} {'t23':>6} {'t13':>6} {'ratio':>8} {'chi2':>8} {'NH':>3}")
print("-"*75)
for nm,r in [("S1: partition 9:3:4",best1),("S2: nonlinear alpha",best2),
             ("S3: non-Hermitian 9:6:1",best3),("S1+3: 9:3:4 + non-Herm",best13)]:
    print(f"{nm:<32} {r['t12']:6.1f} {r['t23']:6.1f} {r['t13']:6.1f} {r['ratio']:8.5f} {r['chi2']:8.1f} {r['nh']:>3}")
print("-"*75)
print(f"{'Experiment':<32} {EXP['theta12'][0]:6.1f} {EXP['theta23'][0]:6.1f} {EXP['theta13'][0]:6.1f} {EXP['ratio'][0]:8.5f}")

# === PULLS for best ===
print("\n"+"="*75)
print("PULLS FOR BEST RESULT")
print("="*75)
allr=[(best1,"S1"),(best2,"S2"),(best3,"S3"),(best13,"S1+3")]
best_all=min(allr,key=lambda x:x[0]['chi2'])
b,nm=best_all
print(f"\nBest: {nm}, chi2={b['chi2']:.2f}, chi2/DoF={b['chi2']/2:.2f}")
for obs,key,sig in [('theta12','t12',0),('theta23','t23',1),('theta13','t13',2),('ratio','ratio',3)]:
    ev=EXP[obs]; pull=abs(b[key]-ev[0])/ev[1]
    print(f"  {obs:>10}: PQT={b[key]:8.3f}  exp={ev[0]:8.3f}+/-{ev[1]:.3f}  pull={pull:.1f}s")

# Masses
print("\nMass predictions (Lambda_T scaled to m3~50 meV):")
for nm,r in [("S1",best1),("S2",best2),("S3",best3),("S1+3",best13)]:
    if r['nh']=='NH' and r['m'][2]>0:
        sc=0.050/r['m'][2]; me=r['m']*sc
        print(f"  {nm}: m1={me[0]*1e3:.2f} m2={me[1]*1e3:.2f} m3={me[2]*1e3:.2f} Sum={sum(me)*1e3:.1f} meV")

nfp={("S1",):2,("S2",):3,("S3",):3,("S1+3",):3}
print(f"\nFree parameters: S1=2(kappa,LT), S2=3(kappa,alpha,LT), S3=3(kappa,lam,LT), S1+3=3(kappa,lam,LT)")
