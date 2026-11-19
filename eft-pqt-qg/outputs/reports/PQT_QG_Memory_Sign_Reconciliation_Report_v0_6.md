# PQT-QG Memory Sign Reconciliation Report v0.6

## 1. Goal
Reconcile old plus-sign local memory benchmarks with the patched UV/bath minus-sign self-energy convention.

## 2. Canon issue
v0.1-v0.5 used `m_iota_eff2 = miota2 + LambdaT2_kappa0`. Patched UV/bath logic suggests `Delta_iota^{-1}=k^2+m_iota_eff2-Sigma_E`, so the corrected local benchmark tests `m_iota_eff2 = miota2 - kappa0`.

## 3. Exact sign conventions
- plus mode: `V0 += +0.5*LambdaT2_kappa0*s^2`, axis `miota2_eff = miota2 + LambdaT2_kappa0`.
- minus mode: `V0 += -0.5*LambdaT2_kappa0*s^2`, axis `miota2_eff = miota2 - LambdaT2_kappa0`.

## 4. Phase boundary comparison
| memory_sign | quadrant_agreement | topology_status | fraction_Prema | fraction_Gurutva | fraction_Tamas | fraction_Mixed | fraction_Other |
|---|---|---|---|---|---|---|---|
| plus | 0.9447 | strongly deformed | 0.2260 | 0.2378 | 0.2395 | 0.2967 | 0.0000 |
| minus | 0.9447 | strongly deformed | 0.2260 | 0.2378 | 0.2395 | 0.2967 | 0.0000 |

### Plus vs minus comparison
| changed_phase_fraction_plus_vs_minus | changed_cells_count_plus_vs_minus | delta_mixed_fraction | delta_tamas_fraction | delta_quadrant_agreement | minus_matches_plus_effective_axis | minus_quadrant_law_preserved_threshold_passed |
|---|---|---|---|---|---|---|
| 0.0000 | 0 | 0.0000 | 0.0000 | 0.0000 | True | False |

### Transition matrix
Rows are plus phases; columns are minus phases.

```json
{
  "Prema": {
    "Prema": 841,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 0,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Gurutva": {
    "Prema": 0,
    "Gurutva": 885,
    "Tamas": 0,
    "Mixed": 0,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Tamas": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 891,
    "Mixed": 0,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Mixed": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 1104,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Symmetric": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 0,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Rho_only": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 0,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Iota_only": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 0,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Other": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 0,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Unstable": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 0,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  }
}
```

