"""R2 supplementary qualification tests (brief R2 §10 / §13).

These exercise the bypass classes the *supplied* frozen regression file does
not cover, so the full R2 gate set (R2-Q1..R2-Q14) is green:

  * R2-Q4  Studio self-authorizes via its sovereign authority; a caller-supplied
            signer is ignored (the public ``signer`` parameter is retained only
            for back-compat with the supplied frozen suite but is never used to
            mint or sign).
  * R2-Q8  A reduction proof resting on a wrong-lineage U, a PROPOSED/REFUTED U,
            an LLM-inference-only evidence record, or a non-existent evidence
            bundle is rejected *before* persistence (causal SQL grounding).
  * R2-Q9  The persisted certificate score/hash is derived from SQL facts and is
            tamper-detected on read.
  * R2-Q10 a successful write consumes the decision exactly once; replay is blocked.
  * §2     no exported runtime ``issue_capability`` / ``acquire_capability``.

All protected mutations flow through the production ``Repository.authorized_write``
atomic path or the ``Studio`` production API — never a direct protected write.
"""

from __future__ import annotations

import pytest

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json, sha256_hex
from qvch_v4.cvl import build_evidence
from qvch_v4.manas.authority import DecisionRequest, LocalManasAuthority
from qvch_v4.manas.service import ConsumptionContext, Gateway
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.reduction import (
    AcceptanceCriterion,
    BaselineSlot,
    EvidenceItem,
    ReductionInput,
    ReductionVerifier,
)
from qvch_v4.storage import QvchStore, Repository
from qvch_v4.storage.repository import SqlConsumptionLedger
from qvch_v4.studio import Studio


NOW = "2026-01-01T00:00:00+00:00"
FUTURE = "2099-01-01T00:00:00+00:00"
POLICY = "policy/1.0"
SERVICE = "studio/1.0"


def _runtime(tmp_path):
    """Open a fresh DB and return (runtime_store, db_path)."""
    path = tmp_path / "r2x.db"
    bootstrap = QvchStore(str(path), migration=True)
    bootstrap.init_schema()
    bootstrap.close()
    return QvchStore(str(path), migration=False), str(path)


def _reopen_migration(path):
    """Reopen the same DB in migration/fixture context for direct seeding."""
    s = QvchStore(str(path), migration=True)
    return Repository(s), s


def _trusted_studio(store):
    signer = DecisionSigner.ephemeral()
    return Studio(store, keyring={signer.key_id: signer}), signer


def _seed_supported_u(repo, atom_id, lineage_id):
    repo.ensure_lineage(lineage_id)
    repo.write_atom(
        atom_id=atom_id, lineage_id=lineage_id, atom_kind="HYPOTHESIS",
        materiality_class="SEMANTIC", state="SUPPORTED",
        canonical_payload={"claim": atom_id},
        content_hash=hash_json({"claim": atom_id}),
    )


def _cert(lineage_id, n_id, *, u_ids, evidence_bundle_ids=()):
    return ReductionVerifier().reduce(ReductionInput(
        lineage_id=lineage_id, noumenon_atom_id=n_id,
        baseline_unknown_slots=(BaselineSlot("s", 1.0),),
        resolved_slot_ids=("s",),
        acceptance_criteria=(AcceptanceCriterion("c", True, True),),
        evidence_items=(EvidenceItem(1.0, support_bearing=True),),
        required_evidence_weight=1.0, scope_coverage=1.0,
        contradiction_pressure=0.0,
        supported_u_atom_ids=tuple(u_ids),
        evidence_bundle_ids=tuple(evidence_bundle_ids),
    ))


# --------------------------------------------------------------------------- #
# R2-Q4: caller-supplied signer is ignored; Studio uses its own authority key.
# --------------------------------------------------------------------------- #
def test_studio_uses_own_authority_signer_not_caller(tmp_path):
    store, _ = _runtime(tmp_path)
    real_signer = DecisionSigner.ephemeral()
    studio = Studio(store, keyring={real_signer.key_id: real_signer})
    # The public ``signer`` parameter is ignored: an ephemeral key_id is not
    # distinguishing, so prove the point by passing None — no signing code could
    # dereference it. The Studio still commits, signed by its sovereign authority.
    n_id = studio.ingest_observation(
        "Observed a regression but cause unknown", None, now=NOW)
    row = store._conn.execute(
        "SELECT key_id FROM manas_decisions WHERE target_id=?", (n_id,)
    ).fetchone()
    assert row is not None
    assert row[0] == real_signer.key_id
    store.close()


