# PQT-QG Nonlocal Micro-Scan Validation Report v0.8.1

## 1. Goal
Validate the v0.8 full nonlocal minimization result before expanding to a v0.9 atlas.

## 2. Why validation is needed
v0.8 found phase changes for single-pole/exp-gap kernels, determinant-health improvement, and a large max delta. v0.8.1 checks sign-symmetry reduction, changed-cell details, optimizer reliability, and resolution stability.

## 3. Canon assumptions
Synthetic benchmark only; Euclidean nonlocal memory; no physical prediction; no proof of PQT-QG.

## 4. Numerical setup
Runs: `[{'run_name': 'runA_reproduce', 'grid': 11, 'num_k': 96, 'kmax': 5.0}]`. Kernels: `['local_constant', 'single_pole', 'exp_gap']`. Objective and seeds reuse v0.8 full nonlocal minimization.

## 5. Symmetry-distance analysis
| run_name | kernel | max_raw_delta_position_norm | max_symmetry_reduced_delta_position_norm | max_canonical_delta_position_norm | average_raw_delta_position_norm | average_symmetry_reduced_delta_position_norm | average_canonical_delta_position_norm |
|---|---|---|---|---|---|---|---|
| runA_reproduce | local_constant | 0 | 0 | 0 | 0 | 0 | 0 |
| runA_reproduce | single_pole | 2.0641 | 2.0641 | 2.0641 | 0.11193 | 0.11193 | 0.11193 |
| runA_reproduce | exp_gap | 2.0641 | 2.0641 | 2.0641 | 0.1121 | 0.1121 | 0.1121 |

## 6. Changed-cell audit
| run_name | kernel | mrho2 | miota2_eff | local_phase | nonlocal_phase | raw_delta_position_norm | canonical_delta_position_norm | symmetry_reduced_delta_position_norm | optimizer_success |
|---|---|---|---|---|---|---|---|---|---|
| runA_reproduce | single_pole | -0.55 | -0.55 | Other | Mixed | 2.0597 | 2.0597 | 2.0597 | True |
| runA_reproduce | single_pole | -0.5 | -0.55 | Other | Mixed | 2.062 | 2.062 | 2.062 | True |
| runA_reproduce | single_pole | -0.45 | -0.55 | Tamas | Mixed | 1.5179 | 1.5179 | 1.5179 | True |
| runA_reproduce | single_pole | -0.55 | -0.5 | Gurutva | Mixed | 1.4704 | 1.4704 | 1.4704 | True |
| runA_reproduce | single_pole | -0.5 | -0.5 | Other | Mixed | 2.0641 | 2.0641 | 2.0641 | True |
| runA_reproduce | single_pole | -0.55 | -0.45 | Gurutva | Mixed | 1.4356 | 1.4356 | 1.4356 | True |
| runA_reproduce | single_pole | -0.5 | -0.45 | Gurutva | Mixed | 1.447 | 1.447 | 1.447 | True |
| runA_reproduce | single_pole | -0.55 | -0.4 | Gurutva | Mixed | 1.4001 | 1.4001 | 1.4001 | True |
| runA_reproduce | exp_gap | -0.55 | -0.55 | Other | Mixed | 2.0597 | 2.0597 | 2.0597 | True |
| runA_reproduce | exp_gap | -0.5 | -0.55 | Other | Mixed | 2.062 | 2.062 | 2.062 | True |
| runA_reproduce | exp_gap | -0.45 | -0.55 | Tamas | Mixed | 1.518 | 1.518 | 1.518 | True |
| runA_reproduce | exp_gap | -0.55 | -0.5 | Gurutva | Mixed | 1.4704 | 1.4704 | 1.4704 | True |
| runA_reproduce | exp_gap | -0.5 | -0.5 | Other | Mixed | 2.0641 | 2.0641 | 2.0641 | True |
| runA_reproduce | exp_gap | -0.55 | -0.45 | Gurutva | Mixed | 1.4358 | 1.4358 | 1.4358 | True |
| runA_reproduce | exp_gap | -0.5 | -0.45 | Gurutva | Mixed | 1.447 | 1.447 | 1.447 | True |
| runA_reproduce | exp_gap | -0.55 | -0.4 | Gurutva | Mixed | 1.4002 | 1.4002 | 1.4002 | True |

## 7. Resolution check
Only one run was executed; resolution comparison not available.

## 8. Kernel validation table
| run_name | kernel | changed_phase_fraction | Gurutva_to_Mixed | Tamas_to_Mixed | Other_to_Mixed | Mixed_to_Mixed | determinant_health_fraction | optimizer_success_fraction | failed_changed_cell_count |
|---|---|---|---|---|---|---|---|---|---|
| runA_reproduce | local_constant | 0 | 0 | 0 | 0 | 113 | 0.93388 | 1 | 0 |
| runA_reproduce | single_pole | 0.066116 | 4 | 1 | 3 | 113 | 1 | 0.91736 | 0 |
| runA_reproduce | exp_gap | 0.066116 | 4 | 1 | 3 | 113 | 1 | 0.93388 | 0 |

## 9. Main answer
- `runA_reproduce` / `local_constant`: changed `0.0000`, max raw `0.0000`, max canonical `0.0000` => real canonical displacement present.
- `runA_reproduce` / `single_pole`: changed `0.0661`, max raw `2.0641`, max canonical `2.0641` => real canonical displacement present.
- `runA_reproduce` / `exp_gap`: changed `0.0661`, max raw `2.0641`, max canonical `2.0641` => real canonical displacement present.

## 10. Warnings
- micro-scan only
- cutoff/scheme dependent
- optimizer-sensitive
- determinant health diagnostic, not theorem
- no RG improvement
- no physical prediction