# PQT-QG Nonlocal Micro-Scan Report v0.8

## 1. Goal
Full nonlocal minimization micro-scan for the cooperative sector.

## 2. Why v0.8 exists
v0.7 evaluated nonlocal determinant diagnostics at local active-set minima. v0.8 includes nonlocal `deltaV` in the minimization objective on a small targeted grid.

## 3. Canon assumptions
Core Psi is frozen into `muH_eff2`; H is observed-sector; memory is Euclidean `Sigma_E`; no physical prediction or proof is claimed.

## 4. Numerical method
Grid `[11, 11]` over `mrho2=[-0.55, -0.05]`, `miota2_eff=[-0.55, -0.05]`. kmax `5.0`, num_k `96`. Seeds: `all`. Optimizer: L-BFGS-B. Objective uses determinant-ratio subtraction and corrected zero-mode memory.

## 5. Kernel comparison table
| kernel | changed_phase_fraction | average_delta_position_norm | max_delta_position_norm | determinant_health_fraction | optimizer_success_fraction | min_iota_inverse_global | min_det_global |
|---|---|---|---|---|---|---|---|
| local_constant | 0 | 0 | 0 | 0.93388 | 1 | -0.77758 | -0.73734 |
| single_pole | 0.066116 | 0.11193 | 2.0641 | 1 | 0.91736 | 0.48657 | 0.071118 |
| exp_gap | 0.066116 | 0.1121 | 2.0641 | 1 | 0.93388 | 0.48747 | 0.071289 |

## 6. Transition matrices
### local_constant
```json
{
  "Prema": {
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
  "Gurutva": {
    "Prema": 0,
    "Gurutva": 4,
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
    "Tamas": 1,
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
    "Mixed": 113,
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
    "Other": 3,
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
### single_pole
```json
{
  "Prema": {
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
  "Gurutva": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 4,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Tamas": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 1,
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
    "Mixed": 113,
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
    "Mixed": 3,
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
### exp_gap
```json
{
  "Prema": {
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
  "Gurutva": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 4,
    "Symmetric": 0,
    "Rho_only": 0,
    "Iota_only": 0,
    "Other": 0,
    "Unstable": 0
  },
  "Tamas": {
    "Prema": 0,
    "Gurutva": 0,
    "Tamas": 0,
    "Mixed": 1,
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
    "Mixed": 113,
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
    "Mixed": 3,
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

## 7. Main answers
- `local_constant`: changed phase fraction `0.0000`, avg movement `0`, determinant health `0.9339`.
- `single_pole`: changed phase fraction `0.0661`, avg movement `0.1119`, determinant health `1.0000`.
- `exp_gap`: changed phase fraction `0.0661`, avg movement `0.1121`, determinant health `1.0000`.
- If changed fraction is near zero but determinant health is low, stress is diagnostic rather than phase-moving on this micro-grid.
- Broader v0.9 scans should be considered only for kernels with acceptable optimizer and determinant health.

## 8. Warnings
- synthetic benchmark only
- micro-scan only
- cutoff/scheme dependent
- no RG improvement
- no full renormalization
- no physical prediction
- determinant health is diagnostic, not theorem