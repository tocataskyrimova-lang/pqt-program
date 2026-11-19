# PQT-QG Robustness Atlas v0.3

## 1. Goal
Test whether the synthetic tree-level quadrant phase law remains robust under portal/quartic deformations over `mrho2` and `miota2_eff = miota2 + LambdaT2_kappa0`.

## 2. Canon assumptions
- Core Psi remains frozen into `muH_eff2`.
- `H` does not replace Psi; this is the observed scalar landscape only.
- Memory enters only through local `LambdaT2_kappa0`.
- Hessian normalization keeps diagonal portal factors as `a/2`.

## 3. Baseline v0.2 summary
The v0.2 mixed-friendly baseline produced a four-region map over the same mass axes, with Prema/Gurutva/Tamas/Mixed regions present. v0.3 tests parameter sensitivity of that topology.

## Agreement audit note
Agreement values in this report are regenerated from `outputs/data/robustness_atlas_v0_3.json`. Plot titles should match the same per-slice `quadrant_agreement_fraction`; if an older PNG/report was open in a viewer, refresh it after regeneration.

## 4. Sweep definitions
- `arho`: -0.20, -0.10, -0.08, 0.00, 0.10, 0.20
- `aiota`: -0.20, -0.10, -0.08, 0.00, 0.10, 0.20
- `c`: -0.20, -0.10, -0.05, 0.00, 0.10, 0.20
- compact `(arho, aiota)` grid: {-0.20, -0.08, 0.10} x {-0.20, -0.08, 0.10}, with `c=-0.05`

## 5. Phase fraction table
| slice | fraction_Prema | fraction_Gurutva | fraction_Tamas | fraction_Mixed | fraction_Other | fraction_Rho_only | fraction_Iota_only | fraction_Unstable |
|---|---|---|---|---|---|---|---|---|
| arho_-0.20 | 0.2070 | 0.2447 | 0.2142 | 0.3341 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arho_-0.10 | 0.2212 | 0.2409 | 0.2348 | 0.3032 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arho_-0.08 | 0.2259 | 0.2378 | 0.2390 | 0.2973 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arho_+0.00 | 0.2353 | 0.2282 | 0.2552 | 0.2763 | 0.0000 | 0.0000 | 0.0000 | 0.0050 |
| arho_+0.10 | 0.2541 | 0.2187 | 0.2760 | 0.2512 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arho_+0.20 | 0.2682 | 0.1412 | 0.2961 | 0.1979 | 0.0307 | 0.0659 | 0.0000 | 0.0000 |
| aiota_-0.20 | 0.2070 | 0.2124 | 0.2475 | 0.3330 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiota_-0.10 | 0.2212 | 0.2335 | 0.2423 | 0.3030 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiota_-0.08 | 0.2259 | 0.2378 | 0.2390 | 0.2973 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiota_+0.00 | 0.2353 | 0.2546 | 0.2291 | 0.2761 | 0.0000 | 0.0000 | 0.0000 | 0.0050 |
| aiota_+0.10 | 0.2541 | 0.2758 | 0.2190 | 0.2512 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiota_+0.20 | 0.2682 | 0.2961 | 0.1600 | 0.2163 | 0.0124 | 0.0000 | 0.0471 | 0.0000 |
| c_-0.20 | 0.2259 | 0.2142 | 0.2178 | 0.3421 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| c_-0.10 | 0.2259 | 0.2302 | 0.2318 | 0.3121 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| c_-0.05 | 0.2259 | 0.2378 | 0.2390 | 0.2973 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| c_+0.00 | 0.2259 | 0.2460 | 0.2462 | 0.2820 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| c_+0.10 | 0.2259 | 0.2612 | 0.2602 | 0.2528 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| c_+0.20 | 0.2259 | 0.2774 | 0.2741 | 0.2226 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| portal_grid_arho_-0.20_aiota_-0.20_c_-0.05 | 0.1898 | 0.2042 | 0.2093 | 0.3967 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| portal_grid_arho_-0.20_aiota_-0.08_c_-0.05 | 0.2070 | 0.2447 | 0.2142 | 0.3341 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| portal_grid_arho_-0.20_aiota_+0.10_c_-0.05 | 0.2329 | 0.3054 | 0.2068 | 0.2548 | 0.0000 | 0.0000 | 0.0000 | 0.0001 |
| portal_grid_arho_-0.08_aiota_-0.20_c_-0.05 | 0.2070 | 0.2124 | 0.2475 | 0.3330 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| portal_grid_arho_-0.08_aiota_-0.08_c_-0.05 | 0.2259 | 0.2378 | 0.2390 | 0.2973 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| portal_grid_arho_-0.08_aiota_+0.10_c_-0.05 | 0.2541 | 0.2758 | 0.2190 | 0.2512 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| portal_grid_arho_+0.10_aiota_-0.20_c_-0.05 | 0.2329 | 0.2072 | 0.3046 | 0.2553 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| portal_grid_arho_+0.10_aiota_-0.08_c_-0.05 | 0.2541 | 0.2187 | 0.2760 | 0.2512 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| portal_grid_arho_+0.10_aiota_+0.10_c_-0.05 | 0.2859 | 0.2358 | 0.2369 | 0.2027 | 0.0387 | 0.0000 | 0.0000 | 0.0000 |

