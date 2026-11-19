"""PQT-QG v0.7 nonlocal Sigma_E(k) benchmark scanner."""

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
from .nonlocal_memory import NonlocalKernelParams, Veff_nonlocal, kernel_sanity, sigma_E, iota_inverse, V1_neutral_nonlocal
from .phase_boundary import PHASE_ORDER, PHASE_TO_CODE
from .robustness import _topology_status, expected_quadrant_phase
from .memory_sign import active_set_minimum_signed, MemorySignConfig

SELECTED_SLICES = [
    {"name": "preserved_c_plus_0_10", "muH_eff2": 0.13, "lambdaH": 0.13, "mrho2": 0.0, "brho": 0.45, "arho": -0.08, "miota2": 0.0, "biota": 0.50, "aiota": -0.08, "c": 0.10, "LambdaT2_kappa0": 0.05},
    {"name": "baseline_mild_deformed", "muH_eff2": 0.13, "lambdaH": 0.13, "mrho2": 0.0, "brho": 0.45, "arho": -0.08, "miota2": 0.0, "biota": 0.50, "aiota": -0.08, "c": -0.05, "LambdaT2_kappa0": 0.05},
    {"name": "cooperative_strongly_deformed", "muH_eff2": 0.13, "lambdaH": 0.13, "mrho2": 0.0, "brho": 0.45, "arho": -0.20, "miota2": 0.0, "biota": 0.50, "aiota": -0.20, "c": -0.05, "LambdaT2_kappa0": 0.05},
]


class NonlocalScanConfig:
    def __init__(self, grid: int = 31):
        self.mrho2_range = (-0.8, 0.8)
        self.miota2_eff_range = (-0.8, 0.8)
        self.grid_shape = (grid, grid)
        self.field_bounds = ((0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0))
        self.axis_ignore_eps = 0.02

    def as_dict(self):
        return {
            "mrho2_range": list(self.mrho2_range),
            "miota2_eff_range": list(self.miota2_eff_range),
            "grid_shape": list(self.grid_shape),
            "field_bounds": [list(b) for b in self.field_bounds],
            "axis_ignore_eps": self.axis_ignore_eps,
        }


def _phase_counts(codes):
    arr = np.asarray(codes)
    return {phase: int(np.sum(arr == code)) for phase, code in PHASE_TO_CODE.items()}


def _transition_matrix(a_codes, b_codes):
    a = np.asarray(a_codes, dtype=int)
    b = np.asarray(b_codes, dtype=int)
    code_to_phase = {v: k for k, v in PHASE_TO_CODE.items()}
    out = {p: {q: 0 for q in PHASE_ORDER} for p in PHASE_ORDER}
    for x, y in zip(a.ravel(), b.ravel()):
        out[code_to_phase.get(int(x), "Other")][code_to_phase.get(int(y), "Other")] += 1
    return out


def _standard_seeds(local_seed):
    return [
        np.asarray(local_seed, dtype=float),
        np.array([1.0, 0.0, 0.0]),
        np.array([1.0, 0.8, 0.0]),
        np.array([1.0, 0.0, 0.8]),
        np.array([1.0, 0.8, 0.8]),
        np.array([0.0, 0.0, 0.0]),
    ]


def _minimize_cell(params, kernel_name: str, kp: NonlocalKernelParams, config: NonlocalScanConfig, local_seed):
    """Fast v0.7 smoke evaluator.

    Nonlocal determinant minimization is expensive; v0.7 uses the corrected
    zero-mode active-set minimum as the deterministic phase point and evaluates
    nonlocal determinant diagnostics there. Full nonlocal minimization is a v0.8
    candidate once kernel health is established.
    """
    x0 = np.asarray(local_seed, dtype=float)
    return x0, float(Veff_nonlocal(x0, params, kernel_name, kp)), True, "zero-mode active-set seed (fast v0.7)"

def _agreement(records, eps):
    comparable = matches = 0
    for r in records:
        exp = expected_quadrant_phase(r["mrho2"], r["miota2_eff"], eps)
        if exp is None:
            continue
        comparable += 1
        matches += int(r["phase"] == exp)
    return (matches / comparable if comparable else None, comparable - matches, comparable)


