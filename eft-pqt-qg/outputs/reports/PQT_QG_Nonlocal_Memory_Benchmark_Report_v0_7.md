# PQT-QG Nonlocal Memory Benchmark Report v0.7

## 1. Goal
Test momentum-dependent Euclidean memory self-energy `Sigma_E(k^2)` rather than only local memory sign conventions.

## 2. Canon recovery context
v0.6 showed plus/minus local memory signs are equivalent on the effective `miota2_eff` axis. v0.7 tests whether nonlocal momentum dependence changes phase mechanics.

## 3. Kernel definitions
- `local_constant`: `Sigma_E(q)=sigma0`.
- `single_pole`: `Sigma_E(q)=sigma0*M2/(q+M2)`.
- `exp_gap`: normalized gapped exponential spectral shape using `exp1`.

## 4. Exact formula
`Delta_iota^{-1}(k)=Z_iota*k^2+m_ss_local2-Sigma_E(k^2)`; no `LambdaT2_kappa0` is double counted in nonlocal mode.

## 5. Numerical method
Grid: `[31, 31]`; kmax: `5.0`; num_k: `96`; determinant reference: same kernel at `(phi,r,s)=(0,0,0)`.
Bounded L-BFGS-B is seeded from the corrected local zero-mode active-set minimum and standard phase seeds. Results are cutoff/scheme dependent.

## 6. Phase comparison table
| slice | kernel | quadrant_agreement | topology_status | fraction_Prema | fraction_Gurutva | fraction_Tamas | fraction_Mixed | changed_phase_fraction_vs_local | determinant_health_fraction |
|---|---|---|---|---|---|---|---|---|---|
| preserved_c_plus_0_10 | local_constant | 1.0000 | preserved | 0.2341 | 0.2581 | 0.2570 | 0.2508 | 0.0000 | 1.0000 |
| preserved_c_plus_0_10 | single_pole | 1.0000 | preserved | 0.2341 | 0.2581 | 0.2570 | 0.2508 | 0.0000 | 1.0000 |
| preserved_c_plus_0_10 | exp_gap | 1.0000 | preserved | 0.2341 | 0.2581 | 0.2570 | 0.2508 | 0.0000 | 1.0000 |
| baseline_mild_deformed | local_constant | 0.9689 | mildly deformed | 0.2341 | 0.2341 | 0.2362 | 0.2955 | 0.0000 | 1.0000 |
| baseline_mild_deformed | single_pole | 0.9689 | mildly deformed | 0.2341 | 0.2341 | 0.2362 | 0.2955 | 0.0000 | 1.0000 |
| baseline_mild_deformed | exp_gap | 0.9689 | mildly deformed | 0.2341 | 0.2341 | 0.2362 | 0.2955 | 0.0000 | 1.0000 |
| cooperative_strongly_deformed | local_constant | 0.7533 | strongly deformed | 0.2040 | 0.2331 | 0.2248 | 0.3163 | 0.0000 | 0.9209 |
| cooperative_strongly_deformed | single_pole | 0.8378 | strongly deformed | 0.2040 | 0.1977 | 0.2029 | 0.3954 | 0.0791 | 1.0000 |
| cooperative_strongly_deformed | exp_gap | 0.8378 | strongly deformed | 0.2040 | 0.1977 | 0.2029 | 0.3954 | 0.0791 | 1.0000 |

## 7. Kernel sanity results
| kernel | Sigma_E_0 | Sigma_E_kmax2 | monotone_nonincreasing | min_iota_inverse_representative |
|---|---|---|---|---|
| local_constant | 0.0500 | 0.0500 | True | 0.0000 |
| single_pole | 0.0500 | 0.0019 | True | 0.0000 |
| exp_gap | 0.0500 | 0.0004 | True | 0.0000 |

## 8. Interpretation
- `preserved_c_plus_0_10` / `single_pole`: changed vs local `0.0000`, Mixed delta `0.0000`, determinant health `1.0000`.
- `preserved_c_plus_0_10` / `exp_gap`: changed vs local `0.0000`, Mixed delta `0.0000`, determinant health `1.0000`.
- `baseline_mild_deformed` / `single_pole`: changed vs local `0.0000`, Mixed delta `0.0000`, determinant health `1.0000`.
- `baseline_mild_deformed` / `exp_gap`: changed vs local `0.0000`, Mixed delta `0.0000`, determinant health `1.0000`.
- `cooperative_strongly_deformed` / `single_pole`: changed vs local `0.0791`, Mixed delta `0.0791`, determinant health `1.0000`.
- `cooperative_strongly_deformed` / `exp_gap`: changed vs local `0.0791`, Mixed delta `0.0791`, determinant health `1.0000`.
- Single-pole closeness and exp-gap deformation should be judged by changed fraction, agreement, and determinant health columns.
- v0.8 should include full nonlocal memory in loop-level scans only if determinant diagnostics remain controlled.

## 9. Warnings
- synthetic benchmark only
- nonlocal Euclidean memory only
- cutoff/scheme dependent
- no full renormalization
- no RG improvement
- no physical prediction
- no proof of PQT-QG
- determinant flags are diagnostic, not a final stability theorem