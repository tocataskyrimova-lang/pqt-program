"""Markdown and tabular reporting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def flatten_raw_minima(results: Iterable[dict]) -> list[dict]:
    rows = []
    for result in results:
        for m in result["raw_minima"]:
            row = dict(m)
            row["hessian_eigenvalues"] = ";".join(f"{v:.12g}" for v in m["hessian_eigenvalues"])
            row.pop("hessian", None)
            row.pop("params", None)
            rows.append(row)
    return rows


def write_csv(rows: list[dict], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _minima_table(minima: list[dict], grouped: bool = False) -> str:
    if not minima:
        return "No minima found."
    headers = ["id", "phase", "stability", "phi", "r/abs_r", "s/abs_s", "V0", "eigvals", "mult"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for m in minima:
        r = m.get("r", m.get("abs_r"))
        s = m.get("s", m.get("abs_s"))
        eig = ", ".join(f"{v:.6g}" for v in m["hessian_eigenvalues"])
        mult = str(m.get("symmetry_multiplicity", ""))
        lines.append(
            f"| {m['id']} | {m['phase']} | {m['stability']} | {m['phi']:.8g} | "
            f"{r:.8g} | {s:.8g} | {m['V0']:.10g} | {eig} | {mult} |"
        )
    return "\n".join(lines)


def write_report(results: list[dict], plot_paths: dict[str, list[str]], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PQT-QG Benchmark Report v0.1",
        "",
        "## Goal",
        "Scan and visualize the tree-level PQT-QG observed scalar vacuum landscape `V0(phi,r,s)` for synthetic benchmark parameter sets.",
        "",
        "## Canon assumptions used",
        "- `Core Psi` is frozen into `muH_eff2`; it is not replaced by `H`.",
        "- Background: `H=(0,phi)/sqrt(2)`, `rho=r`, `iota=s`.",
        "- Local memory approximation only: `K_T(k) ≈ kappa0`, included as `+0.5*LambdaT2_kappa0*s^2`.",
        "- Canonical portal normalization: diagonal Hessian shifts use `a/2`, not `2a`.",
        "",
        "## Warnings",
        "- Synthetic benchmark only.",
        "- Tree-level only.",
        "- No physical prediction.",
        "- No one-loop correction yet.",
        "- No nonlocal `K_T` determinant yet.",
        "",
    ]

    for result in results:
        name = result["benchmark"]
        lines.extend([f"## Benchmark {name}", "", "### Parameters", "", "```json"])
        import json

        lines.append(json.dumps(result["params"], indent=2))
        lines.extend(["```", "", "### Copositivity sanity check", ""])
        cop = result["copositivity_pairwise"]
        lines.append(f"Status: **{cop['status']}**")
        for key, value in cop["checks"].items():
            lines.append(f"- `{key}`: {value}")
        lines.append(f"- Note: {cop['note']}")
        lines.extend(["", "### Plots", ""])
        for p in plot_paths.get(name, []):
            lines.append(f"- `{p}`")
        lines.extend(["", "### Global minimum", ""])
        gm = result.get("global_minimum")
        lines.append(_minima_table([gm] if gm else []))
        lines.extend(["", "### All stable raw minima", ""])
        lines.append(_minima_table(result.get("all_stable_minima", [])))
        lines.extend(["", "### Symmetry-grouped minima", ""])
        lines.append(_minima_table(result.get("symmetry_grouped_minima", []), grouped=True))
        lines.extend(["", "### Phase representatives", ""])
        reps = result.get("phase_representatives", {})
        lines.append(_minima_table(list(reps.values()), grouped=True))
        phases = sorted({m["phase"] for m in result.get("symmetry_grouped_minima", [])})
        lines.extend([
            "",
            "### Branch notes",
            f"Observed grouped phases: {', '.join(phases) if phases else 'none'}.",
            "Stable branches are identified by positive Hessian eigenvalues within `eps_eigen=1e-6`.",
            "",
        ])

    Path(path).write_text("\n".join(lines), encoding="utf-8")
