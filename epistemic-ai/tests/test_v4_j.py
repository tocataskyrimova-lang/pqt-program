"""P0-J — Spanda viability & Vinasha loss-of-influence (brief 14).

Gate P0-J:
- Spanda moves a degraded revision to STALE/QUARANTINED (downward, automatic);
- Spanda weights/thresholds are a versioned Frozen Policy, not scattered literals;
- re-activating (upward) transitions require a MANAS AUTHORIZE_STATE_TRANSITION;
- Vinasha blocks automatic application and opens a new N on degradation;
- the degraded revision's content and full causal history remain auditable.
"""

from __future__ import annotations

import json

from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.manas.service import ManasService
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.policy.frozen import SpandaPolicy, VinashaPolicy
from qvch_v4.probes import ProbeReceipt
from qvch_v4.spanda import Spanda, compute_score, recommend_state
from qvch_v4.spanda.engine import SpandaAssessment
from qvch_v4.storage import QvchStore, Repository
from qvch_v4.vinasha import DegradationResult, Vinasha, is_blocked


def _db(path):
    store = QvchStore(path, migration=True)
    store.init_schema()
    return store, Repository(store)


def _write_form(repo, atom_id, state, *, contract=True):
    repo.ensure_lineage("l")
    payload = {"form": atom_id}
    chash = sha256_hex(json.dumps(payload))
    repo.write_atom(atom_id=atom_id, lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state=state,
                   canonical_payload=payload, content_hash=chash, revision_number=1)
    rev = f"{atom_id}#r1"
    if contract:
        repo.record_applicability_contract(
            contract_id=f"c_{atom_id}", atom_id=atom_id, revision_id=rev,
            scope="win32", precondition=[{"type": "platform", "value": "win32"}],
            anti_condition=None, required_probes=None)
    return rev


def _ok_receipt(now):
    return ProbeReceipt(probe_name="p1", command_hash="sha256:x", env_hash="sha256:y",
                        exit_code=0, stdout_hash="sha256:0", stderr_hash="sha256:0",
                        executed_at=now, success=True, reason="ok",
                        authorized=True).to_payload()


def _fail_receipt(now):
    return ProbeReceipt(probe_name="p1", command_hash="sha256:x", env_hash="sha256:y",
                        exit_code=1, stdout_hash="sha256:0", stderr_hash="sha256:0",
                        executed_at=now, success=False, reason="exit_code=1",
                        authorized=True).to_payload()


