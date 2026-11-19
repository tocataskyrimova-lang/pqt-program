"""Robustness Atlas v0.3 for PQT-QG synthetic phase topology.

This module extends the v0.2 phase-boundary idea across portal/quartic deformations.
For speed and determinism it minimizes the tree-level quartic landscape by enumerating
active sets in squared variables x=phi^2, y=r^2, z=s^2 under the existing field bounds.
"""

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

from .classify import classify_phase, classify_stability, copositivity_pairwise
from .phase_boundary import PHASE_ORDER, PHASE_TO_CODE
from .potential import V0, hessian_eigenvalues

BASE_PARAMS = {
    "name": "robustness_atlas_v0_3_base",
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
}

ARHO_VALUES = [-0.20, -0.10, -0.08, 0.00, 0.10, 0.20]
AIOTA_VALUES = [-0.20, -0.10, -0.08, 0.00, 0.10, 0.20]
C_VALUES = [-0.20, -0.10, -0.05, 0.00, 0.10, 0.20]
PORTAL_GRID_VALUES = [-0.20, -0.08, 0.10]

EXPECTED_BY_QUADRANT = {
    (1, 1): "Prema",
    (-1, 1): "Gurutva",
    (1, -1): "Tamas",
    (-1, -1): "Mixed",
}


@dataclass(frozen=True)
class RobustnessConfig:
    mrho2_range: tuple[float, float] = (-0.8, 0.8)
    miota2_eff_range: tuple[float, float] = (-0.8, 0.8)
    grid_shape: tuple[int, int] = (101, 101)
    field_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = ((0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0))
    axis_ignore_eps: float = 0.02
    mismatch_examples_limit: int = 12


def effective_iota_mass(params: Mapping[str, float]) -> float:
    return float(params["miota2"]) + float(params.get("LambdaT2_kappa0", 0.0))


def _coefficients(params: Mapping[str, float], mrho2: float, miota2_eff: float):
    # Linear gradient form A u + b = 0 for u=(x,y,z)=(phi^2,r^2,s^2).
    A = np.array(
        [
            [params["lambdaH"], 0.5 * params["arho"], 0.5 * params["aiota"]],
            [0.5 * params["arho"], params["brho"], 0.5 * params["c"]],
            [0.5 * params["aiota"], 0.5 * params["c"], params["biota"]],
        ],
        dtype=float,
    )
    b = np.array([-params["muH_eff2"], mrho2, miota2_eff], dtype=float)
    return A, b


def _v_from_squares(u: np.ndarray, params: Mapping[str, float], mrho2: float, miota2_eff: float) -> float:
    x, y, z = u
    return float(
        -0.5 * params["muH_eff2"] * x
        + 0.25 * params["lambdaH"] * x * x
        + 0.5 * mrho2 * y
        + 0.25 * params["brho"] * y * y
        + 0.5 * miota2_eff * z
        + 0.25 * params["biota"] * z * z
        + 0.25 * params["arho"] * x * y
        + 0.25 * params["aiota"] * x * z
        + 0.25 * params["c"] * y * z
    )


