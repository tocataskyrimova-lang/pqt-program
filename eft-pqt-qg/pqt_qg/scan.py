"""Grid scanning and local minimization for PQT-QG benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from scipy.optimize import minimize

from .classify import classify_phase, classify_stability, copositivity_pairwise
from .potential import V0, V0_vec, grad_V0, hessian_V0, hessian_eigenvalues


@dataclass(frozen=True)
class ScanConfig:
    phi_range: tuple[float, float] = (0.0, 2.0)
    r_range: tuple[float, float] = (-2.0, 2.0)
    s_range: tuple[float, float] = (-2.0, 2.0)
    grid_shape: tuple[int, int, int] = (121, 161, 161)
    candidate_count: int = 32
    low_energy_count: int = 500
    duplicate_coord_tol: float = 1e-5
    duplicate_energy_tol: float = 1e-8
    group_coord_decimals: int = 7


def _linspaces(config: ScanConfig):
    return (
        np.linspace(*config.phi_range, config.grid_shape[0]),
        np.linspace(*config.r_range, config.grid_shape[1]),
        np.linspace(*config.s_range, config.grid_shape[2]),
    )


def _grid_scan(params: Mapping[str, float], config: ScanConfig):
    phis, rs, ss = _linspaces(config)
    R, S = np.meshgrid(rs, ss, indexing="ij")
    total = len(phis) * len(rs) * len(ss)
    keep_n = min(max(config.candidate_count * 8, config.low_energy_count), total)
    best_vals = np.empty(0, dtype=float)
    best_pts = np.empty((0, 3), dtype=float)

    min_value = float("inf")
    min_point = None
    max_value = -float("inf")

    for phi in phis:
        vals = V0(phi, R, S, params)
        local_min_idx = int(np.argmin(vals))
        local_max = float(np.max(vals))
        if local_max > max_value:
            max_value = local_max
        local_min = float(vals.ravel()[local_min_idx])
        if local_min < min_value:
            rr = R.ravel()[local_min_idx]
            ss0 = S.ravel()[local_min_idx]
            min_value = local_min
            min_point = [float(phi), float(rr), float(ss0)]

        flat = vals.ravel()
        take = min(keep_n, flat.size)
        idx = np.argpartition(flat, take - 1)[:take]
        pts = np.column_stack(
            [np.full(idx.shape, phi, dtype=float), R.ravel()[idx].astype(float), S.ravel()[idx].astype(float)]
        )
        merged_vals = np.concatenate([best_vals, flat[idx].astype(float)])
        merged_pts = np.vstack([best_pts, pts])
        take2 = min(keep_n, merged_vals.size)
        idx2 = np.argpartition(merged_vals, take2 - 1)[:take2]
        best_vals = merged_vals[idx2]
        best_pts = merged_pts[idx2]

    order = np.argsort(best_vals)
    best_vals = best_vals[order]
    best_pts = best_pts[order]
    return {
        "grid_shape": list(config.grid_shape),
        "domain": {"phi": list(config.phi_range), "r": list(config.r_range), "s": list(config.s_range)},
        "grid_minimum": {"phi": min_point[0], "r": min_point[1], "s": min_point[2], "V0": min_value},
        "grid_value_range": {"min": min_value, "max": max_value},
        "candidate_points": best_pts[: config.candidate_count],
        "candidate_values": best_vals[: config.candidate_count],
        "low_energy_points": best_pts[: config.low_energy_count],
        "low_energy_values": best_vals[: config.low_energy_count],
    }


def _extra_seeds(config: ScanConfig):
    seeds = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 0.8, 0.0],
        [1.0, -0.8, 0.0],
        [1.0, 0.0, 0.8],
        [1.0, 0.0, -0.8],
        [1.0, 0.8, 0.8],
        [1.0, 0.8, -0.8],
        [1.0, -0.8, 0.8],
        [1.0, -0.8, -0.8],
        [1.5, 1.0, 1.0],
        [1.5, -1.0, 1.0],
        [1.5, 1.0, -1.0],
        [1.5, -1.0, -1.0],
    ]
    lo = np.array([config.phi_range[0], config.r_range[0], config.s_range[0]])
    hi = np.array([config.phi_range[1], config.r_range[1], config.s_range[1]])
    return np.clip(np.asarray(seeds, dtype=float), lo, hi)


def _refine_minima(params: Mapping[str, float], grid_result: dict, config: ScanConfig):
    seed_array = np.vstack([grid_result["candidate_points"], _extra_seeds(config)])
    bounds = [config.phi_range, config.r_range, config.s_range]
    refined = []
    for seed in seed_array:
        res = minimize(
            lambda x: V0_vec(x, params),
            np.asarray(seed, dtype=float),
            jac=lambda x: grad_V0(x, params),
            bounds=bounds,
            method="L-BFGS-B",
            options={"ftol": 1e-12, "gtol": 1e-10, "maxiter": 1000},
        )
        x = np.asarray(res.x, dtype=float)
        val = float(V0_vec(x, params))
        refined.append({"x": x, "V0": val, "success": bool(res.success), "message": str(res.message)})
    refined.sort(key=lambda item: item["V0"])
    return refined


def _merge_raw_minima(refined: list[dict], params: Mapping[str, float], config: ScanConfig, benchmark_name: str):
    minima = []
    for item in refined:
        x = np.asarray(item["x"], dtype=float)
        val = float(item["V0"])
        duplicate = False
        for existing in minima:
            xe = np.array([existing["phi"], existing["r"], existing["s"]], dtype=float)
            if np.linalg.norm(x - xe, ord=np.inf) <= config.duplicate_coord_tol and abs(val - existing["V0"]) <= config.duplicate_energy_tol:
                duplicate = True
                break
        if duplicate:
            continue
        hess = hessian_V0(x, params)
        eig = hessian_eigenvalues(x, params)
        phase = classify_phase(*x)
        stability = classify_stability(eig)
        minima.append(
            {
                "id": f"{benchmark_name}_raw_{len(minima)}",
                "benchmark": benchmark_name,
                "phase": phase,
                "stability": stability,
                "phi": float(x[0]),
                "r": float(x[1]),
                "s": float(x[2]),
                "V0": val,
                "hessian_eigenvalues": [float(v) for v in eig],
                "hessian": hess.tolist(),
                "optimizer_success": item["success"],
                "optimizer_message": item["message"],
                "params": dict(params),
            }
        )
    return minima


def _group_symmetry_minima(raw_minima: list[dict], params: Mapping[str, float], config: ScanConfig, benchmark_name: str):
    groups: dict[tuple, list[dict]] = {}
    for m in raw_minima:
        key = (
            round(float(m["phi"]), config.group_coord_decimals),
            round(abs(float(m["r"])), config.group_coord_decimals),
            round(abs(float(m["s"])), config.group_coord_decimals),
        )
        groups.setdefault(key, []).append(m)

    grouped = []
    for idx, (key, members) in enumerate(sorted(groups.items(), key=lambda kv: min(m["V0"] for m in kv[1]))):
        rep = min(members, key=lambda m: m["V0"])
        phi, ar, aas = key
        x = np.array([float(phi), float(ar), float(aas)])
        hess = hessian_V0(x, params)
        eig = hessian_eigenvalues(x, params)
        phase = classify_phase(*x)
        stability = classify_stability(eig)
        grouped.append(
            {
                "id": f"{benchmark_name}_group_{idx}",
                "benchmark": benchmark_name,
                "phase": phase,
                "stability": stability,
                "phi": float(phi),
                "abs_r": float(ar),
                "abs_s": float(aas),
                "V0": float(rep["V0"]),
                "hessian_eigenvalues": [float(v) for v in eig],
                "hessian": hess.tolist(),
                "symmetry_key": f"({phi}, {ar}, {aas})",
                "symmetry_multiplicity": len(members),
                "raw_minima_ids": [m["id"] for m in members],
                "params": dict(params),
            }
        )
    return grouped


def _phase_representatives(grouped_minima: list[dict]):
    reps = {}
    for m in grouped_minima:
        phase = m["phase"]
        if phase not in reps or m["V0"] < reps[phase]["V0"]:
            reps[phase] = m
    return reps


def scan_benchmark(params: Mapping[str, float], config: ScanConfig | None = None) -> dict:
    config = config or ScanConfig()
    name = str(params["name"])
    print(f"\n=== {name} ===")
    print(f"grid shape: {config.grid_shape}")
    cop = copositivity_pairwise(params)
    print(f"quartic pairwise copositivity: {cop['status']}")

    grid = _grid_scan(params, config)
    print("best grid candidate:", grid["grid_minimum"])
    refined = _refine_minima(params, grid, config)
    raw_minima = _merge_raw_minima(refined, params, config, name)
    grouped_minima = _group_symmetry_minima(raw_minima, params, config, name)
    stable = [m for m in raw_minima if m["stability"] == "stable_minimum"]
    global_minimum = raw_minima[0] if raw_minima else None
    print(f"refined raw minima: {len(raw_minima)}")
    for m in raw_minima[:8]:
        print(
            f"  {m['id']}: phase={m['phase']} stability={m['stability']} "
            f"x=({m['phi']:.6g}, {m['r']:.6g}, {m['s']:.6g}) V0={m['V0']:.9g}"
        )

    return {
        "benchmark": name,
        "params": dict(params),
        "copositivity_pairwise": cop,
        "grid_summary": {
            "grid_shape": grid["grid_shape"],
            "domain": grid["domain"],
            "grid_minimum": grid["grid_minimum"],
            "grid_value_range": grid["grid_value_range"],
            "best_grid_candidates": [
                {"phi": float(p[0]), "r": float(p[1]), "s": float(p[2]), "V0": float(v)}
                for p, v in zip(grid["candidate_points"].tolist(), grid["candidate_values"].tolist())
            ],
        },
        "low_energy_points": grid["low_energy_points"],
        "low_energy_values": grid["low_energy_values"],
        "raw_minima": raw_minima,
        "symmetry_grouped_minima": grouped_minima,
        "global_minimum": global_minimum,
        "all_stable_minima": stable,
        "phase_representatives": _phase_representatives(grouped_minima),
    }
