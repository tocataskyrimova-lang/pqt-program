# Collider v2.3 Event-Level Gate Report

**Date:** 2026-11-19  
**Status:** `BLOCKED_MISSING_EVENT_LEVEL_DATA`  
**Execution Environment:** Native Windows (`C:\Python314\python.exe`)

---

## 1. Executive Summary

In accordance with **Strict Epistemic Rule 3**, execution of the 144-point Collider Benchmark v2.3 Cut Stability Map requires true event-level kinematics $(m_{4\ell}, m_{jj}, \Delta\eta_{jj})$ for every generated Monte Carlo event. Fabricating, interpolating, or approximating per-event cutflows from aggregate summary tables (`forensic_v22b_report.md`, `background_summary_v20.json`, `observable_grid_v31.csv`) is strictly prohibited.

A comprehensive read-only search across all local drives (`C:`, `D:`, `E:`, `O:`) and WSL2 volumes determined that **zero event-level files exist on the system**. Therefore, Benchmark v2.3 is gated and halted safely without mutating any project state.

---

## 2. Searched Locations & Findings

| Location / File Pattern | Intended Artifact | Actual Finding |
|---|---|---|
| `C:\AGI\benchmark_v31_out\` | Delphes ROOT trees / HEP outputs | **Directory does not exist** |
| `C:\AGI\PQT-transformers\benchmark_v31_out\` | Benchmark v31 output files | Only 100x100 grid summaries (`observable_grid_v31.csv`) |
| `C:\AGI\PQT-transformers\CAGIbenchmark_v31_outv20_background_closure\root\` | `zzjj_delphes.root`, `m150_*.root` | **Directory exists but is empty (0 bytes)** |
| `C:\AGI\PQT\MAIN\PQT_FORMALIZATION_PACKAGE\` | Forensic reports & scripts | Only summary reports and figures |
| `C:\AGI\PQT-AUDIT-001\REPRO_FREEZE_2026-10-25\` | Frozen audit package | Verified offline sources, no raw collider event trees |
| `D:\WSL\Ubuntu\ext4.vhdx` | Default WSL distro volume | **File missing** (`ERROR_PATH_NOT_FOUND`) |
| `D:\WSL\Ubuntu2204\ext4.vhdx` (`Ubuntu-22.04-PQT`) | Active secondary WSL volume | Reachable, but `/root/hep` does not exist |
| Drives `C:\`, `D:\`, `E:\`, `O:\` (`*.root`, `*.hepmc`, `*.lhe`, `*.parquet`) | Full-disk root search | 0 event-level collider data files found |

---

## 3. Statistical Caveat & Epistemic Analysis

From `forensic_v22b_report.md` and `PQT_FULL_FORMALIZATION_v1.md` Section 10:
1. **Low Raw Signal Statistics:** At the benchmark signal point $m150\_s2\_1e-3\_modeA$, the original 10,000 Delphes event pass yielded only:
   $$N_{\text{signal, raw}} = 2 \text{ events}$$
2. **Analysis Mismatch:** Under loose cuts ($100 < m_{4\ell} < 180$ GeV), $Z_{3000} = 5.32$ ($S_{3000} = 71.6$, $B_{3000} = 181.2$, $N_{\text{bg, raw}} = 799$). However, when applying tight VBF cuts ($m_{jj} > 400$ GeV, $\Delta\eta_{jj} > 3.0$) inside a narrow mass window ($130 < m_{4\ell} < 165$ GeV), background collapsed to $N_{\text{bg, raw}} = 0$ ($B_{3000} = 0$), producing an undefined or artificial statistical artifact ($Z = \infty$ / $Z$ undefined).
3. **Recovery Requirement:** Because of Poisson fluctuations on $N_{\text{signal, raw}} = 2$, legitimate resolution of the v2.3 cut landscape requires generating a fresh, high-statistics Monte Carlo sample ($\ge 50\,000$–$100\,000$ events per channel in MadGraph5 $\to$ Pythia8 $\to$ Delphes), rather than attempting to slice existing zero-event background bins.

---

## 4. Gate Decision

* **Status:** `BLOCKED_MISSING_EVENT_LEVEL_DATA`
* **Collider v2.3 Action:** Gated (No synthetic or interpolated data emitted).
* **Next Step:** Immediate transition to **Part B: PQT-QG Spectral Patch & A/B Audit**.