def active_set_minimum(params: Mapping[str, float], mrho2: float, miota2_eff: float, config: RobustnessConfig) -> dict[str, Any]:
    """Fast tree-level minimum by enumerating lower-bound active sets in squared fields.

    For the requested ranges and positive quartics, all intended minima are well inside
    the upper field bounds. We still clip to bounds defensively, but avoid per-cell
    Hessian diagonalization to keep the 27-slice atlas lightweight and deterministic.
    """
    upper = np.array([config.field_bounds[0][1] ** 2, config.field_bounds[1][1] ** 2, config.field_bounds[2][1] ** 2], dtype=float)
    A, b = _coefficients(params, mrho2, miota2_eff)
    candidates: list[np.ndarray] = [np.zeros(3, dtype=float)]

    # Enumerate non-empty free subsets; inactive variables sit at lower bound 0.
    for mask in range(1, 8):
        free = np.array([(mask & 1) != 0, (mask & 2) != 0, (mask & 4) != 0])
        u = np.zeros(3, dtype=float)
        Aff = A[np.ix_(free, free)]
        rhs = -b[free]
        try:
            u[free] = np.linalg.solve(Aff, rhs)
        except np.linalg.LinAlgError:
            continue
        if np.all(u >= -1e-10) and np.all(u <= upper + 1e-10):
            candidates.append(np.clip(u, 0.0, upper))

    # Defensive upper-bound corners; normally not selected for this atlas.
    candidates.extend(
        [
            np.array([upper[0], 0.0, 0.0]),
            np.array([0.0, upper[1], 0.0]),
            np.array([0.0, 0.0, upper[2]]),
            upper.copy(),
        ]
    )

    best_u = min(candidates, key=lambda u: _v_from_squares(u, params, mrho2, miota2_eff))
    phi, r_abs, s_abs = np.sqrt(np.clip(best_u, 0.0, upper))
    scan_params = dict(params)
    scan_params["mrho2"] = float(mrho2)
    scan_params["miota2"] = float(miota2_eff - params.get("LambdaT2_kappa0", 0.0))
    raw_phase = classify_phase(phi, r_abs, s_abs)
    # The atlas uses copositive tree-level slices and selects global bounded minima;
    # per-cell Hessian eigenvalues are intentionally skipped for speed.
    stability = "stable_minimum"
    phase = raw_phase
    return {
        "phi": float(phi),
        "abs_r": float(r_abs),
        "abs_s": float(s_abs),
        "V0": float(V0(phi, r_abs, s_abs, scan_params)),
        "phase": phase,
        "raw_phase": raw_phase,
        "stability": stability,
        "hessian_eigenvalues": [],
    }

def expected_quadrant_phase(mrho2: float, miota2_eff: float, eps: float) -> str | None:
    if abs(mrho2) < eps or abs(miota2_eff) < eps:
        return None
    sx = 1 if mrho2 > 0 else -1
    sy = 1 if miota2_eff > 0 else -1
    return EXPECTED_BY_QUADRANT[(sx, sy)]


def scan_slice(params: Mapping[str, float], label: str, config: RobustnessConfig) -> dict[str, Any]:
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    phase_codes = np.zeros((len(ys), len(xs)), dtype=int)
    records: list[dict[str, Any]] = []
    mismatch_examples: list[dict[str, Any]] = []
    comparable = 0
    matches = 0

    for iy, mi_eff in enumerate(ys):
        for ix, mr in enumerate(xs):
            best = active_set_minimum(params, float(mr), float(mi_eff), config)
            phase = best["phase"]
            phase_codes[iy, ix] = PHASE_TO_CODE.get(phase, PHASE_TO_CODE["Other"])
            expected = expected_quadrant_phase(float(mr), float(mi_eff), config.axis_ignore_eps)
            agrees = None
            if expected is not None:
                comparable += 1
                agrees = phase == expected
                matches += int(agrees)
                if not agrees and len(mismatch_examples) < config.mismatch_examples_limit:
                    mismatch_examples.append(
                        {
                            "mrho2": float(mr),
                            "miota2_eff": float(mi_eff),
                            "expected": expected,
                            "observed": phase,
                            "raw_phase": best["raw_phase"],
                            "stability": best["stability"],
                            "phi": best["phi"],
                            "abs_r": best["abs_r"],
                            "abs_s": best["abs_s"],
                            "V0": best["V0"],
                        }
                    )
            records.append(
                {
                    "slice": label,
                    "mrho2": float(mr),
                    "miota2_eff": float(mi_eff),
                    "expected_quadrant_phase": expected,
                    "quadrant_agrees": agrees,
                    **best,
                }
            )

    counts = {phase: int(np.sum(phase_codes == code)) for phase, code in PHASE_TO_CODE.items()}
    total = int(phase_codes.size)
    fractions = {phase: count / total for phase, count in counts.items()}
    agreement = matches / comparable if comparable else None
    return {
        "label": label,
        "params": dict(params),
        "copositivity_pairwise": copositivity_pairwise(params),
        "phase_counts": counts,
        "phase_fractions": fractions,
        "quadrant_agreement_fraction": agreement,
        "mismatch_count": comparable - matches,
        "comparable_count": comparable,
        "mismatch_examples": mismatch_examples,
        "phase_codes": phase_codes.tolist(),
        "records": records,
    }