def scan_slice_kernel(slice_params: dict[str, Any], kernel_name: str, config: NonlocalScanConfig, kp: NonlocalKernelParams):
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    codes = np.zeros((len(ys), len(xs)), dtype=int)
    health = np.zeros_like(codes, dtype=bool)
    records = []
    mconfig = MemorySignConfig(grid_shape=config.grid_shape, mrho2_range=config.mrho2_range, miota2_eff_range=config.miota2_eff_range, field_bounds=config.field_bounds, axis_ignore_eps=config.axis_ignore_eps)
    for iy, mi_eff in enumerate(ys):
        for ix, mr in enumerate(xs):
            params = dict(slice_params)
            params["mrho2"] = float(mr)
            # effective axis: miota2_eff = miota2 - sigma0
            params["miota2"] = float(mi_eff + kp.sigma0)
            local = active_set_minimum_signed(params, float(mr), float(mi_eff), "minus", mconfig)
            local_seed = [local["phi"], local["abs_r"], local["abs_s"]]
            x, val, success, msg = _minimize_cell(params, kernel_name, kp, config, local_seed)
            phase = classify_phase(float(x[0]), float(x[1]), float(x[2]))
            diag = V1_neutral_nonlocal(float(x[0]), float(x[1]), float(x[2]), params, kernel_name, kp)
            codes[iy, ix] = PHASE_TO_CODE.get(phase, PHASE_TO_CODE["Other"])
            health[iy, ix] = bool(diag["nonlocal_det_healthy"])
            records.append(
                {
                    "slice": slice_params["name"],
                    "kernel": kernel_name,
                    "mrho2": float(mr),
                    "miota2_eff": float(mi_eff),
                    "phase": phase,
                    "phi": float(x[0]),
                    "r": float(x[1]),
                    "s": float(x[2]),
                    "Veff": val,
                    "optimizer_success": success,
                    "optimizer_message": msg,
                    **{k: v for k, v in diag.items() if k != "V1"},
                }
            )
    counts = _phase_counts(codes)
    total = int(codes.size)
    agree, mismatch, comparable = _agreement(records, config.axis_ignore_eps)
    min_iota = min(r["min_iota_inverse"] for r in records)
    min_det = min(r["min_det"] for r in records)
    return {
        "slice": slice_params["name"],
        "kernel": kernel_name,
        "phase_codes": codes.tolist(),
        "det_health_mask": health.tolist(),
        "phase_counts": counts,
        "phase_fractions": {k: v / total for k, v in counts.items()},
        "quadrant_agreement": agree,
        "topology_status": _topology_status(float(agree or 0.0)),
        "mixed_fraction": counts.get("Mixed", 0) / total,
        "tamas_fraction": counts.get("Tamas", 0) / total,
        "determinant_health_fraction": int(np.sum(health)) / total,
        "min_iota_inverse_global": float(min_iota),
        "min_det_global": float(min_det),
        "mismatch_count": mismatch,
        "comparable_count": comparable,
        "records": records,
    }


def _plot_phase(codes, title, path: Path, config: NonlocalScanConfig):
    path.parent.mkdir(parents=True, exist_ok=True)
    colors = ["#4daf4a", "#377eb8", "#984ea3", "#ff7f00", "#dddddd", "#a6cee3", "#cab2d6", "#b15928", "#e41a1c"]
    cmap = matplotlib.colors.ListedColormap(colors)
    norm = matplotlib.colors.BoundaryNorm(np.arange(-0.5, len(PHASE_ORDER) + 0.5, 1), cmap.N)
    fig, ax = plt.subplots(figsize=(7.8, 6.2), constrained_layout=True)
    im = ax.imshow(np.asarray(codes), origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
    cb = fig.colorbar(im, ax=ax, ticks=np.arange(len(PHASE_ORDER)))
    cb.ax.set_yticklabels(PHASE_ORDER)
    ax.axvline(0, color="black", lw=0.55, alpha=0.5)
    ax.axhline(0, color="black", lw=0.55, alpha=0.5)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff = miota2 - sigma0")
    ax.set_title(title)
    fig.savefig(path, dpi=155)
    plt.close(fig)
    return str(path)


def _plot_mask(mask, title, path: Path, config: NonlocalScanConfig, cmap="Reds"):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.5, 5.8), constrained_layout=True)
    im = ax.imshow(np.asarray(mask, dtype=int), origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap=cmap, interpolation="nearest", vmin=0, vmax=1)
    fig.colorbar(im, ax=ax, ticks=[0, 1])
    ax.axvline(0, color="black", lw=0.55, alpha=0.5)
    ax.axhline(0, color="black", lw=0.55, alpha=0.5)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    fig.savefig(path, dpi=155)
    plt.close(fig)
    return str(path)


