# PQT-005 evidence map

Read README_REPRO.md first. Expected scientific FAIL and SCAN_ONLY are preserved separately from replay verification PASS.

| ID | Claim | Scientific status | Portable test | Source | Artifact |
|---|---|---|---|---|---|
| N01 | v10 exact original operator spectrum | PASS | v10_exact_operator | sources/formalization_package/neutrino_pqt_v10.py | evidence/CODEX/NEUTRINO_SOURCE_REPLAY/PYTHON_OPERATOR_REPLAY.json |
| N02 | published rho=.1528/.2294 at four decimals | FAIL | v10_exact_operator | same as N01 | evidence/HIX/h1b_results.json |
| N03 | theta23=58.740208 source output; experimental fit failure | CONDITIONAL | v10_exact_operator | same as N01 | evidence/CODEX/NEUTRINO_SOURCE_REPLAY/CODEX_AUDIT_REPORT.md |
| N04 | 3 effective shape parameters; rank/doF caveats; kappa1 rank2 | PASS | symmetric_projectors_rank_basis | same as N01 | evidence/HIX/h1e_results.json |
| N05 | old incoherent operator invariant under degenerate-basis rotation | FAIL | symmetric_projectors_rank_basis | same as N01 | evidence/HIX/H1E_RANK_BASIS.md |
| N06 | projector identity for symmetric source; separate joint sectors gamma0 | PASS | symmetric_projectors_rank_basis | same as N01 | evidence/CODEX/ROUND3_COMPLEX_PHASE/PROJECTOR_AND_PHASE_PROOFS.wl |
| N07 | arbitrary-source projector equivalence | FAIL | symmetric_projectors_rank_basis | same as N01 | evidence/HIX/h4_results.json |
| C01 | literal complex ansatz and all eight sign assignments | PASS | complex_8_signs_and_counterexamples | evidence/CODEX/ROUND3_COMPLEX_PHASE/FORUM_SOURCE_SNAPSHOT.json | evidence/HIX/h4_results.json |
| C02 | Argon supplied numerical table follows literal formula | FAIL | complex_8_signs_and_counterexamples | same as C01 | evidence/CODEX/ROUND3_COMPLEX_PHASE/PYTHON_LITERAL_REPLAY.json |
| C03 | universal cos(delta)>0 at fixed +pi/2 | FAIL | complex_8_signs_and_counterexamples | same as C01 | evidence/CODEX/ROUND3_COMPLEX_PHASE/FIXED90_COUNTEREXAMPLE.wl |
| C04 | fixed-phase historical and Bari pseudo fits, constrained scans | SCAN_ONLY | extended_frozen_optimization_protocols | same as C01 | evidence/CODEX/ROUND4_CP_RESIDUES/CP_SCAN.json |
| C05 | physical phase origin and sign allocation | PROVENANCE_PENDING | NOT_RUN | missing primary phase derivation | evidence/CODEX/ROUND3_COMPLEX_PHASE/CODEX_COMPLEX_PHASE_AUDIT.md |
| C06 | global upper-octant theorem | NOT_RUN | NOT_RUN | no supplied rigorous eigenvector proof | forum/forum-7966a9411004a1e0a14243a7.json |
| B01 | Bari 90-node marginal CP graphical extraction | PASS | Bari_graphical_profiles_and_2D | evidence/CODEX/ROUND4_CP_RESIDUES/BARI_RESULTS.html | evidence/HIX/h4c_official_cp_profile.json |
| B02 | specific point outside published outer dotted NO contour | PASS | Bari_graphical_profiles_and_2D | evidence/CODEX/ROUND4_CP_RESIDUES/BARI_s23_delta.png | evidence/CODEX/ROUND5_2D_AND_SOURCE_POLES/FIGURE_AUDIT.json |
| B03 | exact official 2D/6D likelihood, calibrated full-model significance | SOURCE_BLOCKED | NOT_RUN | numeric tables unavailable in frozen release | evidence/CODEX/ROUND5_2D_AND_SOURCE_POLES/CODEX_ROUND5_2D_SOURCE_AUDIT.md |
| E01 | correct continuation derivative, healthy 2x2 and exact 4-pole benchmark | PASS | EFT_source_HIX_exact_patch_and_rollback | sources/nonlocal_memory.py | evidence/HIX/h2d_results.json |
| E02 | Argon minus-sign ghost criterion | FAIL | EFT_source_HIX_exact_patch_and_rollback | same as E01 | evidence/CODEX/ROUND4_CP_RESIDUES/EFT_PYTHON.json |
| E03 | exact HIX patch API13, V1 bitwise9/9, eigen gate, copy-only rollback | PASS | EFT_source_HIX_exact_patch_and_rollback | evidence/HIX/PROPOSED_nonlocal_memory_health.patch | evidence/HIX/h2e_results.json |
| E04 | general nonlocal physical stability and source patch release | CONDITIONAL | NOT_RUN | unified action and approval absent | evidence/HIX/H2E_HEALTH_RELEASE_GATE_ADDENDUM.md |
| Q01 | PDG-width ratios and frozen Cornell sensitivity near g2=.114 | CONDITIONAL | bottomonium_frozen_model | evidence/HIX/h3_bottomonium.py | evidence/CODEX/HIX_REVIEW/HIX_REVIEW.md |
| Q02 | general model-independent coupling/string bound | FAIL | NOT_RUN | nuisance/refit degeneracy | evidence/CODEX/NEUTRINO_SOURCE_REPLAY/BOTTOMONIUM_DIMENSIONS.md |
| R01 | RG doc-code audit, not a physical no-go | CONDITIONAL | NOT_RUN | sources/formalization_package/pqt_neutrino_rg_v2.py | evidence/HIX/h1c_results.json |
| Z01 | collider Z significance historical claims | NOT_RUN | NOT_RUN | formalization historical scripts only | sources/formalization_package |
| I01 | Round4 Markdown original freeze still matches current file | FAIL | quarantined_integrity | evidence/CODEX/ROUND4_CP_RESIDUES/CODEX_ROUND4_CP_EFT_AUDIT.md | evidence/CODEX/ROUND5_2D_AND_SOURCE_POLES/postfreeze_integrity/INTEGRITY.json |
| I02 | both incident variants and exact reconstructed digest preserved | PASS | quarantined_integrity | same as I01 | evidence/CODEX/ROUND5_2D_AND_SOURCE_POLES/postfreeze_integrity |

Attribution: evidence/CODEX and evidence/HIX retain separate original bytes. validation/clean_extended contains a fresh integration replay; it does not replace either contributor freeze.

The archival gap list is metadata/PRIMARY_SOURCE_GAPS.json. Version and wheel/license indexes are under environment/. The incident is in evidence/CODEX/ROUND5_2D_AND_SOURCE_POLES/postfreeze_integrity/. Point/mask CSVs are under data/.
