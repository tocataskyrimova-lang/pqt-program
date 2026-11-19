"""P0 — Studio/CLI surface (brief 15).

The Studio/CLI must (a) keep a usable API, (b) never accept client approval
flags, (c) commit protected writes only through a valid MANAS envelope verified
by the Gateway, and (d) sanitize secrets (constraint #7).
"""

from __future__ import annotations

import json
import os

from qvch_v4.cli import main
from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.migration import seed_legacy_db
from qvch_v4.studio import Studio
from qvch_v4.studio.api import _guard_no_client_approval
from qvch_v4.storage import QvchStore, Repository


def _store(path):
    store = QvchStore(path, migration=True)
    store.init_schema()
    return store, Repository(store)


def test_cli_init_creates_schema(tmp_path):
    db = str(tmp_path / "m.db")
    assert main(["init", "--db", db]) == 0
    store = QvchStore(db, migration=True)
    rows = store._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_atoms'"
    ).fetchall()
    assert rows
    store.close()


def test_ingest_creates_n_through_manas(tmp_path):
    store, repo = _store(str(tmp_path / "m.db"))
    signer = DecisionSigner.ephemeral()
    atom_id = Studio(store, keyring={signer.key_id: signer}).ingest_observation(
        "Observed latency spike; we are unsure why it happens.", signer)
    arow = repo.get_atom(atom_id)
    assert arow is not None
    assert arow[2] == "NOUMENON"  # atom_kind
    # The write went through MANAS + Gateway: a decision + write attempt exist.
    n_dec = store._conn.execute(
        "SELECT COUNT(*) FROM manas_decisions WHERE purpose='AUTHORIZE_WRITE'"
    ).fetchone()[0]
    assert n_dec >= 1
    wa = store._conn.execute(
        "SELECT COUNT(*) FROM write_attempts WHERE allowed=1"
    ).fetchone()[0]
    assert wa >= 1
    ev = store._conn.execute(
        "SELECT COUNT(*) FROM evidence_refs WHERE source_type='SOURCE_ANCHOR'"
    ).fetchone()[0]
    assert ev >= 1
    store.close()


def test_ingest_secret_is_sanitized(tmp_path):
    store, repo = _store(str(tmp_path / "m.db"))
    signer = DecisionSigner.ephemeral()
    secret = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9secretvalue"
    atom_id = Studio(store, keyring={signer.key_id: signer}).ingest_observation(
        f"Config note contains a token: {secret}", signer)
    arow = repo.get_atom(atom_id)
    assert arow[3] == enums.MaterialityClass.SECRET_REF.value  # materiality
    # No TEXT column must contain the literal secret.
    bad = store._conn.execute(
        "SELECT 1 FROM atom_revisions WHERE canonical_payload_json LIKE ?",
        (f"%{secret}%",),
    ).fetchone()
    assert bad is None, "secret leaked into atom revision payload"
    bad2 = store._conn.execute(
        "SELECT 1 FROM evidence_refs WHERE canonical_payload_json LIKE ?",
        (f"%{secret}%",),
    ).fetchone()
    assert bad2 is None, "secret leaked into evidence payload"
    store.close()


def test_analyze_does_not_write(tmp_path):
    store, _ = _store(str(tmp_path / "m.db"))
    out = Studio(store).analyze("We observed X but are unsure of the cause.")
    assert "claim_types" in out
    assert out["draft_id"]
    # analyze is read-only: no atoms were created.
    assert store._conn.execute("SELECT COUNT(*) FROM memory_atoms").fetchone()[0] == 0
    store.close()


def test_studio_refuses_client_approval_flags():
    for flag in ("approved", "safe_to_commit", "verdict", "approved_by"):
        try:
            _guard_no_client_approval(**{flag: True})
            raise AssertionError(f"guard should reject {flag}")
        except ValueError:
            pass


def test_cli_ingest_and_retrieve(tmp_path, monkeypatch):
    # Production ingest requires the sovereign signing key (brief R1 §2 /
    # fail-closed). The CLI reads it from QVCH_MANAS_SIGNING_KEY.
    monkeypatch.setenv("QVCH_MANAS_SIGNING_KEY", "0" * 64)
    db = str(tmp_path / "m.db")
    text = "Observation: the cache hit rate dropped; cause unknown."
    assert main(["init", "--db", db]) == 0
    assert main(["ingest", "--db", db, "--text", text]) == 0
    # retrieve exercises the epistemic retrieval path.
    assert main(["retrieve", "--db", db, "--query", "cache hit rate", "--limit", "5"]) == 0


def test_cli_migrate_and_reconcile(tmp_path):
    legacy = str(tmp_path / "legacy.db")
    v4 = str(tmp_path / "v4.db")
    seed_legacy_db(legacy)
    assert main(["migrate", "--from", legacy, "--to", v4]) == 0
    assert main(["reconcile", "--from", legacy, "--to", v4]) == 0


def test_studio_maintain_runs_spanda(tmp_path):
    store, repo = _store(str(tmp_path / "m.db"))
    # A FORM crystal that has degraded: QUARANTINE gate + failed probes.
    repo.ensure_lineage("l")
    payload = {"form": "f1"}
    chash = hash_json(payload)
    repo.write_atom(atom_id="fact", lineage_id="l", atom_kind="FORM",
                   materiality_class="SEMANTIC", state="ACTIVE",
                   canonical_payload=payload, content_hash=chash, revision_number=1)
    rev = "fact#r1"
    repo.record_applicability_contract(contract_id="c_fact", atom_id="fact",
        revision_id=rev, scope="win32",
        precondition=[{"type": "platform", "value": "win32"}],
        anti_condition=None, required_probes=None)
    from qvch_v4.probes import ProbeReceipt
    repo.record_gate_decision(gate_id="g1", atom_id="fact", revision_id=rev,
        contract_id="c_fact", verdict="QUARANTINE", reason="probe failed")
    repo.record_probe_run(probe_run_id="pr1", probe_plan_id="p1", atom_id="fact",
        decision_id=None,
        receipt=ProbeReceipt(probe_name="p1", command_hash="sha256:x",
            env_hash="sha256:y", exit_code=1, stdout_hash="sha256:0",
            stderr_hash="sha256:0", executed_at="2026-01-01T00:00:00+00:00",
            success=False, reason="exit_code=1", authorized=True).to_payload())
    repo.record_usage_outcome(outcome_id="u1", atom_id="fact", revision_id=rev,
        gate_id="g1", outcome="FAILURE")
    results = Studio(store).maintain(now="2026-02-01T00:00:00+00:00")
    assert results, "expected at least one FORM atom assessed"
    fact = next(r for r in results if r["atom_id"] == "fact")
    assert fact["applied"] is True
    assert repo.get_atom("fact")[4] in ("STALE", "QUARANTINED")
    store.close()


__all__ = []
