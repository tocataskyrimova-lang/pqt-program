"""Field-bound stress test for PQT-QG nonlocal micro-scan v0.8.2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .classify import classify_phase
from .memory_sign import MemorySignConfig, active_set_minimum_signed
from .nonlocal_memory import NonlocalKernelParams, V0_zero_mode_corrected, det_delta_N, iota_inverse, neutral_mass_entries, quadrature_grid
from .nonlocal_minimize import COOPERATIVE_SLICE
from .phase_boundary import PHASE_ORDER, PHASE_TO_CODE

TRACKED_CELLS = [
    (-0.55, -0.55), (-0.50, -0.55), (-0.45, -0.55), (-0.55, -0.50),
    (-0.50, -0.50), (-0.55, -0.45), (-0.50, -0.45), (-0.55, -0.40),
]

BOUND_MODES = {
    "baseline": {"label": "bound_phi_2_baseline", "bounds": ((0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0)), "wall_at": None},
    "phi3": {"label": "bound_phi_3", "bounds": ((0.0, 3.0), (-2.5, 2.5), (-2.5, 2.5)), "wall_at": None},
    "phi4": {"label": "bound_phi_4_optional", "bounds": ((0.0, 4.0), (-3.0, 3.0), (-3.0, 3.0)), "wall_at": None},
    "soft25": {"label": "soft_wall_phi_2_5", "bounds": ((0.0, 3.0), (-2.5, 2.5), (-2.5, 2.5)), "wall_at": 2.5},
    "soft20": {"label": "soft_wall_phi_2_0", "bounds": ((0.0, 3.0), (-2.5, 2.5), (-2.5, 2.5)), "wall_at": 2.0},
}


class BoundConfig:
    def __init__(self, grid: int, bounds, wall_at=None, wall_strength: float = 1.0):
        self.mrho2_range = (-0.55, -0.05)
        self.miota2_eff_range = (-0.55, -0.05)
        self.grid_shape = (grid, grid)
        self.field_bounds = bounds
        self.wall_at = wall_at
        self.wall_strength = wall_strength
        self.health_eps = 1e-8
        self.det_eps = 1e-8

    def as_dict(self):
        return {"mrho2_range": list(self.mrho2_range), "miota2_eff_range": list(self.miota2_eff_range), "grid_shape": list(self.grid_shape), "field_bounds": [list(b) for b in self.field_bounds], "wall_at": self.wall_at, "wall_strength": self.wall_strength}


def _wall(phi: float, config: BoundConfig) -> float:
    if config.wall_at is None:
        return 0.0
    return float(config.wall_strength * max(0.0, phi - config.wall_at) ** 4)


def _objective_factory(params, kernel, kp: NonlocalKernelParams, config: BoundConfig):
    k, weights, q = quadrature_grid(kp)
    ref_kernel = det_delta_N(q, 0.0, 0.0, 0.0, params, kernel, kp)
    ref_local = det_delta_N(q, 0.0, 0.0, 0.0, params, "local_constant", kp)
    log_ref_kernel = np.log(np.abs(ref_kernel) + kp.eps_det)
    log_ref_local = np.log(np.abs(ref_local) + kp.eps_det)
    pref = weights * k**3 / (16.0 * np.pi * np.pi)

    def v1(x, kern, ref):
        phi, r, s = np.asarray(x, dtype=float)
        det = det_delta_N(q, phi, r, s, params, kern, kp)
        return float(np.sum(pref * (np.log(np.abs(det) + kp.eps_det) - ref)))

    def obj(x):
        phi, r, s = np.asarray(x, dtype=float)
        base = V0_zero_mode_corrected(phi, r, s, params, kp.sigma0) + _wall(phi, config)
        if kernel == "local_constant" or kp.nonlocal_scale == 0.0:
            return float(base)
        return float(base + kp.nonlocal_scale * (v1(x, kernel, log_ref_kernel) - v1(x, "local_constant", log_ref_local)))

    def diag(x):
        phi, r, s = np.asarray(x, dtype=float)
        det = det_delta_N(q, phi, r, s, params, kernel, kp)
        inv = iota_inverse(q, neutral_mass_entries(phi, r, s, params)["m_ss_local2"], kernel, kp)
        return {"min_det": float(np.min(det)), "min_iota_inverse": float(np.min(inv)), "determinant_health": bool(np.min(inv) > -config.health_eps and np.min(det) > -config.det_eps)}

    return obj, diag


def _seeds(local_x, config: BoundConfig, include_phi4=False):
    lo = np.array([b[0] for b in config.field_bounds])
    hi = np.array([b[1] for b in config.field_bounds])
    base = np.asarray(local_x, dtype=float)
    seeds = [base]
    for p in ([0.05,0,0],[-0.05,0,0],[0,0.05,0],[0,-0.05,0],[0,0,0.05],[0,0,-0.05]):
        seeds.append(base + np.array(p))
    seeds += [np.array(x, dtype=float) for x in [(1,0,0),(1,0.8,0),(1,0,0.8),(1,0.8,0.8),(0,0,0),(2.0,1.4,1.4),(2.5,1.4,1.4),(3.0,1.4,1.4)]]
    if include_phi4:
        seeds.append(np.array([4.0,1.4,1.4]))
    return [np.clip(s, lo, hi) for s in seeds]


def _minimize(obj, seeds, bounds):
    ranked = sorted([(obj(s), s) for s in seeds], key=lambda t: t[0])[:5]
    best_v, best_x = ranked[0]
    best_ok, best_msg = True, "seed"
    for _, seed in ranked:
        res = minimize(obj, seed, method="L-BFGS-B", bounds=list(bounds), options={"maxiter": 55, "ftol": 1e-9, "gtol": 1e-6, "eps": 2e-4})
        val = float(obj(res.x))
        if val < best_v:
            best_v, best_x, best_ok, best_msg = val, np.asarray(res.x), bool(res.success), str(res.message)
    return np.asarray(best_x), float(best_v), best_ok, best_msg


def scan_bound_mode(kernel: str, mode_key: str, grid: int, kp: NonlocalKernelParams, wall_strength: float, include_phi4: bool):
    mode = BOUND_MODES[mode_key]
    config = BoundConfig(grid, mode["bounds"], mode["wall_at"], wall_strength)
    xs = np.linspace(*config.mrho2_range, config.grid_shape[0])
    ys = np.linspace(*config.miota2_eff_range, config.grid_shape[1])
    records=[]
    codes=np.zeros((len(ys), len(xs)), dtype=int)
    phi_grid=np.zeros_like(codes, dtype=float)
    obj_grid=np.zeros_like(codes, dtype=float)
    health=np.zeros_like(codes, dtype=bool)
    min_iota=np.zeros_like(codes, dtype=float)
    min_det=np.zeros_like(codes, dtype=float)
    mconfig=MemorySignConfig(grid_shape=config.grid_shape, mrho2_range=config.mrho2_range, miota2_eff_range=config.miota2_eff_range, field_bounds=config.field_bounds)
    for iy,y in enumerate(ys):
        for ix,x in enumerate(xs):
            params=dict(COOPERATIVE_SLICE); params['mrho2']=float(x); params['miota2']=float(y + kp.sigma0)
            local=active_set_minimum_signed(params, float(x), float(y), 'minus', mconfig)
            local_x=np.array([local['phi'], local['abs_r'], local['abs_s']], dtype=float)
            obj, diag = _objective_factory(params, kernel, kp, config)
            nx, val, ok, msg = _minimize(obj, _seeds(local_x, config, include_phi4), config.field_bounds)
            d=diag(nx); phase=classify_phase(*nx)
            phi_upper=config.field_bounds[0][1]
            r_upper=config.field_bounds[1][1]
            s_upper=config.field_bounds[2][1]
            rec={
                'kernel':kernel,'bound_mode':mode_key,'bound_label':mode['label'],'grid_i':ix,'grid_j':iy,'mrho2':float(x),'miota2_eff':float(y),
                'phi':float(nx[0]),'r':float(nx[1]),'s':float(nx[2]),'phase':phase,'objective_value':val,'optimizer_success':bool(ok),'optimizer_message':msg,
                **d,
                'phi_at_upper_bound': bool(abs(nx[0]-phi_upper)<1e-4),'phi_near_upper_bound': bool(nx[0] > phi_upper-0.05),
                'r_at_bound': bool(abs(abs(nx[1])-r_upper)<1e-4),'s_at_bound': bool(abs(abs(nx[2])-s_upper)<1e-4),
            }
            records.append(rec); codes[iy,ix]=PHASE_TO_CODE.get(phase, PHASE_TO_CODE['Other']); phi_grid[iy,ix]=nx[0]; obj_grid[iy,ix]=val; health[iy,ix]=d['determinant_health']; min_iota[iy,ix]=d['min_iota_inverse']; min_det[iy,ix]=d['min_det']
        print(f"  {kernel}/{mode_key}: row {iy+1}/{len(ys)}")
    return {'kernel':kernel,'bound_mode':mode_key,'config':config.as_dict(),'records':records,'phase_codes':codes,'phi_grid':phi_grid,'objective_grid':obj_grid,'det_health_mask':health,'min_iota_grid':min_iota,'min_det_grid':min_det}


def summarize(result, baseline_by_kernel=None):
    rec=result['records']; total=len(rec); codes=result['phase_codes']; counts={p:int(np.sum(codes==c)) for p,c in PHASE_TO_CODE.items()}
    phi=[r['phi'] for r in rec]
    row={'kernel':result['kernel'],'bound_mode':result['bound_mode'],'phase_counts':counts,'mixed_fraction':counts.get('Mixed',0)/total,'avg_phi':float(np.mean(phi)),'max_phi':float(np.max(phi)),'fraction_phi_at_upper_bound':float(np.mean([r['phi_at_upper_bound'] for r in rec])),'fraction_phi_near_upper_bound':float(np.mean([r['phi_near_upper_bound'] for r in rec])),'determinant_health_fraction':float(np.mean([r['determinant_health'] for r in rec])),'optimizer_success_fraction':float(np.mean([r['optimizer_success'] for r in rec]))}
    row.update({f'count_{p}': counts.get(p,0) for p in PHASE_ORDER})
    base = baseline_by_kernel.get(result['kernel']) if baseline_by_kernel else None
    if base:
        bmap={(r['mrho2'],r['miota2_eff']):r for r in base['records']}
        changes=[]; deltas=[]; objd=[]; max_phi_base=max(r['phi'] for r in base['records'])
        for r in rec:
            b=bmap[(r['mrho2'],r['miota2_eff'])]
            changes.append(r['phase']!=b['phase']); deltas.append(float(np.linalg.norm(np.array([r['phi'],r['r'],r['s']])-np.array([b['phi'],b['r'],b['s']])))); objd.append(r['objective_value']-b['objective_value'])
            r['delta_phi_vs_baseline']=r['phi']-b['phi']; r['delta_r_vs_baseline']=r['r']-b['r']; r['delta_s_vs_baseline']=r['s']-b['s']; r['delta_position_vs_baseline']=deltas[-1]; r['phase_changed_vs_baseline']=changes[-1]; r['objective_delta_vs_baseline']=objd[-1]
        row['changed_phase_fraction_vs_phi2_baseline']=float(np.mean(changes)); row['avg_delta_position_vs_phi2']=float(np.mean(deltas)); row['max_delta_position_vs_phi2']=float(np.max(deltas)); row['max_phi_increase_vs_baseline']=row['max_phi']-max_phi_base
    else:
        row['changed_phase_fraction_vs_phi2_baseline']=0.0; row['avg_delta_position_vs_phi2']=0.0; row['max_delta_position_vs_phi2']=0.0; row['max_phi_increase_vs_baseline']=0.0
    if row['fraction_phi_near_upper_bound'] < 0.05 and row['changed_phase_fraction_vs_phi2_baseline'] < 0.05 and row['determinant_health_fraction'] >= 0.95:
        label='interior_stable'
    elif row['fraction_phi_near_upper_bound'] >= 0.05 and row['changed_phase_fraction_vs_phi2_baseline'] < 0.05 and row['max_phi_increase_vs_baseline'] <= 0.5:
        label='boundary_pinned_but_phase_stable'
    elif row['max_phi_increase_vs_baseline'] > 0.5 or row['fraction_phi_near_upper_bound'] >= 0.05:
        label='large_field_drift'
    else:
        label='runaway_suspect' if row['determinant_health_fraction'] < 0.8 else 'interior_stable'
    row['behavior_label']=label
    return row


def tracked_changed_cells(all_records):
    out=[]
    for x,y in TRACKED_CELLS:
        for r in all_records:
            if abs(r['mrho2']-x)<1e-9 and abs(r['miota2_eff']-y)<1e-9:
                row=dict(r); row['tracked_cell']=f"({x},{y})"; row['mixed_conversion_persists']=r['phase']=='Mixed'; out.append(row)
    return out


def _plot_grid(grid,title,path,config,cmap='viridis'):
    path.parent.mkdir(parents=True, exist_ok=True); fig,ax=plt.subplots(figsize=(7,5.5),constrained_layout=True); im=ax.imshow(grid,origin='lower',extent=[*config['mrho2_range'],*config['miota2_eff_range']],aspect='auto',cmap=cmap,interpolation='nearest'); fig.colorbar(im,ax=ax); ax.set_xlabel('mrho2'); ax.set_ylabel('miota2_eff'); ax.set_title(title); fig.savefig(path,dpi=150); plt.close(fig); return str(path)

def _bar(rows, metric, title, path):
    path.parent.mkdir(parents=True, exist_ok=True); labels=[f"{r['kernel']}\n{r['bound_mode']}" for r in rows]; fig,ax=plt.subplots(figsize=(max(8,.55*len(rows)),5),constrained_layout=True); ax.bar(range(len(rows)),[r[metric] for r in rows]); ax.set_xticks(range(len(rows)),labels,rotation=65,ha='right',fontsize=7); ax.set_ylabel(metric); ax.set_title(title); ax.grid(axis='y',alpha=.25); fig.savefig(path,dpi=150); plt.close(fig); return str(path)

def write_report(payload,path):
    path.parent.mkdir(parents=True, exist_ok=True); rows=payload['summary_rows']; tracked=payload['tracked_cells']
    def table(rows,cols,max_rows=None):
        rr=rows[:max_rows] if max_rows else rows; out=['| '+' | '.join(cols)+' |','|'+'|'.join(['---']*len(cols))+'|']
        for r in rr:
            out.append('| '+' | '.join(f"{r.get(c,''):.5g}" if isinstance(r.get(c,''),float) else str(r.get(c,'')) for c in cols)+' |')
        return out
    lines=['# PQT-QG Field-Bound Stress Report v0.8.2','', '## 1. Goal','Test whether v0.8/v0.8.1 nonlocal Mixed conversion is an interior effect or phi-boundary artifact.','', '## 2. Why needed','v0.8.1 showed real canonical displacement and optimizer-successful changed cells, but several minima saturated phi=2.0.','', '## 3. Canon assumptions','Synthetic Euclidean nonlocal memory benchmark only; no physical prediction or proof.','', '## 4. Numerical setup',f"Grid `{payload['grid']}`, kernels `{payload['kernels']}`, bound modes `{payload['bound_modes']}`, kmax `{payload['kmax']}`, num_k `{payload['num_k']}`, wall strength `{payload['wall_strength']}`.",'', '## 5. Bound behavior summary']
    lines+=table(rows,['kernel','bound_mode','mixed_fraction','max_phi','avg_phi','fraction_phi_at_upper_bound','fraction_phi_near_upper_bound','determinant_health_fraction','optimizer_success_fraction','changed_phase_fraction_vs_phi2_baseline','behavior_label'])
    lines+=['','## 6. Changed-cell tracking']
    lines+=table(tracked,['kernel','bound_mode','tracked_cell','phase','phi','objective_value','determinant_health','mixed_conversion_persists'],max_rows=120)
    lines+=['','## 7. Main answers']
    for r in rows:
        lines.append(f"- `{r['kernel']}` / `{r['bound_mode']}`: max_phi `{r['max_phi']:.4f}`, near-bound `{r['fraction_phi_near_upper_bound']:.4f}`, Mixed `{r['mixed_fraction']:.4f}`, label `{r['behavior_label']}`.")
    lines+=['','## 8. Warnings','- micro-scan only','- boundary stress test only','- not physical prediction','- determinant health diagnostic, not theorem','- no RG improvement','- no full renormalization']
    path.write_text('\n'.join(lines),encoding='utf-8'); return str(path)

def run_field_bound_stress(root:Path, grid:int=11, num_k:int=96, kmax:float=5.0, bound_modes:Iterable[str]|None=None, kernels:Iterable[str]|None=None, wall_strength:float=1.0, include_phi4:bool=False, skip_plots:bool=False):
    bound_modes=list(bound_modes or ['baseline','phi3','soft25']);
    if include_phi4 and 'phi4' not in bound_modes: bound_modes.append('phi4')
    kernels=['local_constant' if k=='local' else k for k in (kernels or ['single_pole','exp_gap'])]
    kp=NonlocalKernelParams(kmax=kmax,num_k=num_k)
    data_dir=root/'outputs'/'data'; plot_dir=root/'outputs'/'plots'/'field_bound_v0_8_2'; report_dir=root/'outputs'/'reports'
    for d in (data_dir,plot_dir,report_dir): d.mkdir(parents=True,exist_ok=True)
    print('PQT-QG Benchmark v0.8.2 — Field-bound Stress Test')
    print(f'grid={grid}; kernels={kernels}; bound_modes={bound_modes}; kmax={kmax}; num_k={num_k}')
    results=[]; all_records=[]; summaries=[]; plots={}; baseline_by_kernel={}
    for kernel in kernels:
        for mode in bound_modes:
            print(f"\n=== kernel={kernel} bound_mode={mode} ===")
            res=scan_bound_mode(kernel,mode,grid,kp,wall_strength,include_phi4)
            if mode=='baseline': baseline_by_kernel[kernel]=res
            summary=summarize(res, baseline_by_kernel)
            summaries.append(summary); results.append({'kernel':kernel,'bound_mode':mode,'summary':summary}); all_records.extend(res['records'])
            print(f"max_phi={summary['max_phi']:.4f}; near_bound={summary['fraction_phi_near_upper_bound']:.4f}; Mixed={summary['mixed_fraction']:.4f}; det_health={summary['determinant_health_fraction']:.4f}; label={summary['behavior_label']}")
            if not skip_plots:
                cfg=res['config']; prefix=f"{kernel}_{mode}"
                plots[f'{prefix}_phase_map']=_plot_grid(res['phase_codes'],f'{prefix} phase',plot_dir/f'{prefix}_phase_map.png',cfg)
                plots[f'{prefix}_phi_heatmap']=_plot_grid(res['phi_grid'],f'{prefix} phi',plot_dir/f'{prefix}_phi_heatmap.png',cfg)
                plots[f'{prefix}_phi_near_bound_mask']=_plot_grid(np.array([[r['phi_near_upper_bound'] for r in res['records']][i*grid:(i+1)*grid] for i in range(grid)],dtype=int),f'{prefix} phi near bound',plot_dir/f'{prefix}_phi_near_bound_mask.png',cfg,cmap='Reds')
                plots[f'{prefix}_det_health_mask']=_plot_grid(res['det_health_mask'].astype(int),f'{prefix} det health',plot_dir/f'{prefix}_det_health_mask.png',cfg,cmap='Greens')
                plots[f'{prefix}_objective_heatmap']=_plot_grid(res['objective_grid'],f'{prefix} objective',plot_dir/f'{prefix}_objective_heatmap.png',cfg)
    tracked=tracked_changed_cells(all_records)
    if not skip_plots:
        plots['summary_max_phi_by_bound_mode']=_bar(summaries,'max_phi','max phi by bound mode',plot_dir/'summary_max_phi_by_bound_mode.png')
        plots['summary_fraction_phi_near_bound']=_bar(summaries,'fraction_phi_near_upper_bound','fraction phi near bound',plot_dir/'summary_fraction_phi_near_bound.png')
        plots['summary_mixed_fraction_by_bound_mode']=_bar(summaries,'mixed_fraction','Mixed fraction',plot_dir/'summary_mixed_fraction_by_bound_mode.png')
        plots['summary_det_health_by_bound_mode']=_bar(summaries,'determinant_health_fraction','det health',plot_dir/'summary_det_health_by_bound_mode.png')
        plots['summary_changed_fraction_vs_phi2']=_bar(summaries,'changed_phase_fraction_vs_phi2_baseline','changed vs phi2 baseline',plot_dir/'summary_changed_fraction_vs_phi2.png')
    payload={'name':'PQT-QG Benchmark v0.8.2 — Field-bound Stress Test','grid':grid,'num_k':num_k,'kmax':kmax,'kernels':kernels,'bound_modes':bound_modes,'wall_strength':wall_strength,'summary_rows':summaries,'tracked_cells':tracked,'plots':plots}
    json_path=data_dir/'field_bound_stress_v0_8_2.json'; csv_path=data_dir/'field_bound_stress_v0_8_2.csv'; summary_path=data_dir/'field_bound_stress_summary_v0_8_2.json'; changed_path=data_dir/'field_bound_stress_changed_cells_v0_8_2.json'; report_path=report_dir/'PQT_QG_Field_Bound_Stress_Report_v0_8_2.md'
    json_path.write_text(json.dumps(payload,indent=2),encoding='utf-8'); pd.DataFrame(all_records).to_csv(csv_path,index=False); summary_path.write_text(json.dumps({'summary_rows':summaries,'plots':plots},indent=2),encoding='utf-8'); changed_path.write_text(json.dumps(tracked,indent=2),encoding='utf-8'); report=write_report(payload,report_path)
    print(f'wrote data: {json_path}'); print(f'wrote data: {csv_path}'); print(f'wrote data: {summary_path}'); print(f'wrote data: {changed_path}'); print(f'wrote report: {report}')
    return {'json':json_path,'csv':csv_path,'summary':summary_path,'changed_cells':changed_path,'report':report_path,'plot_dir':plot_dir}
