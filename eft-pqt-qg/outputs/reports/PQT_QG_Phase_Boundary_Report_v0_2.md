# PQT-QG Phase Boundary Scanner v0.2

## Goal
Sweep the two main tree-level vacuum levers `mrho2` and `miota2_eff = miota2 + LambdaT2_kappa0` and classify the global refined minimum phase at each grid point.

## Canon / scope
- Tree-level only.
- Local memory approximation only: `K_T(k) ≈ kappa0`.
- `Core Psi` remains frozen into `muH_eff2`; it is not replaced by `H`.
- Synthetic exploratory phase-structure map; no physical prediction.

## Base parameters held fixed
```json
{
  "name": "phase_boundary_v0_2_mixed_friendly",
  "muH_eff2": 0.13,
  "lambdaH": 0.13,
  "mrho2": 0.0,
  "brho": 0.45,
  "arho": -0.08,
  "miota2": 0.0,
  "biota": 0.5,
  "aiota": -0.08,
  "c": -0.05,
  "LambdaT2_kappa0": 0.05,
  "exploratory": true,
  "note": "v0.2 phase-boundary default uses D-like mixed-friendly quartics/portals while sweeping mass levers."
}
```

## Scan configuration
```json
{
  "mrho2_range": [
    -0.8,
    0.8
  ],
  "miota2_eff_range": [
    -0.8,
    0.8
  ],
  "grid_shape": [
    101,
    101
  ],
  "field_bounds": [
    [
      0.0,
      2.0
    ],
    [
      -2.0,
      2.0
    ],
    [
      -2.0,
      2.0
    ]
  ]
}
```

## Phase map
- Plot: `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\phase_boundary_v0_2_mrho2_miota2eff.png`

## Phase counts
- Prema: 2304
- Gurutva: 2426
- Tamas: 2438
- Mixed: 3033

## Copositivity sanity check
Status: **pass**

This is a pairwise guardrail, not a full three-field copositivity proof.

## Interpretation warning
Phase boundaries are numerical and depend on held-fixed quartics/portals, scan bounds, and minimizer settings.