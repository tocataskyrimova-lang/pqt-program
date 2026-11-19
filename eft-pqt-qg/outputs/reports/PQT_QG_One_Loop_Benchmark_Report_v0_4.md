# PQT-QG One-Loop Local Coleman-Weinberg Benchmark v0.4

## 1. Goal
Test whether selected tree-level Prema/Gurutva/Tamas/Mixed phase topologies survive after a local one-loop Coleman-Weinberg correction.

## 2. Canon assumptions
- Core Psi remains frozen into `muH_eff2`; H does not replace Psi.
- Observed scalar landscape only.
- Local memory approximation only: `K_T(k) ≈ kappa0`, via `LambdaT2_kappa0` as iota mass shift.
- Local CW only; no full nonlocal memory determinant; no RG improvement; no Nielsen analysis.
- `Veff` is gauge-dependent off-shell; negative mass-squared values use Re[V1] with flags.

## 3. Selected slices
- `preserved_c_plus_0_10` — v0.3 preserved slice c_+0.10
- `baseline_mild_deformed` — v0.2/v0.3 baseline mixed-friendly slice
- `cooperative_strongly_deformed` — v0.3 strongly deformed portal grid
- `positive_edge_deformed` — v0.3 arho_+0.20 strongly deformed edge

## 4. One-loop formula and constants
`Veff = V0 + loop_scale * V1`, `mu_ren=1.0`, `g_D=0.65`, `g_Y=0.36`, `y_top=1.0`, top multiplicity `n_top=-12`.
CW terms use `m^4(log(|m^2|/mu_ren^2)-c)` with constants `3/2` for scalars/fermions and `5/6` for vectors.

## 5. Tree vs CW phase fraction table
| slice | tree_Prema | cw_Prema | tree_Gurutva | cw_Gurutva | tree_Tamas | cw_Tamas | tree_Mixed | cw_Mixed | tree_Other | cw_Other |
|---|---|---|---|---|---|---|---|---|---|---|
| preserved_c_plus_0_10 | 0.2260 | 0.2260 | 0.2612 | 0.2642 | 0.2599 | 0.2628 | 0.2529 | 0.2470 | 0.0000 | 0.0000 |
| baseline_mild_deformed | 0.2260 | 0.2260 | 0.2378 | 0.2408 | 0.2395 | 0.2416 | 0.2967 | 0.2916 | 0.0000 | 0.0000 |
| cooperative_strongly_deformed | 0.1959 | 0.2051 | 0.2354 | 0.2064 | 0.2284 | 0.2112 | 0.3185 | 0.3773 | 0.0218 | 0.0000 |
| positive_edge_deformed | 0.2650 | 0.2572 | 0.1403 | 0.1481 | 0.2954 | 0.2911 | 0.1975 | 0.2026 | 0.0317 | 0.0309 |

## 6. Tree vs CW quadrant agreement table
| slice | tree_agreement | cw_agreement | tree_status | cw_status |
|---|---|---|---|---|
| preserved_c_plus_0_10 | 0.9806 | 0.9803 | preserved | preserved |
| baseline_mild_deformed | 0.9447 | 0.9500 | strongly deformed | mildly deformed |
| cooperative_strongly_deformed | 0.7361 | 0.8431 | strongly deformed | strongly deformed |
| positive_edge_deformed | 0.8303 | 0.8431 | strongly deformed | strongly deformed |

## 7. Changed phase fraction table
| slice | changed_phase_fraction | mixed_tree | mixed_cw |
|---|---|---|---|
| preserved_c_plus_0_10 | 0.0059 | 0.2529 | 0.2470 |
| baseline_mild_deformed | 0.0051 | 0.2967 | 0.2916 |
| cooperative_strongly_deformed | 0.1051 | 0.3185 | 0.3773 |
| positive_edge_deformed | 0.0129 | 0.1975 | 0.2026 |

## 8. Instability / negative-mass flags
| slice | instability_fraction_cw | cw_Rho_only | cw_Iota_only | cw_Unstable |
|---|---|---|---|---|
| preserved_c_plus_0_10 | 0.0003 | 0.0000 | 0.0000 | 0.0000 |
| baseline_mild_deformed | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cooperative_strongly_deformed | 0.0105 | 0.0000 | 0.0000 | 0.0000 |
| positive_edge_deformed | 0.0000 | 0.0701 | 0.0000 | 0.0000 |

## 9. Notes
- `preserved_c_plus_0_10`: tree `preserved` -> CW `preserved`, changed cells `22`, CW instability fraction `0.0003`.
- `baseline_mild_deformed`: tree `strongly deformed` -> CW `mildly deformed`, changed cells `19`, CW instability fraction `0.0000`.
- `cooperative_strongly_deformed`: tree `strongly deformed` -> CW `strongly deformed`, changed cells `391`, CW instability fraction `0.0105`.
- `positive_edge_deformed`: tree `strongly deformed` -> CW `strongly deformed`, changed cells `48`, CW instability fraction `0.0000`.
- Check `changed_mask` and `cw_instability_mask` PNGs for where local CW changes phases or flags negative scalar/Goldstone masses.

## 10. Warnings
- synthetic benchmark only
- one-loop local CW only
- gauge-dependent off-shell `Veff`
- Re[Veff] only when negative `m^2` appears
- no RG improvement
- no full nonlocal `K_T` determinant
- no physical prediction
- no proof of PQT-QG