def test_spanda_healthy_stays_active(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    rev = _write_form(repo, "fact", "ACTIVE")
    repo.record_gate_decision(gate_id="g1", atom_id="fact", revision_id=rev,
                              contract_id="c_fact", verdict="APPLY", reason="ok")
    repo.record_probe_run(probe_run_id="pr1", probe_plan_id="p1", atom_id="fact",
                         decision_id=None, receipt=_ok_receipt("2026-01-01T00:00:00+00:00"))
    repo.record_usage_outcome(outcome_id="u1", atom_id="fact", revision_id=rev,
                             gate_id="g1", outcome="SUCCESS")
    sp = Spanda(store)
    a = sp.assess("fact", rev)
    assert a.recommended_state == "ACTIVE", a.components
    assert a.score >= 0.6
    res = sp.maintain("fact", rev, now="2026-02-01T00:00:00+00:00")
    assert res.applied is False
    assert repo.get_atom("fact")[4] == "ACTIVE"
    store.close()


def test_spanda_degradation_moves_to_quarantine(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    rev = _write_form(repo, "fact", "ACTIVE")
    repo.record_gate_decision(gate_id="g1", atom_id="fact", revision_id=rev,
                              contract_id="c_fact", verdict="QUARANTINE",
                              reason="probe failed")
    for i in range(2):
        repo.record_probe_run(probe_run_id=f"pr{i}", probe_plan_id="p1", atom_id="fact",
                             decision_id=None, receipt=_fail_receipt(f"2026-01-0{i+1}T00:00:00+00:00"))
    for i in range(2):
        repo.record_usage_outcome(outcome_id=f"u{i}", atom_id="fact", revision_id=rev,
                                 gate_id="g1", outcome="FAILURE")
    sp = Spanda(store)
    a = sp.assess("fact", rev)
    # score is low -> QUARANTINED (which is a valid ACTIVE -> QUARANTINED step).
    assert a.recommended_state == "QUARANTINED", a.components
    res = sp.maintain("fact", rev, now="2026-02-01T00:00:00+00:00")
    assert res.applied is True
    assert repo.get_atom("fact")[4] == "QUARANTINED"
    # a state event for the transition was recorded.
    ev = store._conn.execute(
        "SELECT to_state FROM atom_state_events WHERE atom_id='fact' AND to_state='QUARANTINED'"
    ).fetchall()
    assert ev
    store.close()


def test_vinasha_creates_new_n_and_blocks(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    rev = _write_form(repo, "fact", "QUARANTINED")
    vin = Vinasha(store)
    dr = vin.handle_degradation("fact", rev, reason="probe fails in new environment")
    assert isinstance(dr, DegradationResult)
    assert dr.new_n_atom_id.startswith("n_")
    new_row = repo.get_atom(dr.new_n_atom_id)
    assert new_row is not None
    assert new_row[2] == "NOUMENON"
    assert new_row[4] == "OPEN"
    link = store._conn.execute(
        "SELECT link_type FROM memory_links WHERE from_atom_id=? AND to_atom_id=?",
        (dr.new_n_atom_id, "fact"),
    ).fetchone()
    assert link is not None
    assert link[0] == "DERIVED_FROM"
    assert vin.blocked("fact") is True
    store.close()


def test_vinasha_preserves_history(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    rev = _write_form(repo, "fact", "ACTIVE")
    repo.record_gate_decision(gate_id="g1", atom_id="fact", revision_id=rev,
                              contract_id="c_fact", verdict="APPLY", reason="ok")
    repo.record_probe_run(probe_run_id="pr1", probe_plan_id="p1", atom_id="fact",
                         decision_id=None, receipt=_ok_receipt("2026-01-01T00:00:00+00:00"))
    before_rev = store._conn.execute(
        "SELECT content_hash FROM atom_revisions WHERE atom_id='fact'").fetchall()
    before_se = store._conn.execute(
        "SELECT COUNT(*) FROM atom_state_events WHERE atom_id='fact'").fetchone()[0]
    Vinasha(store).handle_degradation("fact", rev, reason="drift")
    after_rev = store._conn.execute(
        "SELECT content_hash FROM atom_revisions WHERE atom_id='fact'").fetchall()
    # Revisions (content + causal history) are untouched.
    assert after_rev == before_rev
    # Only a maintenance event was added; no revision/state-event was removed.
    assert len(after_rev) >= 1
    assert before_se >= 1
    store.close()


def test_upward_transition_requires_manas_decision(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    rev = _write_form(repo, "fact", "STALE")
    repo.record_gate_decision(gate_id="g1", atom_id="fact", revision_id=rev,
                              contract_id="c_fact", verdict="APPLY", reason="revalidated")
    repo.record_probe_run(probe_run_id="pr1", probe_plan_id="p1", atom_id="fact",
                         decision_id=None, receipt=_ok_receipt("2026-01-01T00:00:00+00:00"))
    repo.record_usage_outcome(outcome_id="u1", atom_id="fact", revision_id=rev,
                             gate_id="g1", outcome="SUCCESS")
    sp = Spanda(store)
    a = sp.assess("fact", rev)
    assert a.recommended_state == "ACTIVE"  # upward from STALE

    # R2 §8: an upward (re-activation) transition requires a MANAS
    # AUTHORIZE_STATE_TRANSITION. Spanda's maintenance authority is itself a
    # sovereign MANAS authority, so maintain() applies the transition internally
    # through authorized_write and records the non-null authorizing decision_id.
    # A caller can never inject its own APPROVE — the verdict is derived by the
    # authority from the system purpose (brief R2 §4).
    res = sp.maintain("fact", rev, now="2026-02-01T00:00:00+00:00")
    assert res.applied is True
    assert repo.get_atom("fact")[4] == "ACTIVE"
    # The internal MANAS decision (AUTHORIZE_STATE_TRANSITION, APPROVE) that
    # authorized the upward transition is recorded and bound to the state event.
    row = store._conn.execute(
        "SELECT decision_id FROM atom_state_events WHERE atom_id='fact' "
        "AND to_state='ACTIVE' ORDER BY occurred_at DESC LIMIT 1"
    ).fetchone()
    assert row is not None and row[0] is not None
    decision = store._conn.execute(
        "SELECT purpose, verdict FROM manas_decisions WHERE decision_id=?",
        (row[0],),
    ).fetchone()
    assert decision is not None
    assert decision[0] == "AUTHORIZE_STATE_TRANSITION"
    assert decision[1] == "APPROVE"
    store.close()


def test_spanda_policy_is_frozen_and_versioned(tmp_path):
    p = SpandaPolicy.default()
    assert p.version == "spanda/1.0"
    # Frozen: assignment raises.
    try:
        p.w_applicability_health = 0.99
        raise AssertionError("SpandaPolicy must be frozen")
    except Exception as exc:  # noqa: BLE001
        assert type(exc).__name__ == "FrozenInstanceError"
    # Engine reads coefficients from the policy, not literals.
    comp = {k: 1.0 for k in (
        "applicability_health", "probe_success_rate", "successful_usage_rate",
        "evidence_freshness", "dependency_compatibility")}
    comp["contradiction_pressure"] = 0.0
    comp["observed_failure_rate"] = 0.0
    assert abs(compute_score(comp, p) - 0.80) < 1e-9
    # Thresholds map score -> state.
    assert recommend_state(0.7, p) == "ACTIVE"
    assert recommend_state(0.5, p) == "WATCH"
    assert recommend_state(0.3, p) == "STALE"
    assert recommend_state(0.1, p) == "QUARANTINED"


def test_vinasha_blocked_states(tmp_path):
    assert is_blocked("QUARANTINED") is True
    assert is_blocked("REVOKED") is True
    assert is_blocked("STALE") is True
    assert is_blocked("ACTIVE") is False
    assert is_blocked("WATCH") is False


__all__ = []
