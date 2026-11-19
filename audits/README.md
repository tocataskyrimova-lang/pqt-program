# Audit Manifests & Verification Records (`audits/`)

This directory maintains cryptographic evidence, independent audit reports, SHA-256 manifests, and verification scripts for the PQT codebase.

---

## Subdirectories

1. **`repro_freeze_2026_10_25_meta/`**  
   Metadata, manifests, and verification scripts from the byte-frozen audit bundle `C:\AGI\PQT-AUDIT-001\REPRO_FREEZE_2026-10-25`.  
   * Manifests: `EVIDENCE_MANIFEST.json`, `MANIFEST.sha256`, `HISTORICAL_MANIFEST_AUDIT.json`, `CLEAN_ENVIRONMENT_ACCEPTANCE.json`.  
   * Independent Reports: `FINAL_REPRO_FREEZE_REPORT.md`, `HIX_INDEPENDENT_REPORT.md`, `ERRATA_ADDENDUM.md`.  
   * Replay scripts: `verify_hashes.py`, `offline_guard.py`, `replay_all.ps1`.

2. **`spectral_audit_2026_11/`**  
   Controlled A/B audit of exact spectral positivity (`eigvalsh`) versus the legacy determinant proxy:  
   * `PQT_QG_Spectral_Audit_Report_v0_9a.md`: Comprehensive audit report across MicroScan (11×11) and Atlas (15×15, 21×21).  
   * `spectral_audit_ab_summary.json`: Detailed numeric metrics per kernel.  
   * `applied_spectral_patch.diff`: The exact unified diff staged for PR #1.  
   * `unit_test_sylvester.json`: Unit test log confirming detection of the Sylvester counterexample.  
   * `v23_gate_status.md` / `v23_gate_status.json`: Formal blocking of collider v2.3 scan.

3. **`IMPORT_MANIFEST_SHA256.json`**  
   The SHA-256 hash manifest of all staged files in this baseline repository import.
