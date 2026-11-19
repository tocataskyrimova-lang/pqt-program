# PQT-QG Benchmark Report v0.1

## Goal
Scan and visualize the tree-level PQT-QG observed scalar vacuum landscape `V0(phi,r,s)` for synthetic benchmark parameter sets.

## Canon assumptions used
- `Core Psi` is frozen into `muH_eff2`; it is not replaced by `H`.
- Background: `H=(0,phi)/sqrt(2)`, `rho=r`, `iota=s`.
- Local memory approximation only: `K_T(k) ≈ kappa0`, included as `+0.5*LambdaT2_kappa0*s^2`.
- Canonical portal normalization: diagonal Hessian shifts use `a/2`, not `2a`.

## Warnings
- Synthetic benchmark only.
- Tree-level only.
- No physical prediction.
- No one-loop correction yet.
- No nonlocal `K_T` determinant yet.

## Benchmark A_prema_only

### Parameters

```json
{
  "name": "A_prema_only",
  "muH_eff2": 0.13,
  "lambdaH": 0.13,
  "mrho2": 0.5,
  "brho": 0.3,
  "arho": 0.4,
  "miota2": 0.6,
  "biota": 0.3,
  "aiota": 0.4,
  "c": 0.2,
  "LambdaT2_kappa0": 0.2
}
```

### Copositivity sanity check

Status: **pass**
- `lambdaH_positive`: True
- `brho_positive`: True
- `biota_positive`: True
- `arho_pairwise`: True
- `aiota_pairwise`: True
- `c_pairwise`: True
- Note: Pairwise quartic boundedness sanity check only; not a full three-field copositivity proof.

### Plots

- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\A_prema_only_phi_r_s0.png`
- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\A_prema_only_phi_s_r0.png`
- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\A_prema_only_low_energy_points.png`

### Global minimum

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| A_prema_only_raw_0 | Prema | stable_minimum | 1 | 0 | 0 | -0.0325 | 0.26, 0.7, 1 |  |

### All stable raw minima

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| A_prema_only_raw_0 | Prema | stable_minimum | 1 | 0 | 0 | -0.0325 | 0.26, 0.7, 1 |  |

### Symmetry-grouped minima

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| A_prema_only_group_0 | Prema | stable_minimum | 1 | 0 | 0 | -0.0325 | 0.26, 0.7, 1 | 1 |
| A_prema_only_group_1 | Symmetric | unstable_saddle_or_max | 0 | 0 | 0 | 0 | -0.13, 0.5, 0.8 | 1 |

### Phase representatives

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| A_prema_only_group_0 | Prema | stable_minimum | 1 | 0 | 0 | -0.0325 | 0.26, 0.7, 1 | 1 |
| A_prema_only_group_1 | Symmetric | unstable_saddle_or_max | 0 | 0 | 0 | 0 | -0.13, 0.5, 0.8 | 1 |

### Branch notes
Observed grouped phases: Prema, Symmetric.
Stable branches are identified by positive Hessian eigenvalues within `eps_eigen=1e-6`.

## Benchmark B_gurutva_branch

### Parameters

```json
{
  "name": "B_gurutva_branch",
  "muH_eff2": 0.13,
  "lambdaH": 0.13,
  "mrho2": -0.35,
  "brho": 0.4,
  "arho": 0.2,
  "miota2": 0.6,
  "biota": 0.3,
  "aiota": 0.4,
  "c": 0.2,
  "LambdaT2_kappa0": 0.2
}
```

### Copositivity sanity check

Status: **pass**
- `lambdaH_positive`: True
- `brho_positive`: True
- `biota_positive`: True
- `arho_pairwise`: True
- `aiota_pairwise`: True
- `c_pairwise`: True
- Note: Pairwise quartic boundedness sanity check only; not a full three-field copositivity proof.

### Plots

- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\B_gurutva_branch_phi_r_s0.png`
- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\B_gurutva_branch_phi_s_r0.png`
- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\B_gurutva_branch_low_energy_points.png`

### Global minimum

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| B_gurutva_branch_raw_0 | Gurutva | stable_minimum | 0.63620901 | 0.87966444 | 0 | -0.08086309524 | 0.0819137, 0.642372, 0.958333 |  |

### All stable raw minima

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| B_gurutva_branch_raw_0 | Gurutva | stable_minimum | 0.63620901 | 0.87966444 | 0 | -0.08086309524 | 0.0819137, 0.642372, 0.958333 |  |
| B_gurutva_branch_raw_1 | Gurutva | stable_minimum | 0.63620902 | -0.87966444 | 0 | -0.08086309524 | 0.0819137, 0.642372, 0.958333 |  |

