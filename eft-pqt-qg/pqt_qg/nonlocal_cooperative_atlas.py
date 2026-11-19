"""Nonlocal Cooperative Atlas v0.9."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .field_bound_stress import scan_bound_mode
from .nonlocal_memory import NonlocalKernelParams
from .nonlocal_validation import canonical_point, symmetry_reduced_delta
from .phase_boundary import PHASE_ORDER, PHASE_TO_CODE

ATLAS_CLASS_ORDER = [
    "stable_mixed_core",
    "nonlocal_mixed_conversion",
    "nonlocal_phase_disruption",
    "determinant_stress",
    "optimizer_suspect",
    "boundary_caution",
    "other",
]
ATLAS_CLASS_CODE = {name: i for i, name in enumerate(ATLAS_CLASS_ORDER)}

BOUND_MODE_ALIASES = {"phi3": "phi3", "soft25": "soft25"}


def _kernel_alias(k: str) -> str:
    return "local_constant" if k == "local" else k


def _augment_records(records: list[dict[str, Any]], local_records: list[dict[str, Any]] | None, phi_upper: float) -> list[dict[str, Any]]:
    local_map = {(r["mrho2"], r["miota2_eff"]): r for r in local_records} if local_records else None
    out = []
    for r in records:
        row = dict(r)
        if local_map:
            loc = local_map[(r["mrho2"], r["miota2_eff"])]
        else:
            loc = r
        lp = np.array([loc["phi"], loc["r"], loc["s"]], dtype=float)
        npnt = np.array([r["phi"], r["r"], r["s"]], dtype=float)
        cp_l = canonical_point(lp)
        cp_n = canonical_point(npnt)
        row.update(
            {
                "local_phase": loc["phase"],
                "nonlocal_phase": r["phase"],
                "phase_changed": loc["phase"] != r["phase"],
                "local_point": lp.tolist(),
                "nonlocal_point": npnt.tolist(),
                "canonical_local_point": cp_l.tolist(),
                "canonical_nonlocal_point": cp_n.tolist(),
                "raw_delta_position_norm": float(np.linalg.norm(npnt - lp)),
                "canonical_delta_position_norm": float(np.linalg.norm(cp_n - cp_l)),
                "symmetry_reduced_delta_position_norm": symmetry_reduced_delta(lp, npnt),
                "delta_phi": float(npnt[0] - lp[0]),
                "delta_abs_r": float(abs(npnt[1]) - abs(lp[1])),
                "delta_abs_s": float(abs(npnt[2]) - abs(lp[2])),
                "objective_delta": float(r["objective_value"] - loc["objective_value"]),
                "phi_at_upper_bound": bool(abs(r["phi"] - phi_upper) < 1e-4),
                "phi_near_upper_bound": bool(r["phi"] > phi_upper - 0.05),
            }
        )
        row["atlas_class"] = classify_atlas_effect(row)
        out.append(row)
    return out


def classify_atlas_effect(row: dict[str, Any]) -> str:
    if not row.get("optimizer_success", False):
        return "optimizer_suspect"
    if not row.get("determinant_health", False):
        return "determinant_stress"
    if row.get("phi_near_upper_bound", False):
        return "boundary_caution"
    lp, np_ = row["local_phase"], row["nonlocal_phase"]
    if lp == "Mixed" and np_ == "Mixed":
        return "stable_mixed_core"
    if lp in ["Gurutva", "Tamas", "Other", "Rho_only", "Iota_only"] and np_ == "Mixed":
        return "nonlocal_mixed_conversion"
    if lp == "Mixed" and np_ != "Mixed":
        return "nonlocal_phase_disruption"
    return "other"


def _transition(records):
    out = {p: {q: 0 for q in PHASE_ORDER} for p in PHASE_ORDER}
    for r in records:
        out.setdefault(r["local_phase"], {q: 0 for q in PHASE_ORDER})[r["nonlocal_phase"]] += 1
    return out


def _counts(records, key):
    return {p: sum(1 for r in records if r[key] == p) for p in PHASE_ORDER}


def summarize_kernel(kernel: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    phase_counts = _counts(records, "nonlocal_phase")
    class_counts = {c: sum(1 for r in records if r["atlas_class"] == c) for c in ATLAS_CLASS_ORDER}
    changed = [r for r in records if r["phase_changed"]]
    failed_changed = [r for r in changed if not r["optimizer_success"]]
    return {
        "kernel": kernel,
        "phase_counts": phase_counts,
        "phase_fractions": {k: v / n for k, v in phase_counts.items()},
        "mixed_fraction": phase_counts.get("Mixed", 0) / n,
        "other_fraction": phase_counts.get("Other", 0) / n,
        "gurutva_fraction": phase_counts.get("Gurutva", 0) / n,
        "tamas_fraction": phase_counts.get("Tamas", 0) / n,
        "changed_phase_fraction": len(changed) / n,
        "changed_cells_count": len(changed),
        "transition_matrix": _transition(records),
        "Gurutva_to_Mixed": sum(1 for r in records if r["local_phase"] == "Gurutva" and r["nonlocal_phase"] == "Mixed"),
        "Tamas_to_Mixed": sum(1 for r in records if r["local_phase"] == "Tamas" and r["nonlocal_phase"] == "Mixed"),
        "Other_to_Mixed": sum(1 for r in records if r["local_phase"] == "Other" and r["nonlocal_phase"] == "Mixed"),
        "Mixed_to_Mixed": sum(1 for r in records if r["local_phase"] == "Mixed" and r["nonlocal_phase"] == "Mixed"),
        "Mixed_to_nonMixed": sum(1 for r in records if r["local_phase"] == "Mixed" and r["nonlocal_phase"] != "Mixed"),
        "atlas_class_counts": class_counts,
        "atlas_class_fractions": {k: v / n for k, v in class_counts.items()},
        "determinant_health_fraction": float(np.mean([r["determinant_health"] for r in records])),
        "min_iota_inverse_global": float(np.min([r["min_iota_inverse"] for r in records])),
        "min_det_global": float(np.min([r["min_det"] for r in records])),
        "optimizer_success_fraction": float(np.mean([r["optimizer_success"] for r in records])),
        "failed_changed_cell_count": len(failed_changed),
        "max_phi": float(np.max([r["phi"] for r in records])),
        "avg_phi": float(np.mean([r["phi"] for r in records])),
        "fraction_phi_near_upper_bound": float(np.mean([r["phi_near_upper_bound"] for r in records])),
        "avg_raw_delta": float(np.mean([r["raw_delta_position_norm"] for r in records])),
        "max_raw_delta": float(np.max([r["raw_delta_position_norm"] for r in records])),
        "avg_canonical_delta": float(np.mean([r["canonical_delta_position_norm"] for r in records])),
        "max_canonical_delta": float(np.max([r["canonical_delta_position_norm"] for r in records])),
        "avg_symmetry_reduced_delta": float(np.mean([r["symmetry_reduced_delta_position_norm"] for r in records])),
        "max_symmetry_reduced_delta": float(np.max([r["symmetry_reduced_delta_position_norm"] for r in records])),
    }


def _grid_from_records(records, value_key: str, grid: int):
    vals = [r[value_key] for r in records]
    return np.asarray(vals).reshape(grid, grid)


def _phase_grid(records, key: str, grid: int):
    vals = [PHASE_TO_CODE.get(r[key], PHASE_TO_CODE["Other"]) for r in records]
    return np.asarray(vals).reshape(grid, grid)


def _class_grid(records, grid: int):
    vals = [ATLAS_CLASS_CODE.get(r["atlas_class"], ATLAS_CLASS_CODE["other"]) for r in records]
    return np.asarray(vals).reshape(grid, grid)


def _plot_grid(grid_data, title, path: Path, extent, cmap="viridis", discrete_labels=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.4, 5.8), constrained_layout=True)
    if discrete_labels:
        cmap_obj = plt.get_cmap(cmap, len(discrete_labels)) if isinstance(cmap, str) else cmap
        im = ax.imshow(grid_data, origin="lower", extent=extent, aspect="auto", cmap=cmap_obj, interpolation="nearest", vmin=0, vmax=len(discrete_labels)-1)
        cb = fig.colorbar(im, ax=ax, ticks=range(len(discrete_labels)))
        cb.ax.set_yticklabels(discrete_labels)
    else:
        im = ax.imshow(grid_data, origin="lower", extent=extent, aspect="auto", cmap=cmap, interpolation="nearest")
        fig.colorbar(im, ax=ax)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def _bar(rows, metric, title, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [r["kernel"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 4.8), constrained_layout=True)
    ax.bar(labels, [r[metric] for r in rows])
    ax.set_title(title)
    ax.set_ylabel(metric)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def write_report(payload, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["summary_rows"]
    def table(rows, cols):
        out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"]*len(cols)) + "|"]
        for r in rows:
            vals=[]
            for c in cols:
                v=r.get(c, "")
                vals.append(f"{v:.5g}" if isinstance(v,float) else str(v))
            out.append("| " + " | ".join(vals) + " |")
        return out
    lines = [
        "# PQT-QG Nonlocal Cooperative Atlas Report v0.9",
        "",
        "## 1. Goal",
        "Map the wider cooperative nonlocal-memory sector after v0.8–v0.8.2 validation.",
        "",
        "## 2. Why v0.9 is justified",
        "v0.8 showed phase changes under full nonlocal minimization; v0.8.1 showed they were not sign-symmetry or optimizer artifacts; v0.8.2 showed the Mixed attractor was not just a phi=2 boundary artifact.",
        "",
        "## 3. Canon assumptions",
        "Synthetic Euclidean nonlocal memory benchmark; cutoff/scheme dependent; no physical prediction or proof of PQT-QG.",
        "",
        "## 4. Numerical setup",
        f"Region `{payload['region']}`, grid `{payload['grid']}`, kernels `{payload['kernels']}`, kmax `{payload['kmax']}`, num_k `{payload['num_k']}`, bounds `{payload['bounds']}`, bound mode `{payload['bound_mode']}`.",
        "",
        "## 5. Phase table",
    ]
    lines += table(rows, ["kernel", "mixed_fraction", "other_fraction", "gurutva_fraction", "tamas_fraction", "count_Mixed", "count_Gurutva", "count_Tamas", "count_Other"])
    lines += ["", "## 6. Transition table"]
    lines += table(rows, ["kernel", "changed_phase_fraction", "Gurutva_to_Mixed", "Tamas_to_Mixed", "Other_to_Mixed", "Mixed_to_Mixed", "Mixed_to_nonMixed"])
    lines += ["", "## 7. Nonlocal effect atlas fractions"]
    for c in ATLAS_CLASS_ORDER:
        for r in rows:
            r[f"frac_{c}"] = r["atlas_class_fractions"].get(c, 0.0)
    lines += table(rows, ["kernel", "frac_stable_mixed_core", "frac_nonlocal_mixed_conversion", "frac_nonlocal_phase_disruption", "frac_determinant_stress", "frac_optimizer_suspect", "frac_boundary_caution"])
    lines += ["", "## 8. Determinant health"]
    lines += table(rows, ["kernel", "determinant_health_fraction", "min_iota_inverse_global", "min_det_global", "optimizer_success_fraction", "failed_changed_cell_count"])
    lines += ["", "## 9. Boundary audit"]
    lines += table(rows, ["kernel", "max_phi", "avg_phi", "fraction_phi_near_upper_bound"])
    lines += ["", "## 10. Canonical distance audit"]
    lines += table(rows, ["kernel", "avg_raw_delta", "max_raw_delta", "avg_canonical_delta", "max_canonical_delta", "avg_symmetry_reduced_delta", "max_symmetry_reduced_delta"])
    lines += ["", "## 11. Interpretation"]
    for r in rows:
        lines.append(f"- `{r['kernel']}`: Mixed fraction `{r['mixed_fraction']:.4f}`, conversion fraction `{r['atlas_class_fractions'].get('nonlocal_mixed_conversion',0):.4f}`, determinant health `{r['determinant_health_fraction']:.4f}`, boundary caution `{r['atlas_class_fractions'].get('boundary_caution',0):.4f}`.")
    lines += ["", "## 12. Warnings", "- atlas still synthetic", "- no physical prediction", "- no RG", "- no full renormalization", "- determinant health diagnostic, not theorem", "- cutoff/scheme dependence"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def run_atlas(root: Path, grid: int=21, num_k: int=96, kmax: float=5.0, kernels: Iterable[str]|None=None, bound_mode: str="phi3", wall_strength: float=1.0, max_seeds: str="all", skip_plots: bool=False):
    kernels = [_kernel_alias(k) for k in (kernels or ["local_constant", "single_pole", "exp_gap"])]
    if bound_mode not in BOUND_MODE_ALIASES:
        raise ValueError(f"unsupported bound_mode {bound_mode}")
    bm = BOUND_MODE_ALIASES[bound_mode]
    kp = NonlocalKernelParams(kmax=kmax, num_k=num_k)
    data_dir = root / "outputs" / "data"
    plot_dir = root / "outputs" / "plots" / "nonlocal_cooperative_v0_9"
    report_dir = root / "outputs" / "reports"
    for d in (data_dir, plot_dir, report_dir):
        d.mkdir(parents=True, exist_ok=True)
    print("PQT-QG Benchmark v0.9 — Nonlocal Cooperative Atlas")
    print(f"grid={grid}; kernels={kernels}; bound_mode={bound_mode}; kmax={kmax}; num_k={num_k}")
    all_records=[]; summary_rows=[]; plots={}; results={}; local_records=None
    for kernel in kernels:
        print(f"\n=== kernel {kernel} ===")
        res = scan_bound_mode(kernel, bm, grid, kp, wall_strength, include_phi4=False)
        if kernel == "local_constant":
            local_records = res["records"]
        if local_records is None:
            # If local not requested, compare kernel to itself.
            local_records = res["records"]
        aug = _augment_records(res["records"], local_records, phi_upper=res["config"]["field_bounds"][0][1])
        results[kernel] = {"records": aug, "config": res["config"]}
        all_records.extend(aug)
        summ = summarize_kernel(kernel, aug)
        summ.update({f"count_{p}": summ["phase_counts"].get(p,0) for p in PHASE_ORDER})
        summary_rows.append(summ)
        print("phase counts:", {k:v for k,v in summ["phase_counts"].items() if v})
        print(f"mixed={summ['mixed_fraction']:.4f}; changed={summ['changed_phase_fraction']:.4f}; det_health={summ['determinant_health_fraction']:.4f}; boundary={summ['atlas_class_fractions'].get('boundary_caution',0):.4f}; opt={summ['optimizer_success_fraction']:.4f}")
        if not skip_plots:
            cfg=res["config"]; extent=[*cfg["mrho2_range"], *cfg["miota2_eff_range"]]
            plots[f"{kernel}_phase_map"]=_plot_grid(_phase_grid(aug,"nonlocal_phase",grid), f"{kernel} phase map", plot_dir/f"{kernel}_phase_map.png", extent, cmap="tab10", discrete_labels=PHASE_ORDER)
            plots[f"{kernel}_mixed_conversion_mask"]=_plot_grid(np.array([r["atlas_class"]=="nonlocal_mixed_conversion" for r in aug]).reshape(grid,grid), f"{kernel} mixed conversion", plot_dir/f"{kernel}_mixed_conversion_mask.png", extent, cmap="Reds")
            plots[f"{kernel}_phase_changed_mask_vs_local"]=_plot_grid(np.array([r["phase_changed"] for r in aug]).reshape(grid,grid), f"{kernel} changed vs local", plot_dir/f"{kernel}_phase_changed_mask_vs_local.png", extent, cmap="Reds")
            plots[f"{kernel}_det_health_mask"]=_plot_grid(np.array([r["determinant_health"] for r in aug]).reshape(grid,grid), f"{kernel} det health", plot_dir/f"{kernel}_det_health_mask.png", extent, cmap="Greens")
            plots[f"{kernel}_phi_heatmap"]=_plot_grid(_grid_from_records(aug,"phi",grid), f"{kernel} phi", plot_dir/f"{kernel}_phi_heatmap.png", extent)
            plots[f"{kernel}_phi_near_bound_mask"]=_plot_grid(np.array([r["phi_near_upper_bound"] for r in aug]).reshape(grid,grid), f"{kernel} phi near bound", plot_dir/f"{kernel}_phi_near_bound_mask.png", extent, cmap="Reds")
            plots[f"{kernel}_canonical_delta_heatmap"]=_plot_grid(_grid_from_records(aug,"canonical_delta_position_norm",grid), f"{kernel} canonical delta", plot_dir/f"{kernel}_canonical_delta_heatmap.png", extent)
            plots[f"{kernel}_objective_delta_heatmap"]=_plot_grid(_grid_from_records(aug,"objective_delta",grid), f"{kernel} objective delta", plot_dir/f"{kernel}_objective_delta_heatmap.png", extent)
            plots[f"{kernel}_atlas_class_map"]=_plot_grid(_class_grid(aug,grid), f"{kernel} atlas class", plot_dir/f"{kernel}_atlas_class_map.png", extent, cmap="tab10", discrete_labels=ATLAS_CLASS_ORDER)
    if not skip_plots:
        plots["summary_mixed_fraction_by_kernel"]=_bar(summary_rows,"mixed_fraction","Mixed fraction by kernel",plot_dir/"summary_mixed_fraction_by_kernel.png")
        plots["summary_changed_phase_fraction_by_kernel"]=_bar(summary_rows,"changed_phase_fraction","Changed phase fraction",plot_dir/"summary_changed_phase_fraction_by_kernel.png")
        plots["summary_det_health_by_kernel"]=_bar(summary_rows,"determinant_health_fraction","Determinant health",plot_dir/"summary_det_health_by_kernel.png")
        for r in summary_rows:
            r["boundary_caution_fraction"] = r["atlas_class_fractions"].get("boundary_caution",0.0)
        plots["summary_boundary_caution_by_kernel"]=_bar(summary_rows,"boundary_caution_fraction","Boundary caution",plot_dir/"summary_boundary_caution_by_kernel.png")
        plots["summary_canonical_delta_by_kernel"]=_bar(summary_rows,"avg_canonical_delta","Average canonical delta",plot_dir/"summary_canonical_delta_by_kernel.png")
    payload={"name":"PQT-QG Benchmark v0.9 — Nonlocal Cooperative Atlas","grid":grid,"region":{"mrho2_range":[-0.8,0.1],"miota2_eff_range":[-0.8,0.1]},"kernels":kernels,"kmax":kmax,"num_k":num_k,"bound_mode":bound_mode,"bounds":results[kernels[0]]["config"]["field_bounds"],"summary_rows":summary_rows,"plots":plots}
    json_path=data_dir/"nonlocal_cooperative_atlas_v0_9.json"; csv_path=data_dir/"nonlocal_cooperative_atlas_v0_9.csv"; summary_path=data_dir/"nonlocal_cooperative_atlas_summary_v0_9.json"; changed_path=data_dir/"nonlocal_cooperative_atlas_changed_cells_v0_9.json"; report_path=report_dir/"PQT_QG_Nonlocal_Cooperative_Atlas_Report_v0_9.md"
    json_path.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    pd.DataFrame(all_records).to_csv(csv_path,index=False)
    summary_path.write_text(json.dumps({"summary_rows":summary_rows,"plots":plots},indent=2),encoding="utf-8")
    changed=[r for r in all_records if r["phase_changed"]]
    changed_path.write_text(json.dumps(changed,indent=2),encoding="utf-8")
    report=write_report(payload,report_path)
    print(f"wrote data: {json_path}"); print(f"wrote data: {csv_path}"); print(f"wrote data: {summary_path}"); print(f"wrote data: {changed_path}"); print(f"wrote report: {report}")
    return {"json":json_path,"csv":csv_path,"summary":summary_path,"changed_cells":changed_path,"report":report_path,"plot_dir":plot_dir}
