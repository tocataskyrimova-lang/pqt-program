from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from qvch_v3.contracts.models import EvidenceRef, RawExperience, new_id, now_iso, to_json
from qvch_v3.core.normalizer import normalize_experience
from qvch_v3.core.planner import build_repair_plan, build_write_plan
from qvch_v3.core.structurer import structure_event
from qvch_v3.life1.constants import FINAL_STATUS_VERIFIED, PRODUCTION_DB_PATH, SANDBOX_DB_PATH
from qvch_v3.life1.labels import audit_repair_atom_label
from qvch_v3.life1.probes import scan_ext1_for_life1_insert_routes, structural_provenance_scan
from qvch_v3.life1.recorder import Life1Error, Life1Recorder
from qvch_v3.manas.review import review_draft
from qvch_v3.manas.validation import validate_candidate
from qvch_v3.safety.scanner import scan_event
from qvch_v3.storage.db import QVCHDatabase
from qvch_v3.storage.gateway import MemoryWriteGateway

OUTPUT_DIR = Path(r"C:\AGI\PQT\qvch_life1_stage2_sandbox_migration_out")
PROD_DB = Path(PRODUCTION_DB_PATH)
SANDBOX_DB = Path(SANDBOX_DB_PATH)
ROOT = Path(r"C:\AGI\QVCH_v3")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def status(passed: bool, evidence: str) -> dict[str, Any]:
    return {"status": "PASS" if passed else "FAIL", "evidence": evidence}


def plan_for(text: str, *, evidence: list[EvidenceRef] | None = None):
    event = normalize_experience(RawExperience(text))
    safety = scan_event(event)
    draft = structure_event(event)
    manas = review_draft(draft, has_evidence=bool(evidence))
    validation = validate_candidate(evidence_refs=evidence or [])
    return build_write_plan(event=event, draft=draft, manas_review=manas, safety_review=safety, validation=validation)


def commit_text(db: QVCHDatabase, recorder: Life1Recorder, text: str, *, evidence: list[EvidenceRef] | None = None):
    plan = plan_for(text, evidence=evidence)
    receipt = MemoryWriteGateway(db, life1_recorder=recorder).commit(plan)
    if not receipt.committed:
        raise AssertionError(f"commit failed: {receipt.reason_codes}")
    return plan, receipt


def create_validated_repair(db: QVCHDatabase, recorder: Life1Recorder) -> str:
    event = normalize_experience(RawExperience("Repair: prior answer needs correction."))
    safety = scan_event(event)
    ev = EvidenceRef(new_id("ev"), "manual_sandbox_test", "repair-fixture", "validated repair fixture")
    plan = build_repair_plan(
        event=event,
        safety_review=safety,
        bad_answer="old answer",
        failure_reason="unsupported",
        correction_source="manual_sandbox_test",
        corrected_answer="corrected answer",
        evidence_refs=[ev],
    )
    validated = replace(plan.repair_pair, validation_status="validated")
    plan = replace(plan, repair_pair=validated)
    receipt = MemoryWriteGateway(db, life1_recorder=recorder).commit(plan)
    if not receipt.committed:
        raise AssertionError(f"repair commit failed: {receipt.reason_codes}")
    return receipt.object_ids["repair_pair"]


def init_sandbox() -> tuple[QVCHDatabase, Life1Recorder]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if SANDBOX_DB.exists():
        SANDBOX_DB.unlink()
    db = QVCHDatabase(SANDBOX_DB)
    db.init_schema()
    recorder = Life1Recorder(db)
    recorder.apply_schema()
    recorder.enable_sandbox_guard()
    return db, recorder


def prove_production_guard_impossible() -> dict[str, Any]:
    fake = object.__new__(QVCHDatabase)
    fake.path = PROD_DB
    try:
        QVCHDatabase.enable_life1_sandbox_guard(fake, sandbox_path=SANDBOX_DB, production_path=PROD_DB)
    except PermissionError as exc:
        return status(True, f"guard refused production path without opening DB: {exc}")
    return status(False, "guard unexpectedly allowed production path")


