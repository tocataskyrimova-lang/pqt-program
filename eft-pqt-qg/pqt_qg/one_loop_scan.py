"""v0.4 local Coleman-Weinberg phase-map benchmark scans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .classify import classify_phase, copositivity_pairwise
from .one_loop import OneLoopParams, Veff, cw_flags
from .phase_boundary import PHASE_ORDER, PHASE_TO_CODE
from .robustness import active_set_minimum, expected_quadrant_phase, _topology_status, RobustnessConfig

SELECTED_SLICES = [
    {
        "name": "preserved_c_plus_0_10",
        "muH_eff2": 0.13,
        "lambdaH": 0.13,
        "mrho2": 0.0,
        "brho": 0.45,
        "arho": -0.08,
        "miota2": 0.0,
        "biota": 0.50,
        "aiota": -0.08,
        "c": 0.10,
        "LambdaT2_kappa0": 0.05,
        "source": "v0.3 preserved slice c_+0.10",
    },
    {
        "name": "baseline_mild_deformed",
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
        "source": "v0.2/v0.3 baseline mixed-friendly slice",
    },
    {
        "name": "cooperative_strongly_deformed",
        "muH_eff2": 0.13,
        "lambdaH": 0.13,
        "mrho2": 0.0,
        "brho": 0.45,
        "arho": -0.20,
        "miota2": 0.0,
        "biota": 0.50,
        "aiota": -0.20,
        "c": -0.05,
        "LambdaT2_kappa0": 0.05,
        "source": "v0.3 strongly deformed portal grid",
    },
    {
        "name": "positive_edge_deformed",
        "muH_eff2": 0.13,
        "lambdaH": 0.13,
        "mrho2": 0.0,
        "brho": 0.45,
        "arho": 0.20,
        "miota2": 0.0,
        "biota": 0.50,
        "aiota": -0.08,
        "c": -0.05,
        "LambdaT2_kappa0": 0.05,
        "source": "v0.3 arho_+0.20 strongly deformed edge",
    },
]


@dataclass(frozen=True)
class OneLoopScanConfig:
    mrho2_range: tuple[float, float] = (-0.8, 0.8)
    miota2_eff_range: tuple[float, float] = (-0.8, 0.8)
    grid_shape: tuple[int, int] = (61, 61)
    field_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = ((0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0))
    axis_ignore_eps: float = 0.02


def _phase_counts(codes: np.ndarray) -> dict[str, int]:
    return {phase: int(np.sum(codes == code)) for phase, code in PHASE_TO_CODE.items()}


def _agreement(records: list[dict[str, Any]], eps: float) -> tuple[float | None, int, int]:
    comparable = 0
    matches = 0
    for r in records:
        expected = expected_quadrant_phase(r["mrho2"], r["miota2_eff"], eps)
        if expected is None:
            continue
        comparable += 1
        matches += int(r["phase"] == expected)
    if comparable == 0:
        return None, 0, 0
    return matches / comparable, comparable - matches, comparable


def _tree_maps(params: Mapping[str, float], config: OneLoopScanConfig):
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    rconfig = RobustnessConfig(
        mrho2_range=config.mrho2_range,
        miota2_eff_range=config.miota2_eff_range,
        grid_shape=config.grid_shape,
        field_bounds=config.field_bounds,
        axis_ignore_eps=config.axis_ignore_eps,
    )
    codes = np.zeros((len(ys), len(xs)), dtype=int)
    records = []
    minima = np.zeros((len(ys), len(xs), 3), dtype=float)
    for iy, mi_eff in enumerate(ys):
        for ix, mr in enumerate(xs):
            p = dict(params)
            p["mrho2"] = float(mr)
            p["miota2"] = float(mi_eff - p.get("LambdaT2_kappa0", 0.0))
            best = active_set_minimum(p, float(mr), float(mi_eff), rconfig)
            phase = best["phase"]
            codes[iy, ix] = PHASE_TO_CODE.get(phase, PHASE_TO_CODE["Other"])
            minima[iy, ix, :] = [best["phi"], best["abs_r"], best["abs_s"]]
            records.append({"mrho2": float(mr), "miota2_eff": float(mi_eff), "phase": phase, **best})
    return codes, records, minima


def _initial_seed(ix: int, iy: int, tree_minima: np.ndarray, cw_minima: np.ndarray | None, config: OneLoopScanConfig):
    seeds = [tree_minima[iy, ix, :]]
    if cw_minima is not None:
        if ix > 0:
            seeds.append(cw_minima[iy, ix - 1, :])
        if iy > 0:
            seeds.append(cw_minima[iy - 1, ix, :])
    seeds.extend(
        [
            np.array([1.0, 0.0, 0.0]),
            np.array([1.0, 0.8, 0.0]),
            np.array([1.0, 0.0, 0.8]),
            np.array([1.0, 0.8, 0.8]),
        ]
    )
    lo = np.array([b[0] for b in config.field_bounds])
    hi = np.array([b[1] for b in config.field_bounds])
    return [np.clip(np.asarray(s, dtype=float), lo, hi) for s in seeds]


def _minimize_cw(params: Mapping[str, float], seeds: list[np.ndarray], loop: OneLoopParams, config: OneLoopScanConfig):
    bounds = list(config.field_bounds)
    # Evaluate seed candidates first; optimize only the best two to keep smoke runtime bounded.
    ranked = sorted(seeds, key=lambda x: Veff(x, params, loop))[:2]
    best_x = ranked[0]
    best_v = Veff(best_x, params, loop)
    success = True
    msg = "seed"
    for seed in ranked:
        res = minimize(
            lambda x: Veff(x, params, loop),
            seed,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 45, "ftol": 1e-9, "gtol": 1e-6, "eps": 2e-4},
        )
        val = float(Veff(res.x, params, loop))
        if val < best_v:
            best_x = np.asarray(res.x, dtype=float)
            best_v = val
            success = bool(res.success)
            msg = str(res.message)
    return best_x, float(best_v), success, msg


def _cw_maps(params: Mapping[str, float], config: OneLoopScanConfig, loop: OneLoopParams, tree_minima: np.ndarray):
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    codes = np.zeros((len(ys), len(xs)), dtype=int)
    instability = np.zeros((len(ys), len(xs)), dtype=bool)
    records = []
    minima = np.zeros((len(ys), len(xs), 3), dtype=float)
    for iy, mi_eff in enumerate(ys):
        for ix, mr in enumerate(xs):
            p = dict(params)
            p["mrho2"] = float(mr)
            p["miota2"] = float(mi_eff - p.get("LambdaT2_kappa0", 0.0))
            seeds = _initial_seed(ix, iy, tree_minima, minima, config)
            x, val, success, msg = _minimize_cw(p, seeds, loop, config)
            phase = classify_phase(float(x[0]), float(x[1]), float(x[2]))
            flags = cw_flags(float(x[0]), float(x[1]), float(x[2]), p, loop)
            codes[iy, ix] = PHASE_TO_CODE.get(phase, PHASE_TO_CODE["Other"])
            instability[iy, ix] = flags["cw_has_negative_scalar_modes"] or flags["cw_has_negative_goldstone_modes"]
            minima[iy, ix, :] = x
            records.append(
                {
                    "mrho2": float(mr),
                    "miota2_eff": float(mi_eff),
                    "phase": phase,
                    "phi": float(x[0]),
                    "r": float(x[1]),
                    "s": float(x[2]),
                    "Veff": val,
                    "optimizer_success": success,
                    "optimizer_message": msg,
                    **flags,
                }
            )
    return codes, records, instability


def _plot_phase(codes: np.ndarray, title: str, out_path: Path, config: OneLoopScanConfig) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    colors = ["#4daf4a", "#377eb8", "#984ea3", "#ff7f00", "#dddddd", "#a6cee3", "#cab2d6", "#b15928", "#e41a1c"]
    cmap = matplotlib.colors.ListedColormap(colors)
    norm = matplotlib.colors.BoundaryNorm(np.arange(-0.5, len(PHASE_ORDER) + 0.5, 1), cmap.N)
    fig, ax = plt.subplots(figsize=(8.5, 6.8), constrained_layout=True)
    im = ax.imshow(codes, origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
    cb = fig.colorbar(im, ax=ax, ticks=np.arange(len(PHASE_ORDER)))
    cb.ax.set_yticklabels(PHASE_ORDER)
    ax.axvline(0, color="black", lw=0.6, alpha=0.55)
    ax.axhline(0, color="black", lw=0.6, alpha=0.55)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    fig.savefig(out_path, dpi=165)
    plt.close(fig)
    return str(out_path)


def _plot_mask(mask: np.ndarray, title: str, out_path: Path, config: OneLoopScanConfig) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.2, 6.5), constrained_layout=True)
    im = ax.imshow(mask.astype(int), origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap="Reds", interpolation="nearest", vmin=0, vmax=1)
    fig.colorbar(im, ax=ax, ticks=[0, 1])
    ax.axvline(0, color="black", lw=0.6, alpha=0.55)
    ax.axhline(0, color="black", lw=0.6, alpha=0.55)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    fig.savefig(out_path, dpi=165)
    plt.close(fig)
    return str(out_path)


def scan_one_loop_slice(params: Mapping[str, float], config: OneLoopScanConfig, loop: OneLoopParams, plot_dir: Path) -> dict[str, Any]:
    name = str(params["name"])
    print(f"\n=== {name} ===")
    print(f"grid shape: {config.grid_shape}; loop_scale: {loop.loop_scale}")
    print(f"copositivity: {copositivity_pairwise(params)['status']}")
    tree_codes, tree_records, tree_minima = _tree_maps(params, config)
    cw_codes, cw_records, inst_mask = _cw_maps(params, config, loop, tree_minima)
    changed = tree_codes != cw_codes

    tree_agree, tree_mismatch, tree_comp = _agreement(tree_records, config.axis_ignore_eps)
    cw_agree, cw_mismatch, cw_comp = _agreement(cw_records, config.axis_ignore_eps)
    tree_counts = _phase_counts(tree_codes)
    cw_counts = _phase_counts(cw_codes)
    total = int(tree_codes.size)
    changed_count = int(np.sum(changed))
    inst_count = int(np.sum(inst_mask))
    summary = {
        "slice": name,
        "source": params.get("source", ""),
        "tree_phase_counts": tree_counts,
        "cw_phase_counts": cw_counts,
        "tree_phase_fractions": {k: v / total for k, v in tree_counts.items()},
        "cw_phase_fractions": {k: v / total for k, v in cw_counts.items()},
        "tree_quadrant_agreement": tree_agree,
        "cw_quadrant_agreement": cw_agree,
        "tree_mismatch_count": tree_mismatch,
        "cw_mismatch_count": cw_mismatch,
        "comparable_count": tree_comp,
        "changed_phase_fraction": changed_count / total,
        "changed_cells_count": changed_count,
        "mixed_fraction_tree": tree_counts.get("Mixed", 0) / total,
        "mixed_fraction_cw": cw_counts.get("Mixed", 0) / total,
        "topology_status_tree": _topology_status(tree_agree or 0.0),
        "topology_status_cw": _topology_status(cw_agree or 0.0),
        "instability_fraction_cw": inst_count / total,
        "instability_cells_count": inst_count,
        "copositivity_pairwise": copositivity_pairwise(params),
    }
    print("tree phase counts:", {k: v for k, v in tree_counts.items() if v})
    print("CW phase counts:", {k: v for k, v in cw_counts.items() if v})
    print(f"tree agreement: {tree_agree:.6f}; CW agreement: {cw_agree:.6f}")
    print(f"changed phase fraction: {summary['changed_phase_fraction']:.6f}; instability fraction: {summary['instability_fraction_cw']:.6f}")

    plots = {
        "tree_phase_map": _plot_phase(tree_codes, f"{name}: tree phase map", plot_dir / f"{name}_tree_phase_map.png", config),
        "cw_phase_map": _plot_phase(cw_codes, f"{name}: CW phase map scale={loop.loop_scale}", plot_dir / f"{name}_cw_phase_map.png", config),
        "phase_changed_mask": _plot_mask(changed, f"{name}: phase changed under CW", plot_dir / f"{name}_phase_changed_mask.png", config),
        "cw_instability_mask": _plot_mask(inst_mask, f"{name}: negative scalar/Goldstone mass flags", plot_dir / f"{name}_cw_instability_mask.png", config),
    }
    for p in plots.values():
        print(f"wrote plot: {p}")

    rows = []
    for tr, cr in zip(tree_records, cw_records):
        rows.append(
            {
                "slice": name,
                "mrho2": tr["mrho2"],
                "miota2_eff": tr["miota2_eff"],
                "tree_phase": tr["phase"],
                "cw_phase": cr["phase"],
                "phase_changed": tr["phase"] != cr["phase"],
                **{f"cw_{k}": v for k, v in cr.items() if k not in {"mrho2", "miota2_eff", "phase"}},
            }
        )
    return {"params": dict(params), "summary": summary, "plots": plots, "rows": rows}


def write_one_loop_report(result: Mapping[str, Any], out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summaries = result["summaries"]
    def table(rows, cols):
        lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        for r in rows:
            vals=[]
            for c in cols:
                v=r.get(c, "")
                vals.append(f"{v:.4f}" if isinstance(v, float) else str(v))
            lines.append("| " + " | ".join(vals) + " |")
        return lines
    flat = []
    for s in summaries:
        row = {"slice": s["slice"], "source": s["source"], "tree_agreement": s["tree_quadrant_agreement"], "cw_agreement": s["cw_quadrant_agreement"], "changed_phase_fraction": s["changed_phase_fraction"], "instability_fraction_cw": s["instability_fraction_cw"], "tree_status": s["topology_status_tree"], "cw_status": s["topology_status_cw"], "mixed_tree": s["mixed_fraction_tree"], "mixed_cw": s["mixed_fraction_cw"]}
        for phase in ["Prema", "Gurutva", "Tamas", "Mixed", "Other", "Rho_only", "Iota_only", "Unstable"]:
            row[f"tree_{phase}"] = s["tree_phase_fractions"].get(phase, 0.0)
            row[f"cw_{phase}"] = s["cw_phase_fractions"].get(phase, 0.0)
        flat.append(row)
    lines = [
        "# PQT-QG One-Loop Local Coleman-Weinberg Benchmark v0.4",
        "",
        "## 1. Goal",
        "Test whether selected tree-level Prema/Gurutva/Tamas/Mixed phase topologies survive after a local one-loop Coleman-Weinberg correction.",
        "",
        "## 2. Canon assumptions",
        "- Core Psi remains frozen into `muH_eff2`; H does not replace Psi.",
        "- Observed scalar landscape only.",
        "- Local memory approximation only: `K_T(k) ≈ kappa0`, via `LambdaT2_kappa0` as iota mass shift.",
        "- Local CW only; no full nonlocal memory determinant; no RG improvement; no Nielsen analysis.",
        "- `Veff` is gauge-dependent off-shell; negative mass-squared values use Re[V1] with flags.",
        "",
        "## 3. Selected slices",
    ]
    for p in result["slices"]:
        lines.append(f"- `{p['name']}` — {p.get('source','')}")
    lines += [
        "",
        "## 4. One-loop formula and constants",
        "`Veff = V0 + loop_scale * V1`, `mu_ren=1.0`, `g_D=0.65`, `g_Y=0.36`, `y_top=1.0`, top multiplicity `n_top=-12`.",
        "CW terms use `m^4(log(|m^2|/mu_ren^2)-c)` with constants `3/2` for scalars/fermions and `5/6` for vectors.",
        "",
        "## 5. Tree vs CW phase fraction table",
    ]
    lines += table(flat, ["slice", "tree_Prema", "cw_Prema", "tree_Gurutva", "cw_Gurutva", "tree_Tamas", "cw_Tamas", "tree_Mixed", "cw_Mixed", "tree_Other", "cw_Other"])
    lines += ["", "## 6. Tree vs CW quadrant agreement table"]
    lines += table(flat, ["slice", "tree_agreement", "cw_agreement", "tree_status", "cw_status"])
    lines += ["", "## 7. Changed phase fraction table"]
    lines += table(flat, ["slice", "changed_phase_fraction", "mixed_tree", "mixed_cw"])
    lines += ["", "## 8. Instability / negative-mass flags"]
    lines += table(flat, ["slice", "instability_fraction_cw", "cw_Rho_only", "cw_Iota_only", "cw_Unstable"])
    lines += ["", "## 9. Notes"]
    by = {s["slice"]: s for s in summaries}
    for name, s in by.items():
        lines.append(f"- `{name}`: tree `{s['topology_status_tree']}` -> CW `{s['topology_status_cw']}`, changed cells `{s['changed_cells_count']}`, CW instability fraction `{s['instability_fraction_cw']:.4f}`.")
    lines += [
        "- Check `changed_mask` and `cw_instability_mask` PNGs for where local CW changes phases or flags negative scalar/Goldstone masses.",
        "",
        "## 10. Warnings",
        "- synthetic benchmark only",
        "- one-loop local CW only",
        "- gauge-dependent off-shell `Veff`",
        "- Re[Veff] only when negative `m^2` appears",
        "- no RG improvement",
        "- no full nonlocal `K_T` determinant",
        "- no physical prediction",
        "- no proof of PQT-QG",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)


def run_one_loop_benchmark(root: Path, grid: int = 61, loop_scale: float = 1.0) -> dict[str, Path]:
    config = OneLoopScanConfig(grid_shape=(grid, grid))
    loop = OneLoopParams(loop_scale=loop_scale)
    data_dir = root / "outputs" / "data"
    plot_dir = root / "outputs" / "plots" / "one_loop_v0_4"
    report_dir = root / "outputs" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    plot_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    all_results = []
    all_rows = []
    summaries = []
    for p in SELECTED_SLICES:
        r = scan_one_loop_slice(p, config, loop, plot_dir)
        all_results.append({"params": r["params"], "summary": r["summary"], "plots": r["plots"]})
        summaries.append(r["summary"])
        all_rows.extend(r["rows"])
    payload = {"name": "PQT-QG Benchmark v0.4 — One-loop Local Coleman-Weinberg Correction", "grid": grid, "loop_scale": loop_scale, "slices": SELECTED_SLICES, "results": all_results}
    json_path = data_dir / "one_loop_benchmark_v0_4.json"
    csv_path = data_dir / "one_loop_benchmark_v0_4.csv"
    summary_path = data_dir / "one_loop_comparison_summary_v0_4.json"
    report_path = report_dir / "PQT_QG_One_Loop_Benchmark_Report_v0_4.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(all_rows).to_csv(csv_path, index=False)
    summary_payload = {"grid": grid, "loop_scale": loop_scale, "summaries": summaries}
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    report = write_one_loop_report({"slices": SELECTED_SLICES, "summaries": summaries}, report_path)
    print(f"wrote data: {json_path}")
    print(f"wrote data: {csv_path}")
    print(f"wrote data: {summary_path}")
    print(f"wrote report: {report}")
    return {"json": json_path, "csv": csv_path, "summary": summary_path, "report": report_path, "plot_dir": plot_dir}

