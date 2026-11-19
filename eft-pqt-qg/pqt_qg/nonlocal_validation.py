"""Validation patch for PQT-QG nonlocal micro-scan v0.8.1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .nonlocal_minimize import MicroScanConfig, scan_kernel, summarize, COOPERATIVE_SLICE, _plot_grid
from .nonlocal_memory import NonlocalKernelParams


def canonical_point(p):
    p = np.asarray(p, dtype=float)
    return np.array([p[0], abs(p[1]), abs(p[2])], dtype=float)


def symmetry_reduced_delta(local_p, nonlocal_p):
    lp = np.asarray(local_p, dtype=float)
    npnt = np.asarray(nonlocal_p, dtype=float)
    vals = []
    for er in (1.0, -1.0):
        for es in (1.0, -1.0):
            vals.append(np.linalg.norm(np.array([npnt[0], er * npnt[1], es * npnt[2]]) - lp))
    return float(min(vals))


def add_validation_metrics(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in records:
        lp = np.array([r["local_phi"], r["local_r"], r["local_s"]], dtype=float)
        npnt = np.array([r["nonlocal_phi"], r["nonlocal_r"], r["nonlocal_s"]], dtype=float)
        row = dict(r)
        row["raw_delta_position_norm"] = float(np.linalg.norm(npnt - lp))
        row["canonical_local_point"] = canonical_point(lp).tolist()
        row["canonical_nonlocal_point"] = canonical_point(npnt).tolist()
        row["canonical_delta_position_norm"] = float(np.linalg.norm(canonical_point(npnt) - canonical_point(lp)))
        row["symmetry_reduced_delta_position_norm"] = symmetry_reduced_delta(lp, npnt)
        row["local_det_health"] = None  # local diagnostics are represented by local_constant run; kept for audit schema
        row["nonlocal_det_health"] = bool(row.get("determinant_health", False))
        row["local_point"] = lp.tolist()
        row["nonlocal_point"] = npnt.tolist()
        out.append(row)
    return out


def transition_counts(records):
    pairs = [("Gurutva", "Mixed"), ("Tamas", "Mixed"), ("Other", "Mixed"), ("Mixed", "Mixed")]
    return {f"{a}_to_{b}": sum(1 for r in records if r["local_phase"] == a and r["nonlocal_phase"] == b) for a, b in pairs}


def summarize_validation(kernel: str, records: list[dict[str, Any]], base_summary: dict[str, Any]) -> dict[str, Any]:
    raw = [r["raw_delta_position_norm"] for r in records]
    canon = [r["canonical_delta_position_norm"] for r in records]
    sym = [r["symmetry_reduced_delta_position_norm"] for r in records]
    failed = [r for r in records if not r.get("optimizer_success", False)]
    changed = [r for r in records if r.get("phase_changed", False)]
    failed_changed = [r for r in changed if not r.get("optimizer_success", False)]
    failed_unhealthy = [r for r in failed if not r.get("determinant_health", False)]
    return {
        "kernel": kernel,
        **base_summary,
        "average_raw_delta_position_norm": float(np.mean(raw)),
        "max_raw_delta_position_norm": float(np.max(raw)),
        "average_canonical_delta_position_norm": float(np.mean(canon)),
        "max_canonical_delta_position_norm": float(np.max(canon)),
        "average_symmetry_reduced_delta_position_norm": float(np.mean(sym)),
        "max_symmetry_reduced_delta_position_norm": float(np.max(sym)),
        "changed_cell_count": len(changed),
        "failed_cell_count": len(failed),
        "failed_changed_cell_count": len(failed_changed),
        "failed_unhealthy_cell_count": len(failed_unhealthy),
        "changed_cells_optimizer_success_fraction": float(np.mean([r.get("optimizer_success", False) for r in changed])) if changed else 1.0,
        **transition_counts(records),
    }


def _run_spec(name: str, grid: int, num_k: int, kmax: float):
    return {"run_name": name, "grid": grid, "num_k": num_k, "kmax": kmax}


def validation_specs(mode: str, grid: int, num_k: int, kmax: float):
    if mode == "reproduce":
        return [_run_spec("runA_reproduce", grid, num_k, kmax)]
    if mode == "resolution":
        return [_run_spec("runB_resolution", grid, num_k, kmax)]
    if mode == "cutoff":
        return [_run_spec("runC_cutoff", grid, num_k, kmax)]
    if mode == "all":
        return [_run_spec("runA_reproduce", 11, 96, 5.0), _run_spec("runB_resolution", grid, num_k, kmax)]
    raise ValueError(mode)


def _plot_bar(rows, metric_a, metric_b, title, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [f"{r['run_name']}\n{r['kernel']}" for r in rows]
    x = np.arange(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(max(8, 0.65 * len(labels)), 5.2), constrained_layout=True)
    ax.bar(x - width / 2, [r[metric_a] for r in rows], width, label=metric_a)
    ax.bar(x + width / 2, [r[metric_b] for r in rows], width, label=metric_b)
    ax.set_xticks(x, labels, rotation=65, ha="right", fontsize=7)
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def _plot_metric(rows, metric, title, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [f"{r['run_name']}\n{r['kernel']}" for r in rows]
    fig, ax = plt.subplots(figsize=(max(8, 0.65 * len(labels)), 5.2), constrained_layout=True)
    ax.bar(range(len(rows)), [r[metric] for r in rows])
    ax.set_xticks(range(len(rows)), labels, rotation=65, ha="right", fontsize=7)
    ax.set_title(title)
    ax.set_ylabel(metric)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def _plot_changed_scatter(records, title, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    changed = [r for r in records if r.get("phase_changed", False)]
    fig, ax = plt.subplots(figsize=(6.5, 5.3), constrained_layout=True)
    if changed:
        ax.scatter([r["mrho2"] for r in changed], [r["miota2_eff"] for r in changed], c=[r["canonical_delta_position_norm"] for r in changed], cmap="plasma", s=45)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    ax.grid(alpha=0.25)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def _resolution_stability(summary_rows):
    by_kernel = {}
    for r in summary_rows:
        by_kernel.setdefault(r["kernel"], []).append(r)
    out = []
    for kernel, rows in by_kernel.items():
        if len(rows) < 2:
            continue
        rows = sorted(rows, key=lambda r: r["grid"])
        diff = abs(rows[-1]["changed_phase_fraction"] - rows[0]["changed_phase_fraction"])
        label = "stable" if diff < 0.03 else "mildly resolution-sensitive" if diff < 0.08 else "unstable"
        out.append({"kernel": kernel, "changed_fraction_diff": diff, "resolution_stability": label, "from_grid": rows[0]["grid"], "to_grid": rows[-1]["grid"]})
    return out


def write_report(payload, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["summary_rows"]
    changed = payload["changed_cells"]
    stability = payload["resolution_stability"]
    def table(rows, cols, max_rows=None):
        rr = rows[:max_rows] if max_rows else rows
        out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        for r in rr:
            vals=[]
            for c in cols:
                v=r.get(c, "")
                vals.append(f"{v:.5g}" if isinstance(v, float) else str(v))
            out.append("| " + " | ".join(vals) + " |")
        return out
    lines = [
        "# PQT-QG Nonlocal Micro-Scan Validation Report v0.8.1",
        "",
        "## 1. Goal",
        "Validate the v0.8 full nonlocal minimization result before expanding to a v0.9 atlas.",
        "",
        "## 2. Why validation is needed",
        "v0.8 found phase changes for single-pole/exp-gap kernels, determinant-health improvement, and a large max delta. v0.8.1 checks sign-symmetry reduction, changed-cell details, optimizer reliability, and resolution stability.",
        "",
        "## 3. Canon assumptions",
        "Synthetic benchmark only; Euclidean nonlocal memory; no physical prediction; no proof of PQT-QG.",
        "",
        "## 4. Numerical setup",
        f"Runs: `{payload['run_specs']}`. Kernels: `{payload['kernels']}`. Objective and seeds reuse v0.8 full nonlocal minimization.",
        "",
        "## 5. Symmetry-distance analysis",
    ]
    lines += table(rows, ["run_name", "kernel", "max_raw_delta_position_norm", "max_symmetry_reduced_delta_position_norm", "max_canonical_delta_position_norm", "average_raw_delta_position_norm", "average_symmetry_reduced_delta_position_norm", "average_canonical_delta_position_norm"])
    lines += ["", "## 6. Changed-cell audit"]
    lines += table(changed, ["run_name", "kernel", "mrho2", "miota2_eff", "local_phase", "nonlocal_phase", "raw_delta_position_norm", "canonical_delta_position_norm", "symmetry_reduced_delta_position_norm", "optimizer_success"], max_rows=80)
    lines += ["", "## 7. Resolution check"]
    if stability:
        lines += table(stability, ["kernel", "changed_fraction_diff", "resolution_stability", "from_grid", "to_grid"])
    else:
        lines.append("Only one run was executed; resolution comparison not available.")
    lines += ["", "## 8. Kernel validation table"]
    lines += table(rows, ["run_name", "kernel", "changed_phase_fraction", "Gurutva_to_Mixed", "Tamas_to_Mixed", "Other_to_Mixed", "Mixed_to_Mixed", "determinant_health_fraction", "optimizer_success_fraction", "failed_changed_cell_count"])
    lines += ["", "## 9. Main answer"]
    for r in rows:
        artifact = "sign-symmetry dominated" if r["max_canonical_delta_position_norm"] < 0.25 and r["max_raw_delta_position_norm"] > 1.0 else "real canonical displacement present"
        lines.append(f"- `{r['run_name']}` / `{r['kernel']}`: changed `{r['changed_phase_fraction']:.4f}`, max raw `{r['max_raw_delta_position_norm']:.4f}`, max canonical `{r['max_canonical_delta_position_norm']:.4f}` => {artifact}.")
    lines += ["", "## 10. Warnings", "- micro-scan only", "- cutoff/scheme dependent", "- optimizer-sensitive", "- determinant health diagnostic, not theorem", "- no RG improvement", "- no physical prediction"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def run_validation(root: Path, validation_mode: str = "reproduce", grid: int = 11, num_k: int = 96, kmax: float = 5.0, kernels: Iterable[str] | None = None, skip_plots: bool = False):
    kernels = ["local_constant" if k == "local" else k for k in (kernels or ["local_constant", "single_pole", "exp_gap"])]
    specs = validation_specs(validation_mode, grid, num_k, kmax)
    data_dir = root / "outputs" / "data"
    plot_dir = root / "outputs" / "plots" / "nonlocal_micro_v0_8_1"
    report_dir = root / "outputs" / "reports"
    for d in (data_dir, plot_dir, report_dir):
        d.mkdir(parents=True, exist_ok=True)
    print("PQT-QG Benchmark v0.8.1 — Nonlocal Micro-Scan Validation Patch")
    all_rows=[]
    summary_rows=[]
    changed_cells=[]
    plots={}
    for spec in specs:
        config=MicroScanConfig(grid=spec['grid'])
        kp=NonlocalKernelParams(kmax=spec['kmax'], num_k=spec['num_k'])
        for kernel in kernels:
            print(f"\nrun={spec['run_name']} kernel={kernel} grid={spec['grid']} num_k={spec['num_k']} kmax={spec['kmax']}")
            res=scan_kernel(kernel, config, kp, "all")
            records=add_validation_metrics(res['records'])
            base=summarize(res)
            summ=summarize_validation(kernel, records, base)
            summ.update(spec)
            summary_rows.append(summ)
            for r in records:
                r.update(spec)
                all_rows.append(r)
                if r.get('phase_changed', False):
                    changed_cells.append(r)
            print(f"changed_phase_fraction={summ['changed_phase_fraction']:.4f}; max_raw_delta={summ['max_raw_delta_position_norm']:.4f}; max_canonical_delta={summ['max_canonical_delta_position_norm']:.4f}; det_health={summ['determinant_health_fraction']:.4f}; opt_success={summ['optimizer_success_fraction']:.4f}")
            if not skip_plots:
                prefix=f"{spec['run_name']}_{kernel}"
                plots[f"{prefix}_phase_changed_mask"]=_plot_grid(res['changed_mask'].astype(int), f"{prefix} changed mask", plot_dir/f"{prefix}_phase_changed_mask.png", config, cmap='Reds')
                raw_grid=np.array([r['raw_delta_position_norm'] for r in records]).reshape(config.grid_shape[1], config.grid_shape[0])
                can_grid=np.array([r['canonical_delta_position_norm'] for r in records]).reshape(config.grid_shape[1], config.grid_shape[0])
                plots[f"{prefix}_raw_delta_position_norm"]=_plot_grid(raw_grid, f"{prefix} raw delta", plot_dir/f"{prefix}_raw_delta_position_norm.png", config)
                plots[f"{prefix}_canonical_delta_position_norm"]=_plot_grid(can_grid, f"{prefix} canonical delta", plot_dir/f"{prefix}_canonical_delta_position_norm.png", config)
                plots[f"{prefix}_det_health_mask"]=_plot_grid(res['det_health_mask'].astype(int), f"{prefix} det health", plot_dir/f"{prefix}_det_health_mask.png", config, cmap='Greens')
                plots[f"{prefix}_min_iota_inverse_heatmap"]=_plot_grid(res['min_iota_inverse_grid'], f"{prefix} min iota inverse", plot_dir/f"{prefix}_min_iota_inverse_heatmap.png", config)
                plots[f"{prefix}_min_det_heatmap"]=_plot_grid(res['min_det_grid'], f"{prefix} min det", plot_dir/f"{prefix}_min_det_heatmap.png", config)
                plots[f"{prefix}_changed_cells_scatter"]=_plot_changed_scatter(records, f"{prefix} changed cells", plot_dir/f"{prefix}_changed_cells_scatter.png")
    stability=_resolution_stability(summary_rows)
    if not skip_plots:
        plots['summary_raw_vs_canonical_delta_by_kernel']=_plot_bar(summary_rows, 'max_raw_delta_position_norm', 'max_canonical_delta_position_norm', 'Raw vs canonical max delta', plot_dir/'summary_raw_vs_canonical_delta_by_kernel.png')
        plots['summary_changed_fraction_resolution_check']=_plot_metric(summary_rows, 'changed_phase_fraction', 'Changed fraction resolution check', plot_dir/'summary_changed_fraction_resolution_check.png')
        plots['summary_det_health_resolution_check']=_plot_metric(summary_rows, 'determinant_health_fraction', 'Det health resolution check', plot_dir/'summary_det_health_resolution_check.png')
    payload={"name":"PQT-QG Benchmark v0.8.1 — Nonlocal Micro-Scan Validation Patch", "run_specs": specs, "kernels": kernels, "summary_rows": summary_rows, "changed_cells": changed_cells, "resolution_stability": stability, "plots": plots}
    json_path=data_dir/'nonlocal_micro_validation_v0_8_1.json'
    csv_path=data_dir/'nonlocal_micro_validation_v0_8_1.csv'
    summary_path=data_dir/'nonlocal_micro_validation_summary_v0_8_1.json'
    changed_path=data_dir/'nonlocal_micro_validation_changed_cells_v0_8_1.json'
    report_path=report_dir/'PQT_QG_Nonlocal_Micro_Validation_Report_v0_8_1.md'
    json_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    pd.DataFrame(all_rows).to_csv(csv_path, index=False)
    summary_path.write_text(json.dumps({"summary_rows": summary_rows, "resolution_stability": stability, "plots": plots}, indent=2), encoding='utf-8')
    changed_path.write_text(json.dumps(changed_cells, indent=2), encoding='utf-8')
    report=write_report(payload, report_path)
    print(f"wrote data: {json_path}")
    print(f"wrote data: {csv_path}")
    print(f"wrote data: {summary_path}")
    print(f"wrote data: {changed_path}")
    print(f"wrote report: {report}")
    return {"json":json_path,"csv":csv_path,"summary":summary_path,"changed_cells":changed_path,"report":report_path,"plot_dir":plot_dir}
