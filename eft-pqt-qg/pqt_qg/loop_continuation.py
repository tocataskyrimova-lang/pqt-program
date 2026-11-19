"""PQT-QG Benchmark v0.5 loop-scale continuation.

Extends v0.4 local Coleman-Weinberg maps by scanning loop_scale from 0 to 1
and measuring whether phase topology deforms smoothly or abruptly.
"""

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

from .one_loop import OneLoopParams
from .one_loop_scan import SELECTED_SLICES, OneLoopScanConfig, _agreement, _cw_maps, _phase_counts, _plot_phase, _tree_maps
from .phase_boundary import PHASE_ORDER
from .robustness import _topology_status

DEFAULT_LOOP_SCALES = [0.0, 0.25, 0.50, 0.75, 1.0]


def _nonzero_counts(counts: dict[str, int]) -> dict[str, int]:
    return {k: v for k, v in counts.items() if v}


def _fractions(counts: dict[str, int], total: int) -> dict[str, float]:
    return {k: v / total for k, v in counts.items()}


def _trend(values: list[float], eps: float = 0.001) -> str:
    if not values or max(values) - min(values) < eps:
        return "nearly_flat"
    diffs = np.diff(values)
    if np.all(diffs >= -eps):
        return "increasing"
    if np.all(diffs <= eps):
        return "decreasing"
    return "nonmonotonic"


def _smoothness(max_step_change: float) -> str:
    if max_step_change < 0.02:
        return "smooth"
    if max_step_change < 0.08:
        return "mildly_non_smooth"
    return "abrupt"


