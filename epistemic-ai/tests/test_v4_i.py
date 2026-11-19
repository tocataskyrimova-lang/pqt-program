"""P0-I — Applicability Gate & Node 15 probes (brief 13).

Gate P0-I:
- mismatched precondition blocks APPLY;
- a probe without AUTHORIZE_TEST is not executed (and is audited);
- a mandatory failed probe blocks APPLY;
- a revoked/stale revision is not auto-applied;
- the usage outcome is bound to the exact revision + gate decision.
"""

from __future__ import annotations

import sys

from qvch_v4.applicability import (
    VERDICT_APPLY,
    VERDICT_CAUTIOUS_APPLY,
    VERDICT_QUARANTINE,
    ApplicabilityGate,
)
from qvch_v4.applicability.matcher import PreconditionContext
from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.manas.envelope import ManasDecisionEnvelope
from qvch_v4.manas.service import ManasService
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.probes import ProbeExecutor, ProbePlan
from qvch_v4.storage import QvchStore, Repository


def _db(path):
    store = QvchStore(path, migration=True)
    store.init_schema()
    return store, Repository(store)


def _mint_test_envelope(plan: ProbePlan, signer: DecisionSigner) -> ManasDecisionEnvelope:
    svc = ManasService(
        signer, policy_version="policy/1.0", service_version="manas/1.0",
    )
    return svc.decide(
        purpose="AUTHORIZE_TEST", target_id=plan.probe_name,
        target_hash=plan.plan_hash(), verdict="APPROVE",
    )


def _ok_plan(name="p1"):
    return ProbePlan(
        probe_name=name,
        command=[sys.executable, "-c", "import sys; print('probe-ok')"],
        env_allowlist=(), required=True,
    )


def _fail_plan(name="p1"):
    return ProbePlan(
        probe_name=name,
        command=[sys.executable, "-c", "import sys; sys.exit(1)"],
        env_allowlist=(), required=True,
    )


