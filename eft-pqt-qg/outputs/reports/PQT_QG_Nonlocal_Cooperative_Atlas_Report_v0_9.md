# PQT-QG Nonlocal Cooperative Atlas Report v0.9

## 1. Goal
Map the wider cooperative nonlocal-memory sector after v0.8–v0.8.2 validation.

## 2. Why v0.9 is justified
v0.8 showed phase changes under full nonlocal minimization; v0.8.1 showed they were not sign-symmetry or optimizer artifacts; v0.8.2 showed the Mixed attractor was not just a phi=2 boundary artifact.

## 3. Canon assumptions
Synthetic Euclidean nonlocal memory benchmark; cutoff/scheme dependent; no physical prediction or proof of PQT-QG.

## 4. Numerical setup
Region `{'mrho2_range': [-0.8, 0.1], 'miota2_eff_range': [-0.8, 0.1]}`, grid `21`, kernels `['local_constant', 'single_pole', 'exp_gap']`, kmax `5.0`, num_k `96`, bounds `[[0.0, 3.0], [-2.5, 2.5], [-2.5, 2.5]]`, bound mode `phi3`.

## 5. Phase table
| kernel | mixed_fraction | other_fraction | gurutva_fraction | tamas_fraction | count_Mixed | count_Gurutva | count_Tamas | count_Other |
|---|---|---|---|---|---|---|---|---|
| local_constant | 1 | 0 | 0 | 0 | 441 | 0 | 0 | 0 |
| single_pole | 1 | 0 | 0 | 0 | 441 | 0 | 0 | 0 |
| exp_gap | 1 | 0 | 0 | 0 | 441 | 0 | 0 | 0 |

## 6. Transition table
| kernel | changed_phase_fraction | Gurutva_to_Mixed | Tamas_to_Mixed | Other_to_Mixed | Mixed_to_Mixed | Mixed_to_nonMixed |
|---|---|---|---|---|---|---|
| local_constant | 0 | 0 | 0 | 0 | 441 | 0 |
| single_pole | 0 | 0 | 0 | 0 | 441 | 0 |
| exp_gap | 0 | 0 | 0 | 0 | 441 | 0 |

## 7. Nonlocal effect atlas fractions
| kernel | frac_stable_mixed_core | frac_nonlocal_mixed_conversion | frac_nonlocal_phase_disruption | frac_determinant_stress | frac_optimizer_suspect | frac_boundary_caution |
|---|---|---|---|---|---|---|
| local_constant | 1 | 0 | 0 | 0 | 0 | 0 |
| single_pole | 0.91156 | 0 | 0 | 0 | 0.088435 | 0 |
| exp_gap | 0.90023 | 0 | 0 | 0 | 0.099773 | 0 |

## 8. Determinant health
| kernel | determinant_health_fraction | min_iota_inverse_global | min_det_global | optimizer_success_fraction | failed_changed_cell_count |
|---|---|---|---|---|---|
| local_constant | 1 | 0.48321 | 0.070543 | 1 | 0 |
| single_pole | 1 | 0.48657 | 0.071118 | 0.91156 | 0 |
| exp_gap | 1 | 0.48747 | 0.071289 | 0.90023 | 0 |

## 9. Boundary audit
| kernel | max_phi | avg_phi | fraction_phi_near_upper_bound |
|---|---|---|---|
| local_constant | 2.0955 | 1.7495 | 0 |
| single_pole | 2.0956 | 1.7496 | 0 |
| exp_gap | 2.0957 | 1.7497 | 0 |

## 10. Canonical distance audit
| kernel | avg_raw_delta | max_raw_delta | avg_canonical_delta | max_canonical_delta | avg_symmetry_reduced_delta | max_symmetry_reduced_delta |
|---|---|---|---|---|---|---|
| local_constant | 0 | 0 | 0 | 0 | 0 | 0 |
| single_pole | 0.00074341 | 0.0017342 | 0.00074341 | 0.0017342 | 0.00074341 | 0.0017342 |
| exp_gap | 0.00091793 | 0.0022206 | 0.00091793 | 0.0022206 | 0.00091793 | 0.0022206 |

## 11. Interpretation
- `local_constant`: Mixed fraction `1.0000`, conversion fraction `0.0000`, determinant health `1.0000`, boundary caution `0.0000`.
- `single_pole`: Mixed fraction `1.0000`, conversion fraction `0.0000`, determinant health `1.0000`, boundary caution `0.0000`.
- `exp_gap`: Mixed fraction `1.0000`, conversion fraction `0.0000`, determinant health `1.0000`, boundary caution `0.0000`.

## 12. Warnings
- atlas still synthetic
- no physical prediction
- no RG
- no full renormalization
- determinant health diagnostic, not theorem
- cutoff/scheme dependence