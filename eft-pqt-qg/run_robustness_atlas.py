from __future__ import annotations

from pathlib import Path

from pqt_qg.robustness import run_robustness_atlas


ROOT = Path(__file__).resolve().parent


def main() -> None:
    outputs = run_robustness_atlas(ROOT)
    print("Done.")
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
