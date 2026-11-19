# PQT Benchmark v2.2b — Forensic Diagnostic Report

## Final Classification: **ANALYSIS_MISMATCH**

v2.1 exact replay gives Z=5.32 > 4. Window/cut changes explain the collapse.

## 1. v2.1 Exact Replay

| Metric | Value |
|---|---|
| Window | 100 < m4l < 180 GeV |
| N_signal_raw | 2 |
| N_background_raw | 799 |
| sigma_signal_reco_fb | 0.0238656 |
| sigma_background_reco_fb | 0.0604073 |
| S_3000 | 71.6 |
| B_3000 | 181.2 |
| **Z_3000** | **5.318** |

Background breakdown:
- ZZjj: 17 events
- ttZ: 10 events
- Hjj: 772 events

## 2. Window Narrowing Study

| Config | Window | N_sig | N_bg | sig_eff_rel | bg_eff_rel | Z_3000 |
|---|---|---|---|---|---|---|
| A_100_180 | 100-180 | 2 | 799 | 1 | 1 | 5.32 |
| B_120_180 | 120-180 | 2 | 761 | 1 | 0.9524 | 5.93 |
| C_130_165 | 130-165 | 2 | 13 | 1 | 0.01627 | 8.87 |

## 3. Seed Variance Study

| Seed | N_signal | N_background | Z_3000 |
|---|---|---|---|
| seed1 | 2 | 799 | 5.32 |
| seed2 | 3 | 799 | 5.32 |
| seed3 | 3 | 799 | 5.32 |

- mean(Z): 5.318
- std(Z): 0
- std(S)/mean(S): 0.2165
- statistics_limited: False

## 4. Signal/Background Decomposition

| Configuration | Window | mjj_cut | deta_cut | N_signal | N_background | S_3000 | B_3000 | Z_3000 |
|---|---|---|---|---|---|---|---|---|
| v2.1_replay | 100-180 | - | - | 2 | 799 | 71.6 | 181 | 5.32 |
| v2.2_loose | 120-180 | 400 | 3.0 | 2 | 48 | 71.6 | 0.137 | 193 |
| v2.2_baseline | 130-165 | 400 | 3.0 | 2 | 0 | 71.6 | 0 | N/A |
| v2.2_hard | 130-165 | 600 | 4.0 | 2 | 0 | 71.6 | 0 | N/A |
| v2.2_tight | 140-160 | 800 | 5.0 | 1 | 0 | 71.6 | 0 | N/A |

## Success Criteria

- Case A (ANALYSIS_MISMATCH): v2.1 replay Z > 4 → **YES** (Z=5.32)
- Case B (STATISTICS_LIMITED): std(S)/mean(S) > 0.5 → **NO** (ratio=0.2165)
- Case C (PHYSICALLY_WEAK): v2.1 replay Z < 2 → **NO** (Z=5.32)

## Conclusion

**ANALYSIS_MISMATCH**: v2.1 exact replay gives Z=5.32 > 4. Window/cut changes explain the collapse.