## 5. Robustness comparison
| sweep | memory_sign | quadrant_agreement | topology_status | mixed_fraction | tamas_fraction | copositivity_status |
|---|---|---|---|---|---|---|
| arho_-0.20 | plus | 0.8914 | strongly deformed | 0.3340 | 0.2142 | pass |
| arho_-0.20 | minus | 0.8914 | strongly deformed | 0.3340 | 0.2142 | pass |
| arho_-0.08 | plus | 0.9447 | strongly deformed | 0.2967 | 0.2395 | pass |
| arho_-0.08 | minus | 0.9447 | strongly deformed | 0.2967 | 0.2395 | pass |
| arho_+0.00 | plus | 0.9733 | mildly deformed | 0.2763 | 0.2548 | pass |
| arho_+0.00 | minus | 0.9733 | mildly deformed | 0.2763 | 0.2548 | pass |
| arho_+0.10 | plus | 0.9653 | mildly deformed | 0.2510 | 0.2752 | pass |
| arho_+0.10 | minus | 0.9653 | mildly deformed | 0.2510 | 0.2752 | pass |
| arho_+0.20 | plus | 0.8303 | strongly deformed | 0.1975 | 0.2954 | pass |
| arho_+0.20 | minus | 0.8303 | strongly deformed | 0.1975 | 0.2954 | pass |
| aiota_-0.20 | plus | 0.8931 | strongly deformed | 0.3322 | 0.2446 | pass |
| aiota_-0.20 | minus | 0.8931 | strongly deformed | 0.3322 | 0.2446 | pass |
| aiota_-0.08 | plus | 0.9447 | strongly deformed | 0.2967 | 0.2395 | pass |
| aiota_-0.08 | minus | 0.9447 | strongly deformed | 0.2967 | 0.2395 | pass |
| aiota_+0.00 | plus | 0.9739 | mildly deformed | 0.2757 | 0.2284 | pass |
| aiota_+0.00 | minus | 0.9739 | mildly deformed | 0.2757 | 0.2284 | pass |
| aiota_+0.10 | plus | 0.9658 | mildly deformed | 0.2505 | 0.2249 | pass |
| aiota_+0.10 | minus | 0.9658 | mildly deformed | 0.2505 | 0.2249 | pass |
| aiota_+0.20 | plus | 0.8722 | strongly deformed | 0.2158 | 0.1637 | pass |
| aiota_+0.20 | minus | 0.8722 | strongly deformed | 0.2158 | 0.1637 | pass |
| c_-0.20 | plus | 0.8981 | strongly deformed | 0.3418 | 0.2180 | pass |
| c_-0.20 | minus | 0.8981 | strongly deformed | 0.3418 | 0.2180 | pass |
| c_-0.05 | plus | 0.9447 | strongly deformed | 0.2967 | 0.2395 | pass |
| c_-0.05 | minus | 0.9447 | strongly deformed | 0.2967 | 0.2395 | pass |
| c_+0.00 | plus | 0.9597 | mildly deformed | 0.2822 | 0.2462 | pass |
| c_+0.00 | minus | 0.9597 | mildly deformed | 0.2822 | 0.2462 | pass |
| c_+0.10 | plus | 0.9806 | preserved | 0.2529 | 0.2599 | pass |
| c_+0.10 | minus | 0.9806 | preserved | 0.2529 | 0.2599 | pass |
| c_+0.20 | plus | 0.9586 | mildly deformed | 0.2223 | 0.2741 | pass |
| c_+0.20 | minus | 0.9586 | mildly deformed | 0.2223 | 0.2741 | pass |
| portal_grid_arho_-0.20_aiota_-0.20_c_-0.05 | plus | 0.7361 | strongly deformed | 0.3185 | 0.2284 | pass |
| portal_grid_arho_-0.20_aiota_-0.20_c_-0.05 | minus | 0.7361 | strongly deformed | 0.3185 | 0.2284 | pass |
| portal_grid_arho_-0.20_aiota_-0.08_c_-0.05 | plus | 0.8914 | strongly deformed | 0.3340 | 0.2142 | pass |
| portal_grid_arho_-0.20_aiota_-0.08_c_-0.05 | minus | 0.8914 | strongly deformed | 0.3340 | 0.2142 | pass |
| portal_grid_arho_-0.20_aiota_+0.10_c_-0.05 | plus | 0.9256 | strongly deformed | 0.2553 | 0.2110 | pass |
| portal_grid_arho_-0.20_aiota_+0.10_c_-0.05 | minus | 0.9256 | strongly deformed | 0.2553 | 0.2110 | pass |
| portal_grid_arho_-0.08_aiota_-0.20_c_-0.05 | plus | 0.8931 | strongly deformed | 0.3322 | 0.2446 | pass |
| portal_grid_arho_-0.08_aiota_-0.20_c_-0.05 | minus | 0.8931 | strongly deformed | 0.3322 | 0.2446 | pass |
| portal_grid_arho_-0.08_aiota_-0.08_c_-0.05 | plus | 0.9447 | strongly deformed | 0.2967 | 0.2395 | pass |
| portal_grid_arho_-0.08_aiota_-0.08_c_-0.05 | minus | 0.9447 | strongly deformed | 0.2967 | 0.2395 | pass |
| portal_grid_arho_-0.08_aiota_+0.10_c_-0.05 | plus | 0.9658 | mildly deformed | 0.2505 | 0.2249 | pass |
| portal_grid_arho_-0.08_aiota_+0.10_c_-0.05 | minus | 0.9658 | mildly deformed | 0.2505 | 0.2249 | pass |
| portal_grid_arho_+0.10_aiota_-0.20_c_-0.05 | plus | 0.9272 | strongly deformed | 0.2556 | 0.3005 | pass |
| portal_grid_arho_+0.10_aiota_-0.20_c_-0.05 | minus | 0.9272 | strongly deformed | 0.2556 | 0.3005 | pass |
| portal_grid_arho_+0.10_aiota_-0.08_c_-0.05 | plus | 0.9653 | mildly deformed | 0.2510 | 0.2752 | pass |
| portal_grid_arho_+0.10_aiota_-0.08_c_-0.05 | minus | 0.9653 | mildly deformed | 0.2510 | 0.2752 | pass |
| portal_grid_arho_+0.10_aiota_+0.10_c_-0.05 | plus | 0.9364 | strongly deformed | 0.2018 | 0.2421 | pass |
| portal_grid_arho_+0.10_aiota_+0.10_c_-0.05 | minus | 0.9364 | strongly deformed | 0.2018 | 0.2421 | pass |

## 6. Does mass-sign quadrant law survive in effective axes?
Minus-mode phase-boundary agreement is `0.9447` with status `strongly deformed`.

## 7. Does Tamas/Mixed region invert, shrink, expand, or remain structurally similar?
Delta Mixed fraction (minus-plus): `0.0000`. Delta Tamas fraction (minus-plus): `0.0000`.

## 8. Is the v0.1-v0.5 scaffold still valid as a method?
The scaffold remains valid as a computational method because the effective-axis scan can be rerun under either sign convention. Old plus-sign outputs should be treated as baseline artifacts, not final canon, until full `Sigma_E(k)` is implemented.

## 9. Interpretation
Plus and minus modes are identical when compared on the effective `miota2_eff` axis. The sign correction changes how bare `miota2` maps to the effective axis, not the tree-level phase mechanics in this local benchmark.
The corrected minus convention inherits the same below-threshold quadrant agreement as the plus baseline; this deformation is from the chosen D-like portal slice/grid, not from the memory-sign flip itself.

## 10. Warnings
- synthetic benchmark only
- tree-level mostly
- local memory approximation only
- no full nonlocal `Sigma_E(k)`
- no RG improvement
- no physical prediction
- no proof of PQT-QG
- sign reconciliation is canon-recovery, not final phenomenology