## 6. Quadrant-law agreement table
| slice | quadrant_agreement_fraction | mismatch_count | comparable_count |
|---|---|---|---|
| arho_-0.20 | 0.8994 | 966 | 9604 |
| arho_-0.10 | 0.9455 | 523 | 9604 |
| arho_-0.08 | 0.9564 | 419 | 9604 |
| arho_+0.00 | 0.9808 | 184 | 9604 |
| arho_+0.10 | 0.9719 | 270 | 9604 |
| arho_+0.20 | 0.8424 | 1514 | 9604 |
| aiota_-0.20 | 0.9006 | 955 | 9604 |
| aiota_-0.10 | 0.9458 | 521 | 9604 |
| aiota_-0.08 | 0.9564 | 419 | 9604 |
| aiota_+0.00 | 0.9814 | 179 | 9604 |
| aiota_+0.10 | 0.9724 | 265 | 9604 |
| aiota_+0.20 | 0.8800 | 1152 | 9604 |
| c_-0.20 | 0.9092 | 872 | 9604 |
| c_-0.10 | 0.9406 | 570 | 9604 |
| c_-0.05 | 0.9564 | 419 | 9604 |
| c_+0.00 | 0.9726 | 263 | 9604 |
| c_+0.10 | 0.9894 | 102 | 9604 |
| c_+0.20 | 0.9695 | 293 | 9604 |
| portal_grid_arho_-0.20_aiota_-0.20_c_-0.05 | 0.8186 | 1742 | 9604 |
| portal_grid_arho_-0.20_aiota_-0.08_c_-0.05 | 0.8994 | 966 | 9604 |
| portal_grid_arho_-0.20_aiota_+0.10_c_-0.05 | 0.9300 | 672 | 9604 |
| portal_grid_arho_-0.08_aiota_-0.20_c_-0.05 | 0.9006 | 955 | 9604 |
| portal_grid_arho_-0.08_aiota_-0.08_c_-0.05 | 0.9564 | 419 | 9604 |
| portal_grid_arho_-0.08_aiota_+0.10_c_-0.05 | 0.9724 | 265 | 9604 |
| portal_grid_arho_+0.10_aiota_-0.20_c_-0.05 | 0.9314 | 659 | 9604 |
| portal_grid_arho_+0.10_aiota_-0.08_c_-0.05 | 0.9719 | 270 | 9604 |
| portal_grid_arho_+0.10_aiota_+0.10_c_-0.05 | 0.9354 | 620 | 9604 |

## 6a. Agreement min/mean/max by sweep group
| sweep_group | min_agreement | mean_agreement | max_agreement | slice_count |
|---|---|---|---|---|
| arho sweep | 0.8424 | 0.9327 | 0.9808 | 6 |
| aiota sweep | 0.8800 | 0.9394 | 0.9814 | 6 |
| c sweep | 0.9092 | 0.9563 | 0.9894 | 6 |
| portal grid | 0.8186 | 0.9240 | 0.9724 | 9 |

