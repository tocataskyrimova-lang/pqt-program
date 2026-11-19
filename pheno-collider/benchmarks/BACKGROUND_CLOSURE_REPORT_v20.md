# PQT Benchmark v2.0 — SM Background Closure

## Purpose
Estimate Standard Model backgrounds for the same 4l + 2j topology and compute first naive significance estimates using the validated signal pipeline unchanged.

## Background process
- Primary fully processed: `pp > z z j j, z > l+ l-, z > l+ l-`
- Secondary channels `ttZ` and `Hjj` were not run in this pass and remain pending by design.

## Inputs and integrity checks
- MG5 integrated weight: 0.0120579868913 pb
- HepMC shower events: 10000
- Delphes ROOT events: 10000

## Background reconstruction summary
- reco_4l: 1545
- reco_2e2mu: 748
- reco_4l_plus_2j: 1259
- reco_4l_mass_window (m150 window): 18
- reco_4l_mass_window (m200 window): 549
- reco efficiency m150 window: 0.0018
- reco efficiency m200 window: 0.0549
- sigma_reco_fb m150 window: 0.0217044
- sigma_reco_fb m200 window: 0.661983

## Signal comparison and naive significance
- m150_s2_1e-3_modeA: Z_3000=8.87, S/B_3000=1.1, class=strong
- m200_s2_1e-3_onshell: Z_3000=0.108, S/B_3000=0.00243, class=hidden

Classification rules: hidden if Z_3000 < 2; interesting if 2 <= Z_3000 < 5; strong if Z_3000 >= 5.

## Final classification
FULL PASS for the primary ZZjj closure. Secondary channels remain pending.

## Notes
This is an honest first signal-vs-background estimate only. No cut optimization, discovery claim, or official exclusion is implied.

## Next smallest patch
Run ttZ and Hjj background channels if runtime budget allows; otherwise move to a cut-optimization study.
