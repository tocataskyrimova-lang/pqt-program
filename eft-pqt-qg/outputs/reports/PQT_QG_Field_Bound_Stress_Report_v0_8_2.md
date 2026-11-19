# PQT-QG Field-Bound Stress Report v0.8.2

## 1. Goal
Test whether v0.8/v0.8.1 nonlocal Mixed conversion is an interior effect or phi-boundary artifact.

## 2. Why needed
v0.8.1 showed real canonical displacement and optimizer-successful changed cells, but several minima saturated phi=2.0.

## 3. Canon assumptions
Synthetic Euclidean nonlocal memory benchmark only; no physical prediction or proof.

## 4. Numerical setup
Grid `11`, kernels `['single_pole', 'exp_gap']`, bound modes `['baseline', 'phi3', 'soft25']`, kmax `5.0`, num_k `96`, wall strength `1.0`.

## 5. Bound behavior summary
| kernel | bound_mode | mixed_fraction | max_phi | avg_phi | fraction_phi_at_upper_bound | fraction_phi_near_upper_bound | determinant_health_fraction | optimizer_success_fraction | changed_phase_fraction_vs_phi2_baseline | behavior_label |
|---|---|---|---|---|---|---|---|---|---|---|
| single_pole | baseline | 1 | 2 | 1.7462 | 0.066116 | 0.12397 | 1 | 0.92562 | 0 | boundary_pinned_but_phase_stable |
| single_pole | phi3 | 1 | 2.0956 | 1.7489 | 0 | 0 | 1 | 0.92562 | 0 | interior_stable |
| single_pole | soft25 | 1 | 2.0956 | 1.7489 | 0 | 0 | 1 | 0.92562 | 0 | interior_stable |
| exp_gap | baseline | 1 | 2 | 1.7463 | 0.066116 | 0.12397 | 1 | 0.92562 | 0 | boundary_pinned_but_phase_stable |
| exp_gap | phi3 | 1 | 2.0957 | 1.749 | 0 | 0 | 1 | 0.93388 | 0 | interior_stable |
| exp_gap | soft25 | 1 | 2.0957 | 1.749 | 0 | 0 | 1 | 0.93388 | 0 | interior_stable |

