from __future__ import annotations

import json
from pathlib import Path

from pqt_qg.plot import make_plots
from pqt_qg.report import flatten_raw_minima, write_csv, write_report
from pqt_qg.scan import ScanConfig, scan_benchmark

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
PLOTS_DIR = OUTPUTS / "plots"
DATA_DIR = OUTPUTS / "data"
REPORTS_DIR = OUTPUTS / "reports"

BENCHMARKS = [
    {
        "name": "A_prema_only",
        "muH_eff2": 0.13,
        "lambdaH": 0.13,
        "mrho2": 0.50,
        "brho": 0.30,
        "arho": 0.40,
        "miota2": 0.60,
        "biota": 0.30,
        "aiota": 0.40,
        "c": 0.20,
        "LambdaT2_kappa0": 0.20,
    },
    {
        "name": "B_gurutva_branch",
        "muH_eff2": 0.13,
        "lambdaH": 0.13,
        "mrho2": -0.35,
        "brho": 0.40,
        "arho": 0.20,
        "miota2": 0.60,
        "biota": 0.30,
        "aiota": 0.40,
        "c": 0.20,
        "LambdaT2_kappa0": 0.20,
    },
    {
        "name": "C_tamas_branch",
        "muH_eff2": 0.13,
        "lambdaH": 0.13,
        "mrho2": 0.50,
        "brho": 0.30,
        "arho": 0.40,
        "miota2": -0.35,
        "biota": 0.45,
        "aiota": 0.10,
        "c": 0.20,
        "LambdaT2_kappa0": -0.15,
    },
    {
        "name": "D_mixed_exploratory",
        "muH_eff2": 0.13,
        "lambdaH": 0.13,
        "mrho2": -0.35,
        "brho": 0.45,
        "arho": -0.08,
        "miota2": -0.35,
        "biota": 0.50,
        "aiota": -0.08,
        "c": -0.05,
        "LambdaT2_kappa0": 0.05,
        "exploratory": True,
    },
]


def _json_default(obj):
    try:
        import numpy as np

        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
    except Exception:
        pass
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")


def main() -> None:
    print("PQT-QG Benchmark Sheet v0.1 — vacuum landscape scanner")
    print("Tree-level only; synthetic benchmark only; no physical prediction.")
    for d in [PLOTS_DIR, DATA_DIR, REPORTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    config = ScanConfig()
    results = []
    plot_paths: dict[str, list[str]] = {}
    for params in BENCHMARKS:
        result = scan_benchmark(params, config)
        paths = make_plots(result, PLOTS_DIR)
        plot_paths[result["benchmark"]] = paths
        for p in paths:
            print(f"wrote plot: {p}")
        results.append(result)

    minima_rows = flatten_raw_minima(results)
    minima_summary = {
        "raw_minima": [m for result in results for m in result["raw_minima"]],
        "symmetry_grouped_minima": [m for result in results for m in result["symmetry_grouped_minima"]],
        "global_minimum": {result["benchmark"]: result["global_minimum"] for result in results},
        "all_stable_minima": {result["benchmark"]: result["all_stable_minima"] for result in results},
        "phase_representatives": {result["benchmark"]: result["phase_representatives"] for result in results},
    }
    grid_summary = {
        result["benchmark"]: {
            "params": result["params"],
            "copositivity_pairwise": result["copositivity_pairwise"],
            "grid_summary": result["grid_summary"],
        }
        for result in results
    }

    write_json(DATA_DIR / "benchmarks_used.json", BENCHMARKS)
    write_json(DATA_DIR / "minima_summary.json", minima_summary)
    write_csv(minima_rows, DATA_DIR / "minima_summary.csv")
    write_json(DATA_DIR / "grid_scan_summary.json", grid_summary)
    write_report(results, plot_paths, REPORTS_DIR / "PQT_QG_Benchmark_Report_v0_1.md")

    print(f"wrote data: {DATA_DIR / 'benchmarks_used.json'}")
    print(f"wrote data: {DATA_DIR / 'minima_summary.json'}")
    print(f"wrote data: {DATA_DIR / 'minima_summary.csv'}")
    print(f"wrote data: {DATA_DIR / 'grid_scan_summary.json'}")
    print(f"wrote report: {REPORTS_DIR / 'PQT_QG_Benchmark_Report_v0_1.md'}")
    print("Done.")


if __name__ == "__main__":
    main()
