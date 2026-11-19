# Phenomenology & Collider Stack (Track B)

This directory hosts collider physics benchmarks, background closure analyses, forensic validation reports, and gate status records for Process Quantum Theory signatures at hadron colliders (VBF production with 4-lepton decay channel $pp \to j j (X \to 4\ell)$).

---

## 1. Benchmarks & Validation Reports

Archived in `benchmarks/`:

1. **`v20_background_closure` (v2.0):**
   * Analysis of 799 Delphes background events ($ZZ \to 4\ell$) compared against signal benchmarks.
   * Reports: `BACKGROUND_CLOSURE_REPORT_v20.md`, `background_summary_v20.csv`, `background_summary_v20.json`, `significance_v20.csv`.
   * Kinematic plots: `m4l_signal_vs_background.png`, `mjj_signal_vs_background.png`, `significance_barplot.png`.
2. **`forensic_v22b_report.md` (v2.2b):**
   * Statistical forensic analysis of seed variance, window sensitivity, and background contamination.
   * Key finding: original 10k signal point $m150\_s2\_1e-3\_modeA$ contained only $N_{\text{signal, raw}} = 2$ raw events in the acceptance window.
   * Validation plots: `seed_variance_v22b.png`, `signal_background_split_v22b.png`, `window_sensitivity_v22b.png`.
3. **`v23_gate_status.md` / `v23_gate_status.json` (v2.3):**
   * **Status:** `BLOCKED_MISSING_EVENT_LEVEL_DATA`.
   * In compliance with project epistemic rules, the 144-point cut stability map will NOT be interpolated from summary tables. Fresh event-level generation ($\ge 50\text{k}$–$100\text{k}$ events) is required before unblocking this track.

---

## 2. Generator Modules Status

* **FeynRules Extension (`feynrules/`):** See [`feynrules/README.md`](feynrules/README.md).
* **UFO Model (`ufo/`):** See [`ufo/PQT_MemorySector_massbasis/README.md`](ufo/PQT_MemorySector_massbasis/README.md).