def plot_kernel_sanity(kernels, kp: NonlocalKernelParams, plot_dir: Path):
    q = np.linspace(0.0, kp.kmax * kp.kmax, 500)
    plot_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    fig, ax = plt.subplots(figsize=(7.5, 5), constrained_layout=True)
    for k in kernels:
        ax.plot(q, sigma_E(q, k, kp), label=k)
    ax.set_xlabel("q=k_E^2")
    ax.set_ylabel("Sigma_E(q)")
    ax.set_title("Memory kernels Sigma_E(q)")
    ax.grid(alpha=0.3)
    ax.legend()
    p = plot_dir / "kernels_sigmaE_vs_q.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["kernels_sigmaE_vs_q"] = str(p)
    fig, ax = plt.subplots(figsize=(7.5, 5), constrained_layout=True)
    for k in kernels:
        ax.plot(q, iota_inverse(q, kp.sigma0, k, kp), label=k)
    ax.set_xlabel("q=k_E^2")
    ax.set_ylabel("D_iota^{-1}(q), representative m_iota_local2=sigma0")
    ax.set_title("Representative iota inverse")
    ax.grid(alpha=0.3)
    ax.legend()
    p = plot_dir / "kernels_iota_inverse_vs_q.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["kernels_iota_inverse_vs_q"] = str(p)
    return paths


