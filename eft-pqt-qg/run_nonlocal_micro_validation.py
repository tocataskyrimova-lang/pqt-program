from __future__ import annotations

import argparse
from pathlib import Path

from pqt_qg.nonlocal_validation import run_validation

ROOT = Path(__file__).resolve().parent


def _csv(text: str):
    return [x.strip() for x in text.split(',') if x.strip()]


def main() -> None:
    p=argparse.ArgumentParser(description='PQT-QG v0.8.1 nonlocal micro-scan validation')
    p.add_argument('--grid', type=int, default=11, choices=[11,15,21])
    p.add_argument('--num-k', type=int, default=96, choices=[96,160,240])
    p.add_argument('--kmax', type=float, default=5.0, choices=[5.0,7.0])
    p.add_argument('--kernels', default='local,single_pole,exp_gap')
    p.add_argument('--validation-mode', choices=['reproduce','resolution','cutoff','all'], default='reproduce')
    p.add_argument('--skip-plots', action='store_true')
    args=p.parse_args()
    outputs=run_validation(ROOT, validation_mode=args.validation_mode, grid=args.grid, num_k=args.num_k, kmax=args.kmax, kernels=_csv(args.kernels), skip_plots=args.skip_plots)
    print('Done.')
    for k,v in outputs.items():
        print(f'{k}: {v}')

if __name__ == '__main__':
    main()