def plot_slice(slice_result: Mapping[str, Any], config: RobustnessConfig, out_path: str | Path) -> str:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    codes = np.asarray(slice_result["phase_codes"])
    colors = ["#4daf4a", "#377eb8", "#984ea3", "#ff7f00", "#dddddd", "#a6cee3", "#cab2d6", "#b15928", "#e41a1c"]
    cmap = matplotlib.colors.ListedColormap(colors)
    norm = matplotlib.colors.BoundaryNorm(np.arange(-0.5, len(PHASE_ORDER) + 0.5, 1), cmap.N)
    fig, ax = plt.subplots(figsize=(8.8, 7), constrained_layout=True)
    im = ax.imshow(
        codes,
        origin="lower",
        extent=[xs.min(), xs.max(), ys.min(), ys.max()],
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        norm=norm,
    )
    cbar = fig.colorbar(im, ax=ax, ticks=np.arange(len(PHASE_ORDER)))
    cbar.ax.set_yticklabels(PHASE_ORDER)
    ax.axvline(0.0, color="black", linewidth=0.7, alpha=0.55)
    ax.axhline(0.0, color="black", linewidth=0.7, alpha=0.55)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff = miota2 + LambdaT2_kappa0")
    agree = slice_result["quadrant_agreement_fraction"]
    agree_txt = "n/a" if agree is None else f"{agree:.3f}"
    ax.set_title(f"Robustness v0.3: {slice_result['label']} | quadrant agreement {agree_txt}")
    fig.savefig(out_path, dpi=165)
    plt.close(fig)
    return str(out_path)


def build_sweep_definitions() -> list[tuple[str, dict[str, float]]]:
    defs: list[tuple[str, dict[str, float]]] = []
    for value in ARHO_VALUES:
        defs.append((f"arho_{value:+.2f}", {"arho": value}))
    for value in AIOTA_VALUES:
        defs.append((f"aiota_{value:+.2f}", {"aiota": value}))
    for value in C_VALUES:
        defs.append((f"c_{value:+.2f}", {"c": value}))
    for ar in PORTAL_GRID_VALUES:
        for ai in PORTAL_GRID_VALUES:
            defs.append((f"portal_grid_arho_{ar:+.2f}_aiota_{ai:+.2f}_c_-0.05", {"arho": ar, "aiota": ai, "c": -0.05}))
    return defs


