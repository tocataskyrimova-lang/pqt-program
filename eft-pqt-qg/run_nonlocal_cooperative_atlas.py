from __future__ import annotations

import argparse
from pathlib import Path

from pqt_qg.nonlocal_cooperative_atlas import run_atlas

ROOT=Path(__file__).resolve().parent

def _csv(s): return [x.strip() for x in s.split(',') if x.strip()]

def main():
    p=argparse.ArgumentParser(description='PQT-QG v0.9 Nonlocal Cooperative Atlas')
    p.add_argument('--grid',type=int,default=21,choices=[15,21,31,41])
    p.add_argument('--num-k',type=int,default=96,choices=[64,96,160])
    p.add_argument('--kmax',type=float,default=5.0)
    p.add_argument('--kernels',default='local,single_pole,exp_gap')
    p.add_argument('--bound-mode',choices=['phi3','soft25'],default='phi3')
    p.add_argument('--wall-strength',type=float,default=1.0)
    p.add_argument('--max-seeds',choices=['all','local_plus_mixed'],default='all')
    p.add_argument('--skip-exp-gap',action='store_true')
    p.add_argument('--skip-plots',action='store_true')
    args=p.parse_args()
    kernels=_csv(args.kernels)
    if args.skip_exp_gap:
        kernels=[k for k in kernels if k not in {'exp_gap','exp'}]
    out=run_atlas(ROOT,grid=args.grid,num_k=args.num_k,kmax=args.kmax,kernels=kernels,bound_mode=args.bound_mode,wall_strength=args.wall_strength,max_seeds=args.max_seeds,skip_plots=args.skip_plots)
    print('Done.')
    for k,v in out.items(): print(f'{k}: {v}')
if __name__=='__main__': main()