### Symmetry-grouped minima

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| B_gurutva_branch_group_0 | Gurutva | stable_minimum | 0.636209 | 0.8796644 | 0 | -0.08086309524 | 0.0819137, 0.642372, 0.958333 | 2 |
| B_gurutva_branch_group_1 | Prema | unstable_saddle_or_max | 1 | 0 | 0 | -0.0325 | -0.25, 0.26, 1 | 1 |
| B_gurutva_branch_group_2 | Symmetric | unstable_saddle_or_max | 0 | 0 | 0 | 0 | -0.35, -0.13, 0.8 | 1 |

### Phase representatives

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| B_gurutva_branch_group_0 | Gurutva | stable_minimum | 0.636209 | 0.8796644 | 0 | -0.08086309524 | 0.0819137, 0.642372, 0.958333 | 2 |
| B_gurutva_branch_group_1 | Prema | unstable_saddle_or_max | 1 | 0 | 0 | -0.0325 | -0.25, 0.26, 1 | 1 |
| B_gurutva_branch_group_2 | Symmetric | unstable_saddle_or_max | 0 | 0 | 0 | 0 | -0.35, -0.13, 0.8 | 1 |

### Branch notes
Observed grouped phases: Gurutva, Prema, Symmetric.
Stable branches are identified by positive Hessian eigenvalues within `eps_eigen=1e-6`.

## Benchmark C_tamas_branch

### Parameters

```json
{
  "name": "C_tamas_branch",
  "muH_eff2": 0.13,
  "lambdaH": 0.13,
  "mrho2": 0.5,
  "brho": 0.3,
  "arho": 0.4,
  "miota2": -0.35,
  "biota": 0.45,
  "aiota": 0.1,
  "c": 0.2,
  "LambdaT2_kappa0": -0.15
}
```

### Copositivity sanity check

Status: **pass**
- `lambdaH_positive`: True
- `brho_positive`: True
- `biota_positive`: True
- `arho_pairwise`: True
- `aiota_pairwise`: True
- `c_pairwise`: True
- Note: Pairwise quartic boundedness sanity check only; not a full three-field copositivity proof.

### Plots

- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\C_tamas_branch_phi_r_s0.png`
- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\C_tamas_branch_phi_s_r0.png`
- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\C_tamas_branch_low_energy_points.png`

### Global minimum

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| C_tamas_branch_raw_0 | Tamas | stable_minimum | 0.77344314 | 0 | -1.0220777 | -0.1500223214 | 0.147651, 0.724107, 0.948064 |  |

### All stable raw minima

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| C_tamas_branch_raw_0 | Tamas | stable_minimum | 0.77344314 | 0 | -1.0220777 | -0.1500223214 | 0.147651, 0.724107, 0.948064 |  |
| C_tamas_branch_raw_1 | Tamas | stable_minimum | 0.77344314 | 0 | 1.0220777 | -0.1500223214 | 0.147651, 0.724107, 0.948064 |  |

### Symmetry-grouped minima

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| C_tamas_branch_group_0 | Tamas | stable_minimum | 0.7734431 | 0 | 1.0220777 | -0.1500223214 | 0.147651, 0.724107, 0.948064 | 2 |
| C_tamas_branch_group_1 | Prema | unstable_saddle_or_max | 1 | 0 | 0 | -0.0325 | -0.45, 0.26, 0.7 | 1 |
| C_tamas_branch_group_2 | Symmetric | unstable_saddle_or_max | 0 | 0 | 0 | 0 | -0.5, -0.13, 0.5 | 1 |

### Phase representatives

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| C_tamas_branch_group_0 | Tamas | stable_minimum | 0.7734431 | 0 | 1.0220777 | -0.1500223214 | 0.147651, 0.724107, 0.948064 | 2 |
| C_tamas_branch_group_1 | Prema | unstable_saddle_or_max | 1 | 0 | 0 | -0.0325 | -0.45, 0.26, 0.7 | 1 |
| C_tamas_branch_group_2 | Symmetric | unstable_saddle_or_max | 0 | 0 | 0 | 0 | -0.5, -0.13, 0.5 | 1 |

### Branch notes
Observed grouped phases: Prema, Symmetric, Tamas.
Stable branches are identified by positive Hessian eigenvalues within `eps_eigen=1e-6`.

## Benchmark D_mixed_exploratory

### Parameters

```json
{
  "name": "D_mixed_exploratory",
  "muH_eff2": 0.13,
  "lambdaH": 0.13,
  "mrho2": -0.35,
  "brho": 0.45,
  "arho": -0.08,
  "miota2": -0.35,
  "biota": 0.5,
  "aiota": -0.08,
  "c": -0.05,
  "LambdaT2_kappa0": 0.05,
  "exploratory": true
}
```

### Copositivity sanity check

Status: **pass**
- `lambdaH_positive`: True
- `brho_positive`: True
- `biota_positive`: True
- `arho_pairwise`: True
- `aiota_pairwise`: True
- `c_pairwise`: True
- Note: Pairwise quartic boundedness sanity check only; not a full three-field copositivity proof.

### Plots

- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\D_mixed_exploratory_phi_r_s0.png`
- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\D_mixed_exploratory_phi_s_r0.png`
- `C:\AGI\PQT-transformers\pqt_qg_benchmark\outputs\plots\D_mixed_exploratory_low_energy_points.png`

### Global minimum

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| D_mixed_exploratory_raw_0 | Mixed | stable_minimum | 1.237497 | 0.97811 | -0.87769406 | -0.1912576513 | 0.357426, 0.785351, 0.886764 |  |

### All stable raw minima

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| D_mixed_exploratory_raw_0 | Mixed | stable_minimum | 1.237497 | 0.97811 | -0.87769406 | -0.1912576513 | 0.357426, 0.785351, 0.886764 |  |
| D_mixed_exploratory_raw_1 | Mixed | stable_minimum | 1.237497 | 0.97811 | 0.87769406 | -0.1912576513 | 0.357426, 0.785351, 0.886764 |  |
| D_mixed_exploratory_raw_2 | Mixed | stable_minimum | 1.237497 | -0.97811 | 0.87769406 | -0.1912576513 | 0.357426, 0.785351, 0.886764 |  |
| D_mixed_exploratory_raw_3 | Mixed | stable_minimum | 1.237497 | -0.97811 | -0.87769406 | -0.1912576513 | 0.357426, 0.785351, 0.886764 |  |

### Symmetry-grouped minima

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| D_mixed_exploratory_group_0 | Mixed | stable_minimum | 1.237497 | 0.97811 | 0.8776941 | -0.1912576513 | 0.357426, 0.785351, 0.886764 | 4 |
| D_mixed_exploratory_group_1 | Gurutva | unstable_saddle_or_max | 1.1287893 | 0.9439475 | 0 | -0.1193760984 | -0.373243, 0.31632, 0.816896 | 2 |
| D_mixed_exploratory_group_2 | Tamas | unstable_saddle_or_max | 1.1020486 | 0 | 0.8349616 | -0.09175867508 | -0.416009, 0.302058, 0.710876 | 2 |
| D_mixed_exploratory_group_3 | Prema | unstable_saddle_or_max | 1 | 0 | 0 | -0.0325 | -0.39, -0.34, 0.26 | 1 |
| D_mixed_exploratory_group_4 | Symmetric | unstable_saddle_or_max | 0 | 0 | 0 | 0 | -0.35, -0.3, -0.13 | 1 |

### Phase representatives

| id | phase | stability | phi | r/abs_r | s/abs_s | V0 | eigvals | mult |
|---|---|---|---|---|---|---|---|---|
| D_mixed_exploratory_group_0 | Mixed | stable_minimum | 1.237497 | 0.97811 | 0.8776941 | -0.1912576513 | 0.357426, 0.785351, 0.886764 | 4 |
| D_mixed_exploratory_group_1 | Gurutva | unstable_saddle_or_max | 1.1287893 | 0.9439475 | 0 | -0.1193760984 | -0.373243, 0.31632, 0.816896 | 2 |
| D_mixed_exploratory_group_2 | Tamas | unstable_saddle_or_max | 1.1020486 | 0 | 0.8349616 | -0.09175867508 | -0.416009, 0.302058, 0.710876 | 2 |
| D_mixed_exploratory_group_3 | Prema | unstable_saddle_or_max | 1 | 0 | 0 | -0.0325 | -0.39, -0.34, 0.26 | 1 |
| D_mixed_exploratory_group_4 | Symmetric | unstable_saddle_or_max | 0 | 0 | 0 | 0 | -0.35, -0.3, -0.13 | 1 |

### Branch notes
Observed grouped phases: Gurutva, Mixed, Prema, Symmetric, Tamas.
Stable branches are identified by positive Hessian eigenvalues within `eps_eigen=1e-6`.
