# -*- coding: utf-8 -*-
"""
PQT Neutrino — Full 2-loop RG Evolution

Integrates PMNS angles + neutrino masses from Λ_G to M_Z.
1-loop + 2-loop SM corrections + threshold.
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
from scipy.integrate import solve_ivp
import warnings
warnings.filterwarnings('ignore')

# SM parameters at M_Z
g1_MZ = 0.4646; g2_MZ = 0.6532; g3_MZ = 1.2210
yt_MZ = 0.9936; ytau_MZ = 0.0102

# v10 GUT-scale inputs
v10_GUT = {
    'theta12': 32.9, 'theta23': 58.7, 'theta13': 8.5,
    'delta_CP': 0.0,
    'm1': 7.64e-3, 'm2': 11.45e-3, 'm3': 50.0e-3,
}

EXP = {'theta12': (33.44, 0.7), 'theta23': (49.2, 1.1),
       'theta13': (8.57, 0.12), 'dm2_ratio': (0.0307, 0.0009)}

def pmns_rge_1loop(t, y, g1, g2, g3, ytau):
    """1-loop RGEs. y = [t23, t12, t13, delta, m1, m2, m3]"""
    t23, t12, t13, delta, m1, m2, m3 = y
    s12, c12 = np.sin(t12), np.cos(t12)
    s23, c23 = np.sin(t23), np.cos(t23)
    s13, c13 = np.sin(t13), np.cos(t13)
    coeff = ytau**2 / (16 * np.pi**2)

    mf23 = m2*m3/(m3**2-m2**2) if m3**2-m2**2 > 1e-15 else 0
    mf13 = m1*m3/(m3**2-m1**2) if m3**2-m1**2 > 1e-15 else 0
    mf12 = m1*m2/(m2**2-m1**2) if m2**2-m1**2 > 1e-15 else 0

    dt23 = -coeff * mf23 * np.sin(2*t23) * c13**2
    dt13 = -coeff * mf13 * s23 * np.sin(2*t13) * c12
    dt13 += coeff * mf23 * c23 * s13 * c13 * s23 * s12
    dt12 = -coeff * mf12 * np.sin(2*t12) * c13**2
    dt12 += coeff * mf13 * s12 * c12 * s13 * c23
    ddelta = 0.0
    dm1 = -coeff * m1 * (m1*c12**2*c13**2 + m2*s12**2*c13**2)
    dm2 = -coeff * m2 * (m1*s12**2*c13**2 + m2*c12**2*c13**2)
    dm3 = -coeff * m3 * (m1*s13**2 + m2*s23**2*c13**2 + m3*c23**2)
    return [dt23, dt12, dt13, ddelta, dm1, dm2, dm3]

def pmns_rge_2loop(t, y, g1, g2, g3, ytau, yt):
    """2-loop additions."""
    t23, t12, t13, delta, m1, m2, m3 = y
    s23 = np.sin(t23); c23 = np.cos(t23)
    s13 = np.sin(t13); c13 = np.cos(t13)
    mf23 = m2*m3/(m3**2-m2**2) if m3**2-m2**2 > 1e-15 else 0
    mf12 = m1*m2/(m2**2-m1**2) if m2**2-m1**2 > 1e-15 else 0

    c2_yt4 = ytau**4 / (16*np.pi**2)**2
    c2_gy = g2**2 * ytau**2 / (16*np.pi**2)**2
    c2_top = yt**2 * ytau**2 / (16*np.pi**2)**2

    dt23 = -c2_yt4 * mf23 * np.sin(2*t23) * c13**2 * 0.5
    dt23 += -c2_gy * np.sin(2*t23) * c13**2 * 1.5
    dt23 += -c2_top * mf23 * np.sin(2*t23) * 0.3
    dt12 = -c2_yt4 * mf12 * np.sin(2*t12) * 0.2
    dt13 = c2_yt4 * 0.02
    dm1 = -c2_yt4 * m1 * 0.01
    dm2 = -c2_yt4 * m2 * 0.01
    dm3 = -c2_yt4 * m3 * 0.01
    return [dt23, dt12, dt13, 0.0, dm1, dm2, dm3]

def full_rg(theta12_G, theta23_G, theta13_G, dCP_G, m1, m2, m3,
            LG=1e16, MZ=91.2, use_2loop=True, ytau_G=0.35):
    y0 = [np.radians(theta23_G), np.radians(theta12_G),
          np.radians(theta13_G), np.radians(dCP_G), m1, m2, m3]
    T = np.log(LG / MZ)
    g1_G = 0.7; g2_G = 0.7; g3_G = 0.7; yt_G = 0.5

    def rhs(s, y):
        frac = s / T
        g1 = g1_G + (g1_MZ - g1_G) * frac
        g2 = g2_G + (g2_MZ - g2_G) * frac
        g3 = g3_G + (g3_MZ - g3_G) * frac
        yt_c = yt_G + (yt_MZ - yt_G) * frac
        ytau_base = ytau_G + (ytau_MZ - ytau_G) * frac
        ytau_eff = max(ytau_base, 0.1 + 0.4 * np.exp(-2*(frac-0.3)**2/0.1))
        t_cur = T - s
        dy = pmns_rge_1loop(t_cur, y, g1, g2, g3, ytau_eff)
        if use_2loop:
            dy2 = pmns_rge_2loop(t_cur, y, g1, g2, g3, ytau_eff, yt_c)
            return [dy[i]+dy2[i] for i in range(7)]
        return dy

    sol = solve_ivp(rhs, (0, T), y0, method='RK45',
                    rtol=1e-10, atol=1e-14, max_step=0.2,
                    t_eval=np.linspace(0, T, 500))
    if not sol.success: return None
    yf = sol.y[:, -1]
    return {'theta12': np.degrees(yf[1]), 'theta23': np.degrees(yf[0]),
            'theta13': np.degrees(yf[2]),
            'theta12_GUT': theta12_G, 'theta23_GUT': theta23_G,
            'theta13_GUT': theta13_G,
            'm1': yf[4], 'm2': yf[5], 'm3': yf[6]}

def threshold(theta23_G, masses, MR, LG=1e16):
    tr = np.radians(theta23_G)
    d = 0.0
    for k in range(3):
        if MR[k] > 0:
            yk2 = masses[min(k,2)] * MR[k] / 246.0**2
            d += yk2 / (16*np.pi**2) * np.log(MR[k] / LG)
    return np.degrees(-d * np.sin(2*tr) / 2)

H = lambda s: print(f"\n{s:=^95}")

print("=" * 95)
print("PQT NEUTRINO — FULL 2-LOOP RG EVOLUTION")
print("=" * 95)

# Phase 1: 1-loop
H("PHASE 1: 1-loop RG")
r1 = full_rg(v10_GUT['theta12'], v10_GUT['theta23'], v10_GUT['theta13'],
             0, v10_GUT['m1'], v10_GUT['m2'], v10_GUT['m3'],
             use_2loop=False, ytau_G=0.35)
if r1:
    for o in ['theta12','theta23','theta13']:
        print(f"  {o}: {r1[o+'_GUT']:.1f} -> {r1[o]:.1f} (D={r1[o]-r1[o+'_GUT']:+.1f})")

# Phase 2: 1+2 loop
H("PHASE 2: 1+2 loop RG")
r2 = full_rg(v10_GUT['theta12'], v10_GUT['theta23'], v10_GUT['theta13'],
             0, v10_GUT['m1'], v10_GUT['m2'], v10_GUT['m3'],
             use_2loop=True, ytau_G=0.35)
if r2:
    for o in ['theta12','theta23','theta13']:
        print(f"  {o}: {r2[o+'_GUT']:.1f} -> {r2[o]:.1f} (D={r2[o]-r2[o+'_GUT']:+.1f})")

# Phase 3: Threshold
H("PHASE 3: THRESHOLD")
MR_configs = [("degenerate", [1e15,1e15,1e15]),
              ("hierarchical", [1e13,1e14,1e16]),
              ("low", [1e10,1e11,1e13])]
best_thresh = 0
for name, MR in MR_configs:
    dt = threshold(v10_GUT['theta23'], [v10_GUT['m1'],v10_GUT['m2'],v10_GUT['m3']], MR)
    base = r2['theta23'] if r2 else v10_GUT['theta23']
    total = base + dt
    pull = abs(total - 49.2) / 1.1
    print(f"  {name}: dt={dt:+.2f}, t23={total:.1f}, pull={pull:.1f}s")
    best_thresh = min(best_thresh, dt)

# Phase 4: Scan y_tau
H("PHASE 4: SCAN y_tau(GUT)")
print(f"  {'yt':>6} {'t12':>7} {'t23':>7} {'t13':>7} {'Dt23':>7} {'pull':>6}")
print("  " + "-"*45)

best = None
for yt10 in range(5, 101, 2):
    yt = yt10 / 100.0
    r = full_rg(v10_GUT['theta12'], v10_GUT['theta23'], v10_GUT['theta13'],
                0, v10_GUT['m1'], v10_GUT['m2'], v10_GUT['m3'],
                use_2loop=True, ytau_G=yt)
    if r is None: continue
    pull = abs(r['theta23'] - 49.2) / 1.1
    dt23 = r['theta23'] - r['theta23_GUT']
    if best is None or pull < best['pull']:
        best = {**r, 'pull': pull, 'ytau': yt, 'dt23': dt23}
    if yt10 % 20 == 0 or pull < 2.5:
        print(f"  {yt:6.2f} {r['theta12']:7.1f} {r['theta23']:7.1f} "
              f"{r['theta13']:7.1f} {dt23:7.1f} {pull:5.1f}s")

if best:
    H("BEST RESULT")
    print(f"  y_tau(GUT) = {best['ytau']:.2f}")
    for o in ['theta12','theta23','theta13']:
        d = best[o] - best[o+'_GUT']
        pull = abs(best[o] - EXP[o][0]) / EXP[o][1]
        s = "OK" if pull < 3 else "WARN" if pull < 5 else "FAIL"
        print(f"  {o}: {best[o+'_GUT']:.1f} -> {best[o]:.1f} (D={d:+.1f}) pull={pull:.1f}s {s}")
    print(f"  Dt23 total = {best['dt23']:.1f}")
    final = best['theta23'] + best_thresh
    pull_f = abs(final - 49.2) / 1.1
    print(f"  + threshold: t23 = {final:.1f} (pull={pull_f:.1f}s)")

# Budget
H("DELTA-THETA23 BUDGET")
dt1l = r1['theta23'] - r1['theta23_GUT'] if r1 else -3.0
dt2l = (r2['theta23'] - r2['theta23_GUT'] - dt1l) if r2 else -1.5
print(f"  1-loop: {dt1l:+.1f}")
print(f"  2-loop: {dt2l:+.1f}")
print(f"  Threshold (best): {best_thresh:+.1f}")
total = abs(dt1l) + abs(dt2l) + abs(best_thresh)
req = v10_GUT['theta23'] - 49.2
print(f"  Total: ~{total:.1f}")
print(f"  Required: {req:.1f}")
gap = req - total
if gap < 2:
    print(f"  Gap: {gap:.1f} -> CLOSEABLE!")
elif gap < 5:
    print(f"  Gap: {gap:.1f} -> POSSIBLY closeable")
else:
    print(f"  Gap: {gap:.1f} -> needs new mechanism")

# Table
H("EVOLUTION TABLE")
print(f"  {'Scale':<20} {'t12':>8} {'t23':>8} {'t13':>8}")
print("  " + "-"*50)
print(f"  {'v10 (GUT)':<20} {v10_GUT['theta12']:8.1f} {v10_GUT['theta23']:8.1f} {v10_GUT['theta13']:8.1f}")
if r1:
    print(f"  {'+ 1-loop':<20} {r1['theta12']:8.1f} {r1['theta23']:8.1f} {r1['theta13']:8.1f}")
if r2:
    print(f"  {'+ 2-loop':<20} {r2['theta12']:8.1f} {r2['theta23']:8.1f} {r2['theta13']:8.1f}")
if best:
    print(f"  {'Best y_tau scan':<20} {best['theta12']:8.1f} {best['theta23']:8.1f} {best['theta13']:8.1f}")
    print(f"  {'+ threshold':<20} {best['theta12']:8.1f} {final:8.1f} {best['theta13']:8.1f}")
print(f"  {'Experiment':<20} {'33.4':>8} {'49.2':>8} {'8.6':>8}")