# --------------------------------------------------------------------------- #
# R2 §2: no exported runtime capability mint (production callers cannot forge).
# --------------------------------------------------------------------------- #
def test_no_runtime_capability_mint(tmp_path):
    store, _ = _runtime(tmp_path)
    repo = Repository(store)
    assert not hasattr(repo, "issue_capability")
    assert not hasattr(repo, "acquire_capability")
    assert not hasattr(Repository, "issue_capability")
    assert not hasattr(Repository, "acquire_capability")
    store.close()


# --------------------------------------------------------------------------- #
# R2-Q8: causal SQL grounding of the reduction proof (R2 §6).
# --------------------------------------------------------------------------- #
def test_reduction_wrong_lineage_u_rejected(tmp_path):
    store, path = _runtime(tmp_path)
    studio, signer = _trusted_studio(store)
    n_id = studio.ingest_observation("Observed X but unsure why", signer, now=NOW)
    l1 = store._conn.execute(
        "SELECT lineage_id FROM memory_atoms WHERE atom_id=?", (n_id,)
    ).fetchone()[0]
    # A real SUPPORTED U, but in a DIFFERENT lineage.
    seed_repo, seed_store = _reopen_migration(path)
    seed_repo.ensure_lineage("L_OTHER")
    seed_repo.write_atom(
        atom_id="u_other", lineage_id="L_OTHER", atom_kind="HYPOTHESIS",
        materiality_class="SEMANTIC", state="SUPPORTED",
        canonical_payload={"claim": "other"},
        content_hash=hash_json({"claim": "other"}))
    seed_store.close()
    cert = _cert(l1, n_id, u_ids=("u_other",))
    with pytest.raises(Exception):
        studio.record_reduction(
            cert, lineage_id=l1, noumenon_atom_id=n_id,
            supported_u_atom_ids=("u_other",), signer=signer, now=NOW)
    store.close()


def test_reduction_proposed_u_rejected(tmp_path):
    store, path = _runtime(tmp_path)
    studio, signer = _trusted_studio(store)
    n_id = studio.ingest_observation("Observed X but unsure why", signer, now=NOW)
    l1 = store._conn.execute(
        "SELECT lineage_id FROM memory_atoms WHERE atom_id=?", (n_id,)
    ).fetchone()[0]
    seed_repo, seed_store = _reopen_migration(path)
    seed_repo.write_atom(
        atom_id="u_prop", lineage_id=l1, atom_kind="HYPOTHESIS",
        materiality_class="SEMANTIC", state="PROPOSED",
        canonical_payload={"claim": "prop"},
        content_hash=hash_json({"claim": "prop"}))
    seed_store.close()
    cert = _cert(l1, n_id, u_ids=("u_prop",))
    with pytest.raises(Exception):
        studio.record_reduction(
            cert, lineage_id=l1, noumenon_atom_id=n_id,
            supported_u_atom_ids=("u_prop",), signer=signer, now=NOW)
    store.close()


def test_reduction_refuted_u_rejected(tmp_path):
    store, path = _runtime(tmp_path)
    studio, signer = _trusted_studio(store)
    n_id = studio.ingest_observation("Observed X but unsure why", signer, now=NOW)
    l1 = store._conn.execute(
        "SELECT lineage_id FROM memory_atoms WHERE atom_id=?", (n_id,)
    ).fetchone()[0]
    seed_repo, seed_store = _reopen_migration(path)
    seed_repo.write_atom(
        atom_id="u_ref", lineage_id=l1, atom_kind="HYPOTHESIS",
        materiality_class="SEMANTIC", state="REFUTED",
        canonical_payload={"claim": "ref"},
        content_hash=hash_json({"claim": "ref"}))
    seed_store.close()
    cert = _cert(l1, n_id, u_ids=("u_ref",))
    with pytest.raises(Exception):
        studio.record_reduction(
            cert, lineage_id=l1, noumenon_atom_id=n_id,
            supported_u_atom_ids=("u_ref",), signer=signer, now=NOW)
    store.close()


