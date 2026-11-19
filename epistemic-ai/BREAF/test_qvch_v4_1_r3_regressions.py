"""Independent R3 adversarial regressions for QVCH v4.1.

These tests target trust-anchor, atomic-ingest, unconditional F-proof,
SQL-grounded reduction, maintenance-authority and product-cutover classes that
remain after the claimed R2 closure.
"""
from __future__ import annotations

import inspect
import os
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json, sha256_hex
from qvch_v4.cvl import build_evidence
from qvch_v4.manas.authority import DecisionRequest, LocalManasAuthority
from qvch_v4.manas.service import ConsumptionContext
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.reduction.verifier import (
    AcceptanceCriterion,
    BaselineSlot,
    EvidenceItem,
    ReductionInput,
    ReductionVerifier,
)
from qvch_v4.storage import QvchStore, Repository
from qvch_v4.studio import Studio
from qvch_v4.vinasha import Vinasha

NOW = "2026-07-20T00:00:00+00:00"
FUTURE = "2027-07-20T00:00:00+00:00"
POLICY = "policy/1.0"


def _db(tmp_path, name="r3.db"):
    path = tmp_path / name
    boot = QvchStore(str(path), migration=True)
    boot.init_schema()
    boot.close()
    return QvchStore(str(path), migration=False), path


def _trusted_studio(store):
    signer = DecisionSigner.ephemeral()
    return Studio(store, keyring={signer.key_id: signer}), signer


def _all_text_hits(path: Path, needle: str):
    con = sqlite3.connect(str(path))
    hits = []
    try:
        for (table,) in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ):
            for col in con.execute(f"PRAGMA table_info({table})"):
                name, typ = col[1], (col[2] or "").upper()
                if "TEXT" not in typ:
                    continue
                try:
                    n = con.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE {name} LIKE ?",
                        (f"%{needle}%",),
                    ).fetchone()[0]
                except sqlite3.DatabaseError:
                    continue
                if n:
                    hits.append((table, name, n))
    finally:
        con.close()
    return hits


def test_runtime_caller_cannot_choose_studio_trust_root(tmp_path):
    store, _ = _db(tmp_path)
    attacker = DecisionSigner.ephemeral()
    studio = Studio(store, keyring={attacker.key_id: attacker})
    with pytest.raises(Exception):
        studio.ingest_observation("Observed X; unsure why", attacker, now=NOW)
    store.close()


def test_repository_cannot_self_authorize_with_caller_keyring(tmp_path):
    store, _ = _db(tmp_path)
    attacker = DecisionSigner.ephemeral()
    repo = Repository(store, keyring={attacker.key_id: attacker})
    auth = LocalManasAuthority(
        attacker, policy_version=POLICY, service_version="attacker")
    repo.ensure_lineage("L_ATTACK", root_noumenon_id="f_attack", now=NOW)
    target_hash = sha256_hex("attacker-plan")
    env = auth.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="f_attack", target_hash=target_hash,
        route=enums.Route.F_CANDIDATE.value,
        issued_at=NOW, expires_at=FUTURE,
    ))
    ctx = ConsumptionContext(
        observed_target_hash=target_hash,
        observed_route=enums.Route.F_CANDIDATE.value,
        policy_version=POLICY, now_iso=NOW,
    )
    with pytest.raises(Exception):
        repo.authorized_write(
            repo.OP_ATOM_WRITE, env, ctx, attacker,
            lambda c: repo._emit_atom(
                c, atom_id="f_attack", lineage_id="L_ATTACK",
                atom_kind="FORM", materiality_class="SEMANTIC",
                state="ACTIVE", payload_json="{}", content_hash=target_hash,
                decision_id=env.decision_id, reason="caller self-authorized", now=NOW,
            ),
        )
    store.close()


def test_form_requires_reduction_proof_unconditionally(tmp_path):
    store, _ = _db(tmp_path)
    studio, signer = _trusted_studio(store)
    n_id = studio.ingest_observation("Observed X; unsure why", signer, now=NOW)
    lineage = store._conn.execute(
        "SELECT lineage_id FROM memory_atoms WHERE atom_id=?", (n_id,)
    ).fetchone()[0]
    with pytest.raises(Exception):
        studio.commit_form(
            atom_id="f_without_proof", lineage_id=lineage,
            payload={"core": "unsupported"}, signer=signer,
            now="2026-07-20T00:00:01+00:00", reduction_proof_hash=None,
        )
    assert store._conn.execute(
        "SELECT COUNT(*) FROM memory_atoms WHERE atom_id='f_without_proof'"
    ).fetchone()[0] == 0
    store.close()


def test_failed_ingest_is_atomic_and_leaves_no_secret_or_orphans(tmp_path):
    store, path = _db(tmp_path)
    secret = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9R3FailClosedSecret"
    studio = Studio(store)  # no authority: protected write must fail closed
    with pytest.raises(Exception):
        studio.ingest_observation(f"Config token: {secret}", None, now=NOW)
    for table in (
        "structured_drafts", "claims", "epistemic_lineages", "evidence_refs",
        "memory_atoms", "manas_decisions", "decision_consumptions",
    ):
        assert store._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    store.close()
    assert not _all_text_hits(path, secret)
    assert secret.encode() not in path.read_bytes()


def test_successful_ingest_sanitizes_every_persisted_surface(tmp_path):
    store, path = _db(tmp_path)
    studio, signer = _trusted_studio(store)
    secret = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9R3PersistedSecret"
    studio.ingest_observation(f"Config token: {secret}", signer, now=NOW)
    store.close()
    assert not _all_text_hits(path, secret)
    assert secret.encode() not in path.read_bytes()


