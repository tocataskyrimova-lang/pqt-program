from __future__ import annotations

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from qvch_v3.contracts.models import EvidenceRef, RawExperience, new_id
from qvch_v3.core.normalizer import normalize_experience
from qvch_v3.core.planner import build_repair_plan, build_write_plan
from qvch_v3.core.structurer import structure_event
from qvch_v3.life1.constants import PRODUCTION_DB_PATH
from qvch_v3.life1.labels import audit_repair_atom_label
from qvch_v3.life1.probes import scan_ext1_for_life1_insert_routes, structural_provenance_scan
from qvch_v3.life1.recorder import Life1Error, Life1Recorder
from qvch_v3.manas.review import review_draft
from qvch_v3.manas.validation import validate_candidate
from qvch_v3.safety.scanner import scan_event
from qvch_v3.storage.db import QVCHDatabase
from qvch_v3.storage.gateway import MemoryWriteGateway

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def life1_db(tmp_path):
    sandbox = tmp_path / "memory_sandbox.db"
    db = QVCHDatabase(sandbox)
    db.init_schema()
    recorder = Life1Recorder(db, sandbox_path=sandbox, production_path=Path(PRODUCTION_DB_PATH))
    recorder.apply_schema()
    recorder.enable_sandbox_guard()
    yield db, recorder, sandbox
    db.close()


def _plan(text: str, *, evidence=None):
    event = normalize_experience(RawExperience(text))
    safety = scan_event(event)
    draft = structure_event(event)
    manas = review_draft(draft, has_evidence=bool(evidence))
    validation = validate_candidate(evidence_refs=evidence or [])
    return build_write_plan(event=event, draft=draft, manas_review=manas, safety_review=safety, validation=validation)


def test_life1_guard_cannot_enable_on_production_path_without_opening_db(tmp_path):
    fake = object.__new__(QVCHDatabase)
    fake.path = Path(PRODUCTION_DB_PATH)
    with pytest.raises(PermissionError):
        QVCHDatabase.enable_life1_sandbox_guard(fake, sandbox_path=tmp_path / "memory_sandbox.db", production_path=Path(PRODUCTION_DB_PATH))


def test_life1_append_only_and_guard_pairing(life1_db):
    db, recorder, _sandbox = life1_db
    with pytest.raises(PermissionError):
        with db.authorized_write():
            db.execute("INSERT INTO memory_atoms VALUES(?,?,?,?,?,?,?,?,?,?)", ("a", "e", "fact", "F_candidate", "x", "x", 0.1, 0, "{}", "now"))

    recorder.record_lifecycle_event(
        object_type="other",
        object_id="baseline",
        from_state=None,
        to_state="baseline",
        transition_kind="BASELINE_SNAPSHOT_UNKNOWN_HISTORY",
        reason_code="test",
        actor_or_source="manual_sandbox_test",
        idempotency_key="baseline_once",
        provenance_source="manual_sandbox_test",
        mutation_confirmed=False,
    )
    with pytest.raises(sqlite3.DatabaseError):
        with db.authorized_write(), db.life1_transition_context():
            db.execute("UPDATE memory_lifecycle_events SET reason_code='x' WHERE idempotency_key='baseline_once'")
    with pytest.raises(sqlite3.DatabaseError):
        with db.authorized_write(), db.life1_transition_context():
            db.execute("DELETE FROM memory_lifecycle_events WHERE idempotency_key='baseline_once'")


def test_gateway_with_life1_records_forward_atom_event(life1_db):
    db, recorder, _sandbox = life1_db
    ev = EvidenceRef(new_id("ev"), "manual_sandbox_test", "fixture", "confirmed")
    plan = _plan("Execution logs are stored in logs/runtime.", evidence=[ev])
    receipt = MemoryWriteGateway(db, life1_recorder=recorder).commit(plan)
    assert receipt.committed
    atom_id = receipt.object_ids["atom"]
    row = db.one("SELECT transition_kind, provenance_source FROM memory_lifecycle_events WHERE object_type='memory_atom' AND object_id=?", (atom_id,))
    assert row["transition_kind"] == "written"
    assert row["provenance_source"] == "qvch_gateway"