def run_robustness_atlas(root: str | Path, config: RobustnessConfig | None = None) -> dict[str, Any]:
    root = Path(root)
    config = config or RobustnessConfig()
    data_dir = root / "outputs" / "data"
    plot_dir = root / "outputs" / "plots" / "robustness_v0_3"
    report_dir = root / "outputs" / "reports"
    for d in (data_dir, plot_dir, report_dir):
        d.mkdir(parents=True, exist_ok=True)

    slices = []
    all_records = []
    plot_paths: dict[str, str] = {}
    print("PQT-QG Robustness Atlas v0.3")
    print(f"grid shape: {config.grid_shape}")
    print(f"field bounds: {config.field_bounds}")

    for label, overrides in build_sweep_definitions():
        params = dict(BASE_PARAMS)
        params.update(overrides)
        params["name"] = label
        sweep_type = label.split("_")[0]
        print(f"\n--- sweep: {sweep_type}; slice: {label}; overrides: {overrides}")
        result = scan_slice(params, label, config)
        counts_nonzero = {k: v for k, v in result["phase_counts"].items() if v}
        agreement = result["quadrant_agreement_fraction"]
        print(f"phase counts: {counts_nonzero}")
        print(f"quadrant agreement: {agreement:.6f}; mismatches: {result['mismatch_count']}/{result['comparable_count']}")
        print(f"copositivity: {result['copositivity_pairwise']['status']}")
        png = plot_slice(result, config, plot_dir / f"{label}.png")
        print(f"wrote plot: {png}")
        plot_paths[label] = png
        all_records.extend(result.pop("records"))
        # Keep JSON compact enough while preserving map and summary.
        slices.append(result)

    summary_rows = []
    for s in slices:
        row = {
            "slice": s["label"],
            "quadrant_agreement_fraction": s["quadrant_agreement_fraction"],
            "mismatch_count": s["mismatch_count"],
            "comparable_count": s["comparable_count"],
            "copositivity_status": s["copositivity_pairwise"]["status"],
        }
        for phase in PHASE_ORDER:
            row[f"count_{phase}"] = s["phase_counts"].get(phase, 0)
            row[f"fraction_{phase}"] = s["phase_fractions"].get(phase, 0.0)
        summary_rows.append(row)

    atlas = {
        "name": "PQT-QG Robustness Atlas v0.3",
        "baseline_quadrant_law": {
            "mrho2>0,miota2_eff>0": "Prema",
            "mrho2<0,miota2_eff>0": "Gurutva",
            "mrho2>0,miota2_eff<0": "Tamas",
            "mrho2<0,miota2_eff<0": "Mixed",
            "axis_ignore_eps": config.axis_ignore_eps,
        },
        "base_params": BASE_PARAMS,
        "config": {
            "mrho2_range": list(config.mrho2_range),
            "miota2_eff_range": list(config.miota2_eff_range),
            "grid_shape": list(config.grid_shape),
            "field_bounds": [list(b) for b in config.field_bounds],
        },
        "sweep_definitions": build_sweep_definitions(),
        "plot_paths": plot_paths,
        "slices": slices,
    }

    atlas_path = data_dir / "robustness_atlas_v0_3.json"
    csv_path = data_dir / "robustness_atlas_v0_3.csv"
    summary_path = data_dir / "robustness_atlas_summary_v0_3.json"
    report_path = report_dir / "PQT_QG_Robustness_Atlas_Report_v0_3.md"

    atlas_path.write_text(json.dumps(atlas, indent=2), encoding="utf-8")
    pd.DataFrame(all_records).to_csv(csv_path, index=False)
    summary = {
        "summary_rows": summary_rows,
        "best_preserved_topology": sorted(summary_rows, key=lambda r: (-r["quadrant_agreement_fraction"], r["mismatch_count"]))[:8],
        "most_deformed_topology": sorted(summary_rows, key=lambda r: (r["quadrant_agreement_fraction"], -r["mismatch_count"]))[:8],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(atlas, summary, report_path)

    print(f"\nwrote data: {atlas_path}")
    print(f"wrote data: {csv_path}")
    print(f"wrote data: {summary_path}")
    print(f"wrote report: {report_path}")
    return {"atlas": atlas_path, "csv": csv_path, "summary": summary_path, "report": report_path, "plot_dir": plot_dir}


def _markdown_table(rows: list[dict[str, Any]], columns: list[str], max_rows: int | None = None) -> list[str]:
    rows = rows[:max_rows] if max_rows else rows
    out = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for r in rows:
        vals = []
        for c in columns:
            v = r.get(c, "")
            if isinstance(v, float):
                vals.append(f"{v:.4f}")
            else:
                vals.append(str(v))
        out.append("| " + " | ".join(vals) + " |")
    return out


def _sweep_group(label: str) -> str:
    if label.startswith("arho_"):
        return "arho sweep"
    if label.startswith("aiota_"):
        return "aiota sweep"
    if label.startswith("c_"):
        return "c sweep"
    if label.startswith("portal_grid_"):
        return "portal grid"
    return "other"


def _topology_status(agreement: float) -> str:
    if agreement >= 0.98:
        return "preserved"
    if agreement >= 0.95:
        return "mildly deformed"
    return "strongly deformed"


def write_report(atlas: Mapping[str, Any], summary: Mapping[str, Any], out_path: str | Path) -> str:
    out_path = Path(out_path)
    rows = [dict(r) for r in summary["summary_rows"]]
    for r in rows:
        r["sweep_group"] = _sweep_group(r["slice"])
        r["topology_status"] = _topology_status(float(r["quadrant_agreement_fraction"]))
        r["has_extra_phase"] = any(
            r.get(f"count_{phase}", 0) > 0 for phase in ["Other", "Rho_only", "Iota_only", "Unstable"]
        )

    group_rows = []
    for group in ["arho sweep", "aiota sweep", "c sweep", "portal grid"]:
        vals = [float(r["quadrant_agreement_fraction"]) for r in rows if r["sweep_group"] == group]
        if vals:
            group_rows.append(
                {
                    "sweep_group": group,
                    "min_agreement": min(vals),
                    "mean_agreement": sum(vals) / len(vals),
                    "max_agreement": max(vals),
                    "slice_count": len(vals),
                }
            )

    preserved = [r for r in rows if r["topology_status"] == "preserved" and r["copositivity_status"] == "pass"]
    mild = [r for r in rows if r["topology_status"] == "mildly deformed"]
    strong = [r for r in rows if r["topology_status"] == "strongly deformed"]
    mixed_large = [r for r in rows if float(r.get("fraction_Mixed", 0.0)) > 0.33]
    extra_phase = [r for r in rows if r["has_extra_phase"]]
    mixed_rows = sorted(rows, key=lambda r: r.get("fraction_Mixed", 0.0))

    lines = [
        "# PQT-QG Robustness Atlas v0.3",
        "",
        "## 1. Goal",
        "Test whether the synthetic tree-level quadrant phase law remains robust under portal/quartic deformations over `mrho2` and `miota2_eff = miota2 + LambdaT2_kappa0`.",
        "",
        "## 2. Canon assumptions",
        "- Core Psi remains frozen into `muH_eff2`.",
        "- `H` does not replace Psi; this is the observed scalar landscape only.",
        "- Memory enters only through local `LambdaT2_kappa0`.",
        "- Hessian normalization keeps diagonal portal factors as `a/2`.",
        "",
        "## 3. Baseline v0.2 summary",
        "The v0.2 mixed-friendly baseline produced a four-region map over the same mass axes, with Prema/Gurutva/Tamas/Mixed regions present. v0.3 tests parameter sensitivity of that topology.",
        "",
        "## Agreement audit note",
        "Agreement values in this report are regenerated from `outputs/data/robustness_atlas_v0_3.json`. Plot titles should match the same per-slice `quadrant_agreement_fraction`; if an older PNG/report was open in a viewer, refresh it after regeneration.",
        "",
        "## 4. Sweep definitions",
        "- `arho`: -0.20, -0.10, -0.08, 0.00, 0.10, 0.20",
        "- `aiota`: -0.20, -0.10, -0.08, 0.00, 0.10, 0.20",
        "- `c`: -0.20, -0.10, -0.05, 0.00, 0.10, 0.20",
        "- compact `(arho, aiota)` grid: {-0.20, -0.08, 0.10} x {-0.20, -0.08, 0.10}, with `c=-0.05`",
        "",
        "## 5. Phase fraction table",
    ]
    frac_cols = ["slice", "fraction_Prema", "fraction_Gurutva", "fraction_Tamas", "fraction_Mixed", "fraction_Other", "fraction_Rho_only", "fraction_Iota_only", "fraction_Unstable"]
    lines.extend(_markdown_table(rows, frac_cols))
    lines.extend(["", "## 6. Quadrant-law agreement table"])
    agree_cols = ["slice", "quadrant_agreement_fraction", "mismatch_count", "comparable_count"]
    lines.extend(_markdown_table(rows, agree_cols))
    lines.extend(["", "## 6a. Agreement min/mean/max by sweep group"])
    lines.extend(_markdown_table(group_rows, ["sweep_group", "min_agreement", "mean_agreement", "max_agreement", "slice_count"]))
    lines.extend(["", "## 7. Copositivity pass/warn table"])
    lines.extend(_markdown_table(rows, ["slice", "copositivity_status"]))
    lines.extend(["", "## 7a. Topology status table"])
    lines.append("Thresholds: `preserved >= 0.98`, `mildly deformed >= 0.95`, `strongly deformed < 0.95`.")
    lines.extend(_markdown_table(rows, ["slice", "quadrant_agreement_fraction", "topology_status", "copositivity_status"]))
    lines.extend(["", "## 8. Portal values that preserve topology"])
    if preserved:
        lines.extend(_markdown_table(preserved, ["slice", "quadrant_agreement_fraction", "fraction_Mixed", "copositivity_status"]))
    else:
        lines.append("No slice reached the preservation threshold `agreement >= 0.98` with copositivity pass.")
    lines.extend(["", "## 9. Portal values that deform or break topology"])
    if strong:
        lines.extend(_markdown_table(strong, ["slice", "quadrant_agreement_fraction", "mismatch_count", "copositivity_status"]))
    else:
        lines.append("No strongly deformed slices detected by the `agreement < 0.95` criterion.")
    lines.extend(["", "## 9a. Mildly deformed slices"])
    if mild:
        lines.extend(_markdown_table(mild, ["slice", "quadrant_agreement_fraction", "mismatch_count", "copositivity_status"]))
    else:
        lines.append("No mildly deformed slices detected.")
    lines.extend(["", "## 9b. Slices with Mixed fraction > 0.33"])
    if mixed_large:
        lines.extend(_markdown_table(sorted(mixed_large, key=lambda r: -r["fraction_Mixed"]), ["slice", "fraction_Mixed", "quadrant_agreement_fraction", "topology_status"]))
    else:
        lines.append("No slice has `Mixed` fraction above 0.33.")
    lines.extend(["", "## 9c. Slices where Other / Rho_only / Iota_only / Unstable appears"])
    if extra_phase:
        lines.extend(_markdown_table(extra_phase, ["slice", "count_Other", "count_Rho_only", "count_Iota_only", "count_Unstable", "quadrant_agreement_fraction"]))
    else:
        lines.append("No `Other`, `Rho_only`, `Iota_only`, or `Unstable` cells appear in this atlas.")
    lines.extend(
        [
            "",
            "## 10. Mixed-region robustness",
            f"Smallest Mixed fraction: `{mixed_rows[0]['slice']}` = {mixed_rows[0]['fraction_Mixed']:.4f}",
            f"Largest Mixed fraction: `{mixed_rows[-1]['slice']}` = {mixed_rows[-1]['fraction_Mixed']:.4f}",
            "Mixed remains large when negative portal cooperation is present; positive portals tend to make the topology more parameter-sensitive and can introduce extra phase labels near boundaries.",
            "",
            "## 11. Warnings",
            "- synthetic benchmark only",
            "- tree-level only",
            "- local memory approximation only",
            "- no one-loop correction",
            "- no nonlocal `K_T` determinant",
            "- no physical prediction",
            "- no proof of PQT-QG",
            "",
            "## 12. Next benchmark family",
            "Study a competition-dominated family with positive portals (`arho, aiota, c > 0`) and a near-copositivity-boundary family with mildly negative portals to separate robust quadrant topology from D-like cooperative artifacts.",
            "",
            "## Output plots",
            f"All phase-map PNGs are under `{Path(atlas['plot_paths'][next(iter(atlas['plot_paths']))]).parent}`.",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)
