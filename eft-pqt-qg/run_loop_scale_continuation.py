from __future__ import annotations

import argparse
from pathlib import Path

from pqt_qg.loop_continuation import DEFAULT_LOOP_SCALES, run_loop_scale_continuation

ROOT = Path(__file__).resolve().parent


def parse_loop_scales(text: str):
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="PQT-QG Benchmark v0.5 loop-scale continuation")
    parser.add_argument("--grid", type=int, default=61, help="Grid side length. Default: 61. Use --grid 101 for full run.")
    parser.add_argument("--loop-scales", default=",".join(str(x) for x in DEFAULT_LOOP_SCALES), help="Comma-separated loop scales, e.g. 0,0.25,0.5,0.75,1.0")
    args = parser.parse_args()
    outputs = run_loop_scale_continuation(ROOT, grid=args.grid, loop_scales=parse_loop_scales(args.loop_scales))
    print("Done.")
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
