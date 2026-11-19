# PQT-QG Effective Field Theory & Non-Local Memory Benchmarks

This directory contains the computational benchmarks for scanning the scalar vacuum landscape $V_0(\phi, r, s)$, one-loop Coleman-Weinberg corrections, and non-local memory kernel stability for Process Quantum Theory Effective Field Theory (PQT-QG).

---

## 1. Physical & Epistemic Scope

* **Framework:** 3-field scalar potential $(\phi, r, s)$ representing the Higgs background $\phi$, hidden radial mediator $r$, and non-local memory sector $s$.
* **Non-local Kernels Analyzed:**
  1. `local_constant`: Constant local memory approximation ($K_T(k) \approx \kappa_0$).
  2. `single_pole`: Resolvent-type kernel $\Sigma_E(q) = \frac{\sigma_0 M^2}{q + M^2}$.
  3. `exp_gap`: Gapped non-local kernel $\Sigma_E(q) = \sigma_0 e^{-q / M^2}$.
* **Epistemic Classification:** `PASS_EXECUTION` (deterministic benchmark scans on Euclidean momentum quadrature).

---

## 2. Baseline Status & Upcoming Pull Request #1

> [!WARNING]
> **Baseline Diagnostic Defect:**  
> In this initial baseline commit (`v0.9-baseline`), `pqt_qg/nonlocal_memory.py` retains the legacy determinant heuristic:
> ```python
> min_eval = float(min(np.min(det), np.min(inv_iota)))
> ```
> By Sylvester's criterion, a 3×3 real symmetric matrix $M$ with $\det(M) > 0$ and $M_{ss} > 0$ can have two negative eigenvalues, hiding tachyonic instabilities.

* **Pending Fix:** The exact spectral patch is staged in [`patches/PROPOSED_nonlocal_memory_health.patch`](patches/PROPOSED_nonlocal_memory_health.patch), utilizing `scipy.linalg.eigvalsh` to verify:
  $$\lambda_{\min}^{\text{global}} = \min_{q \in [0, k_{\max}^2]} \min(\text{eigvalsh}(M(q))) > 0$$
* **Scheduled Implementation:** **Pull Request #1** will apply this patch and incorporate unit tests into CI.
* **Audit Confirmation:** A/B audit across 2,361 cells confirmed **0 false-positive tachyons** in the cooperative Mixed attractor region ($\lambda_{\min}^{\text{global}} \ge +0.1906$).

---

## 3. Running Benchmarks

```powershell
python -m pip install -r requirements.txt
python run_benchmarks.py
python run_nonlocal_micro_scan.py
python run_nonlocal_cooperative_atlas.py
```

Outputs are archived under `outputs/`:
* `outputs/reports/`: Full Markdown technical audit reports (v0.1 through v0.9).
* `outputs/plots/`: High-resolution phase diagrams, potential contours, and attractor stability scans.
* `outputs/data/`: Compact JSON and CSV summary tables.
