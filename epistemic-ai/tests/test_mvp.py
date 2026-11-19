from __future__ import annotations

import pytest

from qvch_v3.contracts.models import EvidenceRef, ManasReview, RawExperience, ValidationResult, new_id
from qvch_v3.core.normalizer import normalize_experience
from qvch_v3.core.noumenon import open_noumenon_backlog, partially_resolve_noumenon, receive_guidance, resolve_noumenon, revisit_noumenon, transition_noumenon
from qvch_v3.core.planner import build_repair_plan, build_skill_plan, build_write_plan
from qvch_v3.core.structurer import structure_event
from qvch_v3.manas.review import review_draft
from qvch_v3.manas.validation import validate_candidate
from qvch_v3.retrieval.probe import run_memory_probe
from qvch_v3.retrieval.search import retrieve
from qvch_v3.safety.scanner import scan_event
from qvch_v3.storage.db import QVCHDatabase
from qvch_v3.storage.gateway import MemoryWriteGateway


@pytest.fixture()
def db(tmp_path):
    d = QVCHDatabase(tmp_path / "memory.db")
    d.init_schema()
    yield d
    d.close()


def plan_for(text: str, *, evidence=None, llm_confidence=None):
    event = normalize_experience(RawExperience(text))
    safety = scan_event(event)
    draft = structure_event(event, llm_confidence=llm_confidence)
    manas = review_draft(draft, has_evidence=bool(evidence))
    validation = validate_candidate(evidence_refs=evidence or [])
    return build_write_plan(event=event, draft=draft, manas_review=manas, safety_review=safety, validation=validation)


def commit_text(db, text: str, *, evidence=None, llm_confidence=None):
    plan = plan_for(text, evidence=evidence, llm_confidence=llm_confidence)
    receipt = MemoryWriteGateway(db).commit(plan)
    assert receipt.committed
    return plan, receipt


def test_raw_input_cannot_be_written_directly_to_gateway(db):
    with pytest.raises(TypeError):
        MemoryWriteGateway(db).commit("raw text")  # type: ignore[arg-type]


def test_unknown_creates_n_open(db):
    _plan, receipt = commit_text(db, "Where are execution logs stored?")
    n_id = receipt.object_ids["noumenon"]
    row = db.one("SELECT state FROM noumena WHERE n_id=?", (n_id,))
    assert row["state"] == "N_open"


def test_revisited_unknown_creates_transition(db):
    _p, r = commit_text(db, "Where are artifacts stored?")
    tid = revisit_noumenon(db, r.object_ids["noumenon"])
    row = db.one("SELECT to_state FROM noumenon_transitions WHERE transition_id=?", (tid,))
    assert row["to_state"] == "revisited"


def test_guidance_updates_noumenon(db):
    _p, r = commit_text(db, "Where are logs stored?")
    ev = EvidenceRef(new_id("ev"), "user_guidance", "turn2", "Check logs/runtime")
    receive_guidance(db, r.object_ids["noumenon"], ev)
    assert db.one("SELECT state FROM noumena WHERE n_id=?", (r.object_ids["noumenon"],))["state"] == "guidance_received"


def test_partial_answer_is_partially_resolved_not_f(db):
    _p, r = commit_text(db, "Where is the deployment report?")
    ev = EvidenceRef(new_id("ev"), "brain", "b1", "Likely under reports")
    partially_resolve_noumenon(db, r.object_ids["noumenon"], ev)
    assert db.one("SELECT state FROM noumena WHERE n_id=?", (r.object_ids["noumenon"],))["state"] == "partially_resolved"
    assert (db.scalar("SELECT COUNT(*) FROM crystals") or 0) == 0


def test_valid_evidence_resolves_n_to_f_candidate(db):
    _p, r = commit_text(db, "Where are execution logs stored?")
    ev = EvidenceRef(new_id("ev"), "tool_output", "ls", "logs/runtime exists")
    plan, receipt = commit_text(db, "Execution logs are stored in logs/runtime.", evidence=[ev])
    resolve_noumenon(db, r.object_ids["noumenon"], receipt.object_ids["atom"], evidence=ev)
    assert db.one("SELECT state FROM noumena WHERE n_id=?", (r.object_ids["noumenon"],))["state"] == "resolved_to_F_candidate"


def test_crystal_can_link_back_to_resolved_n(db):
    _p, r = commit_text(db, "Where are runtime logs?")
    ev = EvidenceRef(new_id("ev"), "tool_output", "ls", "logs/runtime confirmed")
    event = normalize_experience(RawExperience("Runtime logs are in logs/runtime."))
    safety = scan_event(event)
    draft = structure_event(event)
    manas = ManasReview(new_id("manas"), draft.draft_id, True, "crystal", ["non_llm_evidence"])
    validation = validate_candidate(evidence_refs=[ev])
    plan = build_write_plan(event=event, draft=draft, manas_review=manas, safety_review=safety, validation=validation)
    object.__setattr__(plan.crystal, "resolved_noumenon_ids", [r.object_ids["noumenon"]])
    receipt = MemoryWriteGateway(db).commit(plan)
    assert receipt.committed
    crystal = db.one("SELECT resolved_noumenon_ids_json FROM crystals WHERE crystal_id=?", (receipt.object_ids["crystal"],))
    assert r.object_ids["noumenon"] in crystal["resolved_noumenon_ids_json"]


