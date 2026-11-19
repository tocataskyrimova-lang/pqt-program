from __future__ import annotations

import argparse
from pathlib import Path

from pqt_qg.one_loop_scan import run_one_loop_benchmark

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="PQT-QG Benchmark v0.4 local one-loop CW scanner")
    parser.add_argument("--grid", type=int, default=61, help="Grid side length. Default: 61. Use --grid 101 for full run.")
    parser.add_argument("--loop-scale", type=float, default=1.0, help="Multiplier for V1. Examples: 0.0, 0.25, 1.0")
    args = parser.parse_args()
    outputs = run_one_loop_benchmark(ROOT, grid=args.grid, loop_scale=args.loop_scale)
    print("Done.")
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
