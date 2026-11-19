"""Full nonlocal minimization micro-scan for PQT-QG v0.8."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .classify import classify_phase
from .memory_sign import MemorySignConfig, active_set_minimum_signed
from .nonlocal_memory import (
    NonlocalKernelParams,
    V0_zero_mode_corrected,
    det_delta_N,
    iota_inverse,
    neutral_mass_entries,
    quadrature_grid,
)
from .phase_boundary import PHASE_ORDER, PHASE_TO_CODE

COOPERATIVE_SLICE = {
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
}


class MicroScanConfig:
    def __init__(self, grid: int = 11, wide: bool = False):
        self.mrho2_range = (-0.8, 0.1) if wide else (-0.55, -0.05)
        self.miota2_eff_range = (-0.8, 0.1) if wide else (-0.55, -0.05)
        self.grid_shape = (grid, grid)
        self.field_bounds = ((0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0))
        self.health_eps = 1e-8
        self.det_eps = 1e-8
        self.wide = wide

    def as_dict(self):
        return {
            "mrho2_range": list(self.mrho2_range),
            "miota2_eff_range": list(self.miota2_eff_range),
            "grid_shape": list(self.grid_shape),
            "field_bounds": [list(b) for b in self.field_bounds],
            "health_eps": self.health_eps,
            "det_eps": self.det_eps,
            "wide": self.wide,
        }


def _kernel_alias(name: str) -> str:
    if name == "local":
        return "local_constant"
    return name


def _objective_factory(params: dict[str, float], kernel: str, kp: NonlocalKernelParams):
    k, weights, q = quadrature_grid(kp)
    ref_kernel = det_delta_N(q, 0.0, 0.0, 0.0, params, kernel, kp)
    ref_local = det_delta_N(q, 0.0, 0.0, 0.0, params, "local_constant", kp)
    log_ref_kernel = np.log(np.abs(ref_kernel) + kp.eps_det)
    log_ref_local = np.log(np.abs(ref_local) + kp.eps_det)
    pref = weights * k**3 / (16.0 * np.pi * np.pi)

    def v1_fast(x, kern, log_ref):
        phi, r, s = np.asarray(x, dtype=float)
        det = det_delta_N(q, phi, r, s, params, kern, kp)
        return float(np.sum(pref * (np.log(np.abs(det) + kp.eps_det) - log_ref)))

    def objective(x):
        phi, r, s = np.asarray(x, dtype=float)
        base = V0_zero_mode_corrected(phi, r, s, params, kp.sigma0)
        if kernel == "local_constant" or kp.nonlocal_scale == 0.0:
            return float(base)
        return float(base + kp.nonlocal_scale * (v1_fast(x, kernel, log_ref_kernel) - v1_fast(x, "local_constant", log_ref_local)))

    def diagnostics(x):
        phi, r, s = np.asarray(x, dtype=float)
        det = det_delta_N(q, phi, r, s, params, kernel, kp)
        entries = neutral_mass_entries(phi, r, s, params)
        inv = iota_inverse(q, entries["m_ss_local2"], kernel, kp)
        min_eval_proxy = float(min(np.min(det), np.min(inv)))
        return {
            "determinant_negative_count": int(np.sum(det < 0)),
            "determinant_near_zero_count": int(np.sum(np.abs(det) < 1e-10)),
            "min_det": float(np.min(det)),
            "min_iota_inverse": float(np.min(inv)),
            "min_neutral_eigenvalue_over_k": min_eval_proxy,
            "determinant_health": bool(np.min(inv) > -1e-8 and np.min(det) > -1e-8),
        }

    return objective, diagnostics


def _seeds(local_x: np.ndarray, max_seeds: str, bounds):
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    base = np.asarray(local_x, dtype=float)
    if max_seeds == "local_only":
        return [np.clip(base, lo, hi)]
    perturb = [
        [0.05, 0, 0], [-0.05, 0, 0], [0, 0.05, 0], [0, -0.05, 0], [0, 0, 0.05], [0, 0, -0.05],
    ]
    seeds = [base] + [base + np.array(p) for p in perturb]
    seeds += [np.array(x, dtype=float) for x in [(1, 0, 0), (1, 0.8, 0), (1, 0, 0.8), (1, 0.8, 0.8), (0, 0, 0)]]
    return [np.clip(s, lo, hi) for s in seeds]


def _minimize(objective, seeds, bounds, kernel: str):
    if kernel == "local_constant":
        vals = [(objective(s), s, True, "local seed eval") for s in seeds[:1]]
        val, x, ok, msg = min(vals, key=lambda t: t[0])
        return np.asarray(x), float(val), ok, msg
    # Pre-rank seeds and optimize the best few for runtime.
    ranked = sorted([(objective(s), s) for s in seeds], key=lambda t: t[0])[:4]
    best_v, best_x = ranked[0]
    best_ok, best_msg = True, "seed"
    for _, seed in ranked:
        res = minimize(
            objective,
            seed,
            method="L-BFGS-B",
            bounds=list(bounds),
            options={"maxiter": 45, "ftol": 1e-9, "gtol": 1e-6, "eps": 2e-4},
        )
        val = float(objective(res.x))
        if val < best_v:
            best_v = val
            best_x = np.asarray(res.x, dtype=float)
            best_ok = bool(res.success)
            best_msg = str(res.message)
    return np.asarray(best_x), float(best_v), best_ok, best_msg


def scan_kernel(kernel: str, config: MicroScanConfig, kp: NonlocalKernelParams, max_seeds: str):
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    local_codes = np.zeros((len(ys), len(xs)), dtype=int)
    nonlocal_codes = np.zeros_like(local_codes)
    changed = np.zeros_like(local_codes, dtype=bool)
    det_health = np.zeros_like(local_codes, dtype=bool)
    delta_pos = np.zeros_like(local_codes, dtype=float)
    min_iota = np.zeros_like(local_codes, dtype=float)
    min_det = np.zeros_like(local_codes, dtype=float)
    rows = []
    mconfig = MemorySignConfig(grid_shape=config.grid_shape, mrho2_range=config.mrho2_range, miota2_eff_range=config.miota2_eff_range, field_bounds=config.field_bounds)
    total = len(xs) * len(ys)
    done = 0
    for iy, y in enumerate(ys):
        for ix, x in enumerate(xs):
            params = dict(COOPERATIVE_SLICE)
            params["mrho2"] = float(x)
            params["miota2"] = float(y + kp.sigma0)
            local = active_set_minimum_signed(params, float(x), float(y), "minus", mconfig)
            local_x = np.array([local["phi"], local["abs_r"], local["abs_s"]], dtype=float)
            local_phase = local["phase"]
            objective, diagnostics = _objective_factory(params, kernel, kp)
            local_obj = float(objective(local_x))
            sx = _seeds(local_x, max_seeds, config.field_bounds)
            nonlocal_x, nonlocal_obj, ok, msg = _minimize(objective, sx, config.field_bounds, kernel)
            phase = classify_phase(float(nonlocal_x[0]), float(nonlocal_x[1]), float(nonlocal_x[2]))
            diag = diagnostics(nonlocal_x)
            lp_code = PHASE_TO_CODE.get(local_phase, PHASE_TO_CODE["Other"])
            np_code = PHASE_TO_CODE.get(phase, PHASE_TO_CODE["Other"])
            local_codes[iy, ix] = lp_code
            nonlocal_codes[iy, ix] = np_code
            changed[iy, ix] = lp_code != np_code
            det_health[iy, ix] = diag["determinant_health"]
            delta = nonlocal_x - local_x
            delta_norm = float(np.linalg.norm(delta))
            delta_pos[iy, ix] = delta_norm
            min_iota[iy, ix] = diag["min_iota_inverse"]
            min_det[iy, ix] = diag["min_det"]
            rows.append(
                {
                    "kernel": kernel,
                    "mrho2": float(x),
                    "miota2_eff": float(y),
                    "local_phase": local_phase,
                    "nonlocal_phase": phase,
                    "phase_changed": bool(changed[iy, ix]),
                    "local_phi": float(local_x[0]),
                    "local_r": float(local_x[1]),
                    "local_s": float(local_x[2]),
                    "nonlocal_phi": float(nonlocal_x[0]),
                    "nonlocal_r": float(nonlocal_x[1]),
                    "nonlocal_s": float(nonlocal_x[2]),
                    "delta_position_norm": delta_norm,
                    "delta_phi": float(delta[0]),
                    "delta_r": float(delta[1]),
                    "delta_s": float(delta[2]),
                    "local_objective_value_at_local_min": local_obj,
                    "nonlocal_objective_value_at_local_min": local_obj,
                    "nonlocal_objective_value_at_nonlocal_min": nonlocal_obj,
                    "delta_objective": float(nonlocal_obj - local_obj),
                    "optimizer_success": bool(ok),
                    "optimizer_message": msg,
                    **diag,
                }
            )
            done += 1
        print(f"  {kernel}: row {iy+1}/{len(ys)} ({done}/{total})")
    return {
        "kernel": kernel,
        "local_codes": local_codes,
        "nonlocal_codes": nonlocal_codes,
        "changed_mask": changed,
        "det_health_mask": det_health,
        "delta_position_norm_grid": delta_pos,
        "min_iota_inverse_grid": min_iota,
        "min_det_grid": min_det,
        "records": rows,
    }


def _counts(codes):
    return {p: int(np.sum(codes == c)) for p, c in PHASE_TO_CODE.items()}


def _transition(local_codes, nonlocal_codes):
    code_to_phase = {v: k for k, v in PHASE_TO_CODE.items()}
    out = {p: {q: 0 for q in PHASE_ORDER} for p in PHASE_ORDER}
    for a, b in zip(local_codes.ravel(), nonlocal_codes.ravel()):
        out[code_to_phase.get(int(a), "Other")][code_to_phase.get(int(b), "Other")] += 1
    return out


def summarize(result):
    rows = result["records"]
    total = len(rows)
    return {
        "kernel": result["kernel"],
        "phase_counts_local": _counts(result["local_codes"]),
        "phase_counts_nonlocal": _counts(result["nonlocal_codes"]),
        "changed_phase_fraction": int(np.sum(result["changed_mask"])) / total,
        "changed_cells_count": int(np.sum(result["changed_mask"])),
        "average_delta_position_norm": float(np.mean([r["delta_position_norm"] for r in rows])),
        "max_delta_position_norm": float(np.max([r["delta_position_norm"] for r in rows])),
        "average_delta_objective": float(np.mean([r["delta_objective"] for r in rows])),
        "determinant_health_fraction": int(np.sum(result["det_health_mask"])) / total,
        "min_iota_inverse_global": float(np.min([r["min_iota_inverse"] for r in rows])),
        "min_det_global": float(np.min([r["min_det"] for r in rows])),
        "optimizer_success_fraction": float(np.mean([bool(r["optimizer_success"]) for r in rows])),
        "transition_matrix": _transition(result["local_codes"], result["nonlocal_codes"]),
    }


def _plot_phase(codes, title, path: Path, config: MicroScanConfig):
    path.parent.mkdir(parents=True, exist_ok=True)
    colors = ["#4daf4a", "#377eb8", "#984ea3", "#ff7f00", "#dddddd", "#a6cee3", "#cab2d6", "#b15928", "#e41a1c"]
    cmap = matplotlib.colors.ListedColormap(colors)
    norm = matplotlib.colors.BoundaryNorm(np.arange(-0.5, len(PHASE_ORDER) + 0.5, 1), cmap.N)
    fig, ax = plt.subplots(figsize=(7, 5.6), constrained_layout=True)
    im = ax.imshow(codes, origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
    cb = fig.colorbar(im, ax=ax, ticks=np.arange(len(PHASE_ORDER)))
    cb.ax.set_yticklabels(PHASE_ORDER)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    fig.savefig(path, dpi=155)
    plt.close(fig)
    return str(path)


def _plot_grid(grid, title, path: Path, config: MicroScanConfig, cmap="viridis"):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 5.6), constrained_layout=True)
    im = ax.imshow(grid, origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap=cmap, interpolation="nearest")
    fig.colorbar(im, ax=ax)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    fig.savefig(path, dpi=155)
    plt.close(fig)
    return str(path)


def _bar(summary_rows, metric, title, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [r["kernel"] for r in summary_rows]
    vals = [r[metric] for r in summary_rows]
    fig, ax = plt.subplots(figsize=(6.5, 4.5), constrained_layout=True)
    ax.bar(labels, vals)
    ax.set_ylabel(metric)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(path, dpi=155)
    plt.close(fig)
    return str(path)


def write_report(payload, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["summary_rows"]
    def table(rows, cols):
        out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        for r in rows:
            vals = []
            for c in cols:
                v = r.get(c, "")
                vals.append(f"{v:.5g}" if isinstance(v, float) else str(v))
            out.append("| " + " | ".join(vals) + " |")
        return out
    lines = [
        "# PQT-QG Nonlocal Micro-Scan Report v0.8",
        "",
        "## 1. Goal",
        "Full nonlocal minimization micro-scan for the cooperative sector.",
        "",
        "## 2. Why v0.8 exists",
        "v0.7 evaluated nonlocal determinant diagnostics at local active-set minima. v0.8 includes nonlocal `deltaV` in the minimization objective on a small targeted grid.",
        "",
        "## 3. Canon assumptions",
        "Core Psi is frozen into `muH_eff2`; H is observed-sector; memory is Euclidean `Sigma_E`; no physical prediction or proof is claimed.",
        "",
        "## 4. Numerical method",
        f"Grid `{payload['config']['grid_shape']}` over `mrho2={payload['config']['mrho2_range']}`, `miota2_eff={payload['config']['miota2_eff_range']}`. kmax `{payload['kernel_params']['kmax']}`, num_k `{payload['kernel_params']['num_k']}`. Seeds: `{payload['max_seeds']}`. Optimizer: L-BFGS-B. Objective uses determinant-ratio subtraction and corrected zero-mode memory.",
        "",
        "## 5. Kernel comparison table",
    ]
    lines += table(rows, ["kernel", "changed_phase_fraction", "average_delta_position_norm", "max_delta_position_norm", "determinant_health_fraction", "optimizer_success_fraction", "min_iota_inverse_global", "min_det_global"])
    lines += ["", "## 6. Transition matrices"]
    for r in rows:
        lines += [f"### {r['kernel']}", "```json", json.dumps(r["transition_matrix"], indent=2), "```"]
    lines += ["", "## 7. Main answers"]
    for r in rows:
        lines.append(f"- `{r['kernel']}`: changed phase fraction `{r['changed_phase_fraction']:.4f}`, avg movement `{r['average_delta_position_norm']:.4g}`, determinant health `{r['determinant_health_fraction']:.4f}`.")
    lines += [
        "- If changed fraction is near zero but determinant health is low, stress is diagnostic rather than phase-moving on this micro-grid.",
        "- Broader v0.9 scans should be considered only for kernels with acceptable optimizer and determinant health.",
        "",
        "## 8. Warnings",
        "- synthetic benchmark only",
        "- micro-scan only",
        "- cutoff/scheme dependent",
        "- no RG improvement",
        "- no full renormalization",
        "- no physical prediction",
        "- determinant health is diagnostic, not theorem",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def run_micro_scan(root: Path, grid: int = 11, num_k: int = 96, kmax: float = 5.0, kernels: Iterable[str] | None = None, nonlocal_scale: float = 1.0, wide: bool = False, max_seeds: str = "all", skip_plots: bool = False):
    kernels = ["local_constant" if k == "local" else k for k in (kernels or ["local_constant", "single_pole", "exp_gap"])]
    config = MicroScanConfig(grid=grid, wide=wide)
    kp = NonlocalKernelParams(kmax=kmax, num_k=num_k, nonlocal_scale=nonlocal_scale)
    data_dir = root / "outputs" / "data"
    plot_dir = root / "outputs" / "plots" / "nonlocal_micro_v0_8"
    report_dir = root / "outputs" / "reports"
    for d in (data_dir, plot_dir, report_dir):
        d.mkdir(parents=True, exist_ok=True)
    print("PQT-QG Benchmark v0.8 — Full Nonlocal Minimization Micro-Scan")
    print(f"grid={grid}; kmax={kmax}; num_k={num_k}; kernels={kernels}; max_seeds={max_seeds}; wide={wide}")
    results = []
    all_records = []
    plots = {}
    for kernel in kernels:
        print(f"\n=== kernel {kernel} ===")
        res = scan_kernel(kernel, config, kp, max_seeds)
        summ = summarize(res)
        results.append({"kernel": kernel, "summary": summ})
        all_records.extend(res["records"])
        print(f"optimizer success fraction: {summ['optimizer_success_fraction']:.4f}")
        print(f"changed phase fraction: {summ['changed_phase_fraction']:.4f}")
        print(f"determinant health fraction: {summ['determinant_health_fraction']:.4f}")
        print(f"average delta position: {summ['average_delta_position_norm']:.6g}")
        if not skip_plots:
            if kernel == kernels[0]:
                plots["cooperative_local_phase_map"] = _plot_phase(res["local_codes"], "cooperative local phase map", plot_dir / "cooperative_local_phase_map.png", config)
            plots[f"cooperative_{kernel}_nonlocal_phase_map"] = _plot_phase(res["nonlocal_codes"], f"cooperative {kernel} nonlocal phase", plot_dir / f"cooperative_{kernel}_nonlocal_phase_map.png", config)
            plots[f"cooperative_{kernel}_phase_changed_mask"] = _plot_grid(res["changed_mask"].astype(int), f"{kernel} phase changed", plot_dir / f"cooperative_{kernel}_phase_changed_mask.png", config, cmap="Reds")
            plots[f"cooperative_{kernel}_delta_position_norm"] = _plot_grid(res["delta_position_norm_grid"], f"{kernel} delta position norm", plot_dir / f"cooperative_{kernel}_delta_position_norm.png", config)
            plots[f"cooperative_{kernel}_det_health_mask"] = _plot_grid(res["det_health_mask"].astype(int), f"{kernel} determinant health", plot_dir / f"cooperative_{kernel}_det_health_mask.png", config, cmap="Greens")
            plots[f"cooperative_{kernel}_min_iota_inverse_heatmap"] = _plot_grid(res["min_iota_inverse_grid"], f"{kernel} min iota inverse", plot_dir / f"cooperative_{kernel}_min_iota_inverse_heatmap.png", config)
            plots[f"cooperative_{kernel}_min_det_heatmap"] = _plot_grid(res["min_det_grid"], f"{kernel} min det", plot_dir / f"cooperative_{kernel}_min_det_heatmap.png", config)
    summary_rows = [r["summary"] for r in results]
    if not skip_plots:
        plots["summary_changed_phase_fraction_by_kernel"] = _bar(summary_rows, "changed_phase_fraction", "Changed phase fraction", plot_dir / "summary_changed_phase_fraction_by_kernel.png")
        plots["summary_avg_delta_position_by_kernel"] = _bar(summary_rows, "average_delta_position_norm", "Average delta position", plot_dir / "summary_avg_delta_position_by_kernel.png")
        plots["summary_det_health_by_kernel"] = _bar(summary_rows, "determinant_health_fraction", "Determinant health", plot_dir / "summary_det_health_by_kernel.png")
        for p in plots.values():
            print(f"wrote plot: {p}")
    payload = {"name": "PQT-QG Benchmark v0.8 — Full Nonlocal Minimization Micro-Scan", "slice": COOPERATIVE_SLICE, "config": config.as_dict(), "kernel_params": asdict(kp), "kernels": kernels, "max_seeds": max_seeds, "results": results, "summary_rows": summary_rows, "plots": plots}
    json_path = data_dir / "nonlocal_micro_scan_v0_8.json"
    csv_path = data_dir / "nonlocal_micro_scan_v0_8.csv"
    summary_path = data_dir / "nonlocal_micro_scan_summary_v0_8.json"
    report_path = report_dir / "PQT_QG_Nonlocal_Micro_Scan_Report_v0_8.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(all_records).to_csv(csv_path, index=False)
    summary_path.write_text(json.dumps({"summary_rows": summary_rows, "plots": plots}, indent=2), encoding="utf-8")
    report = write_report(payload, report_path)
    print(f"wrote data: {json_path}")
    print(f"wrote data: {csv_path}")
    print(f"wrote data: {summary_path}")
    print(f"wrote report: {report}")
    return {"json": json_path, "csv": csv_path, "summary": summary_path, "report": report_path, "plot_dir": plot_dir}
