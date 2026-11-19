from __future__ import annotations

import argparse
from pathlib import Path

from pqt_qg.memory_sign import run_memory_sign_reconciliation

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="PQT-QG v0.6 memory sign reconciliation")
    parser.add_argument("--grid", type=int, default=101, choices=[61, 101], help="Grid side length. Use 61 for smoke, 101 for full.")
    parser.add_argument("--skip-robustness", action="store_true", help="Skip compact robustness sign comparison.")
    parser.add_argument("--skip-one-loop-smoke", action="store_true", default=True, help="Skip optional signed one-loop smoke; default true.")
    parser.add_argument("--memory-sign", choices=["plus", "minus", "both"], default="both")
    parser.add_argument("--output-tag", default="v0_6")
    args = parser.parse_args()
    outputs = run_memory_sign_reconciliation(
        ROOT,
        grid=args.grid,
        memory_sign=args.memory_sign,
        skip_robustness=args.skip_robustness,
        skip_one_loop_smoke=args.skip_one_loop_smoke,
        output_tag=args.output_tag,
    )
    print("Done.")
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