def test_bad_answer_correction_creates_repair_pair(db):
    event = normalize_experience(RawExperience("Correct bad answer: logs are not in /tmp, they are in logs/runtime."))
    safety = scan_event(event)
    plan = build_repair_plan(event=event, safety_review=safety, bad_answer="logs are in /tmp", failure_reason="wrong_path", correction_source="user", corrected_answer="logs are in logs/runtime")
    receipt = MemoryWriteGateway(db).commit(plan)
    assert receipt.committed
    assert db.scalar("SELECT COUNT(*) FROM repair_pairs") == 1


def test_repair_pair_can_resolve_n(db):
    _p, r = commit_text(db, "Where are execution logs?")
    event = normalize_experience(RawExperience("Repair: logs are in logs/runtime."))
    plan = build_repair_plan(event=event, safety_review=scan_event(event), bad_answer="unknown", failure_reason="missing_context", correction_source="brain", corrected_answer="logs are in logs/runtime", linked_noumenon_ids=[r.object_ids["noumenon"]], evidence_refs=[EvidenceRef(new_id("ev"), "brain", "b1", "corrected")])
    receipt = MemoryWriteGateway(db).commit(plan)
    resolve_noumenon(db, r.object_ids["noumenon"], receipt.object_ids["repair_pair"], target_type="F_candidate")
    assert db.one("SELECT state FROM noumena WHERE n_id=?", (r.object_ids["noumenon"],))["state"] == "resolved_to_F_candidate"


def test_repeated_repairs_create_skill_candidate(db):
    repairs = []
    for i in range(2):
        event = normalize_experience(RawExperience(f"Repair {i}: prefer tool evidence over guess."))
        plan = build_repair_plan(event=event, safety_review=scan_event(event), bad_answer="guess", failure_reason="unsupported", correction_source="brain", corrected_answer="use tool evidence")
        repairs.append(MemoryWriteGateway(db).commit(plan).object_ids["repair_pair"])
    ev = normalize_experience(RawExperience("Skill from repeated repairs"))
    sp = build_skill_plan(event=ev, safety_review=scan_event(ev), trigger_pattern="unsupported local fact", repair_ids=repairs, procedure_summary="Use tool evidence before answering local facts")
    sr = MemoryWriteGateway(db).commit(sp)
    assert sr.committed
    assert db.scalar("SELECT COUNT(*) FROM skill_candidates") == 1


def test_skill_candidate_does_not_become_reflex_without_validation(db):
    ev = normalize_experience(RawExperience("Skill candidate one repair only"))
    sp = build_skill_plan(event=ev, safety_review=scan_event(ev), trigger_pattern="x", repair_ids=["repair_one"], procedure_summary="do x")
    sr = MemoryWriteGateway(db).commit(sp)
    assert sr.committed
    row = db.one("SELECT validation_status, reflex_readiness FROM skill_candidates WHERE skill_id=?", (sr.object_ids["skill_candidate"],))
    assert row["validation_status"] == "skill_candidate"
    assert row["reflex_readiness"] == 0.0


def test_secret_inside_repair_is_redacted(db):
    event = normalize_experience(RawExperience("Correct answer: API key is sk-test-123456 and logs are in logs/runtime."))
    safety = scan_event(event)
    plan = build_repair_plan(event=event, safety_review=safety, bad_answer="bad", failure_reason="secret_leak", correction_source="user", corrected_answer=event.content)
    MemoryWriteGateway(db).commit(plan)
    row = db.one("SELECT corrected_answer FROM repair_pairs")
    assert "sk-test" not in row["corrected_answer"]
    assert "<REDACTED_SECRET>" in row["corrected_answer"]


def test_llm_confidence_alone_cannot_promote_crystal(db):
    event = normalize_experience(RawExperience("Execution logs are stored in logs/runtime."))
    safety = scan_event(event)
    draft = structure_event(event, llm_confidence=0.99)
    manas = ManasReview(new_id("manas"), draft.draft_id, True, "crystal", ["attempted_llm_only"], llm_confidence_is_evidence=False)
    val = ValidationResult(new_id("val"), False, [EvidenceRef(new_id("ev"), "llm_confidence", "gemma", "0.99", is_llm_confidence=True)], reason_codes=["llm_confidence_not_evidence"])
    receipt = MemoryWriteGateway(db).commit(build_write_plan(event=event, draft=draft, manas_review=manas, safety_review=safety, validation=val))
    assert not receipt.committed
    assert "crystal_requires_non_llm_validation_evidence" in receipt.reason_codes


