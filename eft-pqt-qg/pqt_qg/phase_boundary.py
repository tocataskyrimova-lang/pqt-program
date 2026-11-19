"""Phase boundary scanning over mrho2 and effective iota mass.

The scanned vertical axis is miota2_eff = miota2 + LambdaT2_kappa0.
For each point, the scanner writes params with miota2 = miota2_eff - LambdaT2_kappa0
so the existing v0.1 local-memory potential remains the single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize

from .classify import classify_phase, classify_stability, copositivity_pairwise
from .potential import V0_vec, grad_V0, hessian_eigenvalues


PHASE_ORDER = ["Prema", "Gurutva", "Tamas", "Mixed", "Symmetric", "Rho_only", "Iota_only", "Other", "Unstable"]
PHASE_TO_CODE = {name: i for i, name in enumerate(PHASE_ORDER)}


@dataclass(frozen=True)
class BoundaryScanConfig:
    mrho2_range: tuple[float, float] = (-0.8, 0.8)
    miota2_eff_range: tuple[float, float] = (-0.8, 0.8)
    grid_shape: tuple[int, int] = (101, 101)
    field_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = ((0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0))


DEFAULT_BASE_PARAMS = {
    "name": "phase_boundary_v0_2_mixed_friendly",
    "muH_eff2": 0.13,
    "lambdaH": 0.13,
    "mrho2": 0.0,
    "brho": 0.45,
    "arho": -0.08,
    "miota2": 0.0,
    "biota": 0.50,
    "aiota": -0.08,
    "c": -0.05,
    "LambdaT2_kappa0": 0.05,
    "exploratory": True,
    "note": "v0.2 phase-boundary default uses D-like mixed-friendly quartics/portals while sweeping mass levers.",
}


def _seed_points(bounds):
    seeds = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.9, 0.0],
            [1.0, -0.9, 0.0],
            [1.0, 0.0, 0.9],
            [1.0, 0.0, -0.9],
            [1.1, 0.9, 0.9],
            [1.1, 0.9, -0.9],
            [1.1, -0.9, 0.9],
            [1.1, -0.9, -0.9],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ],
        dtype=float,
    )
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    return np.clip(seeds, lo, hi)


def _best_minimum(params: Mapping[str, float], bounds, warm_seed=None):
    seeds = _seed_points(bounds)
    if warm_seed is not None:
        seeds = np.vstack([np.asarray(warm_seed, dtype=float), seeds])
    best = None
    for seed in seeds:
        res = minimize(
            lambda x: V0_vec(x, params),
            seed,
            jac=lambda x: grad_V0(x, params),
            bounds=bounds,
            method="L-BFGS-B",
            options={"ftol": 1e-11, "gtol": 1e-9, "maxiter": 600},
        )
        val = float(V0_vec(res.x, params))
        if best is None or val < best["V0"]:
            eig = hessian_eigenvalues(res.x, params)
            phase = classify_phase(*res.x)
            stability = classify_stability(eig)
            best = {
                "phi": float(res.x[0]),
                "r": float(res.x[1]),
                "s": float(res.x[2]),
                "V0": val,
                "phase": phase if stability == "stable_minimum" else "Unstable",
                "raw_phase": phase,
                "stability": stability,
                "hessian_eigenvalues": [float(v) for v in eig],
                "optimizer_success": bool(res.success),
            }
    return best


def scan_phase_boundary(
    base_params: Mapping[str, float] | None = None,
    config: BoundaryScanConfig | None = None,
) -> dict:
    base = dict(DEFAULT_BASE_PARAMS if base_params is None else base_params)
    config = config or BoundaryScanConfig()
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    phase_codes = np.zeros((len(ys), len(xs)), dtype=int)
    records = []
    warm = None
    print("\n=== Phase Boundary Scanner v0.2 ===")
    print(f"mrho2 range: {config.mrho2_range}; miota2_eff range: {config.miota2_eff_range}; grid: {config.grid_shape}")
    print("base params:", {k: base[k] for k in sorted(base) if k != "name"})
    cop = copositivity_pairwise(base)
    print(f"quartic pairwise copositivity: {cop['status']}")

    total = len(xs) * len(ys)
    done = 0
    for iy, mi_eff in enumerate(ys):
        row_warm = warm
        for ix, mrho2 in enumerate(xs):
            params = dict(base)
            params["mrho2"] = float(mrho2)
            params["miota2"] = float(mi_eff - params.get("LambdaT2_kappa0", 0.0))
            best = _best_minimum(params, config.field_bounds, row_warm)
            row_warm = [best["phi"], best["r"], best["s"]]
            phase_codes[iy, ix] = PHASE_TO_CODE.get(best["phase"], PHASE_TO_CODE["Other"])
            records.append(
                {
                    "mrho2": float(mrho2),
                    "miota2_eff": float(mi_eff),
                    "miota2": float(params["miota2"]),
                    **best,
                }
            )
            done += 1
        warm = row_warm
        if iy % max(1, len(ys) // 10) == 0 or iy == len(ys) - 1:
            print(f"  progress: {done}/{total}")

    counts = {phase: int(np.sum(phase_codes == code)) for phase, code in PHASE_TO_CODE.items()}
    print("phase counts:", {k: v for k, v in counts.items() if v})
    return {
        "scanner": "PQT-QG Phase Boundary Scanner v0.2",
        "axes": {"x": "mrho2", "y": "miota2_eff = miota2 + LambdaT2_kappa0"},
        "base_params": base,
        "config": {
            "mrho2_range": list(config.mrho2_range),
            "miota2_eff_range": list(config.miota2_eff_range),
            "grid_shape": list(config.grid_shape),
            "field_bounds": [list(b) for b in config.field_bounds],
        },
        "copositivity_pairwise": cop,
        "mrho2_values": xs.tolist(),
        "miota2_eff_values": ys.tolist(),
        "phase_order": PHASE_ORDER,
        "phase_codes": phase_codes.tolist(),
        "phase_counts": counts,
        "records": records,
    }


def plot_phase_boundary(result: dict, out_path: str | Path) -> str:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    xs = np.asarray(result["mrho2_values"])
    ys = np.asarray(result["miota2_eff_values"])
    codes = np.asarray(result["phase_codes"])
    colors = [
        "#4daf4a",  # Prema
        "#377eb8",  # Gurutva
        "#984ea3",  # Tamas
        "#ff7f00",  # Mixed
        "#dddddd",  # Symmetric
        "#a6cee3",  # Rho_only
        "#cab2d6",  # Iota_only
        "#b15928",  # Other
        "#e41a1c",  # Unstable
    ]
    cmap = matplotlib.colors.ListedColormap(colors)
    bounds = np.arange(-0.5, len(PHASE_ORDER) + 0.5, 1)
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    fig, ax = plt.subplots(figsize=(9, 7), constrained_layout=True)
    im = ax.imshow(
        codes,
        origin="lower",
        extent=[xs.min(), xs.max(), ys.min(), ys.max()],
        aspect="auto",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
    )
    cbar = fig.colorbar(im, ax=ax, ticks=np.arange(len(PHASE_ORDER)))
    cbar.ax.set_yticklabels(PHASE_ORDER)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff = miota2 + LambdaT2_kappa0")
    ax.set_title("PQT-QG Phase Boundary Scanner v0.2")
    ax.axvline(0.0, color="black", linewidth=0.6, alpha=0.5)
    ax.axhline(0.0, color="black", linewidth=0.6, alpha=0.5)
    fig.savefig(out_path, dpi=170)
    plt.close(fig)
    return str(out_path)


def write_phase_boundary_report(result: dict, plot_path: str, out_path: str | Path) -> str:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    counts = {k: v for k, v in result["phase_counts"].items() if v}
    lines = [
        "# PQT-QG Phase Boundary Scanner v0.2",
        "",
        "## Goal",
        "Sweep the two main tree-level vacuum levers `mrho2` and `miota2_eff = miota2 + LambdaT2_kappa0` and classify the global refined minimum phase at each grid point.",
        "",
        "## Canon / scope",
        "- Tree-level only.",
        "- Local memory approximation only: `K_T(k) ≈ kappa0`.",
        "- `Core Psi` remains frozen into `muH_eff2`; it is not replaced by `H`.",
        "- Synthetic exploratory phase-structure map; no physical prediction.",
        "",
        "## Base parameters held fixed",
        "```json",
    ]
    import json

    lines.append(json.dumps(result["base_params"], indent=2))
    lines.extend(
        [
            "```",
            "",
            "## Scan configuration",
            "```json",
            json.dumps(result["config"], indent=2),
            "```",
            "",
            "## Phase map",
            f"- Plot: `{plot_path}`",
            "",
            "## Phase counts",
        ]
    )
    for phase, count in counts.items():
        lines.append(f"- {phase}: {count}")
    lines.extend(
        [
            "",
            "## Copositivity sanity check",
            f"Status: **{result['copositivity_pairwise']['status']}**",
            "",
            "This is a pairwise guardrail, not a full three-field copositivity proof.",
            "",
            "## Interpretation warning",
            "Phase boundaries are numerical and depend on held-fixed quartics/portals, scan bounds, and minimizer settings.",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)
