# PQT-QG Loop-Scale Continuation Report v0.5

## 1. Goal
Determine whether local Coleman-Weinberg corrections deform PQT-QG synthetic phase maps smoothly as `loop_scale` increases from 0 to 1, or whether abrupt topology transitions occur.

## 2. Canon assumptions
- Core Psi remains frozen into `muH_eff2`; H does not replace Psi.
- Observed scalar landscape only.
- Memory enters only through local `LambdaT2_kappa0`.
- Local CW only; no full nonlocal `K_T` determinant; no RG improvement.
- Off-shell `Veff` is gauge-dependent; negative `m^2` uses Re[Veff] convention.

## 3. Why continuation is needed after v0.4
v0.4 compared only loop_scale 0 and 1. v0.5 checks whether the interpolation is gentle or phase-flip-like.

## 4. Selected slices
- `preserved_c_plus_0_10`
- `baseline_mild_deformed`
- `cooperative_strongly_deformed`
- `positive_edge_deformed`

## 5. Loop-scale values
0.0, 0.25, 0.5, 0.75, 1.0

## 6. Agreement vs loop-scale table
| slice | loop_scale | quadrant_agreement | topology_status |
|---|---|---|---|
| preserved_c_plus_0_10 | 0.0000 | 0.9806 | preserved |
| preserved_c_plus_0_10 | 0.2500 | 0.9806 | preserved |
| preserved_c_plus_0_10 | 0.5000 | 0.9806 | preserved |
| preserved_c_plus_0_10 | 0.7500 | 0.9803 | preserved |
| preserved_c_plus_0_10 | 1.0000 | 0.9803 | preserved |
| baseline_mild_deformed | 0.0000 | 0.9447 | strongly deformed |
| baseline_mild_deformed | 0.2500 | 0.9461 | strongly deformed |
| baseline_mild_deformed | 0.5000 | 0.9478 | strongly deformed |
| baseline_mild_deformed | 0.7500 | 0.9489 | strongly deformed |
| baseline_mild_deformed | 1.0000 | 0.9500 | mildly deformed |
| cooperative_strongly_deformed | 0.0000 | 0.7361 | strongly deformed |
| cooperative_strongly_deformed | 0.2500 | 0.8206 | strongly deformed |
| cooperative_strongly_deformed | 0.5000 | 0.8247 | strongly deformed |
| cooperative_strongly_deformed | 0.7500 | 0.8292 | strongly deformed |
| cooperative_strongly_deformed | 1.0000 | 0.8431 | strongly deformed |
| positive_edge_deformed | 0.0000 | 0.8303 | strongly deformed |
| positive_edge_deformed | 0.2500 | 0.8339 | strongly deformed |
| positive_edge_deformed | 0.5000 | 0.8344 | strongly deformed |
| positive_edge_deformed | 0.7500 | 0.8361 | strongly deformed |
| positive_edge_deformed | 1.0000 | 0.8431 | strongly deformed |

## 7. Mixed fraction vs loop-scale table
| slice | loop_scale | mixed_fraction | rho_only_fraction | iota_only_fraction | other_fraction |
|---|---|---|---|---|---|
| preserved_c_plus_0_10 | 0.0000 | 0.2529 | 0.0000 | 0.0000 | 0.0000 |
| preserved_c_plus_0_10 | 0.2500 | 0.2513 | 0.0000 | 0.0000 | 0.0000 |
| preserved_c_plus_0_10 | 0.5000 | 0.2497 | 0.0000 | 0.0000 | 0.0000 |
| preserved_c_plus_0_10 | 0.7500 | 0.2486 | 0.0000 | 0.0000 | 0.0000 |
| preserved_c_plus_0_10 | 1.0000 | 0.2470 | 0.0000 | 0.0000 | 0.0000 |
| baseline_mild_deformed | 0.0000 | 0.2967 | 0.0000 | 0.0000 | 0.0000 |
| baseline_mild_deformed | 0.2500 | 0.2954 | 0.0000 | 0.0000 | 0.0000 |
| baseline_mild_deformed | 0.5000 | 0.2937 | 0.0000 | 0.0000 | 0.0000 |
| baseline_mild_deformed | 0.7500 | 0.2927 | 0.0000 | 0.0000 | 0.0000 |
| baseline_mild_deformed | 1.0000 | 0.2916 | 0.0000 | 0.0000 | 0.0000 |
| cooperative_strongly_deformed | 0.0000 | 0.3185 | 0.0000 | 0.0000 | 0.0218 |
| cooperative_strongly_deformed | 0.2500 | 0.3910 | 0.0000 | 0.0000 | 0.0000 |
| cooperative_strongly_deformed | 0.5000 | 0.3865 | 0.0000 | 0.0000 | 0.0000 |
| cooperative_strongly_deformed | 0.7500 | 0.3819 | 0.0000 | 0.0000 | 0.0000 |
| cooperative_strongly_deformed | 1.0000 | 0.3773 | 0.0000 | 0.0000 | 0.0000 |
| positive_edge_deformed | 0.0000 | 0.1975 | 0.0701 | 0.0000 | 0.0317 |
| positive_edge_deformed | 0.2500 | 0.2010 | 0.0701 | 0.0000 | 0.0312 |
| positive_edge_deformed | 0.5000 | 0.2013 | 0.0701 | 0.0000 | 0.0309 |
| positive_edge_deformed | 0.7500 | 0.2029 | 0.0701 | 0.0000 | 0.0293 |
| positive_edge_deformed | 1.0000 | 0.2026 | 0.0701 | 0.0000 | 0.0309 |

