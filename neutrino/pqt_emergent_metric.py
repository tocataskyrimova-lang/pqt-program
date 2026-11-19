# -*- coding: utf-8 -*-
"""
PQT Emergent Metric — Magnetic Laplacian on K₄□K₄
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
from scipy.linalg import inv, eigvalsh, eigh
import warnings
warnings.filterwarnings('ignore')

Q_SIGMA = np.array([1.0, 0.0, 1.0, 0.0])
def n_delta(idx): return 1 if idx == 3 else 0
def get_generation(a, b):
    d2, d3 = n_delta(a), n_delta(b)
    if d2 == 1 and d3 == 0: return 0
    elif d2 == 0 and d3 == 0: return 1
    else: return 2

K4_edges = [(i, j) for i in range(4) for j in range(i+1, 4)]

def build_product_graph():
    vertices = [(a, b) for a in range(4) for b in range(4)]
    vertex_index = {v: i for i, v in enumerate(vertices)}
    edges, edge_types = [], []
    for a, b in vertices:
        for a1, a2 in K4_edges:
            v1, v2 = (a1, b), (a2, b)
            edges.append((vertex_index[v1], vertex_index[v2]))
            edge_types.append('H')
        for b1, b2 in K4_edges:
            v1, v2 = (a, b1), (a, b2)
            edges.append((vertex_index[v1], vertex_index[v2]))
            edge_types.append('V')
    unique_edges, unique_types = [], []
    seen = set()
    for (i, j), etype in zip(edges, edge_types):
        key = (min(i, j), max(i, j))
        if key not in seen:
            seen.add(key)
            unique_edges.append((i, j))
            unique_types.append(etype)
    return vertices, vertex_index, unique_edges, unique_types

def sigma_charge(vertex, eta=0.351):
    a, b = vertex
    return (1 + eta) * Q_SIGMA[a] + (1 - eta) * Q_SIGMA[b]

def build_magnetic_laplacian(vertices, edges, phases):
    N = len(vertices)
    L = np.zeros((N, N), dtype=complex)
    degree = np.zeros(N)
    for (i, j) in edges:
        degree[i] += 1; degree[j] += 1
    for i in range(N): L[i, i] = degree[i]
    for (i, j) in edges:
        theta = phases.get((i, j), phases.get((j, i), 0.0))
        L[i, j] = -np.exp(1j * theta)
        L[j, i] = -np.exp(-1j * theta)
    return L

def emergent_metric(G):
    N = G.shape[0]
    d = np.zeros((N, N))
    diag = np.real(np.diag(G))
    for i in range(N):
        for j in range(i+1, N):
            dist_sq = diag[i] + diag[j] - 2 * np.abs(G[i, j])
            dist = np.sqrt(max(dist_sq, 0))
            d[i, j] = dist; d[j, i] = dist
    return d

def phases_zero(edges): return {(i, j): 0.0 for (i, j) in edges}
def phases_sigma_charge(edges, vertices, alpha=0.1):
    return {(i, j): alpha * (sigma_charge(vertices[i]) - sigma_charge(vertices[j])) for (i, j) in edges}
def phases_tamas_gradient(edges, vertices, alpha=0.1):
    return {(i, j): alpha * ((n_delta(vertices[i][0])+n_delta(vertices[i][1])) - (n_delta(vertices[j][0])+n_delta(vertices[j][1]))) * np.pi/4 for (i, j) in edges}
def phases_topological_twist(edges, edge_types, alpha=0.1):
    return {(i, j): alpha * (edges.index((i, j)) % 4) * np.pi/2 if etype == 'V' else 0.0 for (i, j), etype in zip(edges, edge_types)}

def generation_distances(d, vertices):
    gen = np.array([get_generation(a, b) for (a, b) in vertices])
    dists = {}
    for gi in range(3):
        for gj in range(gi, 3):
            mask_i, mask_j = gen == gi, gen == gj
            d_sub = d[np.ix_(mask_i, mask_j)]
            if gi != gj: avg = np.mean(d_sub[d_sub > 0])
            else: avg = np.mean(d_sub[np.triu_indices(d_sub.shape[0], k=1)])
            dists[f'Gen{gi+1}-Gen{gj+1}'] = avg
    return dists

H = lambda s: print(f"\n{s:=^90}")

print("=" * 90)
print("PQT EMERGENT METRIC -- MAGNETIC LAPLACIAN ON K4xK4")
print("=" * 90)

vertices, vertex_index, edges, edge_types = build_product_graph()
N, E = len(vertices), len(edges)

print(f"\n  Graph: K4xK4, Vertices: {N}, Edges: {E}, Degree: {E*2//N}")

print(f"\n  {'Vertex':>8} {'(a,b)':>8} {'Gen':>5} {'sigma':>10} {'nd':>5}")
print(f"  {'-'*42}")
for i, (a, b) in enumerate(vertices):
    print(f"  {i:8d} ({a},{b})   Gen{get_generation(a,b)+1}  {sigma_charge((a,b)):10.3f}  {n_delta(a)+n_delta(b):5d}")

# Phase configs
phase_configs = [
    ('A: theta=0', lambda: phases_zero(edges)),
    ('B: sigma a=0.1', lambda: phases_sigma_charge(edges, vertices, 0.1)),
    ('B: sigma a=0.5', lambda: phases_sigma_charge(edges, vertices, 0.5)),
    ('B: sigma a=1.0', lambda: phases_sigma_charge(edges, vertices, 1.0)),
    ('B: sigma a=2.0', lambda: phases_sigma_charge(edges, vertices, 2.0)),
    ('D: Tamas a=0.1', lambda: phases_tamas_gradient(edges, vertices, 0.1)),
    ('D: Tamas a=0.5', lambda: phases_tamas_gradient(edges, vertices, 0.5)),
    ('D: Tamas a=1.0', lambda: phases_tamas_gradient(edges, vertices, 1.0)),
]

# Spectral analysis
H("SPECTRAL ANALYSIS")
for name, pf in phase_configs:
    L = build_magnetic_laplacian(vertices, edges, pf())
    eigvals = eigvalsh(L.real)
    print(f"  {name}: L eigenvalues: min={eigvals[0]:.3f}, max={eigvals[-1]:.3f}")

# Emergent metric at m0=1
H("EMERGENT METRIC (m0=1.0)")
m0 = 1.0
for name, pf in phase_configs[:6]:
    L = build_magnetic_laplacian(vertices, edges, pf())
    G = inv(L + m0**2 * np.eye(N))
    d = emergent_metric(G)
    gd = generation_distances(d, vertices)
    print(f"\n  {name}:")
    for pair, avg in gd.items():
        print(f"    {pair}: {avg:.6f}")

# Generation distance ratio
H("GENERATION DISTANCE RATIOS")
print(f"  {'config':>20} {'d12':>10} {'d13':>10} {'d23':>10} {'d23/d12':>10} {'d13/d12':>10}")
print(f"  {'-'*75}")
for name, pf in phase_configs:
    L = build_magnetic_laplacian(vertices, edges, pf())
    G = inv(L + m0**2 * np.eye(N))
    d = emergent_metric(G)
    gd = generation_distances(d, vertices)
    d12, d13, d23 = gd['Gen1-Gen2'], gd['Gen1-Gen3'], gd['Gen2-Gen3']
    r23 = d23/d12 if d12>0 else 0
    r13 = d13/d12 if d12>0 else 0
    print(f"  {name:>20} {d12:10.6f} {d13:10.6f} {d23:10.6f} {r23:10.4f} {r13:10.4f}")

# Lorentz signature test
H("LORENTZ SIGNATURE TEST")
for name, pf in phase_configs[:5]:
    L = build_magnetic_laplacian(vertices, edges, pf())
    G = inv(L + m0**2 * np.eye(N))
    d = emergent_metric(G)
    D_sq = d**2
    J = np.eye(N) - np.ones((N, N)) / N
    Gram = -0.5 * J @ D_sq @ J
    eigvals = eigvalsh(Gram)
    n_pos = np.sum(eigvals > 1e-10)
    n_neg = np.sum(eigvals < -1e-10)
    n_zero = np.sum(np.abs(eigvals) <= 1e-10)
    print(f"  {name}: sig=({n_pos},{n_neg},{n_zero}), top3={np.sort(eigvals)[-3:][::-1]}")

# Distance matrix
H("DISTANCE MATRIX (baseline, m0=1)")
L0 = build_magnetic_laplacian(vertices, edges, phases_zero(edges))
G0 = inv(L0 + m0**2 * np.eye(N))
d0 = emergent_metric(G0)

gen_labels = [f"G{get_generation(a,b)+1}({a}{b})" for a, b in vertices]
print(f"\n  {'':>10}", end="")
for j in range(N): print(f" {gen_labels[j]:>8}", end="")
print()
for i in range(N):
    print(f"  {gen_labels[i]:>10}", end="")
    for j in range(N): print(f" {d0[i,j]:8.4f}", end="")
    print()

# Phase distortion scan
H("PHASE DISTORTION SCAN (sigma-charge)")
print(f"  {'alpha':>8} {'d12':>10} {'d13':>10} {'d23':>10} {'d23/d12':>10}")
print(f"  {'-'*55}")
for a10 in range(0, 51, 5):
    alpha = a10 / 100.0
    L = build_magnetic_laplacian(vertices, edges, phases_sigma_charge(edges, vertices, alpha))
    G = inv(L + m0**2 * np.eye(N))
    d = emergent_metric(G)
    gd = generation_distances(d, vertices)
    d12, d13, d23 = gd['Gen1-Gen2'], gd['Gen1-Gen3'], gd['Gen2-Gen3']
    print(f"  {alpha:8.2f} {d12:10.6f} {d13:10.6f} {d23:10.6f} {d23/d12 if d12>0 else 0:10.4f}")

# m0 scaling
H("METRIC SCALING WITH m0")
gen = np.array([get_generation(a, b) for (a, b) in vertices])
g1, g3 = gen == 0, gen == 2
print(f"  {'m0':>8} {'d11':>10} {'d13':>10} {'d33':>10} {'d13/d11':>10}")
print(f"  {'-'*55}")
for m10 in range(1, 101, 10):
    m = m10 / 10.0
    G = inv(L0 + m**2 * np.eye(N))
    d = emergent_metric(G)
    d11 = np.mean(d[np.ix_(g1, g1)][np.triu_indices(np.sum(g1), k=1)])
    d33 = np.mean(d[np.ix_(g3, g3)][np.triu_indices(np.sum(g3), k=1)])
    d13 = np.mean(d[np.ix_(g1, g3)])
    print(f"  {m:8.2f} {d11:10.6f} {d13:10.6f} {d33:10.6f} {d13/d11 if d11>0 else 0:10.4f}")

# Verification
H("VERIFICATION")
L = build_magnetic_laplacian(vertices, edges, phases_zero(edges))
G = inv(L + 1.0 * np.eye(N))
print(f"  L Hermitian: {np.allclose(L, L.conj().T)}")
print(f"  G Hermitian: {np.allclose(G, G.conj().T)}")
print(f"  G positive diag: {all(np.real(np.diag(G)) > 0)}")
print(f"  G(L+I)=I: {np.allclose(G @ (L + np.eye(N)), np.eye(N))}")
print(f"  Tr(G) = {np.real(np.trace(G)):.6f}")
print(f"  Symmetry group: S4 x S4 (order {24*24})")

# Automorphism test
perm = list(range(N))
for b in range(4):
    i, j = vertex_index[(0, b)], vertex_index[(1, b)]
    perm[i], perm[j] = j, i
d_perm = d0[np.ix_(perm, perm)]
print(f"  Metric invariant under (0<->1) swap: {np.allclose(d0, d_perm)}")

# Emergent dimension
H("EMERGENT DIMENSION")
ref = 0
d_ref = d0[ref, :]
print(f"  Reference: vertex {ref} = {vertices[ref]} (Gen{get_generation(*vertices[ref])+1})")
print(f"  {'r':>10} {'N(r)':>6} {'logN':>8} {'logr':>8}")
print(f"  {'-'*40}")
for re in range(-4, 2):
    r = 10**re
    nr = np.sum(d_ref <= r)
    if nr > 1:
        print(f"  {r:10.4f} {nr:6d} {np.log(nr):8.3f} {np.log(r):8.3f}")