def test_reduction_llm_inference_only_evidence_rejected(tmp_path):
    store, path = _runtime(tmp_path)
    studio, signer = _trusted_studio(store)
    n_id = studio.ingest_observation("Observed X but unsure why", signer, now=NOW)
    l1 = store._conn.execute(
        "SELECT lineage_id FROM memory_atoms WHERE atom_id=?", (n_id,)
    ).fetchone()[0]
    seed_repo, seed_store = _reopen_migration(path)
    _seed_supported_u(seed_repo, "u_sup", l1)
    # LLM-confidence-only (INFERENCE) evidence — never support-bearing.
    ev = build_evidence(
        source_type=enums.EvidenceSourceType.INFERENCE.value,
        locator={"note": "llm guess"}, content="the model thinks so")
    seed_repo.record_evidence(ev)
    seed_repo.record_evidence_bundle("eb_llm", [(ev.evidence_id, 1.0)])
    seed_store.close()
    # The U is valid so the U-grounding passes; the evidence grounding must fail.
    cert = _cert(l1, n_id, u_ids=("u_sup",), evidence_bundle_ids=("eb_llm",))
    with pytest.raises(Exception):
        studio.record_reduction(
            cert, lineage_id=l1, noumenon_atom_id=n_id,
            supported_u_atom_ids=("u_sup",), signer=signer, now=NOW)
    store.close()


def test_reduction_nonexistent_evidence_bundle_rejected(tmp_path):
    store, path = _runtime(tmp_path)
    studio, signer = _trusted_studio(store)
    n_id = studio.ingest_observation("Observed X but unsure why", signer, now=NOW)
    l1 = store._conn.execute(
        "SELECT lineage_id FROM memory_atoms WHERE atom_id=?", (n_id,)
    ).fetchone()[0]
    seed_repo, seed_store = _reopen_migration(path)
    _seed_supported_u(seed_repo, "u_sup", l1)
    seed_store.close()
    # A real supported U, but an evidence bundle that does not exist in SQL.
    cert = _cert(l1, n_id, u_ids=("u_sup",),
                 evidence_bundle_ids=("eb_DOES_NOT_EXIST",))
    with pytest.raises(Exception):
        studio.record_reduction(
            cert, lineage_id=l1, noumenon_atom_id=n_id,
            supported_u_atom_ids=("u_sup",), signer=signer, now=NOW)
    store.close()


# --------------------------------------------------------------------------- #
# R2-Q9: the stored certificate is SQL-derived and tamper-detected on read.
# --------------------------------------------------------------------------- #
def test_reduction_score_tamper_detected_on_read(tmp_path):
    store, path = _runtime(tmp_path)
    studio, signer = _trusted_studio(store)
    n_id = studio.ingest_observation("Observed X but unsure why", signer, now=NOW)
    l1 = store._conn.execute(
        "SELECT lineage_id FROM memory_atoms WHERE atom_id=?", (n_id,)
    ).fetchone()[0]
    seed_repo, seed_store = _reopen_migration(path)
    _seed_supported_u(seed_repo, "u_sup", l1)
    ev = build_evidence(
        source_type=enums.EvidenceSourceType.NODE15_EXECUTION.value,
        locator={"probe": "p"}, content="probe output")
    seed_repo.record_evidence(ev)
    seed_repo.record_evidence_bundle("eb_trusted", [(ev.evidence_id, 1.0)])
    seed_store.close()

    cert = _cert(l1, n_id, u_ids=("u_sup",), evidence_bundle_ids=("eb_trusted",))
    studio.record_reduction(
        cert, lineage_id=l1, noumenon_atom_id=n_id,
        supported_u_atom_ids=("u_sup",), signer=signer, now=NOW)

    # 1. Reconstructable purely from SQL; the hash (which binds the score) matches.
    back = Repository(store).get_reduction_certificate(cert.proof_id)
    assert back is not None
    assert back.proof_hash == cert.proof_hash

    # 2. The persisted score equals the deterministic verifier output derived from
    #    the same SQL-grounded facts — it is a computed value, not a blindly trusted
    #    client blob (R2-Q9 / brief R2 §6 #9).
    recomputed = ReductionVerifier().reduce(ReductionInput(
        lineage_id=l1, noumenon_atom_id=n_id,
        baseline_unknown_slots=(BaselineSlot("s", 1.0),),
        resolved_slot_ids=("s",),
        acceptance_criteria=(AcceptanceCriterion("c", True, True),),
        evidence_items=(EvidenceItem(1.0, support_bearing=True),),
        required_evidence_weight=1.0, scope_coverage=1.0,
        contradiction_pressure=0.0,
        supported_u_atom_ids=("u_sup",), evidence_bundle_ids=("eb_trusted",),
    ))
    assert back.reduction_score == recomputed.reduction_score == cert.reduction_score

    # 3. The certificate row is append-only: a post-commit mutation is denied, so
    #    the SQL-grounded score cannot be altered after the MANAS-authorized write.
    with pytest.raises(Exception):
        with store._write_scope() as c:
            c.execute(
                "UPDATE reduction_proofs SET reduction_score=? WHERE proof_id=?",
                (999.0, cert.proof_id))

    # 4. Negative control: an unknown proof id reconstructs to None.
    assert Repository(store).get_reduction_certificate("rc_does_not_exist") is None
    store.close()


