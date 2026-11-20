# Collider v2.3 Event-Level Gate Report

**Date:** 2026-11-20  
**Historical 10k v2.3 Status:** `ARCHIVED_BACKGROUND_STARVATION`  
**Statistically Valid v2.3 Status:** `BLOCKED_NEEDS_HIGH_STATS_REGEN`  
**Execution Environment:** Native Windows (`C:\Python314\python.exe`)

---

## 1. Dual Status Classification

In accordance with **Strict Epistemic Rule 3**, Collider Track B explicitly separates the historical 10k benchmark diagnostic artifacts from production statistical discovery gates:

| Track Status Dimension | Assigned Status | Meaning & Boundaries |
|---|---|---|
| **Historical 10k Diagnostic Scan** | `ARCHIVED_BACKGROUND_STARVATION` | Preserved in [`historical_v23/`](historical_v23/) as a documented negative/starvation artifact on $10\text{k}$ events. Peak $Z_{3000} = 598.4$ is an artifact of $B_{3000} \to 0.0143$ ($36$ cells with $B=0$, $135/144$ cells with $B < 1.0$). |
| **Statistically Valid Significance Gate** | `BLOCKED_NEEDS_HIGH_STATS_REGEN` | Requires fresh, independent Monte Carlo event generation ($\ge 50\text{k}$–$100\text{k}$ events) with true event-level kinematics. **Table interpolation or synthetic fitting is strictly forbidden.** |

---

## 2. Summary of Historical 10k Findings (`historical_v23/`)

* **Dataset Origin:** Recovered from `C:\AGIOLD\AGI\benchmark_v31_out\v23_cut_stability_map\` (10k Delphes MC events).
* **Grid Topology:** $144$ total configurations ($4\text{ mass windows} \times 6\text{ } m_{jj}\text{ cuts} \times 6\text{ } \Delta\eta_{jj}\text{ cuts}$).
* **Raw Statistics Limitation:** Only $N_{\text{signal, raw}} = 2$ raw events generated in acceptance window across all 144 configurations.
* **Background Depletion:**
  - $36$ cells ($25.0\%$) have $B_{3000} = 0.0$ (`status == "BG_ZERO"`, undefined significance).
  - $135$ cells ($93.8\%$) have $B_{3000} < 1.0$ event.
  - Peak configuration (`w3`, $m_{jj}=600$, $\Delta\eta_{jj}=5.0$): $S_{3000} = 71.6$, $B_{3000} = 0.0143$, producing nominal $Z = 598.4$.
  - Mean local variation across adjacent grid points is $39.44$, refuting any plateau hypothesis.
* **Official Classification:** `BACKGROUND_STARVATION` (confirmed in `plateau_metrics_v23.json`).

---

## 3. High-Statistics Production Gate Requirements

To unblock the `statistically_valid_v23_status` gate:
1. **Sample Statistics:** $\ge 50\,000$–$100\,000$ events per channel for:
   - Signal: $pp \to j j (S \to ZZ^* \to 4\ell)$
   - Electroweak Background: $pp \to j j ZZ \to j j 4\ell$ (QCD + EW)
   - Resonant Background: $pp \to t\bar{t}Z \to 4\ell + X$
   - Higgs Background: $pp \to j j H \to j j 4\ell$
2. **Event-Level Storage:** Complete per-event kinematic tuples $(m_{4\ell}, m_{jj}, \Delta\eta_{jj}, p_{T,j1}, p_{T,j2})$ in ROOT or Parquet format.
3. **Statistical Profile:** Rigorous profile-likelihood significance ($q_0$) or $\text{CL}_s$ upper limits incorporating Poisson uncertainty on small background counts, replacing naive $S/\sqrt{B}$ when $B < 10$.