def _first_status_transition(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    initial = rows[0]["topology_status"]
    for row in rows[1:]:
        if row["topology_status"] != initial:
            return {"from": initial, "to": row["topology_status"], "loop_scale": row["loop_scale"]}
    return None


def _first_instability(rows: list[dict[str, Any]], threshold: float = 0.01) -> float | None:
    for row in rows:
        if row["instability_fraction"] > threshold:
            return row["loop_scale"]
    return None


def _plot_metric(rows: list[dict[str, Any]], metric: str, ylabel: str, title: str, out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    x = [r["loop_scale"] for r in rows]
    y = [r[metric] for r in rows]
    fig, ax = plt.subplots(figsize=(7.5, 4.8), constrained_layout=True)
    ax.plot(x, y, marker="o", linewidth=2)
    ax.set_xlabel("loop_scale")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return str(out_path)


def _plot_summary(all_slice_rows: dict[str, list[dict[str, Any]]], metric: str, ylabel: str, title: str, out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.2, 5.2), constrained_layout=True)
    for name, rows in all_slice_rows.items():
        ax.plot([r["loop_scale"] for r in rows], [r[metric] for r in rows], marker="o", linewidth=1.8, label=name)
    ax.set_xlabel("loop_scale")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return str(out_path)


def _plot_phase_strip(name: str, maps: list[np.ndarray], loop_scales: list[float], config: OneLoopScanConfig, out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    colors = ["#4daf4a", "#377eb8", "#984ea3", "#ff7f00", "#dddddd", "#a6cee3", "#cab2d6", "#b15928", "#e41a1c"]
    cmap = matplotlib.colors.ListedColormap(colors)
    norm = matplotlib.colors.BoundaryNorm(np.arange(-0.5, len(PHASE_ORDER) + 0.5, 1), cmap.N)
    fig, axes = plt.subplots(1, len(maps), figsize=(3.2 * len(maps), 3.8), constrained_layout=True, sharey=True)
    if len(maps) == 1:
        axes = [axes]
    im = None
    for ax, codes, scale in zip(axes, maps, loop_scales):
        im = ax.imshow(codes, origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
        ax.axvline(0, color="black", lw=0.45, alpha=0.5)
        ax.axhline(0, color="black", lw=0.45, alpha=0.5)
        ax.set_title(f"scale={scale:g}", fontsize=9)
        ax.set_xlabel("mrho2")
    axes[0].set_ylabel("miota2_eff")
    fig.suptitle(f"{name}: phase maps across loop_scale")
    cbar = fig.colorbar(im, ax=axes, ticks=np.arange(len(PHASE_ORDER)), shrink=0.85)
    cbar.ax.set_yticklabels(PHASE_ORDER)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return str(out_path)


def scan_slice_continuation(params: dict[str, Any], loop_scales: list[float], config: OneLoopScanConfig, plot_dir: Path) -> dict[str, Any]:
    name = params["name"]
    print(f"\n=== continuation slice: {name} ===")
    print(f"grid shape: {config.grid_shape}; loop_scales: {loop_scales}")

    tree_codes, tree_records, tree_minima = _tree_maps(params, config)
    loop0_codes = tree_codes
    previous_codes = None
    maps = []
    rows = []
    all_cell_rows = []

    for scale in loop_scales:
        print(f"-- loop_scale={scale:g}")
        if abs(scale) < 1e-15:
            codes = tree_codes
            records = tree_records
            inst_mask = np.zeros_like(codes, dtype=bool)
        else:
            loop = OneLoopParams(loop_scale=scale)
            codes, records, inst_mask = _cw_maps(params, config, loop, tree_minima)

        counts = _phase_counts(codes)
        total = int(codes.size)
        agreement, mismatch_count, comparable_count = _agreement(records, config.axis_ignore_eps)
        agreement = float(agreement or 0.0)
        changed_vs_loop0 = codes != loop0_codes
        if previous_codes is None:
            changed_vs_previous = np.zeros_like(codes, dtype=bool)
        else:
            changed_vs_previous = codes != previous_codes
        inst_count = int(np.sum(inst_mask))
        row = {
            "slice": name,
            "loop_scale": float(scale),
            "phase_counts": counts,
            "phase_fractions": _fractions(counts, total),
            "quadrant_agreement": agreement,
            "mismatch_count": int(mismatch_count),
            "comparable_count": int(comparable_count),
            "topology_status": _topology_status(agreement),
            "mixed_fraction": counts.get("Mixed", 0) / total,
            "instability_fraction": inst_count / total,
            "instability_cells_count": inst_count,
            "rho_only_fraction": counts.get("Rho_only", 0) / total,
            "iota_only_fraction": counts.get("Iota_only", 0) / total,
            "other_fraction": counts.get("Other", 0) / total,
            "changed_phase_fraction_vs_loop0": int(np.sum(changed_vs_loop0)) / total,
            "changed_cells_count_vs_loop0": int(np.sum(changed_vs_loop0)),
            "changed_phase_fraction_vs_previous_scale": int(np.sum(changed_vs_previous)) / total,
            "changed_cells_count_vs_previous_scale": int(np.sum(changed_vs_previous)),
        }
        rows.append(row)
        maps.append(codes.copy())
        for rec in records:
            all_cell_rows.append(
                {
                    "slice": name,
                    "loop_scale": float(scale),
                    "mrho2": rec["mrho2"],
                    "miota2_eff": rec["miota2_eff"],
                    "phase": rec["phase"],
                }
            )
        print("phase counts:", _nonzero_counts(counts))
        print(f"quadrant agreement: {agreement:.6f}; topology: {row['topology_status']}")
        print(f"mixed fraction: {row['mixed_fraction']:.6f}; changed vs loop0: {row['changed_phase_fraction_vs_loop0']:.6f}; instability: {row['instability_fraction']:.6f}")
        previous_codes = codes.copy()

    max_step_change = max(r["changed_phase_fraction_vs_previous_scale"] for r in rows[1:]) if len(rows) > 1 else 0.0
    analysis = {
        "slice": name,
        "smoothness": _smoothness(max_step_change),
        "max_step_changed_phase_fraction": max_step_change,
        "agreement_trend": _trend([r["quadrant_agreement"] for r in rows]),
        "mixed_trend": _trend([r["mixed_fraction"] for r in rows]),
        "topology_transition": _first_status_transition(rows),
        "max_instability_fraction": max(r["instability_fraction"] for r in rows),
        "first_loop_scale_instability_gt_0_01": _first_instability(rows, 0.01),
    }

    plots = {
        "agreement_vs_loop_scale": _plot_metric(rows, "quadrant_agreement", "quadrant agreement", f"{name}: agreement vs loop_scale", plot_dir / f"{name}_agreement_vs_loop_scale.png"),
        "mixed_fraction_vs_loop_scale": _plot_metric(rows, "mixed_fraction", "Mixed fraction", f"{name}: Mixed fraction vs loop_scale", plot_dir / f"{name}_mixed_fraction_vs_loop_scale.png"),
        "changed_fraction_vs_loop_scale": _plot_metric(rows, "changed_phase_fraction_vs_loop0", "changed fraction vs loop0", f"{name}: changed fraction vs loop0", plot_dir / f"{name}_changed_fraction_vs_loop_scale.png"),
        "instability_fraction_vs_loop_scale": _plot_metric(rows, "instability_fraction", "instability fraction", f"{name}: instability fraction", plot_dir / f"{name}_instability_fraction_vs_loop_scale.png"),
        "phase_maps_strip": _plot_phase_strip(name, maps, loop_scales, config, plot_dir / f"{name}_phase_maps_strip.png"),
    }
    for p in plots.values():
        print(f"wrote plot: {p}")
    return {"params": params, "rows": rows, "analysis": analysis, "plots": plots, "cell_rows": all_cell_rows}


def _table(rows: list[dict[str, Any]], cols: list[str]) -> list[str]:
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        vals = []
        for c in cols:
            v = r.get(c, "")
            vals.append(f"{v:.4f}" if isinstance(v, float) else str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def write_report(payload: dict[str, Any], report_path: Path) -> str:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    flat = payload["summary_rows"]
    analyses = payload["analyses"]
    lines = [
        "# PQT-QG Loop-Scale Continuation Report v0.5",
        "",
        "## 1. Goal",
        "Determine whether local Coleman-Weinberg corrections deform PQT-QG synthetic phase maps smoothly as `loop_scale` increases from 0 to 1, or whether abrupt topology transitions occur.",
        "",
        "## 2. Canon assumptions",
        "- Core Psi remains frozen into `muH_eff2`; H does not replace Psi.",
        "- Observed scalar landscape only.",
        "- Memory enters only through local `LambdaT2_kappa0`.",
        "- Local CW only; no full nonlocal `K_T` determinant; no RG improvement.",
        "- Off-shell `Veff` is gauge-dependent; negative `m^2` uses Re[Veff] convention.",
        "",
        "## 3. Why continuation is needed after v0.4",
        "v0.4 compared only loop_scale 0 and 1. v0.5 checks whether the interpolation is gentle or phase-flip-like.",
        "",
        "## 4. Selected slices",
    ]
    for p in payload["slices"]:
        lines.append(f"- `{p['name']}`")
    lines += ["", "## 5. Loop-scale values", ", ".join(str(x) for x in payload["loop_scales"]), "", "## 6. Agreement vs loop-scale table"]
    lines += _table(flat, ["slice", "loop_scale", "quadrant_agreement", "topology_status"])
    lines += ["", "## 7. Mixed fraction vs loop-scale table"]
    lines += _table(flat, ["slice", "loop_scale", "mixed_fraction", "rho_only_fraction", "iota_only_fraction", "other_fraction"])
    lines += ["", "## 8. Changed fraction vs loop-scale table"]
    lines += _table(flat, ["slice", "loop_scale", "changed_phase_fraction_vs_loop0", "changed_phase_fraction_vs_previous_scale"])
    lines += ["", "## 9. Instability fraction vs loop-scale table"]
    lines += _table(flat, ["slice", "loop_scale", "instability_fraction", "instability_cells_count"])
    lines += ["", "## 10. Smoothness classification per slice"]
    lines += _table(analyses, ["slice", "smoothness", "max_step_changed_phase_fraction", "agreement_trend", "mixed_trend", "max_instability_fraction", "first_loop_scale_instability_gt_0_01"])
    lines += ["", "## 11. Topology transition points"]
    for a in analyses:
        lines.append(f"- `{a['slice']}`: {a['topology_transition'] or 'no topology-status transition'}")
    lines += ["", "## 12. Interpretation"]
    for a in analyses:
        lines.append(f"- `{a['slice']}`: {a['smoothness']}; agreement trend `{a['agreement_trend']}`; Mixed trend `{a['mixed_trend']}`.")
    lines += [
        "- Loop-stable slices have low max step changes and unchanged topology status.",
        "- Loop-sensitive slices show status transitions, nonmonotonic trends, or elevated changed-cell fractions.",
        "",
        "## 13. Warnings",
        "- synthetic benchmark only",
        "- local CW only",
        "- gauge-dependent off-shell Veff",
        "- Re[Veff] only for negative m2",
        "- no RG improvement",
        "- no full nonlocal K_T determinant",
        "- no physical prediction",
        "- no proof of PQT-QG",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def run_loop_scale_continuation(root: Path, grid: int = 61, loop_scales: Iterable[float] | None = None) -> dict[str, Path]:
    loop_scales = list(DEFAULT_LOOP_SCALES if loop_scales is None else loop_scales)
    config = OneLoopScanConfig(grid_shape=(grid, grid))
    data_dir = root / "outputs" / "data"
    plot_dir = root / "outputs" / "plots" / "loop_scale_v0_5"
    report_dir = root / "outputs" / "reports"
    for d in (data_dir, plot_dir, report_dir):
        d.mkdir(parents=True, exist_ok=True)

    slice_results = []
    summary_rows = []
    analyses = []
    cell_rows = []
    per_slice_rows = {}
    for params in SELECTED_SLICES:
        result = scan_slice_continuation(dict(params), loop_scales, config, plot_dir)
        slice_results.append({k: v for k, v in result.items() if k != "cell_rows"})
        analyses.append(result["analysis"])
        per_slice_rows[params["name"]] = result["rows"]
        cell_rows.extend(result["cell_rows"])
        for row in result["rows"]:
            flat = {k: v for k, v in row.items() if k not in {"phase_counts", "phase_fractions"}}
            for phase in PHASE_ORDER:
                flat[f"count_{phase}"] = row["phase_counts"].get(phase, 0)
                flat[f"fraction_{phase}"] = row["phase_fractions"].get(phase, 0.0)
            summary_rows.append(flat)

    summary_plots = {
        "summary_agreement_all_slices": _plot_summary(per_slice_rows, "quadrant_agreement", "quadrant agreement", "Agreement vs loop_scale", plot_dir / "summary_agreement_all_slices.png"),
        "summary_mixed_fraction_all_slices": _plot_summary(per_slice_rows, "mixed_fraction", "Mixed fraction", "Mixed fraction vs loop_scale", plot_dir / "summary_mixed_fraction_all_slices.png"),
    }
    for p in summary_plots.values():
        print(f"wrote plot: {p}")

    payload = {
        "name": "PQT-QG Benchmark v0.5 — Loop-scale Continuation",
        "grid": grid,
        "loop_scales": loop_scales,
        "config": asdict(config),
        "slices": SELECTED_SLICES,
        "slice_results": slice_results,
        "summary_plots": summary_plots,
    }
    summary = {"grid": grid, "loop_scales": loop_scales, "summary_rows": summary_rows, "analyses": analyses}

    json_path = data_dir / "loop_scale_continuation_v0_5.json"
    csv_path = data_dir / "loop_scale_continuation_v0_5.csv"
    summary_path = data_dir / "loop_scale_continuation_summary_v0_5.json"
    report_path = report_dir / "PQT_QG_Loop_Scale_Continuation_Report_v0_5.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(cell_rows).to_csv(csv_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = write_report({"slices": SELECTED_SLICES, "loop_scales": loop_scales, "summary_rows": summary_rows, "analyses": analyses}, report_path)
    print(f"wrote data: {json_path}")
    print(f"wrote data: {csv_path}")
    print(f"wrote data: {summary_path}")
    print(f"wrote report: {report}")
    return {"json": json_path, "csv": csv_path, "summary": summary_path, "report": report_path, "plot_dir": plot_dir}

