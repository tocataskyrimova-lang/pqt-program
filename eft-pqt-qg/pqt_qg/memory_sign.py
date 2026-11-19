"""PQT-QG v0.6 memory-sign reconciliation benchmark.

Compares legacy plus-sign local memory mass shift against patched bath-memory
minus-sign local self-energy shift, without modifying v0.1-v0.5 code paths.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Any, Iterable, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .classify import classify_phase, copositivity_pairwise
from .phase_boundary import PHASE_ORDER, PHASE_TO_CODE
from .robustness import expected_quadrant_phase, _topology_status

BASE_PARAMS = {
    "name": "D_like_mixed_friendly_base",
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

ARHO_VALUES = [-0.20, -0.08, 0.00, 0.10, 0.20]
AIOTA_VALUES = [-0.20, -0.08, 0.00, 0.10, 0.20]
C_VALUES = [-0.20, -0.05, 0.00, 0.10, 0.20]
PORTAL_GRID_VALUES = [-0.20, -0.08, 0.10]
MEMORY_SIGNS = ["plus", "minus"]


@dataclass(frozen=True)
class MemorySignConfig:
    mrho2_range: tuple[float, float] = (-0.8, 0.8)
    miota2_eff_range: tuple[float, float] = (-0.8, 0.8)
    grid_shape: tuple[int, int] = (61, 61)
    field_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = ((0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0))
    axis_ignore_eps: float = 0.02


def memory_shift(params: Mapping[str, float], memory_sign: str) -> float:
    if memory_sign == "plus":
        return float(params.get("LambdaT2_kappa0", 0.0))
    if memory_sign == "minus":
        return -float(params.get("LambdaT2_kappa0", 0.0))
    raise ValueError(f"unknown memory_sign: {memory_sign!r}")


def miota2_from_effective(miota2_eff: float, params: Mapping[str, float], memory_sign: str) -> float:
    # miota2_eff = miota2 + memory_shift
    return float(miota2_eff) - memory_shift(params, memory_sign)


def V0_signed(phi, r, s, params: Mapping[str, float], memory_sign: str):
    ms = memory_shift(params, memory_sign)
    return (
        -0.5 * params["muH_eff2"] * phi**2
        + 0.25 * params["lambdaH"] * phi**4
        + 0.5 * params["mrho2"] * r**2
        + 0.25 * params["brho"] * r**4
        + 0.5 * params["miota2"] * s**2
        + 0.25 * params["biota"] * s**4
        + 0.25 * params["arho"] * phi**2 * r**2
        + 0.25 * params["aiota"] * phi**2 * s**2
        + 0.25 * params["c"] * r**2 * s**2
        + 0.5 * ms * s**2
    )


def grad_V0_signed(x, params: Mapping[str, float], memory_sign: str) -> np.ndarray:
    phi, r, s = np.asarray(x, dtype=float)
    mi_eff = params["miota2"] + memory_shift(params, memory_sign)
    return np.array(
        [
            -params["muH_eff2"] * phi + params["lambdaH"] * phi**3 + 0.5 * params["arho"] * phi * r**2 + 0.5 * params["aiota"] * phi * s**2,
            params["mrho2"] * r + params["brho"] * r**3 + 0.5 * params["arho"] * phi**2 * r + 0.5 * params["c"] * r * s**2,
            mi_eff * s + params["biota"] * s**3 + 0.5 * params["aiota"] * phi**2 * s + 0.5 * params["c"] * r**2 * s,
        ],
        dtype=float,
    )


def hessian_V0_signed(x, params: Mapping[str, float], memory_sign: str) -> np.ndarray:
    phi, r, s = np.asarray(x, dtype=float)
    mi_eff = params["miota2"] + memory_shift(params, memory_sign)
    m_hh2 = -params["muH_eff2"] + 3.0 * params["lambdaH"] * phi**2 + 0.5 * params["arho"] * r**2 + 0.5 * params["aiota"] * s**2
    m_rr2 = params["mrho2"] + 3.0 * params["brho"] * r**2 + 0.5 * params["arho"] * phi**2 + 0.5 * params["c"] * s**2
    m_ss2 = mi_eff + 3.0 * params["biota"] * s**2 + 0.5 * params["aiota"] * phi**2 + 0.5 * params["c"] * r**2
    m_hr2 = params["arho"] * phi * r
    m_hs2 = params["aiota"] * phi * s
    m_rs2 = params["c"] * r * s
    return np.array([[m_hh2, m_hr2, m_hs2], [m_hr2, m_rr2, m_rs2], [m_hs2, m_rs2, m_ss2]], dtype=float)


def _coefficients(params: Mapping[str, float], mrho2: float, miota2_eff: float):
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


def _v_squares(u: np.ndarray, params: Mapping[str, float], mrho2: float, miota2_eff: float) -> float:
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


def active_set_minimum_signed(params: Mapping[str, float], mrho2: float, miota2_eff: float, memory_sign: str, config: MemorySignConfig) -> dict[str, Any]:
    upper = np.array([config.field_bounds[0][1] ** 2, config.field_bounds[1][1] ** 2, config.field_bounds[2][1] ** 2], dtype=float)
    A, b = _coefficients(params, mrho2, miota2_eff)
    candidates = [np.zeros(3, dtype=float)]
    for mask in range(1, 8):
        free = np.array([(mask & 1) != 0, (mask & 2) != 0, (mask & 4) != 0])
        u = np.zeros(3, dtype=float)
        try:
            u[free] = np.linalg.solve(A[np.ix_(free, free)], -b[free])
        except np.linalg.LinAlgError:
            continue
        if np.all(u >= -1e-10) and np.all(u <= upper + 1e-10):
            candidates.append(np.clip(u, 0.0, upper))
    candidates.extend([np.array([upper[0], 0, 0.0]), np.array([0.0, upper[1], 0.0]), np.array([0.0, 0.0, upper[2]]), upper.copy()])
    best_u = min(candidates, key=lambda u: _v_squares(u, params, mrho2, miota2_eff))
    phi, ar, ais = np.sqrt(np.clip(best_u, 0.0, upper))
    p = dict(params)
    p["mrho2"] = float(mrho2)
    p["miota2"] = miota2_from_effective(miota2_eff, p, memory_sign)
    phase = classify_phase(phi, ar, ais)
    return {
        "phi": float(phi),
        "abs_r": float(ar),
        "abs_s": float(ais),
        "V0": float(V0_signed(phi, ar, ais, p, memory_sign)),
        "phase": phase,
        "memory_sign": memory_sign,
    }


def scan_phase_map_signed(params: Mapping[str, float], memory_sign: str, config: MemorySignConfig, label: str) -> dict[str, Any]:
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    codes = np.zeros((len(ys), len(xs)), dtype=int)
    records: list[dict[str, Any]] = []
    comparable = matches = 0
    for iy, mi_eff in enumerate(ys):
        for ix, mr in enumerate(xs):
            best = active_set_minimum_signed(params, float(mr), float(mi_eff), memory_sign, config)
            phase = best["phase"]
            codes[iy, ix] = PHASE_TO_CODE.get(phase, PHASE_TO_CODE["Other"])
            expected = expected_quadrant_phase(float(mr), float(mi_eff), config.axis_ignore_eps)
            agrees = None
            if expected is not None:
                comparable += 1
                agrees = phase == expected
                matches += int(agrees)
            records.append(
                {
                    "label": label,
                    "memory_sign": memory_sign,
                    "mrho2": float(mr),
                    "miota2_eff": float(mi_eff),
                    "expected_phase": expected,
                    "quadrant_agrees": agrees,
                    **best,
                }
            )
    counts = {phase: int(np.sum(codes == code)) for phase, code in PHASE_TO_CODE.items()}
    total = int(codes.size)
    agreement = matches / comparable if comparable else None
    return {
        "label": label,
        "memory_sign": memory_sign,
        "params": dict(params),
        "phase_codes": codes.tolist(),
        "phase_counts": counts,
        "phase_fractions": {k: v / total for k, v in counts.items()},
        "quadrant_agreement": agreement,
        "mismatch_count": comparable - matches,
        "comparable_count": comparable,
        "topology_status": _topology_status(float(agreement or 0.0)),
        "mixed_fraction": counts.get("Mixed", 0) / total,
        "tamas_fraction": counts.get("Tamas", 0) / total,
        "gurutva_fraction": counts.get("Gurutva", 0) / total,
        "prema_fraction": counts.get("Prema", 0) / total,
        "copositivity_pairwise": copositivity_pairwise(params),
        "records": records,
    }


def transition_matrix(plus_codes, minus_codes) -> dict[str, dict[str, int]]:
    plus = np.asarray(plus_codes, dtype=int)
    minus = np.asarray(minus_codes, dtype=int)
    out = {p: {m: 0 for m in PHASE_ORDER} for p in PHASE_ORDER}
    code_to_phase = {v: k for k, v in PHASE_TO_CODE.items()}
    for a, b in zip(plus.ravel(), minus.ravel()):
        out[code_to_phase.get(int(a), "Other")][code_to_phase.get(int(b), "Other")] += 1
    return out


def compare_plus_minus(plus_result: Mapping[str, Any], minus_result: Mapping[str, Any]) -> dict[str, Any]:
    plus = np.asarray(plus_result["phase_codes"], dtype=int)
    minus = np.asarray(minus_result["phase_codes"], dtype=int)
    changed = plus != minus
    total = int(plus.size)
    return {
        "changed_phase_fraction_plus_vs_minus": int(np.sum(changed)) / total,
        "changed_cells_count_plus_vs_minus": int(np.sum(changed)),
        "phase_transition_matrix": transition_matrix(plus, minus),
        "delta_mixed_fraction": minus_result["mixed_fraction"] - plus_result["mixed_fraction"],
        "delta_tamas_fraction": minus_result["tamas_fraction"] - plus_result["tamas_fraction"],
        "delta_quadrant_agreement": (minus_result["quadrant_agreement"] or 0.0) - (plus_result["quadrant_agreement"] or 0.0),
        "minus_quadrant_law_preserved_threshold_passed": (minus_result["quadrant_agreement"] or 0.0) >= 0.95,
        "minus_matches_plus_effective_axis": int(np.sum(changed)) == 0,
        "legacy_minus_quadrant_law_survives": (minus_result["quadrant_agreement"] or 0.0) >= 0.95,
    }


def build_robustness_defs() -> list[tuple[str, dict[str, float]]]:
    defs: list[tuple[str, dict[str, float]]] = []
    for v in ARHO_VALUES:
        defs.append((f"arho_{v:+.2f}", {"arho": v}))
    for v in AIOTA_VALUES:
        defs.append((f"aiota_{v:+.2f}", {"aiota": v}))
    for v in C_VALUES:
        defs.append((f"c_{v:+.2f}", {"c": v}))
    for ar in PORTAL_GRID_VALUES:
        for ai in PORTAL_GRID_VALUES:
            defs.append((f"portal_grid_arho_{ar:+.2f}_aiota_{ai:+.2f}_c_-0.05", {"arho": ar, "aiota": ai, "c": -0.05}))
    return defs


def _plot_phase(codes, title: str, out_path: Path, config: MemorySignConfig) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    colors = ["#4daf4a", "#377eb8", "#984ea3", "#ff7f00", "#dddddd", "#a6cee3", "#cab2d6", "#b15928", "#e41a1c"]
    cmap = matplotlib.colors.ListedColormap(colors)
    norm = matplotlib.colors.BoundaryNorm(np.arange(-0.5, len(PHASE_ORDER) + 0.5, 1), cmap.N)
    fig, ax = plt.subplots(figsize=(8.4, 6.6), constrained_layout=True)
    im = ax.imshow(np.asarray(codes), origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
    cb = fig.colorbar(im, ax=ax, ticks=np.arange(len(PHASE_ORDER)))
    cb.ax.set_yticklabels(PHASE_ORDER)
    ax.axvline(0, color="black", lw=0.6, alpha=0.55)
    ax.axhline(0, color="black", lw=0.6, alpha=0.55)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return str(out_path)


def _plot_mask(mask, title: str, out_path: Path, config: MemorySignConfig) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6.2), constrained_layout=True)
    im = ax.imshow(np.asarray(mask, dtype=int), origin="lower", extent=[*config.mrho2_range, *config.miota2_eff_range], aspect="auto", cmap="Reds", interpolation="nearest", vmin=0, vmax=1)
    fig.colorbar(im, ax=ax, ticks=[0, 1])
    ax.axvline(0, color="black", lw=0.6, alpha=0.55)
    ax.axhline(0, color="black", lw=0.6, alpha=0.55)
    ax.set_xlabel("mrho2")
    ax.set_ylabel("miota2_eff")
    ax.set_title(title)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return str(out_path)


def _plot_transition(matrix: Mapping[str, Mapping[str, int]], out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.array([[matrix[p][m] for m in PHASE_ORDER] for p in PHASE_ORDER], dtype=float)
    fig, ax = plt.subplots(figsize=(9, 7.5), constrained_layout=True)
    im = ax.imshow(arr, cmap="viridis")
    ax.set_xticks(range(len(PHASE_ORDER)), PHASE_ORDER, rotation=45, ha="right")
    ax.set_yticks(range(len(PHASE_ORDER)), PHASE_ORDER)
    ax.set_xlabel("minus phase")
    ax.set_ylabel("plus phase")
    ax.set_title("Plus -> minus memory-sign transition matrix")
    fig.colorbar(im, ax=ax, label="cells")
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if arr[i, j] > 0:
                ax.text(j, i, str(int(arr[i, j])), ha="center", va="center", color="white" if arr[i, j] > arr.max() * 0.45 else "black", fontsize=7)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return str(out_path)


def _table(rows: list[dict[str, Any]], cols: list[str]) -> list[str]:
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        vals = []
        for c in cols:
            v = r.get(c, "")
            vals.append(f"{v:.4f}" if isinstance(v, float) else str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def write_memory_sign_report(payload: Mapping[str, Any], report_path: Path) -> str:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    pb = payload["phase_boundary"]
    comp = pb["comparison"]
    robust_rows = payload.get("robustness_summary_rows", [])
    lines = [
        "# PQT-QG Memory Sign Reconciliation Report v0.6",
        "",
        "## 1. Goal",
        "Reconcile old plus-sign local memory benchmarks with the patched UV/bath minus-sign self-energy convention.",
        "",
        "## 2. Canon issue",
        "v0.1-v0.5 used `m_iota_eff2 = miota2 + LambdaT2_kappa0`. Patched UV/bath logic suggests `Delta_iota^{-1}=k^2+m_iota_eff2-Sigma_E`, so the corrected local benchmark tests `m_iota_eff2 = miota2 - kappa0`.",
        "",
        "## 3. Exact sign conventions",
        "- plus mode: `V0 += +0.5*LambdaT2_kappa0*s^2`, axis `miota2_eff = miota2 + LambdaT2_kappa0`.",
        "- minus mode: `V0 += -0.5*LambdaT2_kappa0*s^2`, axis `miota2_eff = miota2 - LambdaT2_kappa0`.",
        "",
        "## 4. Phase boundary comparison",
    ]
    pb_rows = []
    for sign in MEMORY_SIGNS:
        r = pb[sign]
        row = {"memory_sign": sign, "quadrant_agreement": r["quadrant_agreement"], "topology_status": r["topology_status"]}
        for phase in ["Prema", "Gurutva", "Tamas", "Mixed", "Other", "Rho_only", "Iota_only", "Unstable"]:
            row[f"count_{phase}"] = r["phase_counts"].get(phase, 0)
            row[f"fraction_{phase}"] = r["phase_fractions"].get(phase, 0.0)
        pb_rows.append(row)
    lines += _table(pb_rows, ["memory_sign", "quadrant_agreement", "topology_status", "fraction_Prema", "fraction_Gurutva", "fraction_Tamas", "fraction_Mixed", "fraction_Other"])
    lines += ["", "### Plus vs minus comparison"]
    lines += _table([comp], ["changed_phase_fraction_plus_vs_minus", "changed_cells_count_plus_vs_minus", "delta_mixed_fraction", "delta_tamas_fraction", "delta_quadrant_agreement", "minus_matches_plus_effective_axis", "minus_quadrant_law_preserved_threshold_passed"])
    lines += ["", "### Transition matrix", "Rows are plus phases; columns are minus phases.", "", "```json", json.dumps(comp["phase_transition_matrix"], indent=2), "```", ""]
    lines += ["## 5. Robustness comparison"]
    if robust_rows:
        lines += _table(robust_rows, ["sweep", "memory_sign", "quadrant_agreement", "topology_status", "mixed_fraction", "tamas_fraction", "copositivity_status"])
    else:
        lines.append("Robustness scan skipped.")
    lines += [
        "",
        "## 6. Does mass-sign quadrant law survive in effective axes?",
        f"Minus-mode phase-boundary agreement is `{pb['minus']['quadrant_agreement']:.4f}` with status `{pb['minus']['topology_status']}`.",
        "",
        "## 7. Does Tamas/Mixed region invert, shrink, expand, or remain structurally similar?",
        f"Delta Mixed fraction (minus-plus): `{comp['delta_mixed_fraction']:.4f}`. Delta Tamas fraction (minus-plus): `{comp['delta_tamas_fraction']:.4f}`.",
        "",
        "## 8. Is the v0.1-v0.5 scaffold still valid as a method?",
        "The scaffold remains valid as a computational method because the effective-axis scan can be rerun under either sign convention. Old plus-sign outputs should be treated as baseline artifacts, not final canon, until full `Sigma_E(k)` is implemented.",
        "",
        "## 9. Interpretation",
    ]
    if abs(comp.get("changed_phase_fraction_plus_vs_minus", 0.0)) < 1e-12:
        lines.append("Plus and minus modes are identical when compared on the effective `miota2_eff` axis. The sign correction changes how bare `miota2` maps to the effective axis, not the tree-level phase mechanics in this local benchmark.")
        if comp["minus_quadrant_law_preserved_threshold_passed"]:
            lines.append("The corrected minus convention also meets the quadrant-law survival threshold on this slice.")
        else:
            lines.append("The corrected minus convention inherits the same below-threshold quadrant agreement as the plus baseline; this deformation is from the chosen D-like portal slice/grid, not from the memory-sign flip itself.")
    elif comp["minus_quadrant_law_preserved_threshold_passed"]:
        lines.append("Minus mode preserves the quadrant law in effective axes despite some cell-level changes: phase mechanics mostly survives and the main change is the convention mapping from bare `miota2` to `miota2_eff`.")
    else:
        lines.append("Minus mode changes the phase map and is below the quadrant-law threshold: downstream one-loop/continuation studies should be rerun under corrected bath-memory sign.")
    lines += [
        "",
        "## 10. Warnings",
        "- synthetic benchmark only",
        "- tree-level mostly",
        "- local memory approximation only",
        "- no full nonlocal `Sigma_E(k)`",
        "- no RG improvement",
        "- no physical prediction",
        "- no proof of PQT-QG",
        "- sign reconciliation is canon-recovery, not final phenomenology",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def run_memory_sign_reconciliation(root: Path, grid: int = 61, memory_sign: str = "both", skip_robustness: bool = False, skip_one_loop_smoke: bool = True, output_tag: str = "v0_6") -> dict[str, Path]:
    signs = MEMORY_SIGNS if memory_sign == "both" else [memory_sign]
    config = MemorySignConfig(grid_shape=(grid, grid))
    data_dir = root / "outputs" / "data"
    plot_dir = root / "outputs" / "plots" / f"memory_sign_{output_tag}"
    report_dir = root / "outputs" / "reports"
    for d in (data_dir, plot_dir, report_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("PQT-QG Benchmark v0.6 — Corrected Bath-Memory Sign Reconciliation")
    print(f"grid shape: {config.grid_shape}; memory_sign={memory_sign}")

    phase_boundary: dict[str, Any] = {}
    all_records: list[dict[str, Any]] = []
    plots: dict[str, str] = {}
    for sign in signs:
        print(f"\nphase boundary scan: memory_sign={sign}")
        res = scan_phase_map_signed(BASE_PARAMS, sign, config, "phase_boundary")
        phase_boundary[sign] = {k: v for k, v in res.items() if k != "records"}
        all_records.extend(res["records"])
        print("phase counts:", {k: v for k, v in res["phase_counts"].items() if v})
        print(f"quadrant agreement: {res['quadrant_agreement']:.6f}; topology: {res['topology_status']}")
        plots[f"phase_boundary_{sign}"] = _plot_phase(res["phase_codes"], f"phase boundary {sign}", plot_dir / f"phase_boundary_{sign}.png", config)
        print(f"wrote plot: {plots[f'phase_boundary_{sign}']}")

    if "plus" in phase_boundary and "minus" in phase_boundary:
        comp = compare_plus_minus(phase_boundary["plus"], phase_boundary["minus"])
        phase_boundary["comparison"] = comp
        changed_mask = np.asarray(phase_boundary["plus"]["phase_codes"]) != np.asarray(phase_boundary["minus"]["phase_codes"])
        plots["phase_boundary_plus_minus_changed_mask"] = _plot_mask(changed_mask, "plus vs minus changed phase mask", plot_dir / "phase_boundary_plus_minus_changed_mask.png", config)
        plots["phase_boundary_plus_minus_transition_matrix"] = _plot_transition(comp["phase_transition_matrix"], plot_dir / "phase_boundary_plus_minus_transition_matrix.png")
        print(f"changed fraction plus vs minus: {comp['changed_phase_fraction_plus_vs_minus']:.6f}")
    else:
        phase_boundary["comparison"] = {}

    robustness_results: list[dict[str, Any]] = []
    robustness_rows: list[dict[str, Any]] = []
    if not skip_robustness:
        for label, overrides in build_robustness_defs():
            for sign in signs:
                params = dict(BASE_PARAMS)
                params.update(overrides)
                params["name"] = label
                print(f"\nrobustness scan: {label}; sign={sign}; overrides={overrides}")
                res = scan_phase_map_signed(params, sign, config, label)
                compact = {k: v for k, v in res.items() if k != "records"}
                robustness_results.append(compact)
                all_records.extend(res["records"])
                row = {
                    "sweep": label,
                    "memory_sign": sign,
                    "quadrant_agreement": res["quadrant_agreement"],
                    "topology_status": res["topology_status"],
                    "mixed_fraction": res["mixed_fraction"],
                    "tamas_fraction": res["tamas_fraction"],
                    "gurutva_fraction": res["gurutva_fraction"],
                    "prema_fraction": res["prema_fraction"],
                    "copositivity_status": res["copositivity_pairwise"]["status"],
                }
                robustness_rows.append(row)
                print("phase counts:", {k: v for k, v in res["phase_counts"].items() if v})
                print(f"quadrant agreement: {res['quadrant_agreement']:.6f}; topology: {res['topology_status']}; copositivity: {row['copositivity_status']}")
                safe_label = label.replace("+", "plus").replace("-", "minus")
                plots[f"robustness_{label}_{sign}"] = _plot_phase(res["phase_codes"], f"{label} {sign}", plot_dir / f"robustness_{safe_label}_{sign}.png", config)
        # changed masks for robustness pairs
        if set(signs) == {"plus", "minus"}:
            by_label = {}
            for r in robustness_results:
                by_label.setdefault(r["label"], {})[r["memory_sign"]] = r
            for label, pair in by_label.items():
                if "plus" in pair and "minus" in pair:
                    safe_label = label.replace("+", "plus").replace("-", "minus")
                    mask = np.asarray(pair["plus"]["phase_codes"]) != np.asarray(pair["minus"]["phase_codes"])
                    plots[f"robustness_{label}_changed_mask"] = _plot_mask(mask, f"{label}: plus vs minus changed", plot_dir / f"robustness_{safe_label}_changed_mask.png", config)

    one_loop_smoke = {"status": "skipped", "reason": "skip_one_loop_smoke default true for v0.6 runtime; TODO run signed one-loop follow-up if needed."}
    payload = {
        "name": "PQT-QG Benchmark v0.6 — Corrected Bath-Memory Sign Reconciliation",
        "config": {"grid_shape": list(config.grid_shape), "mrho2_range": list(config.mrho2_range), "miota2_eff_range": list(config.miota2_eff_range)},
        "base_params": BASE_PARAMS,
        "memory_signs": signs,
        "phase_boundary": phase_boundary,
        "robustness_results": robustness_results,
        "robustness_summary_rows": robustness_rows,
        "one_loop_smoke": one_loop_smoke,
        "plots": plots,
    }

    json_path = data_dir / f"memory_sign_reconciliation_{output_tag}.json"
    csv_path = data_dir / f"memory_sign_reconciliation_{output_tag}.csv"
    summary_path = data_dir / f"memory_sign_reconciliation_summary_{output_tag}.json"
    report_path = report_dir / "PQT_QG_Memory_Sign_Reconciliation_Report_v0_6.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(all_records).to_csv(csv_path, index=False)
    summary = {
        "phase_boundary_summary": phase_boundary,
        "robustness_summary_rows": robustness_rows,
        "one_loop_smoke": one_loop_smoke,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = write_memory_sign_report(payload, report_path)
    print(f"\nwrote data: {json_path}")
    print(f"wrote data: {csv_path}")
    print(f"wrote data: {summary_path}")
    print(f"wrote report: {report}")
    return {"json": json_path, "csv": csv_path, "summary": summary_path, "report": report_path, "plot_dir": plot_dir}


