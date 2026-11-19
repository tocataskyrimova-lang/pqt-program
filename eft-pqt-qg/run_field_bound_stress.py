from __future__ import annotations

import argparse
from pathlib import Path

from pqt_qg.field_bound_stress import run_field_bound_stress

ROOT=Path(__file__).resolve().parent

def _csv(s): return [x.strip() for x in s.split(',') if x.strip()]

def main():
    p=argparse.ArgumentParser(description='PQT-QG v0.8.2 field-bound stress test')
    p.add_argument('--grid',type=int,default=11,choices=[11,15,21])
    p.add_argument('--num-k',type=int,default=96,choices=[96,160])
    p.add_argument('--kmax',type=float,default=5.0,choices=[5.0,7.0])
    p.add_argument('--bound-modes',default='baseline,phi3,soft25')
    p.add_argument('--kernels',default='single_pole,exp_gap')
    p.add_argument('--wall-strength',type=float,default=1.0)
    p.add_argument('--include-phi4',action='store_true')
    p.add_argument('--skip-plots',action='store_true')
    args=p.parse_args()
    out=run_field_bound_stress(ROOT,grid=args.grid,num_k=args.num_k,kmax=args.kmax,bound_modes=_csv(args.bound_modes),kernels=_csv(args.kernels),wall_strength=args.wall_strength,include_phi4=args.include_phi4,skip_plots=args.skip_plots)
    print('Done.')
    for k,v in out.items(): print(f'{k}: {v}')
if __name__=='__main__': main()