## 8. Changed fraction vs loop-scale table
| slice | loop_scale | changed_phase_fraction_vs_loop0 | changed_phase_fraction_vs_previous_scale |
|---|---|---|---|
| preserved_c_plus_0_10 | 0.0000 | 0.0000 | 0.0000 |
| preserved_c_plus_0_10 | 0.2500 | 0.0016 | 0.0016 |
| preserved_c_plus_0_10 | 0.5000 | 0.0032 | 0.0016 |
| preserved_c_plus_0_10 | 0.7500 | 0.0043 | 0.0011 |
| preserved_c_plus_0_10 | 1.0000 | 0.0059 | 0.0016 |
| baseline_mild_deformed | 0.0000 | 0.0000 | 0.0000 |
| baseline_mild_deformed | 0.2500 | 0.0013 | 0.0013 |
| baseline_mild_deformed | 0.5000 | 0.0030 | 0.0016 |
| baseline_mild_deformed | 0.7500 | 0.0040 | 0.0011 |
| baseline_mild_deformed | 1.0000 | 0.0051 | 0.0011 |
| cooperative_strongly_deformed | 0.0000 | 0.0000 | 0.0000 |
| cooperative_strongly_deformed | 0.2500 | 0.0822 | 0.0822 |
| cooperative_strongly_deformed | 0.5000 | 0.0868 | 0.0046 |
| cooperative_strongly_deformed | 0.7500 | 0.0914 | 0.0046 |
| cooperative_strongly_deformed | 1.0000 | 0.1051 | 0.0137 |
| positive_edge_deformed | 0.0000 | 0.0000 | 0.0000 |
| positive_edge_deformed | 0.2500 | 0.0035 | 0.0035 |
| positive_edge_deformed | 0.5000 | 0.0043 | 0.0013 |
| positive_edge_deformed | 0.7500 | 0.0059 | 0.0038 |
| positive_edge_deformed | 1.0000 | 0.0129 | 0.0129 |

## 9. Instability fraction vs loop-scale table
| slice | loop_scale | instability_fraction | instability_cells_count |
|---|---|---|---|
| preserved_c_plus_0_10 | 0.0000 | 0.0000 | 0 |
| preserved_c_plus_0_10 | 0.2500 | 0.0000 | 0 |
| preserved_c_plus_0_10 | 0.5000 | 0.0003 | 1 |
| preserved_c_plus_0_10 | 0.7500 | 0.0000 | 0 |
| preserved_c_plus_0_10 | 1.0000 | 0.0003 | 1 |
| baseline_mild_deformed | 0.0000 | 0.0000 | 0 |
| baseline_mild_deformed | 0.2500 | 0.0000 | 0 |
| baseline_mild_deformed | 0.5000 | 0.0003 | 1 |
| baseline_mild_deformed | 0.7500 | 0.0000 | 0 |
| baseline_mild_deformed | 1.0000 | 0.0000 | 0 |
| cooperative_strongly_deformed | 0.0000 | 0.0000 | 0 |
| cooperative_strongly_deformed | 0.2500 | 0.0003 | 1 |
| cooperative_strongly_deformed | 0.5000 | 0.0003 | 1 |
| cooperative_strongly_deformed | 0.7500 | 0.0000 | 0 |
| cooperative_strongly_deformed | 1.0000 | 0.0105 | 39 |
| positive_edge_deformed | 0.0000 | 0.0000 | 0 |
| positive_edge_deformed | 0.2500 | 0.0000 | 0 |
| positive_edge_deformed | 0.5000 | 0.0000 | 0 |
| positive_edge_deformed | 0.7500 | 0.0000 | 0 |
| positive_edge_deformed | 1.0000 | 0.0000 | 0 |

## 10. Smoothness classification per slice
| slice | smoothness | max_step_changed_phase_fraction | agreement_trend | mixed_trend | max_instability_fraction | first_loop_scale_instability_gt_0_01 |
|---|---|---|---|---|---|---|
| preserved_c_plus_0_10 | smooth | 0.0016 | nearly_flat | decreasing | 0.0003 | None |
| baseline_mild_deformed | smooth | 0.0016 | increasing | decreasing | 0.0003 | None |
| cooperative_strongly_deformed | abrupt | 0.0822 | increasing | nonmonotonic | 0.0105 | 1.0000 |
| positive_edge_deformed | smooth | 0.0129 | increasing | increasing | 0.0000 | None |

## 11. Topology transition points
- `preserved_c_plus_0_10`: no topology-status transition
- `baseline_mild_deformed`: {'from': 'strongly deformed', 'to': 'mildly deformed', 'loop_scale': 1.0}
- `cooperative_strongly_deformed`: no topology-status transition
- `positive_edge_deformed`: no topology-status transition

## 12. Interpretation
- `preserved_c_plus_0_10`: smooth; agreement trend `nearly_flat`; Mixed trend `decreasing`.
- `baseline_mild_deformed`: smooth; agreement trend `increasing`; Mixed trend `decreasing`.
- `cooperative_strongly_deformed`: abrupt; agreement trend `increasing`; Mixed trend `nonmonotonic`.
- `positive_edge_deformed`: smooth; agreement trend `increasing`; Mixed trend `increasing`.
- Loop-stable slices have low max step changes and unchanged topology status.
- Loop-sensitive slices show status transitions, nonmonotonic trends, or elevated changed-cell fractions.

## 13. Warnings
- synthetic benchmark only
- local CW only
- gauge-dependent off-shell Veff
- Re[Veff] only for negative m2
- no RG improvement
- no full nonlocal K_T determinant
- no physical prediction
- no proof of PQT-QG