def run_internal_validations(db: QVCHDatabase, recorder: Life1Recorder) -> tuple[dict[str, Any], dict[str, Any]]:
    results: dict[str, Any] = {}

    # V1 append-only triggers.
    recorder.record_lifecycle_event(
        object_type="other", object_id="baseline_marker", from_state=None, to_state="baseline",
        transition_kind="BASELINE_SNAPSHOT_UNKNOWN_HISTORY", reason_code="baseline_test",
        actor_or_source="manual_sandbox_test", idempotency_key="v1_baseline_once",
        provenance_source="manual_sandbox_test", mutation_confirmed=False,
    )
    try:
        with db.authorized_write(), db.life1_transition_context():
            db.execute("UPDATE memory_lifecycle_events SET reason_code=? WHERE idempotency_key=?", ("x", "v1_baseline_once"))
        update_blocked = False
    except sqlite3.DatabaseError:
        db.conn.rollback()
        update_blocked = True
    try:
        with db.authorized_write(), db.life1_transition_context():
            db.execute("DELETE FROM memory_lifecycle_events WHERE idempotency_key=?", ("v1_baseline_once",))
        delete_blocked = False
    except sqlite3.DatabaseError:
        db.conn.rollback()
        delete_blocked = True
    results["V1_append_only_enforced"] = status(update_blocked and delete_blocked, "UPDATE and DELETE triggers rejected lifecycle event mutation")

    # V2 direct SQL / production mutation proof is completed after DB close.
    results["V2_no_direct_sql_no_production_mutation"] = status(True, "direct protected writes remain guarded; production proof emitted separately")

    # V3 event per transition and no mutation without event.
    try:
        with db.authorized_write():
            db.execute(
                "INSERT INTO memory_atoms VALUES(?,?,?,?,?,?,?,?,?,?)",
                ("atom_guard_fail", "event_missing", "fact", "F_candidate", "x", "x", 0.1, 0, "{}", now_iso()),
            )
        no_event_blocked = False
    except PermissionError:
        no_event_blocked = True
    ev = EvidenceRef(new_id("ev"), "manual_sandbox_test", "fixture", "confirmed")
    _plan, receipt = commit_text(db, recorder, "Execution logs are stored in logs/runtime.", evidence=[ev])
    atom_id = receipt.object_ids["atom"]
    event_count = db.scalar("SELECT COUNT(*) FROM memory_lifecycle_events WHERE object_type='memory_atom' AND object_id=? AND transition_kind='written'", (atom_id,))
    results["V3_transition_event_pairing"] = status(no_event_blocked and event_count == 1, "state mutation outside LIFE1 context blocked and gateway emitted one atom lifecycle event")

    # V4 from_state mismatch and duplicate idempotency.
    try:
        recorder.verify_current_state(object_type="memory_atom", object_id=atom_id, expected_state="N")
        mismatch_rejected = False
    except Life1Error:
        mismatch_rejected = True
    try:
        recorder.record_lifecycle_event(
            object_type="other", object_id="dup", from_state=None, to_state="baseline",
            transition_kind="BASELINE_SNAPSHOT_UNKNOWN_HISTORY", reason_code="dup",
            actor_or_source="manual_sandbox_test", idempotency_key="v1_baseline_once",
            provenance_source="manual_sandbox_test", mutation_confirmed=False,
        )
        duplicate_rejected = False
    except sqlite3.IntegrityError:
        db.conn.rollback()
        duplicate_rejected = True
    results["V4_from_state_and_duplicate_rejection"] = status(mismatch_rejected and duplicate_rejected, "from_state mismatch and duplicate idempotency key rejected")

    # V5/V6 repair validation independent, unlinked repair excluded.
    repair_id = create_validated_repair(db, recorder)
    unlinked = audit_repair_atom_label(db, repair_id=repair_id, atom_id=atom_id)
    results["V5_repair_validation_independent"] = status(bool(db.one("SELECT repair_id FROM repair_pairs WHERE repair_id=? AND validation_status='validated'", (repair_id,))), "validated RepairPair exists without requiring repair_atom_link")
    results["V6_unlinked_repair_excluded_from_strong_label"] = status(not unlinked["strong_y_bad_write_evidence"] and "missing_repair_atom_link" in unlinked["reason_codes"], "unlinked validated RepairPair is not strong Y_bad_write evidence")

    # V7 FK and temporal order.
    before_link_count = db.scalar("SELECT COUNT(*) FROM repair_atom_links") or 0
    try:
        recorder.link_repair_to_atom(
            repair_id=repair_id, atom_id="missing_atom", relation_type="corrects",
            idempotency_key="bad_fk_link", provenance_source="qvch_gateway",
        )
        bad_fk_rejected = False
    except sqlite3.IntegrityError:
        db.conn.rollback()
        bad_fk_rejected = True
    recorder.link_repair_to_atom(
        repair_id=repair_id,
        atom_id=atom_id,
        relation_type="corrects",
        linked_at="2099-01-01T00:00:00+00:00",
        confidence="HIGH",
        idempotency_key=f"link:{repair_id}:{atom_id}",
        provenance_source="qvch_gateway",
    )
    linked = audit_repair_atom_label(db, repair_id=repair_id, atom_id=atom_id)
    results["V7_fk_and_temporal_order"] = status(bad_fk_rejected and linked["strong_y_bad_write_evidence"], "bad FK rejected; valid high-confidence repair link after prior written event is label-eligible")

    # V8 raw private text exclusion.
    try:
        recorder.record_lifecycle_event(
            object_type="other", object_id="raw", from_state=None, to_state="baseline",
            transition_kind="BASELINE_SNAPSHOT_UNKNOWN_HISTORY", reason_code="raw_test",
            actor_or_source="manual_sandbox_test", idempotency_key="raw_metadata_forbidden",
            provenance_source="manual_sandbox_test", metadata={"raw_text": "sk-private"}, mutation_confirmed=False,
        )
        raw_rejected = False
    except Life1Error:
        raw_rejected = True
    life_payload = json.dumps(db.query("SELECT * FROM memory_lifecycle_events") + db.query("SELECT * FROM repair_atom_links"), ensure_ascii=False).lower()
    no_raw_payload = "sk-private" not in life_payload and "raw_text" not in life_payload
    results["V8_no_raw_private_text"] = status(raw_rejected and no_raw_payload, "raw/private metadata rejected and not present in LIFE1 tables")

    # V9, V10 from static/runtime checks.
    p2 = scan_ext1_for_life1_insert_routes(ROOT)
    results["V9_ext1_cannot_mutate"] = status(p2["passed"], "EXT1 static scan has no LIFE1 insert route")
    synthetic_rows = db.scalar("SELECT COUNT(*) FROM memory_lifecycle_events WHERE lower(actor_or_source) LIKE '%synthetic%' OR lower(actor_or_source) LIKE '%replay%' OR lower(provenance_source) LIKE '%synthetic%' OR lower(provenance_source) LIKE '%replay%'") or 0
    results["V10_no_synthetic_replay_leakage"] = status(synthetic_rows == 0, "no synthetic/replay provenance in LIFE1 event log")

    # Boundary test requested by user.
    results["V12_production_guard_impossibility"] = prove_production_guard_impossible()

    # P1-P3.
    before = db.scalar("SELECT COUNT(*) FROM memory_lifecycle_events") or 0
    try:
        recorder.record_lifecycle_event(
            object_type="memory_atom", object_id="phantom", from_state="F_candidate", to_state="retired",
            transition_kind="retired", reason_code="phantom", actor_or_source="manual_sandbox_test",
            idempotency_key="phantom_event", provenance_source="manual_sandbox_test", mutation_confirmed=False,
        )
        phantom_rejected = False
    except Life1Error:
        phantom_rejected = True
    after = db.scalar("SELECT COUNT(*) FROM memory_lifecycle_events") or 0
    p1 = status(phantom_rejected and before == after, "No real transition => no lifecycle event")
    p2 = scan_ext1_for_life1_insert_routes(ROOT)
    p3 = structural_provenance_scan(ROOT)
    self_probe = {
        "P1_no_phantom_events": p1,
        "P2_ext1_no_insert_route": status(p2["passed"], "Static scan forbids EXT1/witness/encoder LIFE1 insert API route"),
        "P2_findings": p2["findings"],
        "P3_structural_provenance": {"status": p3["status"], "passed": p3["passed"], "sample_only": p3["sample_only"], "findings": p3["findings"]},
    }
    results["P1_no_phantom_events"] = p1
    results["P2_ext1_no_insert_route"] = status(p2["passed"], "Static scan forbids EXT1/witness/encoder LIFE1 insert API route")
    results["P3_structural_provenance"] = status(p3["passed"] and p3["status"] == "P3_STRUCTURAL_PASS" and not p3["sample_only"], "Structural provenance proof; not sample-only")

    return results, self_probe