## 6. Changed-cell tracking
| kernel | bound_mode | tracked_cell | phase | phi | objective_value | determinant_health | mixed_conversion_persists |
|---|---|---|---|---|---|---|---|
| single_pole | baseline | (-0.55,-0.55) | Mixed | 2 | -0.74645 | True | True |
| single_pole | phi3 | (-0.55,-0.55) | Mixed | 2.0956 | -0.74973 | True | True |
| single_pole | soft25 | (-0.55,-0.55) | Mixed | 2.0956 | -0.74973 | True | True |
| exp_gap | baseline | (-0.55,-0.55) | Mixed | 2 | -0.74638 | True | True |
| exp_gap | phi3 | (-0.55,-0.55) | Mixed | 2.0957 | -0.74967 | True | True |
| exp_gap | soft25 | (-0.55,-0.55) | Mixed | 2.0957 | -0.74967 | True | True |
| single_pole | baseline | (-0.5,-0.55) | Mixed | 2 | -0.69227 | True | True |
| single_pole | phi3 | (-0.5,-0.55) | Mixed | 2.0624 | -0.69366 | True | True |
| single_pole | soft25 | (-0.5,-0.55) | Mixed | 2.0624 | -0.69366 | True | True |
| exp_gap | baseline | (-0.5,-0.55) | Mixed | 2 | -0.6922 | True | True |
| exp_gap | phi3 | (-0.5,-0.55) | Mixed | 2.0625 | -0.69359 | True | True |
| exp_gap | soft25 | (-0.5,-0.55) | Mixed | 2.0625 | -0.69359 | True | True |
| single_pole | baseline | (-0.45,-0.55) | Mixed | 2 | -0.64088 | True | True |
| single_pole | phi3 | (-0.45,-0.55) | Mixed | 2.029 | -0.64118 | True | True |
| single_pole | soft25 | (-0.45,-0.55) | Mixed | 2.029 | -0.64118 | True | True |
| exp_gap | baseline | (-0.45,-0.55) | Mixed | 2 | -0.64081 | True | True |
| exp_gap | phi3 | (-0.45,-0.55) | Mixed | 2.029 | -0.64111 | True | True |
| exp_gap | soft25 | (-0.45,-0.55) | Mixed | 2.029 | -0.64111 | True | True |
| single_pole | baseline | (-0.55,-0.5) | Mixed | 2 | -0.69756 | True | True |
| single_pole | phi3 | (-0.55,-0.5) | Mixed | 2.0656 | -0.6991 | True | True |
| single_pole | soft25 | (-0.55,-0.5) | Mixed | 2.0656 | -0.6991 | True | True |
| exp_gap | baseline | (-0.55,-0.5) | Mixed | 2 | -0.69778 | True | True |
| exp_gap | phi3 | (-0.55,-0.5) | Mixed | 2.0656 | -0.69932 | True | True |
| exp_gap | soft25 | (-0.55,-0.5) | Mixed | 2.0656 | -0.69932 | True | True |
| single_pole | baseline | (-0.5,-0.5) | Mixed | 2 | -0.64352 | True | True |
| single_pole | phi3 | (-0.5,-0.5) | Mixed | 2.0325 | -0.64389 | True | True |
| single_pole | soft25 | (-0.5,-0.5) | Mixed | 2.0325 | -0.64389 | True | True |
| exp_gap | baseline | (-0.5,-0.5) | Mixed | 2 | -0.64374 | True | True |
| exp_gap | phi3 | (-0.5,-0.5) | Mixed | 2.0325 | -0.64411 | True | True |
| exp_gap | soft25 | (-0.5,-0.5) | Mixed | 2.0325 | -0.64411 | True | True |
| single_pole | baseline | (-0.55,-0.45) | Mixed | 2 | -0.65072 | True | True |
| single_pole | phi3 | (-0.55,-0.45) | Mixed | 2.0354 | -0.65116 | True | True |
| single_pole | soft25 | (-0.55,-0.45) | Mixed | 2.0354 | -0.65116 | True | True |
| exp_gap | baseline | (-0.55,-0.45) | Mixed | 2 | -0.651 | True | True |
| exp_gap | phi3 | (-0.55,-0.45) | Mixed | 2.0354 | -0.65145 | True | True |
| exp_gap | soft25 | (-0.55,-0.45) | Mixed | 2.0354 | -0.65145 | True | True |
| single_pole | baseline | (-0.5,-0.45) | Mixed | 2 | -0.59682 | True | True |
| single_pole | phi3 | (-0.5,-0.45) | Mixed | 2.0015 | -0.59682 | True | True |
| single_pole | soft25 | (-0.5,-0.45) | Mixed | 2.0015 | -0.59682 | True | True |
| exp_gap | baseline | (-0.5,-0.45) | Mixed | 2 | -0.5971 | True | True |
| exp_gap | phi3 | (-0.5,-0.45) | Mixed | 2.0016 | -0.5971 | True | True |
| exp_gap | soft25 | (-0.5,-0.45) | Mixed | 2.0016 | -0.5971 | True | True |
| single_pole | baseline | (-0.55,-0.4) | Mixed | 2 | -0.60677 | True | True |
| single_pole | phi3 | (-0.55,-0.4) | Mixed | 2.0048 | -0.60678 | True | True |
| single_pole | soft25 | (-0.55,-0.4) | Mixed | 2.0048 | -0.60678 | True | True |
| exp_gap | baseline | (-0.55,-0.4) | Mixed | 2 | -0.60673 | True | True |
| exp_gap | phi3 | (-0.55,-0.4) | Mixed | 2.0048 | -0.60674 | True | True |
| exp_gap | soft25 | (-0.55,-0.4) | Mixed | 2.0048 | -0.60674 | True | True |

## 7. Main answers
- `single_pole` / `baseline`: max_phi `2.0000`, near-bound `0.1240`, Mixed `1.0000`, label `boundary_pinned_but_phase_stable`.
- `single_pole` / `phi3`: max_phi `2.0956`, near-bound `0.0000`, Mixed `1.0000`, label `interior_stable`.
- `single_pole` / `soft25`: max_phi `2.0956`, near-bound `0.0000`, Mixed `1.0000`, label `interior_stable`.
- `exp_gap` / `baseline`: max_phi `2.0000`, near-bound `0.1240`, Mixed `1.0000`, label `boundary_pinned_but_phase_stable`.
- `exp_gap` / `phi3`: max_phi `2.0957`, near-bound `0.0000`, Mixed `1.0000`, label `interior_stable`.
- `exp_gap` / `soft25`: max_phi `2.0957`, near-bound `0.0000`, Mixed `1.0000`, label `interior_stable`.

## 8. Warnings
- micro-scan only
- boundary stress test only
- not physical prediction
- determinant health diagnostic, not theorem
- no RG improvement
- no full renormalization