"""PQT Neutrino v4b — Fixed scan with proper constraints"""
import numpy as np
from scipy.linalg import eigh, eig

EXP = {'theta12':(33.44,0.7),'theta23':(49.2,1.1),'theta13':(8.57,0.12),'ratio':(0.0307,0.0009)}
PHI_12=np.pi/4; PHI_23=np.pi/4; PHI_13=np.arctan(np.sqrt(2))

def angles_h(K):
    M=(K+K.conj().T)/2; ev,U=eigh(M.real)
    idx=np.argsort(ev); ev=ev[idx]; U=U[:,idx]
    if any(e<=0 for e in ev): return None
    s13=min(abs(U[0,2]),0.999); c13=np.sqrt(1-s13**2)
    t13=np.degrees(np.arcsin(s13))
    s12=min(abs(U[0,1])/c13,0.999) if c13>1e-10 else 0
    s23=min(abs(U[1,2])/c13,0.999) if c13>1e-10 else 0
    dm21=ev[1]**2-ev[0]**2; dm31=ev[2]**2-ev[0]**2
    r=dm21/dm31 if dm31>1e-30 else 0
    return {'t12':np.degrees(np.arcsin(s12)),'t23':np.degrees(np.arcsin(s23)),
            't13':t13,'ratio':r,'m':ev,'nh':ev[0]<ev[1]<ev[2]}

def angles_nh(K):
    ev,VR=eig(K); idx=np.argsort(np.abs(ev)); ev=ev[idx]; VR=VR[:,idx]
    m=np.abs(ev)
    if any(x<=1e-30 for x in m): return None
    U=VR
    s13=min(abs(U[0,2]),0.999); c13=np.sqrt(1-s13**2)
    t13=np.degrees(np.arcsin(s13))
    s12=min(abs(U[0,1])/c13,0.999) if c13>1e-10 else 0
    s23=min(abs(U[1,2])/c13,0.999) if c13>1e-10 else 0
    dm21=m[1]**2-m[0]**2; dm31=m[2]**2-m[0]**2
    r=dm21/dm31 if dm31>1e-30 else 0
    return {'t12':np.degrees(np.arcsin(s12)),'t23':np.degrees(np.arcsin(s23)),
            't13':t13,'ratio':r,'m':m,'nh':m[0]<m[1]<m[2]}

def chi2(r):
    if r is None or not r['nh']: return 1e10
    c=((r['t12']-EXP['theta12'][0])/EXP['theta12'][1])**2
    c+=((r['t23']-EXP['theta23'][0])/EXP['theta23'][1])**2
    c+=((r['t13']-EXP['theta13'][0])/EXP['theta13'][1])**2
    c+=((r['ratio']-EXP['ratio'][0])/EXP['ratio'][1])**2
    return c

def pulls(r):
    return {
        't12':abs(r['t12']-EXP['theta12'][0])/EXP['theta12'][1],
        't23':abs(r['t23']-EXP['theta23'][0])/EXP['theta23'][1],
        't13':abs(r['t13']-EXP['theta13'][0])/EXP['theta13'][1],
        'ratio':abs(r['ratio']-EXP['ratio'][0])/EXP['ratio'][1],
    }

results = []

# === S1: Partition 9:3:4, Hermitian, geometric scaling ===
print("="*75)
print("S1: Partition 9:3:4 (eps12=1/3, eps23=1/4, eps13=1/4)")
print("="*75)
best={'chi2':1e10}
for kappa in np.arange(0.3,8.0,0.01):
    k=np.array([9,3,4],dtype=float)**kappa
    K=np.diag(k.astype(complex))
    for i,j,e,p in [(0,1,1/3,PHI_12),(0,2,1/4,PHI_13),(1,2,1/4,PHI_23)]:
        v=e*np.sqrt(k[i]*k[j])*np.exp(1j*p); K[i,j]=v; K[j,i]=v.conj()
    r=angles_h(K)
    c=chi2(r)
    if c<best['chi2']: best={**r,'chi2':c,'kappa':kappa,'label':'S1:9:3:4'}
print(f"  kappa={best['kappa']:.3f} t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f} ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")
results.append(best)

# === S1b: Partition 9:3:4, product scaling ===
print("\n"+"="*75)
print("S1b: Partition 9:3:4, product scaling (off-diag ~ ki*kj)")
print("="*75)
best={'chi2':1e10}
for kappa in np.arange(0.3,8.0,0.01):
    k=np.array([9,3,4],dtype=float)**kappa; kn=k/sum(k)
    K=np.diag(kn.astype(complex))
    for i,j,e,p in [(0,1,1/3,PHI_12),(0,2,1/4,PHI_13),(1,2,1/4,PHI_23)]:
        v=e*kn[i]*kn[j]*np.exp(1j*p); K[i,j]=v; K[j,i]=v.conj()
    r=angles_h(K)
    c=chi2(r)
    if c<best['chi2']: best={**r,'chi2':c,'kappa':kappa,'label':'S1b:prod'}
print(f"  kappa={best['kappa']:.3f} t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f} ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")
results.append(best)