def test_validated_unlinked_repair_is_not_strong_label(life1_db):
    db, recorder, _sandbox = life1_db
    ev = EvidenceRef(new_id("ev"), "manual_sandbox_test", "fixture", "confirmed")
    atom_plan = _plan("Execution logs are stored in logs/runtime.", evidence=[ev])
    atom_receipt = MemoryWriteGateway(db, life1_recorder=recorder).commit(atom_plan)
    atom_id = atom_receipt.object_ids["atom"]

    event = normalize_experience(RawExperience("Repair: logs path correction."))
    repair_plan = build_repair_plan(
        event=event,
        safety_review=scan_event(event),
        bad_answer="wrong path",
        failure_reason="unsupported",
        correction_source="manual_sandbox_test",
        corrected_answer="logs/runtime",
        evidence_refs=[ev],
    )
    repair_plan = replace(repair_plan, repair_pair=replace(repair_plan.repair_pair, validation_status="validated"))
    repair_receipt = MemoryWriteGateway(db, life1_recorder=recorder).commit(repair_plan)
    repair_id = repair_receipt.object_ids["repair_pair"]

    unlinked = audit_repair_atom_label(db, repair_id=repair_id, atom_id=atom_id)
    assert not unlinked["strong_y_bad_write_evidence"]
    assert "missing_repair_atom_link" in unlinked["reason_codes"]

    recorder.link_repair_to_atom(
        repair_id=repair_id,
        atom_id=atom_id,
        relation_type="corrects",
        linked_at="2099-01-01T00:00:00+00:00",
        confidence="HIGH",
        idempotency_key="repair_atom_link_once",
        provenance_source="qvch_gateway",
    )
    linked = audit_repair_atom_label(db, repair_id=repair_id, atom_id=atom_id)
    assert linked["strong_y_bad_write_evidence"]


def test_life1_rejects_raw_private_metadata(life1_db):
    _db, recorder, _sandbox = life1_db
    with pytest.raises(Life1Error):
        recorder.record_lifecycle_event(
            object_type="other",
            object_id="raw",
            from_state=None,
            to_state="baseline",
            transition_kind="BASELINE_SNAPSHOT_UNKNOWN_HISTORY",
            reason_code="raw",
            actor_or_source="manual_sandbox_test",
            idempotency_key="raw",
            provenance_source="manual_sandbox_test",
            metadata={"raw_text": "sk-secret"},
            mutation_confirmed=False,
        )


def test_self_emission_firewall_static_probes_are_structural():
    p2 = scan_ext1_for_life1_insert_routes(ROOT)
    p3 = structural_provenance_scan(ROOT)
    assert p2["passed"], p2["findings"]
    assert p3["passed"], p3["findings"]
    assert p3["status"] == "P3_STRUCTURAL_PASS"
    assert p3["sample_only"] is False


def test_life1_rejects_api_key_metadata(life1_db):
    db, recorder, _ = life1_db
    with pytest.raises(Life1Error):
        recorder.record_lifecycle_event(
            object_type="other",
            object_id="api_key_test",
            from_state=None,
            to_state="baseline",
            transition_kind="BASELINE_SNAPSHOT_UNKNOWN_HISTORY",
            reason_code="test",
            idempotency_key="api_key_key",
            provenance_source="manual_sandbox_test",
            metadata={"api_key": "x"},
            mutation_confirmed=False,
        )


def test_life1_rejects_secret_in_value(life1_db):
    db, recorder, _ = life1_db
    with pytest.raises(Life1Error):
        recorder.record_lifecycle_event(
            object_type="other",
            object_id="secret_val_test",
            from_state=None,
            to_state="baseline",
            transition_kind="BASELINE_SNAPSHOT_UNKNOWN_HISTORY",
            reason_code="test",
            idempotency_key="secret_val_key",
            provenance_source="manual_sandbox_test",
            metadata={"note": "token=abc123"},
            mutation_confirmed=False,
        )


def test_probes_detect_getattr_and_forbidden_import(tmp_path):
    manas_dir = tmp_path / "qvch_v3" / "manas"
    manas_dir.mkdir(parents=True)
    
    review_file = manas_dir / "review.py"
    review_file.write_text("getattr(r, 'record_lifecycle_event')", encoding="utf-8")
    
    p2 = scan_ext1_for_life1_insert_routes(tmp_path)
    assert not p2["passed"]
    assert any(f["kind"] == "forbidden_getattr" and f["symbol"] == "record_lifecycle_event" for f in p2["findings"])
    
    review_file.write_text("import qvch_v3.life1.recorder", encoding="utf-8")
    p2 = scan_ext1_for_life1_insert_routes(tmp_path)
    assert not p2["passed"]
    assert any(f["kind"] == "forbidden_import" for f in p2["findings"])
    
    review_file.write_text("pass", encoding="utf-8")
    p2 = scan_ext1_for_life1_insert_routes(tmp_path)
    assert p2["passed"]
    assert not p2["findings"]

