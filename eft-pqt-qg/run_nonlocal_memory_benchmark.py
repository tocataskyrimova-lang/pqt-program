from __future__ import annotations

import argparse
from pathlib import Path

from pqt_qg.nonlocal_scan import run_nonlocal_benchmark

ROOT = Path(__file__).resolve().parent


def _csv(text: str):
    return [x.strip() for x in text.split(",") if x.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description="PQT-QG v0.7 nonlocal Sigma_E(k) memory benchmark")
    p.add_argument("--grid", type=int, default=31, choices=[31, 41, 61])
    p.add_argument("--num-k", type=int, default=96)
    p.add_argument("--kmax", type=float, default=5.0)
    p.add_argument("--kernels", default="local_constant,single_pole,exp_gap")
    p.add_argument("--slices", default="preserved,baseline,cooperative")
    p.add_argument("--nonlocal-scale", type=float, default=1.0)
    p.add_argument("--skip-plots", action="store_true")
    args = p.parse_args()
    outputs = run_nonlocal_benchmark(ROOT, grid=args.grid, num_k=args.num_k, kmax=args.kmax, kernels=_csv(args.kernels), slices=_csv(args.slices), nonlocal_scale=args.nonlocal_scale, skip_plots=args.skip_plots)
    print("Done.")
    for k, v in outputs.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
