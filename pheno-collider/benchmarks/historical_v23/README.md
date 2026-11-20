# Historical Collider Benchmark v2.3: 144-Point Cut Stability Map

## 1. Provenance & Dataset Origin
This directory archives the historical 144-point Collider Cut Stability Scan generated during the PQT v3.1 evaluation campaign:
* **Source Archive:** Recovered from `C:\AGIOLD\AGI\benchmark_v31_out\v23_cut_stability_map\` (November 2026 audit).
* **Generator / Detector Stack:** MadGraph5_aMC@NLO v3.7.1 $\to$ Pythia8 $\to$ Delphes 3.5.0 ($10\text{k}$ Monte Carlo event sample for signal benchmark $m150\_s2\_1e-3\_modeA$ and electroweak backgrounds $ZZjj$, $ttZ$, $Hjj$).
* **Scan Grid:** 144 total configurations exploring:
  - 4 4-lepton invariant mass windows ($w_1, w_2, w_3, w_4$) centered around $M_S = 150\text{ GeV}$.
  - 6 dijet invariant mass cuts ($m_{jj} \in [300, 400, 500, 600, 700, 800]\text{ GeV}$).
  - 6 pseudorapidity separation cuts ($\Delta\eta_{jj} \in [2.5, 3.0, 3.5, 4.0, 4.5, 5.0]$).

---

## 2. Epistemic Classification: `BACKGROUND_STARVATION`

> [!WARNING]
> **Diagnostic Artifact — NOT a Physical Discovery Claim:**
> The nominal significance values in this dataset reach an apparent peak of $Z_{3000} \approx 598.4$. This is **NOT** a physical discovery claim and does **NOT** indicate a robust signal plateau. It is a well-documented **statistical artifact of background starvation** on small ($10\text{k}$ event) Monte Carlo samples.

### Mechanism of the Artifact
1. **Constant Signal Yield:** Across all 144 configurations, the raw Monte Carlo signal yield inside the acceptance window was only **$N_{\text{signal, raw}} = 2$ events** (extrapolated to $S_{3000} = 71.5968$ at $\mathcal{L} = 3000\text{ fb}^{-1}$).
2. **Background Depletion at Tight VBF Cuts:** The dominant baseline background ($Hjj \to 4\ell$) is progressively eliminated as $m_{jj}$ and $\Delta\eta_{jj}$ cuts are tightened. At tight cuts, zero or single raw background events survive in the $10\text{k}$ sample:
   - **36 cells (25.0%)** have exactly zero surviving background events ($B_{3000} = 0.0$, `status == "BG_ZERO"`, $Z_{3000}$ undefined).
   - **135 cells (93.8%)** have $B_{3000} < 1.0$ event.
   - At the nominal peak configuration (`w3`, $m_{jj} = 600\text{ GeV}$, $\Delta\eta_{jj} = 5.0$), the background yield is merely $B_{3000} \approx 0.0143$ events.
3. **Artifactual Significance Spikes:** Computing $Z = S / \sqrt{B}$ when $B \to 0$ leads to runaway division by near-zero denominators:
   $$Z_{3000} = \frac{71.5968}{\sqrt{0.014317}} \approx 598.36$$
   The mean local variation across adjacent grid points is $39.44$, demonstrating extreme hypersensitivity to individual cut boundaries.

---

## 3. Verified Summary Metrics

| Metric | Verified Value | Reference Artifact |
|---|---|---|
| **Total Grid Configurations** | `144` ($4 \times 6 \times 6$) | `cut_stability_scan_v23.csv` |
| **Unique Grid Points** | `144` (zero duplicates) | `cut_stability_scan_v23.csv` |
| **Valid Significance Cells (`B > 0`)** | `108` (`status == "OK"`) | `cut_stability_scan_v23.csv` |
| **Background-Zero Cells (`B == 0`)** | `36` (`status == "BG_ZERO"`) | `cut_stability_scan_v23.csv` |
| **Starved Background Cells ($B_{3000} < 1.0$)** | `135` ($93.8\%$) | `cut_stability_scan_v23.csv` |
| **Peak $Z_{3000}$** | `598.362` ($598.4$) | `plateau_metrics_v23.json` |
| **Peak Configuration** | `window: w3`, $m_{jj} = 600$, $\Delta\eta_{jj} = 5.0$ | `top_configs_v23.csv` |
| **Yields at Peak** | $S_{3000} = 71.597$, $B_{3000} = 0.0143$ | `top_configs_v23.csv` |
| **Mean Local Variation** | `39.44` | `plateau_metrics_v23.json` |
| **Official Verdict** | `BACKGROUND_STARVATION` | `plateau_metrics_v23.json` |

---

## 4. Archived Artifact Manifest

* `cut_stability_scan_v23.csv` — Full 144-row scan results table with per-channel raw event counts (`n_sig`, `n_zzjj`, `n_ttz`, `n_hhj`), normalized yields ($S_{3000}, B_{3000}$), and nominal $Z_{3000}$.
* `cut_stability_scan_v23.json` — Structured JSON export of all 144 configurations.
* `top_configs_v23.csv` — Top 10 nominal configurations ranked by $Z_{3000}$ (all suffering from background starvation).
* `plateau_metrics_v23.json` — Summary metrics and classification record.
* `cut_stability_summary_v23.md` — Historical diagnostic markdown report.
* `z_heatmap_window_w1.png` ... `w4.png` — Heatmaps of nominal $Z_{3000}$ across $(m_{jj}, \Delta\eta_{jj})$ for each mass window.
* `plateau_mask_Zgt3_v23.png` — Mask of cells exceeding $3\sigma$ nominal significance.
* `signal_background_tradeoff_v23.png` — Scatter plot of $S_{3000}$ vs. $B_{3000}$.
* `plateau_connectivity_graph_v23.png` — Adjacency graph of connected plateau cells.
* `z_distribution_hist_v23.png` — Histogram of nominal $Z_{3000}$ values.

---

## 5. Decision Boundary for Future Regeneration
In accordance with PQT project epistemic policy:
- These historical $10\text{k}$ tables will **NEVER** be used to interpolate or claim physical discovery limits.
- Validating the VBF collider channel strictly requires a fresh, high-statistics Monte Carlo production campaign ($\ge 50\text{k}$–$100\text{k}$ events) with full event-level 4-momenta and rigorous profile-likelihood ratio significance calculations ($q_0 / \text{CL}_s$) that properly account for Poisson background uncertainties when $B \to 0$.