## 7. Copositivity pass/warn table
| slice | copositivity_status |
|---|---|
| arho_-0.20 | pass |
| arho_-0.10 | pass |
| arho_-0.08 | pass |
| arho_+0.00 | pass |
| arho_+0.10 | pass |
| arho_+0.20 | pass |
| aiota_-0.20 | pass |
| aiota_-0.10 | pass |
| aiota_-0.08 | pass |
| aiota_+0.00 | pass |
| aiota_+0.10 | pass |
| aiota_+0.20 | pass |
| c_-0.20 | pass |
| c_-0.10 | pass |
| c_-0.05 | pass |
| c_+0.00 | pass |
| c_+0.10 | pass |
| c_+0.20 | pass |
| portal_grid_arho_-0.20_aiota_-0.20_c_-0.05 | pass |
| portal_grid_arho_-0.20_aiota_-0.08_c_-0.05 | pass |
| portal_grid_arho_-0.20_aiota_+0.10_c_-0.05 | pass |
| portal_grid_arho_-0.08_aiota_-0.20_c_-0.05 | pass |
| portal_grid_arho_-0.08_aiota_-0.08_c_-0.05 | pass |
| portal_grid_arho_-0.08_aiota_+0.10_c_-0.05 | pass |
| portal_grid_arho_+0.10_aiota_-0.20_c_-0.05 | pass |
| portal_grid_arho_+0.10_aiota_-0.08_c_-0.05 | pass |
| portal_grid_arho_+0.10_aiota_+0.10_c_-0.05 | pass |

## 7a. Topology status table
Thresholds: `preserved >= 0.98`, `mildly deformed >= 0.95`, `strongly deformed < 0.95`.
| slice | quadrant_agreement_fraction | topology_status | copositivity_status |
|---|---|---|---|
| arho_-0.20 | 0.8994 | strongly deformed | pass |
| arho_-0.10 | 0.9455 | strongly deformed | pass |
| arho_-0.08 | 0.9564 | mildly deformed | pass |
| arho_+0.00 | 0.9808 | preserved | pass |
| arho_+0.10 | 0.9719 | mildly deformed | pass |
| arho_+0.20 | 0.8424 | strongly deformed | pass |
| aiota_-0.20 | 0.9006 | strongly deformed | pass |
| aiota_-0.10 | 0.9458 | strongly deformed | pass |
| aiota_-0.08 | 0.9564 | mildly deformed | pass |
| aiota_+0.00 | 0.9814 | preserved | pass |
| aiota_+0.10 | 0.9724 | mildly deformed | pass |
| aiota_+0.20 | 0.8800 | strongly deformed | pass |
| c_-0.20 | 0.9092 | strongly deformed | pass |
| c_-0.10 | 0.9406 | strongly deformed | pass |
| c_-0.05 | 0.9564 | mildly deformed | pass |
| c_+0.00 | 0.9726 | mildly deformed | pass |
| c_+0.10 | 0.9894 | preserved | pass |
| c_+0.20 | 0.9695 | mildly deformed | pass |
| portal_grid_arho_-0.20_aiota_-0.20_c_-0.05 | 0.8186 | strongly deformed | pass |
| portal_grid_arho_-0.20_aiota_-0.08_c_-0.05 | 0.8994 | strongly deformed | pass |
| portal_grid_arho_-0.20_aiota_+0.10_c_-0.05 | 0.9300 | strongly deformed | pass |
| portal_grid_arho_-0.08_aiota_-0.20_c_-0.05 | 0.9006 | strongly deformed | pass |
| portal_grid_arho_-0.08_aiota_-0.08_c_-0.05 | 0.9564 | mildly deformed | pass |
| portal_grid_arho_-0.08_aiota_+0.10_c_-0.05 | 0.9724 | mildly deformed | pass |
| portal_grid_arho_+0.10_aiota_-0.20_c_-0.05 | 0.9314 | strongly deformed | pass |
| portal_grid_arho_+0.10_aiota_-0.08_c_-0.05 | 0.9719 | mildly deformed | pass |
| portal_grid_arho_+0.10_aiota_+0.10_c_-0.05 | 0.9354 | strongly deformed | pass |

## 8. Portal values that preserve topology
| slice | quadrant_agreement_fraction | fraction_Mixed | copositivity_status |
|---|---|---|---|
| arho_+0.00 | 0.9808 | 0.2763 | pass |
| aiota_+0.00 | 0.9814 | 0.2761 | pass |
| c_+0.10 | 0.9894 | 0.2528 | pass |