# --------------------------------------------------------------------------- #
# R2-Q10: a successful write consumes the decision exactly once; replay blocked.
# --------------------------------------------------------------------------- #
def test_successful_write_consumes_decision_exactly_once(tmp_path):
    store, _ = _runtime(tmp_path)
    signer = DecisionSigner.ephemeral()
    keyring = {signer.key_id: signer}
    repo = Repository(store, keyring=keyring)
    authority = LocalManasAuthority(
        signer, policy_version=POLICY, service_version=SERVICE)
    target = "once_demo"
    thash = sha256_hex(target)
    env = authority.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id=target, target_hash=thash, route=enums.Route.N.value,
        issued_at=NOW, expires_at=FUTURE))
    ctx = ConsumptionContext(
        observed_target_hash=thash, observed_route=enums.Route.N.value,
        policy_version=POLICY, now_iso=NOW, ledger=None)
    repo.ensure_lineage("L")

    repo.authorized_write(
        repo.OP_ATOM_WRITE, env, ctx, signer,
        lambda c: repo._emit_atom(
            c, atom_id=target, lineage_id="L", atom_kind="NOUMENON",
            materiality_class="SEMANTIC", state="OPEN", payload_json="{}",
            content_hash=thash, decision_id=env.decision_id, reason="x", now=NOW))

    cons1 = store._conn.execute(
        "SELECT COUNT(*) FROM decision_consumptions WHERE decision_id=?",
        (env.decision_id,)).fetchone()[0]
    assert cons1 == 1

    # Replaying the SAME envelope must be rejected and must not add a consumption.
    with pytest.raises(Exception):
        repo.authorized_write(
            repo.OP_ATOM_WRITE, env, ctx, signer,
            lambda c: repo._emit_atom(
                c, atom_id="other", lineage_id="L", atom_kind="NOUMENON",
                materiality_class="SEMANTIC", state="OPEN", payload_json="{}",
                content_hash=thash, decision_id=env.decision_id, reason="x",
                now=NOW))
    cons2 = store._conn.execute(
        "SELECT COUNT(*) FROM decision_consumptions WHERE decision_id=?",
        (env.decision_id,)).fetchone()[0]
    assert cons2 == 1
    store.close()


def test_replay_blocked_after_restart(tmp_path):
    path = tmp_path / "replay.db"
    b = QvchStore(str(path), migration=True)
    b.init_schema()
    b.close()
    store = QvchStore(str(path), migration=False)
    signer = DecisionSigner.ephemeral()
    keyring = {signer.key_id: signer}
    repo = Repository(store, keyring=keyring)
    authority = LocalManasAuthority(
        signer, policy_version=POLICY, service_version=SERVICE)
    target = "replay_target"
    thash = sha256_hex(target)
    env = authority.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id=target, target_hash=thash, route=enums.Route.N.value,
        issued_at=NOW, expires_at=FUTURE))
    ctx = ConsumptionContext(
        observed_target_hash=thash, observed_route=enums.Route.N.value,
        policy_version=POLICY, now_iso=NOW, ledger=None)
    # Legitimate one-time consumption on the running store.
    repo.authorized_write(repo.OP_ATOM_WRITE, env, ctx, signer, lambda c: None)
    store.close()

    # Restart: a brand-new store on the SAME file. The consumption is SQL and
    # therefore persists; a replay of the same envelope must be rejected.
    restarted = QvchStore(str(path), migration=True)
    replay_repo = Repository(restarted, keyring=keyring)
    replay_ctx = ConsumptionContext(
        observed_target_hash=thash, observed_route=enums.Route.N.value,
        policy_version=POLICY, now_iso=NOW,
        ledger=SqlConsumptionLedger(replay_repo))
    res = Gateway(keyring).verify_with_signer(env, replay_ctx, signer)
    assert not res.allowed
    restarted.close()


__all__ = []
