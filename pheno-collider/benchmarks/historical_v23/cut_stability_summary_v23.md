# PQT Benchmark v2.3 - Cut Stability Map Report

## Classification: **BACKGROUND_STARVATION**

### Interpretation

The maximum Z_3000 = 598 is driven almost entirely by **background starvation** (minimum B_3000 = 0.0143 events), not by signal strength (S_3000 = 71.6 is constant across all configurations). VBF cuts (high mjj, high deta) combined with narrower mass windows reduce the background yield to near zero while the signal yield (2 events in the mass window) remains stable. The mean local variation of 39.44 confirms that significance is **extremely sensitive** to cut choices -- this is the hallmark of a background-starvation-dominated result, not a robust signal detection.

## Summary Metrics

| Metric | Value |
|---|---|
| Max Z_3000 | 598.4 |
| Mean Z_3000 | 304.2 |
| Valid configs (Z finite) | 108 / 144 |
| Hot points (Z >= 3) | 108 |
| Hot fraction | 100.00% |
| Largest connected component (Z >= 3) | 108 |
| Mean local variation | 39.44 |
| Min B_3000 (nonzero) | 0.014317 |
| Max B_3000 | 3.8551 |
| Background starvation artifact | **YES** |

## Best Configuration

| Field | Value |
|---|---|
| Window | w3 (120-180 GeV) |
| mjj cut | 600 GeV |
| deta cut | 5.0 |
| n_sig | 2 |
| VBF efficiency | 1.0 |
| Z_3000 | 598.4 |
| S_3000 | 71.6 |
| B_3000 | 0.014317 |

## Worst Configuration

| Field | Value |
|---|---|
| Window | w1 (100-180 GeV) |
| mjj cut | 300 GeV |
| deta cut | 2.5 |
| n_sig | 2 |
| VBF efficiency | 1.0 |
| Z_3000 | 36.47 |
| S_3000 | 71.6 |
| B_3000 | 3.855 |

## Classification Rules Applied

- **ROBUST_PLATEAU**: max_Z >= 5 AND largest_component >= 8 AND hot_fraction >= 10% AND mean_local_variation < 0.5
- **BACKGROUND_STARVATION**: max_Z >= 5 AND largest_component >= 8 AND mean_local_variation >= 1.0 AND min_B near zero (artifact of background elimination, not signal strength)
- **FRAGILE_SPIKE**: max_Z >= 5 AND largest_component < 4
- **INTERESTING_BUT_WEAK**: 3 <= max_Z < 5
- **HIDDEN**: max_Z < 1

## Top 20 Configurations by Z_3000

| Window | mjj | deta | n_sig | VBF_eff | S_3000 | B_3000 | Z_3000 |
|---|---|---|---|---|---|---|---|
| w3 | 600 | 5.0 | 2 | 1.0 | 71.6 | 0.014317 | 598.4 |
| w3 | 700 | 5.0 | 2 | 1.0 | 71.6 | 0.014317 | 598.4 |
| w3 | 800 | 5.0 | 2 | 1.0 | 71.6 | 0.014317 | 598.4 |
| w1 | 600 | 5.0 | 2 | 1.0 | 71.6 | 0.020044 | 505.7 |
| w2 | 600 | 5.0 | 2 | 1.0 | 71.6 | 0.020044 | 505.7 |
| w1 | 700 | 5.0 | 2 | 1.0 | 71.6 | 0.020044 | 505.7 |
| w2 | 700 | 5.0 | 2 | 1.0 | 71.6 | 0.020044 | 505.7 |
| w1 | 800 | 5.0 | 2 | 1.0 | 71.6 | 0.020044 | 505.7 |
| w2 | 800 | 5.0 | 2 | 1.0 | 71.6 | 0.020044 | 505.7 |
| w3 | 400 | 5.0 | 2 | 1.0 | 71.6 | 0.022908 | 473.0 |
| w3 | 500 | 5.0 | 2 | 1.0 | 71.6 | 0.022908 | 473.0 |
| w3 | 800 | 4.5 | 2 | 1.0 | 71.6 | 0.022908 | 473.0 |
| w3 | 700 | 4.5 | 2 | 1.0 | 71.6 | 0.025771 | 446.0 |
| w3 | 300 | 5.0 | 2 | 1.0 | 71.6 | 0.028634 | 423.1 |
| w2 | 400 | 5.0 | 2 | 1.0 | 71.6 | 0.028634 | 423.1 |
| w2 | 500 | 5.0 | 2 | 1.0 | 71.6 | 0.028634 | 423.1 |
| w3 | 800 | 4.0 | 2 | 1.0 | 71.6 | 0.028634 | 423.1 |
| w1 | 800 | 4.5 | 2 | 1.0 | 71.6 | 0.028634 | 423.1 |
| w2 | 800 | 4.5 | 2 | 1.0 | 71.6 | 0.028634 | 423.1 |
| w1 | 400 | 5.0 | 2 | 1.0 | 71.6 | 0.031498 | 403.4 |

