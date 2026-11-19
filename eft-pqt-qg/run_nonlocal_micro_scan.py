from __future__ import annotations

import argparse
from pathlib import Path

from pqt_qg.nonlocal_minimize import run_micro_scan

ROOT = Path(__file__).resolve().parent


def _csv(text: str):
    return [x.strip() for x in text.split(",") if x.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description="PQT-QG v0.8 full nonlocal minimization micro-scan")
    p.add_argument("--grid", type=int, default=11, choices=[7, 11, 15, 21])
    p.add_argument("--num-k", type=int, default=96, choices=[64, 96, 160])
    p.add_argument("--kmax", type=float, default=5.0, choices=[5.0, 7.0, 10.0])
    p.add_argument("--kernels", default="local,single_pole,exp_gap")
    p.add_argument("--nonlocal-scale", type=float, default=1.0)
    p.add_argument("--wide", action="store_true")
    p.add_argument("--max-seeds", choices=["all", "local_only"], default="all")
    p.add_argument("--skip-plots", action="store_true")
    args = p.parse_args()
    outputs = run_micro_scan(ROOT, grid=args.grid, num_k=args.num_k, kmax=args.kmax, kernels=_csv(args.kernels), nonlocal_scale=args.nonlocal_scale, wide=args.wide, max_seeds=args.max_seeds, skip_plots=args.skip_plots)
    print("Done.")
    for k, v in outputs.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