def _bar_summary(rows, metric, title, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [f"{r['slice']}\n{r['kernel']}" for r in rows]
    vals = [r[metric] for r in rows]
    fig, ax = plt.subplots(figsize=(max(8, 0.65 * len(rows)), 5.5), constrained_layout=True)
    ax.bar(range(len(vals)), vals)
    ax.set_xticks(range(len(vals)), labels, rotation=65, ha="right", fontsize=7)
    ax.set_ylabel(metric)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def write_report(payload, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["summary_rows"]
    sanity = payload["kernel_sanity"]
    def table(rows, cols):
        out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        for r in rows:
            vals=[]
            for c in cols:
                v=r.get(c, "")
                vals.append(f"{v:.4f}" if isinstance(v, float) else str(v))
            out.append("| " + " | ".join(vals) + " |")
        return out
    lines = [
        "# PQT-QG Nonlocal Memory Benchmark Report v0.7",
        "",
        "## 1. Goal",
        "Test momentum-dependent Euclidean memory self-energy `Sigma_E(k^2)` rather than only local memory sign conventions.",
        "",
        "## 2. Canon recovery context",
        "v0.6 showed plus/minus local memory signs are equivalent on the effective `miota2_eff` axis. v0.7 tests whether nonlocal momentum dependence changes phase mechanics.",
        "",
        "## 3. Kernel definitions",
        "- `local_constant`: `Sigma_E(q)=sigma0`.",
        "- `single_pole`: `Sigma_E(q)=sigma0*M2/(q+M2)`.",
        "- `exp_gap`: normalized gapped exponential spectral shape using `exp1`.",
        "",
        "## 4. Exact formula",
        "`Delta_iota^{-1}(k)=Z_iota*k^2+m_ss_local2-Sigma_E(k^2)`; no `LambdaT2_kappa0` is double counted in nonlocal mode.",
        "",
        "## 5. Numerical method",
        f"Grid: `{payload['config']['grid_shape']}`; kmax: `{payload['kernel_params']['kmax']}`; num_k: `{payload['kernel_params']['num_k']}`; determinant reference: same kernel at `(phi,r,s)=(0,0,0)`.",
        "v0.7 smoke uses the corrected local zero-mode active-set minimum as a deterministic phase point, then evaluates nonlocal determinant diagnostics and delta potentials there. Full nonlocal L-BFGS-B minimization is deferred to v0.8 because determinant integration is expensive. Results are cutoff/scheme dependent.",
        "",
        "## 6. Phase comparison table",
    ]
    lines += table(rows, ["slice", "kernel", "quadrant_agreement", "topology_status", "fraction_Prema", "fraction_Gurutva", "fraction_Tamas", "fraction_Mixed", "changed_phase_fraction_vs_local", "determinant_health_fraction"])
    lines += ["", "## 7. Kernel sanity results"]
    lines += table(sanity, ["kernel", "Sigma_E_0", "Sigma_E_kmax2", "monotone_nonincreasing", "min_iota_inverse_representative"])
    lines += ["", "## 8. Interpretation"]
    for r in rows:
        if r["kernel"] != "local_constant":
            lines.append(f"- `{r['slice']}` / `{r['kernel']}`: changed vs local `{r['changed_phase_fraction_vs_local']:.4f}`, Mixed delta `{r['delta_mixed_fraction_vs_local']:.4f}`, determinant health `{r['determinant_health_fraction']:.4f}`.")
    lines += [
        "- Single-pole closeness and exp-gap deformation should be judged by changed fraction, agreement, and determinant health columns.",
        "- v0.8 should include full nonlocal memory in loop-level scans only if determinant diagnostics remain controlled.",
        "",
        "## 9. Warnings",
        "- synthetic benchmark only",
        "- nonlocal Euclidean memory only",
        "- cutoff/scheme dependent",
        "- no full renormalization",
        "- no RG improvement",
        "- no physical prediction",
        "- no proof of PQT-QG",
        "- determinant flags are diagnostic, not a final stability theorem",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def run_nonlocal_benchmark(root: Path, grid: int = 31, num_k: int = 96, kmax: float = 5.0, kernels: Iterable[str] | None = None, slices: Iterable[str] | None = None, nonlocal_scale: float = 1.0, skip_plots: bool = False):
    kernels = list(kernels or ["local_constant", "single_pole", "exp_gap"])
    selected_names = set(slices or ["preserved", "baseline", "cooperative"])
    chosen_slices = []
    for s in SELECTED_SLICES:
        if any(s["name"].startswith(x) or x in s["name"] for x in selected_names):
            chosen_slices.append(s)
    config = NonlocalScanConfig(grid)
    kp = NonlocalKernelParams(kmax=kmax, num_k=num_k, nonlocal_scale=nonlocal_scale)
    data_dir = root / "outputs" / "data"
    plot_dir = root / "outputs" / "plots" / "nonlocal_memory_v0_7"
    report_dir = root / "outputs" / "reports"
    for d in (data_dir, plot_dir, report_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("PQT-QG Benchmark v0.7 — Nonlocal Sigma_E(k) Memory Kernel")
    print(f"grid={grid}; num_k={num_k}; kmax={kmax}; kernels={kernels}; nonlocal_scale={nonlocal_scale}")
    plots = {} if skip_plots else plot_kernel_sanity(kernels, kp, plot_dir)
    sanity = [kernel_sanity(k, kp) for k in kernels]
    results = []
    all_records = []
    by_slice_kernel = {}
    for sp in chosen_slices:
        local_result = None
        for kernel in kernels:
            print(f"\nscan slice={sp['name']} kernel={kernel}")
            res = scan_slice_kernel(dict(sp), kernel, config, kp)
            by_slice_kernel[(sp["name"], kernel)] = res
            if kernel == "local_constant":
                local_result = res
            results.append({k: v for k, v in res.items() if k != "records"})
            all_records.extend(res["records"])
            print("phase counts:", {k: v for k, v in res["phase_counts"].items() if v})
            print(f"agreement={res['quadrant_agreement']:.6f}; topology={res['topology_status']}; det health={res['determinant_health_fraction']:.6f}")
            if not skip_plots:
                plots[f"{sp['name']}_{kernel}_phase_map"] = _plot_phase(res["phase_codes"], f"{sp['name']} {kernel}", plot_dir / f"{sp['name']}_{kernel}_phase_map.png", config)
                plots[f"{sp['name']}_{kernel}_det_health_mask"] = _plot_mask(res["det_health_mask"], f"{sp['name']} {kernel} determinant health", plot_dir / f"{sp['name']}_{kernel}_det_health_mask.png", config, cmap="Greens")
        if not skip_plots and local_result is not None:
            local_codes = np.asarray(local_result["phase_codes"])
            for kernel in kernels:
                res = by_slice_kernel[(sp["name"], kernel)]
                mask = np.asarray(res["phase_codes"]) != local_codes
                plots[f"{sp['name']}_{kernel}_changed_mask_vs_local"] = _plot_mask(mask, f"{sp['name']} {kernel} changed vs local", plot_dir / f"{sp['name']}_{kernel}_changed_mask_vs_local.png", config)

    summary_rows = []
    for res in results:
        local = by_slice_kernel[(res["slice"], "local_constant")]
        changed = np.asarray(res["phase_codes"]) != np.asarray(local["phase_codes"])
        row = {
            "slice": res["slice"],
            "kernel": res["kernel"],
            "quadrant_agreement": res["quadrant_agreement"],
            "topology_status": res["topology_status"],
            "mixed_fraction": res["mixed_fraction"],
            "tamas_fraction": res["tamas_fraction"],
            "changed_phase_fraction_vs_local": int(np.sum(changed)) / changed.size,
            "changed_cells_count_vs_local": int(np.sum(changed)),
            "transition_matrix_vs_local": _transition_matrix(local["phase_codes"], res["phase_codes"]),
            "delta_mixed_fraction_vs_local": res["mixed_fraction"] - local["mixed_fraction"],
            "determinant_health_fraction": res["determinant_health_fraction"],
            "min_iota_inverse_global": res["min_iota_inverse_global"],
            "min_det_global": res["min_det_global"],
        }
        for ph in PHASE_ORDER:
            row[f"fraction_{ph}"] = res["phase_fractions"].get(ph, 0.0)
        summary_rows.append(row)
    if not skip_plots:
        plots["summary_changed_fraction_by_kernel"] = _bar_summary(summary_rows, "changed_phase_fraction_vs_local", "Changed fraction vs local", plot_dir / "summary_changed_fraction_by_kernel.png")
        plots["summary_quadrant_agreement_by_kernel"] = _bar_summary(summary_rows, "quadrant_agreement", "Quadrant agreement", plot_dir / "summary_quadrant_agreement_by_kernel.png")
        plots["summary_mixed_fraction_by_kernel"] = _bar_summary(summary_rows, "mixed_fraction", "Mixed fraction", plot_dir / "summary_mixed_fraction_by_kernel.png")

    payload = {"name": "PQT-QG Benchmark v0.7 — Nonlocal Sigma_E(k) Memory Kernel", "config": config.as_dict(), "kernel_params": asdict(kp), "kernels": kernels, "slices": chosen_slices, "kernel_sanity": sanity, "results": results, "summary_rows": summary_rows, "plots": plots}
    json_path = data_dir / "nonlocal_memory_benchmark_v0_7.json"
    csv_path = data_dir / "nonlocal_memory_benchmark_v0_7.csv"
    summary_path = data_dir / "nonlocal_memory_summary_v0_7.json"
    report_path = report_dir / "PQT_QG_Nonlocal_Memory_Benchmark_Report_v0_7.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(all_records).to_csv(csv_path, index=False)
    summary_path.write_text(json.dumps({"summary_rows": summary_rows, "kernel_sanity": sanity, "plots": plots}, indent=2), encoding="utf-8")
    report = write_report(payload, report_path)
    print(f"\nwrote data: {json_path}")
    print(f"wrote data: {csv_path}")
    print(f"wrote data: {summary_path}")
    print(f"wrote report: {report}")
    return {"json": json_path, "csv": csv_path, "summary": summary_path, "report": report_path, "plot_dir": plot_dir}