## Background-Zero Configurations (36 of 144)

These configurations have zero background events surviving all cuts (most restrictive VBF + tightest mass window):

| Window | mjj | deta |
|---|---|---|
| w4 | 300 | 2.5 |
| w4 | 300 | 3.0 |
| w4 | 300 | 3.5 |
| w4 | 300 | 4.0 |
| w4 | 300 | 4.5 |
| w4 | 300 | 5.0 |
| w4 | 400 | 2.5 |
| w4 | 400 | 3.0 |
| w4 | 400 | 3.5 |
| w4 | 400 | 4.0 |
| w4 | 400 | 4.5 |
| w4 | 400 | 5.0 |
| w4 | 500 | 2.5 |
| w4 | 500 | 3.0 |
| w4 | 500 | 3.5 |
| w4 | 500 | 4.0 |
| w4 | 500 | 4.5 |
| w4 | 500 | 5.0 |
| w4 | 600 | 2.5 |
| w4 | 600 | 3.0 |
| w4 | 600 | 3.5 |
| w4 | 600 | 4.0 |
| w4 | 600 | 4.5 |
| w4 | 600 | 5.0 |
| w4 | 700 | 2.5 |
| w4 | 700 | 3.0 |
| w4 | 700 | 3.5 |
| w4 | 700 | 4.0 |
| w4 | 700 | 4.5 |
| w4 | 700 | 5.0 |
| w4 | 800 | 2.5 |
| w4 | 800 | 3.0 |
| w4 | 800 | 3.5 |
| w4 | 800 | 4.0 |
| w4 | 800 | 4.5 |
| w4 | 800 | 5.0 |

## Physical Interpretation

The extremely high Z_3000 values (up to 598) are driven by **background starvation**, not by signal strength. S_3000 is constant at 71.6 across all configurations (2 signal events in the mass window, scaled by VBF efficiency and the fixed sigma_reco_fb). Tighter VBF cuts (higher mjj, higher deta) combined with narrower windows reduce the background yield to near zero while the signal yield remains stable. The mean local variation of 39.44 confirms that significance is **extremely sensitive** to cut choices -- this is the hallmark of a background-starvation-dominated result, not a robust signal detection.

Key observations:
- Window w4 (130-165 GeV) produces 36 BG-zero configs out of 36 possible -- the tightest window eliminates all background
- The best configs (Z ~ 600) have B_3000 = 0.014, meaning only 0.014 background events expected in 3000 fb^-1
- Even the worst config (w1, 300 GeV, 2.5) achieves Z=36, which is still far above 5-sigma
- Signal events (n_sig = 2) are constant across all configurations since the signal MC has only 10k events

## Conclusion

**BACKGROUND_STARVATION**: The significance is entirely dominated by background starvation rather than genuine signal excess. The VBF cuts and mass windows are so effective at eliminating background that B_3000 approaches zero across most of the scan space. While Z_3000 nominally reaches 598, this does not indicate a robust signal detection -- it reflects the absence of background events in the MC sample (only 10k events per process). In an experimental analysis with real data, systematic uncertainties, higher-order QCD processes, and larger background samples would substantially modify these results. The signal itself (H->ZZ->4l at m_S=150 GeV) is produced at the expected rate but cannot be robustly claimed as discovered based on this background-limited study.