## 9. Portal values that deform or break topology
| slice | quadrant_agreement_fraction | mismatch_count | copositivity_status |
|---|---|---|---|
| arho_-0.20 | 0.8994 | 966 | pass |
| arho_-0.10 | 0.9455 | 523 | pass |
| arho_+0.20 | 0.8424 | 1514 | pass |
| aiota_-0.20 | 0.9006 | 955 | pass |
| aiota_-0.10 | 0.9458 | 521 | pass |
| aiota_+0.20 | 0.8800 | 1152 | pass |
| c_-0.20 | 0.9092 | 872 | pass |
| c_-0.10 | 0.9406 | 570 | pass |
| portal_grid_arho_-0.20_aiota_-0.20_c_-0.05 | 0.8186 | 1742 | pass |
| portal_grid_arho_-0.20_aiota_-0.08_c_-0.05 | 0.8994 | 966 | pass |
| portal_grid_arho_-0.20_aiota_+0.10_c_-0.05 | 0.9300 | 672 | pass |
| portal_grid_arho_-0.08_aiota_-0.20_c_-0.05 | 0.9006 | 955 | pass |
| portal_grid_arho_+0.10_aiota_-0.20_c_-0.05 | 0.9314 | 659 | pass |
| portal_grid_arho_+0.10_aiota_+0.10_c_-0.05 | 0.9354 | 620 | pass |

## 9a. Mildly deformed slices
| slice | quadrant_agreement_fraction | mismatch_count | copositivity_status |
|---|---|---|---|
| arho_-0.08 | 0.9564 | 419 | pass |
| arho_+0.10 | 0.9719 | 270 | pass |
| aiota_-0.08 | 0.9564 | 419 | pass |
| aiota_+0.10 | 0.9724 | 265 | pass |
| c_-0.05 | 0.9564 | 419 | pass |
| c_+0.00 | 0.9726 | 263 | pass |
| c_+0.20 | 0.9695 | 293 | pass |
| portal_grid_arho_-0.08_aiota_-0.08_c_-0.05 | 0.9564 | 419 | pass |
| portal_grid_arho_-0.08_aiota_+0.10_c_-0.05 | 0.9724 | 265 | pass |
| portal_grid_arho_+0.10_aiota_-0.08_c_-0.05 | 0.9719 | 270 | pass |

## 9b. Slices with Mixed fraction > 0.33
| slice | fraction_Mixed | quadrant_agreement_fraction | topology_status |
|---|---|---|---|
| portal_grid_arho_-0.20_aiota_-0.20_c_-0.05 | 0.3967 | 0.8186 | strongly deformed |
| c_-0.20 | 0.3421 | 0.9092 | strongly deformed |
| arho_-0.20 | 0.3341 | 0.8994 | strongly deformed |
| portal_grid_arho_-0.20_aiota_-0.08_c_-0.05 | 0.3341 | 0.8994 | strongly deformed |
| aiota_-0.20 | 0.3330 | 0.9006 | strongly deformed |
| portal_grid_arho_-0.08_aiota_-0.20_c_-0.05 | 0.3330 | 0.9006 | strongly deformed |

## 9c. Slices where Other / Rho_only / Iota_only / Unstable appears
| slice | count_Other | count_Rho_only | count_Iota_only | count_Unstable | quadrant_agreement_fraction |
|---|---|---|---|---|---|
| arho_+0.00 | 0 | 0 | 0 | 51 | 0.9808 |
| arho_+0.20 | 313 | 672 | 0 | 0 | 0.8424 |
| aiota_+0.00 | 0 | 0 | 0 | 51 | 0.9814 |
| aiota_+0.20 | 126 | 0 | 480 | 0 | 0.8800 |
| portal_grid_arho_-0.20_aiota_+0.10_c_-0.05 | 0 | 0 | 0 | 1 | 0.9300 |
| portal_grid_arho_+0.10_aiota_+0.10_c_-0.05 | 395 | 0 | 0 | 0 | 0.9354 |

## 10. Mixed-region robustness
Smallest Mixed fraction: `arho_+0.20` = 0.1979
Largest Mixed fraction: `portal_grid_arho_-0.20_aiota_-0.20_c_-0.05` = 0.3967
Mixed remains large when negative portal cooperation is present; positive portals tend to make the topology more parameter-sensitive and can introduce extra phase labels near boundaries.

## 11. Warnings
- synthetic benchmark only
- tree-level only
- local memory approximation only
- no one-loop correction
- no nonlocal `K_T` determinant
- no physical prediction
- no proof of PQT-QG

## 12. Next benchmark family
Study a competition-dominated family with positive portals (`arho, aiota, c > 0`) and a near-copositivity-boundary family with mildly negative portals to separate robust quadrant topology from D-like cooperative artifacts.

## Output plots
All phase-map PNGs are under `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\robustness_v0_3`.