def test_authority_does_not_approve_by_purpose_alone():
    signer = DecisionSigner.ephemeral()
    authority = LocalManasAuthority(
        signer, policy_version=POLICY, service_version="test")
    env = authority.decide(DecisionRequest(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="arbitrary-active-form", target_hash=sha256_hex("arbitrary"),
        route=enums.Route.F_CANDIDATE.value,
        issued_at=NOW, expires_at=FUTURE,
    ))
    assert env.verdict != enums.Verdict.APPROVE.value


def test_reduction_score_is_recomputed_not_caller_supplied(tmp_path):
    store, path = _db(tmp_path)
    studio, signer = _trusted_studio(store)
    n_id = studio.ingest_observation("Observed X; unsure why", signer, now=NOW)
    lineage = store._conn.execute(
        "SELECT lineage_id FROM memory_atoms WHERE atom_id=?", (n_id,)
    ).fetchone()[0]

    # Seed only factual substrate in the explicit fixture/migration context.
    store.close()
    seed = QvchStore(str(path), migration=True)
    repo = Repository(seed)
    repo.write_atom(
        atom_id="u_supported", lineage_id=lineage, atom_kind="HYPOTHESIS",
        materiality_class="SEMANTIC", state="SUPPORTED",
        canonical_payload={"claim": "supported"},
        content_hash=hash_json({"claim": "supported"}),
    )
    ev = build_evidence(
        source_type=enums.EvidenceSourceType.NODE15_EXECUTION.value,
        locator={"probe": "p"}, content="ok")
    repo.record_evidence(ev, now=NOW)
    repo.record_evidence_bundle("eb_trusted", [(ev.evidence_id, 1.0)], now=NOW)
    seed.close()

    store = QvchStore(str(path), migration=False)
    studio, signer = _trusted_studio(store)
    valid = ReductionVerifier().reduce(ReductionInput(
        lineage_id=lineage, noumenon_atom_id=n_id,
        baseline_unknown_slots=(BaselineSlot("s1", 1.0), BaselineSlot("s2", 1.0)),
        resolved_slot_ids=("s1",),
        acceptance_criteria=(AcceptanceCriterion("c", True, True),),
        evidence_items=(EvidenceItem(1.0, True),), required_evidence_weight=1.0,
        scope_coverage=0.5, contradiction_pressure=0.0,
        supported_u_atom_ids=("u_supported",),
        evidence_bundle_ids=("eb_trusted",), scope="local",
    ))
    assert valid.reduction_score == pytest.approx(0.25)

    # Produce a content-consistent but causally false score. Production must
    # recompute from SQL and reject it, not merely verify self-consistent bytes.
    forged = replace(valid, reduction_score=0.99, slot_reduction=0.99,
                     proof_id="", proof_hash="")
    payload = forged.to_payload()
    payload["proof_id"] = ""
    payload["proof_hash"] = ""
    forged_hash = hash_json(payload)
    forged = replace(
        forged,
        proof_id=f"rc_{sha256_hex(forged_hash)[7:23]}",
        proof_hash=forged_hash,
    )
    with pytest.raises(Exception):
        studio.record_reduction(
            forged, lineage_id=lineage, noumenon_atom_id=n_id,
            supported_u_atom_ids=("u_supported",), signer=signer, now=NOW)
    store.close()


def test_ordinary_caller_cannot_invoke_vinasha_on_active_form(tmp_path):
    store, path = _db(tmp_path)
    store.close()
    # Fixture-only seed of an ACTIVE FORM; the test targets the runtime maintenance API.
    seed = QvchStore(str(path), migration=True)
    repo = Repository(seed)
    repo.ensure_lineage("L", root_noumenon_id="n_root", now=NOW)
    repo.write_atom(
        atom_id="n_root", lineage_id="L", atom_kind="NOUMENON",
        materiality_class="SEMANTIC", state="OPEN", canonical_payload={"n": 1},
        content_hash=hash_json({"n": 1}), now=NOW)
    repo.write_atom(
        atom_id="f_active", lineage_id="L", atom_kind="FORM",
        materiality_class="SEMANTIC", state="ACTIVE", canonical_payload={"f": 1},
        content_hash=hash_json({"f": 1}), now=NOW)
    seed.close()

    runtime = QvchStore(str(path), migration=False)
    before = runtime._conn.execute(
        "SELECT COUNT(*) FROM memory_atoms WHERE atom_kind='NOUMENON'"
    ).fetchone()[0]
    with pytest.raises(Exception):
        Vinasha(runtime).handle_degradation(
            "f_active", "f_active#r1", reason="ordinary caller invented drift", now=NOW)
    after = runtime._conn.execute(
        "SELECT COUNT(*) FROM memory_atoms WHERE atom_kind='NOUMENON'"
    ).fetchone()[0]
    assert after == before
    runtime.close()


def test_product_studio_is_not_legacy_self_approving():
    root = Path(__file__).resolve().parents[1]
    server = (root / "apps" / "qvch_studio" / "server.py").read_text(encoding="utf-8")
    assert "from qvch_v3" not in server
    assert "ManasReview" not in server
    assert "approved=True" not in server
    assert "draft.draft_id, True" not in server


def test_public_studio_mutations_do_not_accept_signer():
    mutation_names = (
        "ingest_observation", "commit_understanding", "commit_form", "transition",
        "bind_link", "record_reduction", "declare_applicability", "run_node15_probe",
    )
    for name in mutation_names:
        sig = inspect.signature(getattr(Studio, name))
        assert "signer" not in sig.parameters, f"{name} still accepts caller signer"