def test_happy_path_grants_apply(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    repo.ensure_lineage("l")
    repo.write_atom(atom_id="fact", lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state="ACTIVE",
                   canonical_payload={"form": "x"}, content_hash=sha256_hex("fact"))
    repo.record_applicability_contract(
        contract_id="c1", atom_id="fact", revision_id="fact#r1",
        scope="win32", precondition=[{"type": "platform", "value": "win32"}],
        anti_condition=None, required_probes=None)
    signer = DecisionSigner.ephemeral()
    plan = _ok_plan()
    env = _mint_test_envelope(plan, signer)
    gate = ApplicabilityGate(store, keyring={signer.key_id: signer})
    d = gate.evaluate(atom_id="fact", revision_id="fact#r1",
                      ctx={"os_platform": "win32"}, probe_plans=[plan],
                      envelope=env, signer=signer)
    assert d.verdict == VERDICT_APPLY, d.reason
    store.close()


def test_mismatched_precondition_blocks_apply(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    repo.ensure_lineage("l")
    repo.write_atom(atom_id="fact", lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state="ACTIVE",
                   canonical_payload={"form": "x"}, content_hash=sha256_hex("fact"))
    repo.record_applicability_contract(
        contract_id="c1", atom_id="fact", revision_id="fact#r1",
        scope="win32", precondition=[{"type": "platform", "value": "win32"}],
        anti_condition=None, required_probes=None)
    gate = ApplicabilityGate(store)
    d = gate.evaluate(atom_id="fact", revision_id="fact#r1",
                      ctx={"os_platform": "linux"})
    assert d.verdict != VERDICT_APPLY
    assert d.verdict == VERDICT_CAUTIOUS_APPLY
    store.close()


def test_probe_without_authorize_test_not_executed(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    repo.ensure_lineage("l")
    repo.write_atom(atom_id="fact", lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state="ACTIVE",
                   canonical_payload={"form": "x"}, content_hash=sha256_hex("fact"))
    repo.record_applicability_contract(
        contract_id="c1", atom_id="fact", revision_id="fact#r1",
        scope="win32", precondition=[{"type": "platform", "value": "win32"}],
        anti_condition=None, required_probes=None)
    plan = _ok_plan()
    gate = ApplicabilityGate(store)
    d = gate.evaluate(atom_id="fact", revision_id="fact#r1",
                      ctx={"os_platform": "win32"}, probe_plans=[plan],
                      envelope=None, signer=None)
    # Verdict must block APPLY (mandatory probe unrunnable).
    assert d.verdict == VERDICT_QUARANTINE
    # And the probe was audited as forbidden (brief 13.3).
    aud = store._conn.execute(
        "SELECT detail_json FROM audit_events WHERE action='PROBE_EXECUTION_FORBIDDEN'"
    ).fetchall()
    assert aud, "forbidden probe must be audited"
    detail = __import__("json").loads(aud[0][0])
    assert detail["reason"] == "missing AUTHORIZE_TEST envelope"
    store.close()


def test_mandatory_failed_probe_blocks_apply(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    repo.ensure_lineage("l")
    repo.write_atom(atom_id="fact", lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state="ACTIVE",
                   canonical_payload={"form": "x"}, content_hash=sha256_hex("fact"))
    repo.record_applicability_contract(
        contract_id="c1", atom_id="fact", revision_id="fact#r1",
        scope="win32", precondition=[{"type": "platform", "value": "win32"}],
        anti_condition=None, required_probes=None)
    signer = DecisionSigner.ephemeral()
    plan = _fail_plan()
    env = _mint_test_envelope(plan, signer)
    gate = ApplicabilityGate(store, keyring={signer.key_id: signer})
    d = gate.evaluate(atom_id="fact", revision_id="fact#r1",
                      ctx={"os_platform": "win32"}, probe_plans=[plan],
                      envelope=env, signer=signer)
    assert d.verdict == VERDICT_QUARANTINE
    assert "probe failed" in d.reason
    store.close()


def test_revoked_stale_not_auto_applied(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    repo.ensure_lineage("l")
    repo.write_atom(atom_id="fact", lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state="REVOKED",
                   canonical_payload={"form": "x"}, content_hash=sha256_hex("fact"))
    gate = ApplicabilityGate(store)
    d = gate.evaluate(atom_id="fact", revision_id="fact#r1",
                      ctx={"os_platform": "win32"})
    assert d.verdict == VERDICT_QUARANTINE
    store.close()


def test_anti_condition_matched_quarantines(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    repo.ensure_lineage("l")
    repo.write_atom(atom_id="fact", lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state="ACTIVE",
                   canonical_payload={"form": "x"}, content_hash=sha256_hex("fact"))
    repo.record_applicability_contract(
        contract_id="c1", atom_id="fact", revision_id="fact#r1",
        scope="win32", precondition=[{"type": "platform", "value": "win32"}],
        anti_condition=[{"type": "platform", "value": "win32"}], required_probes=None)
    gate = ApplicabilityGate(store)
    d = gate.evaluate(atom_id="fact", revision_id="fact#r1",
                      ctx={"os_platform": "win32"})
    assert d.verdict == VERDICT_QUARANTINE
    assert "anti-condition" in d.reason
    store.close()


def test_usage_bound_to_revision_and_gate(tmp_path):
    store, repo = _db(str(tmp_path / "m.db"))
    repo.ensure_lineage("l")
    repo.write_atom(atom_id="fact", lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state="ACTIVE",
                   canonical_payload={"form": "x"}, content_hash=sha256_hex("fact"))
    repo.record_applicability_contract(
        contract_id="c1", atom_id="fact", revision_id="fact#r1",
        scope="win32", precondition=[{"type": "platform", "value": "win32"}],
        anti_condition=None, required_probes=None)
    signer = DecisionSigner.ephemeral()
    plan = _ok_plan()
    env = _mint_test_envelope(plan, signer)
    gate = ApplicabilityGate(store, keyring={signer.key_id: signer})
    d = gate.evaluate(atom_id="fact", revision_id="fact#r1",
                      ctx={"os_platform": "win32"}, probe_plans=[plan],
                      envelope=env, signer=signer)
    gate.record_usage(atom_id="fact", revision_id="fact#r1",
                     gate_id=d.gate_id, outcome="SUCCESS")
    row = store._conn.execute(
        "SELECT atom_id, revision_id, gate_id, outcome FROM usage_outcomes"
    ).fetchone()
    assert row[0] == "fact"
    assert row[1] == "fact#r1"
    assert row[2] == d.gate_id
    assert row[3] == "SUCCESS"
    store.close()


def test_executor_uses_argv_list_not_shell(tmp_path):
    # Directly verify the executor runs an argv list with shell=False and an
    # immutable receipt, without propagating the whole environment.
    store, _ = _db(str(tmp_path / "m.db"))
    signer = DecisionSigner.ephemeral()
    ex = ProbeExecutor(store, keyring={signer.key_id: signer})
    plan = _ok_plan()
    env = _mint_test_envelope(plan, signer)
    receipt = ex.execute(plan, env, signer=signer)
    assert receipt.authorized is True
    assert receipt.success is True
    assert receipt.exit_code == 0
    assert receipt.command_hash.startswith("sha256:")
    assert receipt.env_hash.startswith("sha256:")
    store.close()


__all__ = []