# === S2: 9:6:1 + alpha scan ===
print("\n"+"="*75)
print("S2: Original 9:6:1, scan alpha (off-diag ~ (ki*kj)^alpha)")
print("="*75)
best={'chi2':1e10}
for kappa in np.arange(0.2,6.0,0.05):
    for alpha in np.arange(0.0,2.5,0.02):
        k=np.array([9,6,1],dtype=float)**kappa
        K=np.diag(k.astype(complex))
        for i,j,e,p in [(0,1,1/3,PHI_12),(0,2,1/9,PHI_13),(1,2,1.0,PHI_23)]:
            v=e*(k[i]*k[j])**alpha*np.exp(1j*p); K[i,j]=v; K[j,i]=v.conj()
        r=angles_h(K)
        c=chi2(r)
        if c<best['chi2']: best={**r,'chi2':c,'kappa':kappa,'alpha':alpha,'label':'S2:alpha'}
print(f"  kappa={best['kappa']:.3f} alpha={best.get('alpha',0):.2f} t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f} ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")
results.append(best)

# === S3: Non-Hermitian 9:6:1 ===
print("\n"+"="*75)
print("S3: Non-Hermitian braiding (9:6:1, geometric)")
print("="*75)
best={'chi2':1e10}
db=np.array([[0,1,1],[-1,0,0.2],[-1,-0.2,0]])
em=np.array([[0,1/3,1/9],[1/3,0,1],[1/9,1,0]])
pm=np.array([[0,PHI_12,PHI_13],[-PHI_12,0,PHI_23],[-PHI_13,-PHI_23,0]])
for kappa in np.arange(0.3,6.0,0.05):
    for lam in np.arange(0.0,1.0,0.02):
        k=np.array([9,6,1],dtype=float)**kappa
        KH=np.diag(k.astype(complex))
        KA=np.zeros((3,3),dtype=complex)
        for i in range(3):
            for j in range(3):
                if i!=j:
                    s=np.sqrt(k[i]*k[j])
                    KH[i,j]=em[i,j]*s*np.exp(1j*pm[i,j])
                    KA[i,j]=em[i,j]*db[i,j]*s*np.exp(1j*pm[i,j])
        KH=(KH+KH.conj().T)/2
        K=KH+1j*lam*KA
        r=angles_nh(K)
        c=chi2(r)
        if c<best['chi2']: best={**r,'chi2':c,'kappa':kappa,'lambda_A':lam,'label':'S3:nonH'}
print(f"  kappa={best['kappa']:.3f} lam={best.get('lambda_A',0):.3f} t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f} ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")
results.append(best)

# === S1+3: 9:3:4 + non-Hermitian ===
print("\n"+"="*75)
print("S1+3: Partition 9:3:4 + Non-Hermitian")
print("="*75)
best={'chi2':1e10}
em2=np.array([[0,1/3,1/4],[1/3,0,1/4],[1/4,1/4,0]])
db2=np.array([[0,1,1],[-1,0,0.33],[-1,-0.33,0]])
for kappa in np.arange(0.3,8.0,0.05):
    for lam in np.arange(0.0,1.0,0.02):
        k=np.array([9,3,4],dtype=float)**kappa
        KH=np.diag(k.astype(complex))
        KA=np.zeros((3,3),dtype=complex)
        for i in range(3):
            for j in range(3):
                if i!=j:
                    s=np.sqrt(k[i]*k[j])
                    KH[i,j]=em2[i,j]*s*np.exp(1j*pm[i,j])
                    KA[i,j]=em2[i,j]*db2[i,j]*s*np.exp(1j*pm[i,j])
        KH=(KH+KH.conj().T)/2
        K=KH+1j*lam*KA
        r=angles_nh(K)
        c=chi2(r)
        if c<best['chi2']: best={**r,'chi2':c,'kappa':kappa,'lambda_A':lam,'label':'S1+3'}
print(f"  kappa={best['kappa']:.3f} lam={best.get('lambda_A',0):.3f} t12={best['t12']:.2f} t23={best['t23']:.2f} t13={best['t13']:.2f} ratio={best['ratio']:.5f} chi2={best['chi2']:.1f}")
results.append(best)

# === SUMMARY ===
print("\n"+"="*75)
print("SUMMARY TABLE")
print("="*75)
print(f"{'Strategy':<28} {'t12':>7} {'t23':>7} {'t13':>7} {'ratio':>9} {'chi2':>9} {'#p':>3}")
print("-"*75)
for r in sorted(results,key=lambda x:x['chi2']):
    np_=3 if 'alpha' in r or 'lambda_A' in r else 2
    print(f"{r['label']:<28} {r['t12']:7.2f} {r['t23']:7.2f} {r['t13']:7.2f} {r['ratio']:9.5f} {r['chi2']:9.1f} {np_:3d}")
print("-"*75)
print(f"{'Experiment':<28} {33.44:7.2f} {49.2:7.2f} {8.57:7.2f} {0.0307:9.5f}")

# Pulls for best
br=min(results,key=lambda x:x['chi2'])
print(f"\nBest: {br['label']}")
p=pulls(br)
print(f"  t12: {br['t12']:.2f} ({p['t12']:.1f}s)  t23: {br['t23']:.2f} ({p['t23']:.1f}s)  t13: {br['t13']:.2f} ({p['t13']:.1f}s)  ratio: {br['ratio']:.5f} ({p['ratio']:.1f}s)")
print(f"  chi2={br['chi2']:.1f}, chi2/DoF={br['chi2']/max(4-2,1):.1f}")

# Mass predictions
print("\nMass predictions:")
for r in results:
    if r['nh'] and r['m'][2]>0:
        sc=0.050/r['m'][2]; me=r['m']*sc
        print(f"  {r['label']}: m1={me[0]*1e3:.1f} m2={me[1]*1e3:.1f} m3={me[2]*1e3:.1f} Sum={sum(me)*1e3:.0f} meV")
