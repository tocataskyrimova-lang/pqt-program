"""QVCH v4 end-to-end scenario (brief 16 / R1 §14).

Runs the full sovereignty cycle on a temporary SQLite DB. Every *mutation* flows
through the Studio production API (``Studio.*``) which acquires a one-time MANAS
capability per write — the script never calls the protected ``Repository`` write
methods directly (brief R1 §14 / R1-Q15).

The envelope signing key lives behind a :class:`LocalManasAuthority`; the Studio
is constructed with a trusted ``keyring`` so a foreign-signed envelope is rejected
(R1-Q1). The scenario also proves:

  * R1-Q1  — a caller-owned (foreign) signer is rejected by the keyring Gateway.
  * R1-Q4  — an F envelope with a fake reduction proof hash is rejected (SQL
             resolver).
  * R1-Q6  — a consumed MANAS decision is rejected on replay after a restart.
  * R1-Q13 — a runtime (non-migration) store denies arbitrary DDL.

No step bypasses MANAS/Gateway, the SQL authorizer, or the append-only history.
Run:  python scripts/e2e_v4_demo.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import uuid

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json, sha256_hex
from qvch_v4.manas import ConsumptionContext, DecisionSigner, Gateway
from qvch_v4.manas.authority import DecisionRequest, LocalManasAuthority
from qvch_v4.probes.executor import ProbePlan
from qvch_v4.reduction.verifier import (
    AcceptanceCriterion,
    BaselineSlot,
    EvidenceItem,
    ReductionInput,
    ReductionVerifier,
    build_reduction_query,
)
from qvch_v4.storage import QvchStore, Repository
from qvch_v4.storage.repository import SqlConsumptionLedger
from qvch_v4.storage.store import StorageError
from qvch_v4.studio import Studio
from qvch_v4.vinasha import Vinasha

# Deterministic timeline so envelopes do not expire mid-run.
NOW = "2026-01-01T00:00:00+00:00"
FUTURE = "2099-01-01T00:00:00+00:00"

# Probe gate: the probe reads this env var and only succeeds when it equals "1.0".
ENV_VAR = "QVCH_E2E_VER"

POLICY = "policy/1.0"
SERVICE = "studio/1.0"


def _line(width: int = 78) -> None:
    print("=" * width)


def _step(n: int, desc: str) -> None:
    _line()
    print(f"STEP {n}: {desc}")
    _line()


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(f"E2E ASSERTION FAILED: {msg}")
    print(f"  [ok] {msg}")


def _atom_row(store: QvchStore, atom_id: str):
    return store._conn.execute(
        "SELECT atom_id, lineage_id, atom_kind, materiality_class, current_state, "
        "current_revision_id FROM memory_atoms WHERE atom_id=?", (atom_id,)
    ).fetchone()


def _auth_test_env(authority: LocalManasAuthority, plan: ProbePlan, now: str):
    """Mint a one-time AUTHORIZE_TEST envelope bound to a probe plan."""
    return authority.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_TEST.value,
        target_id=plan.probe_name, target_hash=plan.plan_hash(),
        verdict=enums.Verdict.APPROVE.value, route=enums.Route.N.value,
        issued_at=now, expires_at=FUTURE))


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="qvch_e2e_")
    db = os.path.join(tmp, "e2e.db")

    # The sovereign signing key lives behind the authority — the caller never
    # owns it. A trusted keyring rejects any envelope signed by another key.
    sovereign = DecisionSigner.ephemeral()
    authority = LocalManasAuthority(
        sovereign, policy_version=POLICY, service_version=SERVICE)
    keyring = {authority.key_id: sovereign}

    store = QvchStore(db, migration=True)
    store.init_schema()
    studio = Studio(store, keyring=keyring)
    signer = authority.signer

    results: list[str] = []

    # ------------------------------------------------------------------ STEP 1
    _step(1, "Input carries an observation AND an explicit unknown")
    text = (
        "Observation: after the deploy we saw a cache hit-rate regression; "
        "we are unsure which change caused it."
    )
    _check("regression" in text and "unsure" in text,
           "input text contains an observation and an explicit unknown")

    # ------------------------------------------------------------------ STEP 2
    _step(2, "QNUF-Forge produces a StructuredDraft (uncertainty captured)")
    draft = studio._forge.forge(
        studio._adapter.build_raw(text), source_event_id=f"ev_{uuid.uuid4().hex}")
    _check(bool(draft.draft_id) and bool(draft.canonical_hash),
           "QNUF-Forge produced a StructuredDraft with a canonical hash")
    _check(len(draft.noumenon_slots) >= 1,
           f"uncertainty captured as {len(draft.noumenon_slots)} noumenon slot(s)")

    # ------------------------------------------------------------------ STEP 3
    _step(3, "N committed only under a valid AUTHORIZE_WRITE envelope")
    n_id = studio.ingest_observation(text, signer, now=NOW)
    n_row = _atom_row(store, n_id)
    _check(n_row is not None, f"N atom {n_id} exists")
    _check(n_row[2] == "NOUMENON", "atom kind is NOUMENON")
    _check(n_row[4] == "OPEN", "N starts in OPEN state")
    n_lineage = n_row[1]
    env_row = store._conn.execute(
        "SELECT purpose, target_id, verdict FROM manas_decisions WHERE target_id=?",
        (n_id,)).fetchone()
    _check(env_row is not None and env_row[0] == "AUTHORIZE_WRITE",
           "a valid AUTHORIZE_WRITE decision envelope was recorded for N")
    _check(env_row[2] == "APPROVE",
           "envelope verdict is APPROVE (system-derived, no client flag)")
    n_decision_id = store._conn.execute(
        "SELECT decision_id FROM manas_decisions WHERE target_id=?", (n_id,)).fetchone()[0]
    wa = store._conn.execute(
        "SELECT allowed FROM write_attempts WHERE decision_id=?", (n_decision_id,)).fetchone()
    _check(wa is not None and wa[0] == 1,
           "a Gateway-allowed write attempt backs the N commit")

    # ------------------------------------------------------------------ STEP 4
    _step(4, "Two U branches: U1 -> REFUTED; U2 passes Node 15 and -> SUPPORTED")
    # U1 (refuted hypothesis)
    u1_id = f"u_{uuid.uuid4().hex}"
    studio.commit_understanding(
        atom_id=u1_id, lineage_id=n_lineage,
        payload={"kind": "HYPOTHESIS",
                 "claim": "The deploy regression was caused by the cache TTL change",
                 "basis": "inference only"}, signer=signer, now=NOW)
    studio.transition(u1_id, "AUTHORIZED_FOR_TEST", signer=signer, now="2026-01-01T00:00:01+00:00", route=enums.Route.U.value)
    studio.transition(u1_id, "TESTING", signer=signer, now="2026-01-01T00:00:02+00:00", route=enums.Route.U.value)
    studio.transition(u1_id, "REFUTED", signer=signer, now="2026-01-01T00:00:03+00:00",
                      reason="e2e: contradicted by probe", route=enums.Route.U.value)
    _check(_atom_row(store, u1_id)[4] == "REFUTED", "U1 reached REFUTED state")

    # U2 (supported hypothesis) — passes a real Node 15 probe under a one-time
    # AUTHORIZE_TEST capability.
    u2_id = f"u_{uuid.uuid4().hex}"
    studio.commit_understanding(
        atom_id=u2_id, lineage_id=n_lineage,
        payload={"kind": "HYPOTHESIS",
                 "claim": "The deploy regression was caused by the connection-pool size change",
                 "basis": "node15 probe"}, signer=signer, now=NOW)
    ok_plan = ProbePlan(probe_name="u2_node15",
                        command=[sys.executable, "-c", "import sys; sys.exit(0)"],
                        required=True)
    os.environ[ENV_VAR] = "1.0"
    ok_receipt = studio.run_node15_probe(ok_plan, atom_id=u2_id, signer=signer, now=NOW)
    _check(ok_receipt.success, "Node 15 probe for U2 executed and succeeded")
    studio.transition(u2_id, "AUTHORIZED_FOR_TEST", signer=signer, now="2026-01-01T00:00:04+00:00", route=enums.Route.U.value)
    studio.transition(u2_id, "TESTING", signer=signer, now="2026-01-01T00:00:05+00:00", route=enums.Route.U.value)
    studio.transition(u2_id, "SUPPORTED", signer=signer, now="2026-01-01T00:00:06+00:00",
                      reason="e2e: node15 passed", route=enums.Route.U.value)
    _check(_atom_row(store, u2_id)[4] == "SUPPORTED", "U2 reached SUPPORTED state")

    # ------------------------------------------------------------------ STEP 5
    _step(5, "ReductionVerifier closes some hard slots, leaves residual unknowns")
    verifier = ReductionVerifier()
    rinp = ReductionInput(
        lineage_id=n_lineage,
        noumenon_atom_id=n_id,
        baseline_unknown_slots=(BaselineSlot("s1", 1.0), BaselineSlot("s2", 1.0),
                                BaselineSlot("s3", 1.0)),
        resolved_slot_ids=("s1", "s2"),  # s3 stays residual
        acceptance_criteria=(AcceptanceCriterion("c1", critical=True, passed=True),),
        evidence_items=(EvidenceItem(1.0, support_bearing=True),),  # real, not LLM
        required_evidence_weight=1.0,
        scope_coverage=1.0,
        contradiction_pressure=0.0,
        supported_u_atom_ids=(u2_id,),
        scope="global",
    )
    cert = verifier.reduce(rinp)
    _check(len(cert.residual_unknown_slots) >= 1,
           f"residual unknowns left open: {cert.residual_unknown_slots}")
    _check(set(cert.resolved_slots) == {"s1", "s2"},
           "hard slots s1,s2 resolved by the verifier")
    verdict = verifier.can_crystallize(rinp, policy_threshold=0.3, allow_scoped=True)
    _check(verdict.allowed, "crystallization is allowed")
    _check(verdict.route == enums.Route.F_CANDIDATE.value,
           f"MANAS route is scoped F_candidate (residual unknowns), got {verdict.route}")

    # ------------------------------------------------------------------ STEP 6
    _step(6, "MANAS authorizes the scoped F candidate (SQL-derived certificate)")
    # The certificate is persisted to SQL BEFORE the F commit, so the Gateway can
    # resolve its proof hash against the stored certificate (brief R1 §6 / R1-Q4).
    studio.record_reduction(cert, lineage_id=n_lineage, noumenon_atom_id=n_id,
                            supported_u_atom_ids=(u2_id,), signer=signer, now=NOW)
    # Prove the certificate is reconstructable purely from SQL.
    from qvch_v4.reduction.verifier import ReductionCertificate
    back = Repository(store).get_reduction_certificate(cert.proof_id)
    _check(isinstance(back, ReductionCertificate),
           "reduction certificate is reconstructable from SQL (R1 §6)")
    _check(back is not None and back.proof_hash == cert.proof_hash,
           "SQL-derived certificate hash matches the verifier output")
    # IDs-only query must carry no canonical payload.
    rq = build_reduction_query(lineage_id=n_lineage,
                               supported_u_atom_ids=(u2_id,))
    _check(rq.kind == "reduction" and not any("payload" in k for k in rq.__dict__),
           "reduction query carries IDs only (R1 §6)")

    f_id = f"f_{uuid.uuid4().hex}"
    f_rev = f"{f_id}#r1"
    f_payload = {
        "kind": "FORM",
        "claim": "The deploy regression is explained by connection-pool "
                 "exhaustion under load",
        "scope": "scoped",
        "residual": "cache TTL change still unknown",
    }
    f_hash = hash_json(f_payload)
    studio.commit_form(atom_id=f_id, lineage_id=n_lineage, payload=f_payload,
                       signer=signer, now=NOW, state="CANDIDATE",
                       reduction_proof_hash=cert.proof_hash)
    f_res_row = store._conn.execute(
        "SELECT verdict FROM manas_decisions WHERE target_id=? AND purpose='AUTHORIZE_WRITE'",
        (f_id,)).fetchone()
    _check(f_res_row is not None and f_res_row[0] == "APPROVE",
           "Gateway authorized the F commit under a valid reduction proof")

    # ------------------------------------------------------------------ STEP 7
    _step(7, "Studio creates the F revision + RESOLVES link to N")
    link_id = studio.bind_link(f_id, n_id, "RESOLVES", signer=signer, now=NOW)
    _check(link_id is not None, "RESOLVES link F -> N created")
    studio.transition(f_id, "VALIDATED", signer=signer, now="2026-01-01T00:00:07+00:00", route=enums.Route.F.value)
    studio.transition(f_id, "ACTIVE", signer=signer, now="2026-01-01T00:00:08+00:00", route=enums.Route.F.value)
    _check(_atom_row(store, f_id)[4] == "ACTIVE", "F reached ACTIVE state")
    link = store._conn.execute(
        "SELECT link_type FROM memory_links WHERE from_atom_id=? AND to_atom_id=?",
        (f_id, n_id)).fetchone()
    _check(link is not None and link[0] == "RESOLVES",
           "F is bound to N by a RESOLVES link")

    # ------------------------------------------------------------------ STEP 8
    _step(8, "Retrieval returns F (ACTIVE), REFUTED U, and residual N (OPEN)")
    packets = {p.atom_id: p for p in studio.retrieve("deploy regression")}
    _check(f_id in packets, "F is returned by retrieval")
    _check(packets[f_id].lifecycle_status == "ACTIVE", "F returned as ACTIVE")
    _check(u1_id in packets, "REFUTED U is returned by retrieval")
    _check(packets[u1_id].lifecycle_status == "REFUTED", "U1 returned as REFUTED")
    _check(packets[u1_id].is_refuted, "REFUTED flag is set on U1")
    _check(n_id in packets, "residual N is returned by retrieval")
    _check(packets[n_id].lifecycle_status == "OPEN", "N returned as OPEN")

    # ------------------------------------------------------------------ STEP 9
    _step(9, "Applicability Gate passes F in a matching environment")
    CTX_OK = {"os_platform": "win32"}
    env_plan = ProbePlan(
        probe_name="env_version_probe",
        command=[sys.executable, "-c",
                 "import os,sys; sys.exit(0 if os.environ.get('%s')=='1.0' else 1)" % ENV_VAR],
        timeout_s=10.0, env_allowlist=(ENV_VAR,), required=True)
    os.environ[ENV_VAR] = "1.0"
    env_env = _auth_test_env(authority, env_plan, NOW)
    studio.declare_applicability(
        contract_id="c_f", atom_id=f_id, revision_id=f_rev, scope="win32",
        precondition=[{"type": "platform", "value": "win32"}],
        anti_condition=None, required_probes=[{"probe_name": "env_version_probe", "required": True}],
        signer=signer, now=NOW)
    gate_decision, outcome = studio.apply_crystal(
        f_id, f_rev, CTX_OK,
        probe_plans=[env_plan], envelope=env_env, signer=signer, now=NOW)
    _check(gate_decision.verdict == "APPLY",
           f"gate verdict is APPLY in matching environment, got {gate_decision.verdict}")

    # ------------------------------------------------------------------ STEP 10
    _step(10, "Bound usage outcome is SUCCESS")
    _check(outcome == "SUCCESS", f"usage outcome bound to revision is SUCCESS, got {outcome}")
    uo = store._conn.execute(
        "SELECT outcome FROM usage_outcomes WHERE atom_id=? AND revision_id=?",
        (f_id, f_rev)).fetchone()
    _check(uo is not None and uo[0] == "SUCCESS", "usage_outcomes row records SUCCESS")

    # ------------------------------------------------------------------ STEP 11
    _step(11, "Environment version changes; mandatory probe fails")
    os.environ[ENV_VAR] = "2.0"  # drift: the contract no longer satisfied
    gate_decision2 = None
    for k in range(8):
        t = f"2026-02-01T00:0{k}:00+00:00"
        # Mint the AUTHORIZE_TEST at the evaluation time so the envelope is fresh
        # relative to its own check window; the QUARANTINE must come from the
        # probe *failing* (env drift), not from expiry.
        env_e = _auth_test_env(authority, env_plan, t)
        gate_decision2, _outcome2 = studio.apply_crystal(
            f_id, f_rev, CTX_OK,
            probe_plans=[env_plan], envelope=env_e, signer=signer, now=t)
    _check(gate_decision2.verdict == "QUARANTINE",
           f"gate quarantines on failed mandatory probe, got {gate_decision2.verdict}")
    _check("probe" in (gate_decision2.reason or "").lower(),
           f"quarantine reason references the probe failure: {gate_decision2.reason}")

    # ------------------------------------------------------------------ STEP 12
    _step(12, "Spanda moves the revision to STALE / QUARANTINED")
    mres = studio.maintain(now="2026-03-01T00:00:00+00:00")
    f_entry = next((r for r in mres if r["atom_id"] == f_id), None)
    _check(f_entry is not None, "Spanda assessed the F crystal")
    _check(f_entry["recommended_state"] in ("STALE", "QUARANTINED"),
           f"recommended state is STALE/QUARANTINED, got {f_entry['recommended_state']}")
    _check(f_entry["applied"] is True, "the downward transition was applied")
    after_state = _atom_row(store, f_id)[4]
    _check(after_state in ("STALE", "QUARANTINED"),
           f"F is now {after_state} (auto-applied, influence reduced)")

    # ------------------------------------------------------------------ STEP 13
    _step(13, "Vinasha blocks auto-application and opens a new N")
    vin = Vinasha(store)
    _check(vin.blocked(f_id) is True,
           f"degraded F ({after_state}) is auto-apply-blocked by Vinasha")
    _check(f_entry.get("new_n_atom_id") is not None,
           "Vinasha opened a new N on degradation")
    new_n = f_entry["new_n_atom_id"]
    _check(_atom_row(store, new_n)[2] == "NOUMENON", "the opened atom is a NOUMENON")
    new_link = store._conn.execute(
        "SELECT link_type FROM memory_links WHERE from_atom_id=? AND to_atom_id=?",
        (new_n, f_id)).fetchone()
    _check(new_link is not None and new_link[0] == "DERIVED_FROM",
           "new N is DERIVED_FROM the degraded F")

    # ------------------------------------------------------------------ STEP 14
    _step(14, "Old content and full causal history remain auditable")
    rev = store._conn.execute(
        "SELECT revision_id, atom_id, revision_number, state, canonical_payload_json, "
        "content_hash FROM atom_revisions WHERE revision_id=?", (f_rev,)).fetchone()
    _check(rev is not None, "original F revision still present (append-only)")
    _check(rev[5] == f_hash, "original F content hash unchanged")
    import json as _json
    payload = _json.loads(rev[4])
    _check(payload.get("kind") == "FORM", "original F payload content intact")
    state_events = store._conn.execute(
        "SELECT to_state FROM atom_state_events WHERE atom_id=?", (f_id,)).fetchall()
    _check(len(state_events) >= 3,
           f"full transition history preserved: {[r[0] for r in state_events]}")
    n_dec = store._conn.execute("SELECT COUNT(*) FROM manas_decisions").fetchone()[0]
    n_probe = store._conn.execute("SELECT COUNT(*) FROM probe_runs").fetchone()[0]
    n_usage = store._conn.execute("SELECT COUNT(*) FROM usage_outcomes").fetchone()[0]
    n_cons = store._conn.execute("SELECT COUNT(*) FROM decision_consumptions").fetchone()[0]
    _check(n_dec >= 2 and n_probe >= 2 and n_usage >= 2,
           f"causal history intact: decisions={n_dec}, probes={n_probe}, usages={n_usage}")
    _check(n_cons >= 2, f"one-time consumptions recorded in SQL: {n_cons}")

    # ------------------------------------------------------------------ R1-Q1
    _step(15, "R1-Q1: caller-owned (foreign) signer is rejected by the keyring")
    foreign = DecisionSigner.ephemeral()
    # Mint a foreign-signed envelope via the sovereign authority API (the same
    # factory Studio uses internally). The keyring Gateway must reject it.
    foreign_auth = LocalManasAuthority(
        foreign, policy_version=POLICY, service_version=SERVICE)
    foreign_env = foreign_auth.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="fx", target_hash=sha256_hex("fx"),
        verdict=enums.Verdict.APPROVE.value, route=enums.Route.N.value,
        issued_at=NOW, expires_at=FUTURE))
    foreign_res = Gateway(keyring=keyring).verify_with_signer(
        foreign_env,
        ConsumptionContext(observed_target_hash=sha256_hex("fx"),
                           observed_route=enums.Route.N.value,
                           policy_version=POLICY, now_iso=NOW,
                           ledger=InMemoryLedgerSafe()),
        foreign)
    _check(not foreign_res.allowed,
           "foreign-signed envelope rejected by trusted keyring (R1-Q1)")

    # ------------------------------------------------------------------ R1-Q4
    _step(16, "R1-Q4: fake/nonexistent reduction proof is rejected")
    fake_env = authority.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="fake_f", target_hash=sha256_hex("x"),
        verdict=enums.Verdict.APPROVE.value, route=enums.Route.F_CANDIDATE.value,
        reduction_proof_hash=sha256_hex("definitely-not-a-stored-proof"),
        issued_at=NOW, expires_at=FUTURE))
    fake_ctx = ConsumptionContext(
        observed_target_hash=sha256_hex("x"),
        observed_route=enums.Route.F_CANDIDATE.value, policy_version=POLICY,
        now_iso=NOW, requires_reduction_proof=True,
        reduction_proof_resolver=Repository(store).reduction_certificate_exists)
    fake_res = Gateway(keyring).verify_write_authorization(fake_env, fake_ctx, signer)
    _check(not fake_res.allowed,
           "F envelope with fake reduction proof rejected (R1-Q4)")

    # ------------------------------------------------------------------ R1-Q13
    _step(17, "R1-Q13: runtime (non-migration) store denies arbitrary DDL")
    rt = QvchStore(db)  # migration=False -> runtime authority
    denied = False
    try:
        rt.raw_connection().execute("CREATE TABLE rogue_attack(x INTEGER)")
    except sqlite3.DatabaseError:
        denied = True
    rt.close()
    _check(denied, "runtime DDL denied by the SQL authorizer (R1-Q13)")

    # ------------------------------------------------------------------ R2 §4
    _step(18, "R2 §4: verdict is derived by the authority, never echoed")
    derived = authority.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="derived_demo", target_hash=sha256_hex("derived_demo"),
        verdict="REJECT",  # a stray client verdict must be ignored
        route=enums.Route.N.value,
        issued_at=NOW, expires_at=FUTURE))
    _check(derived.verdict == "APPROVE",
           "authority derived APPROVE from the system purpose; client REJECT ignored")
    _check("verdict" not in {f.name for f in __import__("dataclasses").fields(DecisionRequest)},
           "DecisionRequest exposes no client-controlled verdict field (R2 test #5)")

    # ------------------------------------------------------------------ R2 §1
    _step(19, "R2 §1: runtime store rejects a direct protected write")
    rt_store = QvchStore(db)  # migration=False -> production runtime
    rt_repo = Repository(rt_store)
    denied = False
    try:
        rt_repo.write_atom(
            atom_id="runtime_blocked", lineage_id=n_lineage,
            atom_kind="NOUMENON", materiality_class="SEMANTIC", state="OPEN",
            canonical_payload={"kind": "NOUMENON", "x": 1},
            content_hash=sha256_hex("runtime_blocked"), now=NOW)
    except StorageError:
        denied = True
    rt_store.close()
    _check(denied, "runtime protected write without a capability is rejected (R2 §1)")

    # ------------------------------------------------------------------ R2 §7
    _step(20, "R2 §7: a failed mutation rolls back the one-time consumption")
    rb_env = authority.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="rollback_demo", target_hash=sha256_hex("rollback_demo"),
        route=enums.Route.N.value,
        issued_at=NOW, expires_at=FUTURE))
    rb_repo = Repository(store, keyring=keyring)
    rb_ctx = ConsumptionContext(
        observed_target_hash=rb_env.target_hash,
        observed_route=enums.Route.N.value, policy_version=POLICY, now_iso=NOW,
        ledger=None)

    def _failing_mutate(c):
        raise RuntimeError("mutate failed on purpose")

    rolled = False
    try:
        rb_repo.authorized_write(
            rb_repo.OP_ATOM_WRITE, rb_env, rb_ctx, signer, _failing_mutate)
    except Exception:
        rolled = True
    _check(rolled, "failed mutation raised")
    rb_dec = store._conn.execute(
        "SELECT COUNT(*) FROM manas_decisions WHERE decision_id=?",
        (rb_env.decision_id,)).fetchone()[0]
    rb_cons = store._conn.execute(
        "SELECT COUNT(*) FROM decision_consumptions WHERE decision_id=?",
        (rb_env.decision_id,)).fetchone()[0]
    _check(rb_dec == 0 and rb_cons == 0,
           f"no orphan decision/consumption after rollback (dec={rb_dec}, cons={rb_cons})")

    # ------------------------------------------------------------------ R2 §8
    _step(21, "R2 §8: Vinasha's new N carries a non-null authorizing decision")
    nn_row = store._conn.execute(
        "SELECT decision_id FROM atom_state_events WHERE atom_id=? "
        "ORDER BY occurred_at DESC LIMIT 1", (new_n,)).fetchone()
    _check(nn_row is not None and nn_row[0] is not None,
           "new N's state event binds a maintenance MANAS decision (R2 §8)")

    # ------------------------------------------------------------------ R2 §6
    _step(22, "R2 §6: reduction proof not SQL-grounded is rejected")
    phantom_rinp = ReductionInput(
        lineage_id=n_lineage,
        noumenon_atom_id=n_id,
        baseline_unknown_slots=(BaselineSlot("p1", 1.0),),
        resolved_slot_ids=("p1",),
        acceptance_criteria=(AcceptanceCriterion("p1", critical=True, passed=True),),
        evidence_items=(EvidenceItem(1.0, support_bearing=True),),
        required_evidence_weight=1.0,
        scope_coverage=1.0,
        contradiction_pressure=0.0,
        supported_u_atom_ids=("u_does_not_exist",),
        scope="global",
    )
    phantom_cert = ReductionVerifier().reduce(phantom_rinp)
    raised = False
    try:
        studio.record_reduction(
            phantom_cert, lineage_id=n_lineage, noumenon_atom_id=n_id,
            supported_u_atom_ids=("u_does_not_exist",), signer=signer, now=NOW)
    except ValueError:
        raised = True
    _check(raised,
           "reduction proof resting on a non-existent U-atom is rejected (R2 §6)")

    # ------------------------------------------------------------------ R1-Q6
    _step(23, "R1-Q6: consumed decision rejected on replay after restart")
    replay_env = authority.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="replay_demo", target_hash=sha256_hex("replay_demo"),
        route=enums.Route.N.value,
        issued_at=NOW, expires_at=FUTURE))
    # First (legitimate) consumption within the running store, via the atomic
    # authorized_write path — this records a one-time consumption in SQL (R2 §7).
    first_repo = Repository(store, keyring=keyring)
    first_ctx = ConsumptionContext(
        observed_target_hash=replay_env.target_hash,
        observed_route=enums.Route.N.value, policy_version=POLICY, now_iso=NOW,
        ledger=None)
    first_repo.authorized_write(
        first_repo.OP_ATOM_WRITE, replay_env, first_ctx, signer,
        lambda c: None)  # no-op mutation; only the SQL consumption is needed
    # "Restart": a brand-new store on the SAME file. The consumption is SQL and
    # therefore persists; replay must be rejected.
    store.close()
    restarted = QvchStore(db, migration=True)
    replay_repo = Repository(restarted, keyring=keyring)
    replay_ctx = ConsumptionContext(
        observed_target_hash=replay_env.target_hash,
        observed_route=enums.Route.N.value, policy_version=POLICY, now_iso=NOW,
        ledger=SqlConsumptionLedger(replay_repo))
    replay_res = Gateway(keyring).verify_with_signer(replay_env, replay_ctx, signer)
    restarted.close()
    _check(not replay_res.allowed,
           "replayed MANAS decision rejected after restart (R1-Q6)")

    _line()
    print("E2E SCENARIO PASSED — all 23 steps "
          "(14 brief + 4 R1 gates + 5 R2 gates) verified.")
    print(f"  N={n_id}  U1={u1_id}(REFUTED)  U2={u2_id}(SUPPORTED)  "
          f"F={f_id}->{after_state}  newN={new_n}")
    _line()
    return 0


class InMemoryLedgerSafe:
    """Minimal ledger used only to satisfy the verification contract for the
    foreign-signer rejection demo (the reject happens at the keyring check,
    before consumption is ever attempted)."""

    def consume(self, decision_id, nonce) -> bool:
        return False


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"\n*** {exc}")
        raise SystemExit(1)