def test_retrieval_returns_status_and_lineage(db):
    _p, r = commit_text(db, "Where is memory.db stored?")
    revisit_noumenon(db, r.object_ids["noumenon"])
    result = retrieve(db, "memory.db")
    assert result.status in {"N_open", "revisited"}
    assert any(x["kind"] == "noumenon_transition" for x in result.lineage)


def test_memory_probe_verifies_usability(db):
    commit_text(db, "Execution logs are stored in logs/runtime.", evidence=[EvidenceRef(new_id("ev"), "tool", "ls", "confirmed")])
    probe = run_memory_probe(db, query="logs/runtime", expected="logs/runtime", expected_status="F_candidate")
    assert probe.passed


def test_gateway_commit_is_atomic_on_failure(db, monkeypatch):
    plan = plan_for("Execution logs are stored in logs/runtime.", evidence=[EvidenceRef(new_id("ev"), "tool", "ls", "confirmed")])
    gateway = MemoryWriteGateway(db)

    def boom(*args, **kwargs):
        raise RuntimeError("forced failure after event insert")

    monkeypatch.setattr(gateway, "_insert_atoms", boom)
    receipt = gateway.commit(plan)
    assert not receipt.committed
    assert "gateway_transaction_rolled_back" in receipt.reason_codes
    assert db.scalar("SELECT COUNT(*) FROM memory_events") == 0
    assert db.scalar("SELECT COUNT(*) FROM write_plans") == 0
    assert db.scalar("SELECT COUNT(*) FROM write_audit") == 1


def test_secret_redacted_in_all_repair_pair_text_fields(db):
    event = normalize_experience(RawExperience("Repair with secret material"))
    safety = scan_event(event)
    plan = build_repair_plan(
        event=event,
        safety_review=safety,
        bad_answer="bad sk-badsecret123",
        failure_reason="password=abc12345 leaked",
        correction_source="token=sourceSecret999",
        corrected_answer="correct sk-correctsecret123",
    )
    receipt = MemoryWriteGateway(db).commit(plan)
    assert receipt.committed
    row = db.one("SELECT bad_answer, failure_reason, correction_source, corrected_answer FROM repair_pairs")
    combined = " ".join(row.values())
    assert "sk-" not in combined
    assert "abc12345" not in combined
    assert "sourceSecret999" not in combined
    assert combined.count("<REDACTED_SECRET>") >= 4


def test_direct_sql_bypass_to_protected_tables_is_blocked(db):
    with pytest.raises(PermissionError):
        db.execute(
            "INSERT INTO memory_events VALUES(?,?,?,?,?,?,?)",
            ("evt_bypass", "dialogue", "user", "raw", "hash", "now", "{}"),
        )
    assert db.scalar("SELECT COUNT(*) FROM memory_events") == 0


def test_duplicate_fact_accumulates_distinct_evidence_without_atom_spam(db):
    ev1 = EvidenceRef(new_id("ev"), "tool", "ls1", "first confirmation")
    ev2 = EvidenceRef(new_id("ev"), "tool", "ls2", "second confirmation")
    commit_text(db, "Execution logs are stored in logs/runtime.", evidence=[ev1])
    commit_text(db, "Execution logs are stored in logs/runtime.", evidence=[ev2])
    assert db.scalar("SELECT COUNT(*) FROM memory_atoms WHERE epistemic_status='F_candidate'") == 1
    atom = db.one("SELECT atom_id, support_count FROM memory_atoms WHERE epistemic_status='F_candidate'")
    assert atom["support_count"] == 2
    assert db.scalar("SELECT COUNT(*) FROM atom_evidence WHERE atom_id=?", (atom["atom_id"],)) == 2


def test_minimal_conflict_detector_blocks_conflicting_f_candidate(db):
    ev1 = EvidenceRef(new_id("ev"), "tool", "ls1", "logs/runtime confirmed")
    ev2 = EvidenceRef(new_id("ev"), "tool", "ls2", "output/logs claimed")
    commit_text(db, "Execution logs are stored in logs/runtime.", evidence=[ev1])
    plan = plan_for("Execution logs are stored in output/logs.", evidence=[ev2])
    receipt = MemoryWriteGateway(db).commit(plan)
    assert not receipt.committed
    assert "conflict_detected" in receipt.reason_codes
    assert db.scalar("SELECT COUNT(*) FROM memory_atoms WHERE epistemic_status='F_candidate'") == 1


def test_end_to_end_demo_script_runs_raw_commit_retrieval_probe(tmp_path):
    from scripts.e2e_demo import run_demo

    report = run_demo(tmp_path / "demo.db")
    assert report["receipt"]["committed"] is True
    assert report["retrieval_status"] == "F_candidate"
    assert report["probe"]["passed"] is True