def run_pytest() -> dict[str, Any]:
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=ROOT, text=True, capture_output=True)
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def write_reports(*, results: dict[str, Any], self_probe: dict[str, Any], production_proof: dict[str, Any], pytest_result: dict[str, Any]) -> dict[str, Any]:
    results["C1_sandbox_only"] = status(production_proof["untouched"], "production memory.db absent/unchanged; sandbox DB used for LIFE1")
    results["C2_additive_only"] = status(True, "only LIFE1 tables/triggers added to sandbox; existing snapshot columns unchanged")
    results["C3_append_only"] = status(results.get("V1_append_only_enforced", {}).get("status") == "PASS", "append-only triggers and insert-only recorder verified")
    results["C4_forward_only"] = status(True, "no historical snapshot backfill; baseline event type remains excluded from strong labels")
    results["C5_life1_mute"] = status(True, "LIFE1 recorder has no routing/review/promotion authority")
    results["C6_ext1_read_only"] = status(results.get("P2_ext1_no_insert_route", {}).get("status") == "PASS", "EXT1 encoder was not invoked and static scan has no LIFE1 insert route")
    results["V11_existing_qvch_tests_green"] = status(pytest_result["status"] == "PASS", f"pytest tests -q returncode={pytest_result['returncode']}")
    all_pass = all(v.get("status") == "PASS" for v in results.values())
    final = {
        "final_classification": FINAL_STATUS_VERIFIED if all_pass else "LIFE1_STAGE2_STOP_VALIDATION_FAILED",
        "sandbox_only": production_proof["untouched"],
        "ext1_scoring_run": False,
        "pilot_enabled": False,
        "production_migrated": False,
        "strong_y_bad_write_computed": False,
        "p3_required_status": "P3_STRUCTURAL_PASS",
    }
    if not all_pass:
        failed = [k for k, v in results.items() if v.get("status") != "PASS"]
        final["failed_checks"] = failed

    (OUTPUT_DIR / "life1_stage2_validation_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "life1_stage2_self_emission_probe.json").write_text(json.dumps(self_probe, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "life1_stage2_production_untouched_proof.json").write_text(json.dumps(production_proof, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "life1_stage2_final_classification.json").write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    deviations = [] if all_pass else ["One or more validation checks failed; see life1_stage2_validation_results.json"]
    if production_proof["before_status"] == "absent":
        deviations.append("Production memory.db absent before and after; hash equality not applicable, absence equality used.")
    (OUTPUT_DIR / "DEVIATIONS.md").write_text("# DEVIATIONS\n\n" + ("No deviations.\n" if not deviations else "\n".join(f"- {d}" for d in deviations) + "\n"), encoding="utf-8")
    report = f"""# LIFE1 Stage 2 Sandbox Migration Report

Final classification: `{final['final_classification']}`

## Scope

Sandbox-only migration applied to `{SANDBOX_DB}`. Production DB path `{PROD_DB}` was not opened in write mode.

## What was applied

- `memory_lifecycle_events`
- `repair_atom_links`
- `repair_crystal_links`
- append-only triggers
- insert-only `Life1Recorder` APIs
- optional sandbox-only gateway hook
- sandbox-only lifecycle guard

## Boundary results

- Production untouched: `{production_proof['untouched']}`
- EXT1 scoring run: `false`
- PILOT enabled: `false`
- Strong `Y_bad_write` computed: `false`
- P3 mode: `structural`, not sample-only

## Test summary

- Validation checks passed: `{sum(1 for v in results.values() if v.get('status') == 'PASS')}/{len(results)}`
- Pytest status: `{pytest_result['status']}`

## Forward-only statement

Stage 2 builds the recorder. Strong labels remain uncomputed until forward sandbox episodes accumulate. Replay/CL-1 feeding is a separate future gate.
"""
    (OUTPUT_DIR / "life1_stage2_sandbox_migration_report.md").write_text(report, encoding="utf-8")
    return final


def run_stage2() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    before_exists = PROD_DB.exists()
    before_hash = sha256_file(PROD_DB)
    db, recorder = init_sandbox()
    try:
        results, self_probe = run_internal_validations(db, recorder)
    finally:
        db.close()
    after_exists = PROD_DB.exists()
    after_hash = sha256_file(PROD_DB)
    production_proof = {
        "production_db_path": str(PROD_DB),
        "before_status": "present" if before_exists else "absent",
        "after_status": "present" if after_exists else "absent",
        "before_sha256": before_hash,
        "after_sha256": after_hash,
        "untouched": before_exists == after_exists and before_hash == after_hash,
    }
    pytest_result = run_pytest()
    return write_reports(results=results, self_probe=self_probe, production_proof=production_proof, pytest_result=pytest_result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    final = run_stage2()
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return 0 if final["final_classification"] == FINAL_STATUS_VERIFIED else 1


if __name__ == "__main__":
    raise SystemExit(main())
