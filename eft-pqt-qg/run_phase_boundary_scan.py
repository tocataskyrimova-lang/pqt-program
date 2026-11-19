from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pqt_qg.phase_boundary import plot_phase_boundary, scan_phase_boundary, write_phase_boundary_report

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
DATA = OUT / "data"
PLOTS = OUT / "plots"
REPORTS = OUT / "reports"


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    result = scan_phase_boundary()
    json_path = DATA / "phase_boundary_scan_v0_2.json"
    csv_path = DATA / "phase_boundary_scan_v0_2.csv"
    plot_path = PLOTS / "phase_boundary_v0_2_mrho2_miota2eff.png"
    report_path = REPORTS / "PQT_QG_Phase_Boundary_Report_v0_2.md"

    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame(result["records"]).to_csv(csv_path, index=False)
    plot_written = plot_phase_boundary(result, plot_path)
    report_written = write_phase_boundary_report(result, plot_written, report_path)

    print(f"wrote data: {json_path}")
    print(f"wrote data: {csv_path}")
    print(f"wrote plot: {plot_written}")
    print(f"wrote report: {report_written}")
    print("Done.")


if __name__ == "__main__":
    main()
