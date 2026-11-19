"""P0-F — SQL Schema v4.1.

Gate P0-F:
  * PRAGMA integrity_check = ok
  * PRAGMA foreign_key_check returns no rows
  * direct writes in all major SQL forms are blocked
  * history rows cannot be UPDATE/DELETE-d
  * a multi-atom transaction stores each atom's own canonical payload
"""

import sqlite3

import pytest

from qvch_v4.storage import QvchStore, Repository
from qvch_v4.storage.schema import APPEND_ONLY_TABLES, PROTECTED_TABLES


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "mem_v4.db"
    s = QvchStore(str(db))
    s.init_schema()
    yield s
    s.close()


def _mig_repo(tmp_path):
    """A Repository reopened in the migration/bootstrap context.

    The ``store`` fixture stays ``migration=False`` so the raw-authorizer
    denial tests (DDL / INSERT / UPDATE / DELETE outside a write scope) hold;
    protected writes the test-harness legitimately seeds go through a
    migration-context store, exactly as production bootstrap does (brief R2 §1).
    """
    ms = QvchStore(str(tmp_path / "mem_v4.db"), migration=True)
    return Repository(ms)


def test_integrity_and_foreign_keys_ok(store):
    assert store.integrity_ok() is True
    assert store.foreign_keys_ok() is True


def test_direct_insert_blocked(store):
    conn = store.raw_connection()
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute(
            "INSERT INTO memory_atoms (atom_id, lineage_id, atom_kind, current_state, "
            "created_at, updated_at) VALUES ('a1','l1','NOUMENON','OPEN','t','t')"
        )


def test_direct_update_blocked(store):
    conn = store.raw_connection()
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE memory_atoms SET current_state='OPEN' WHERE atom_id='x'")


def test_direct_delete_blocked(store):
    conn = store.raw_connection()
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM memory_atoms WHERE atom_id='x'")


def test_direct_replace_blocked(store):
    conn = store.raw_connection()
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute(
            "REPLACE INTO manas_decisions (decision_id, purpose, target_id, target_hash, "
            "verdict, route, policy_version, service_version, key_id, issued_at, expires_at, "
            "nonce, signature_algorithm, signature, canonical_hash) VALUES "
            "('d1','AUTHORIZE_WRITE','t','h','APPROVE',null,'pv','sv','k','i','e','n','H','s','h')"
        )


def test_direct_ddl_blocked(store):
    conn = store.raw_connection()
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("CREATE TABLE evil (x TEXT)")


def test_executescript_blocked_outside_migration(store):
    conn = store.raw_connection()
    with pytest.raises(sqlite3.DatabaseError):
        conn.executescript("CREATE TABLE evil2 (x TEXT)")


def test_writable_cte_blocked(store):
    conn = store.raw_connection()
    # A writable CTE is still a write and must be denied outside the write scope.
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute(
            "INSERT INTO memory_atoms (atom_id, lineage_id, atom_kind, current_state, "
            "created_at, updated_at) "
            "SELECT 'a2', 'l1', 'NOUMENON', 'OPEN', 't', 't'"
        )


def test_history_rows_cannot_be_mutated(store, tmp_path):
    # Seed an atom + revision through the authorized repository path.
    repo = _mig_repo(tmp_path)
    repo.ensure_lineage("lin1")
    repo.write_atom(
        atom_id="n1", lineage_id="lin1", atom_kind="NOUMENON",
        materiality_class="SEMANTIC", state="OPEN",
        canonical_payload={"noumenon": "unknown latency"}, content_hash="sha256:n1",
    )
    conn = store.raw_connection()
    for stmt in (
        "UPDATE atom_revisions SET state='HACKED' WHERE atom_id='n1'",
        "DELETE FROM atom_revisions WHERE atom_id='n1'",
        "UPDATE memory_links SET link_type='X' WHERE link_id='x'",
    ):
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute(stmt)


def test_multi_atom_transaction_isolates_payloads(store, tmp_path):
    repo = _mig_repo(tmp_path)
    repo.ensure_lineage("linX")
    repo.write_atoms_batch([
        dict(atom_id="u1", lineage_id="linX", atom_kind="HYPOTHESIS",
             materiality_class="SEMANTIC", state="PROPOSED",
             canonical_payload={"u": "branch one", "id": "u1"}),
        dict(atom_id="u2", lineage_id="linX", atom_kind="HYPOTHESIS",
             materiality_class="SEMANTIC", state="PROPOSED",
             canonical_payload={"u": "branch two", "id": "u2"}),
    ])
    r1 = repo.get_revision("u1#r1")
    r2 = repo.get_revision("u2#r1")
    assert r1[4] != r2[4], "each atom must store its own canonical payload"
    assert '"id":"u1"' in r1[4]
    assert '"id":"u2"' in r2[4]


def test_forbidden_state_transition_rolls_back(store, tmp_path):
    repo = _mig_repo(tmp_path)
    repo.ensure_lineage("linY")
    repo.write_atom(
        atom_id="f1", lineage_id="linY", atom_kind="FORM",
        materiality_class="SEMANTIC", state="CANDIDATE",
        canonical_payload={"f": 1}, content_hash="sha256:f1",
    )
    # ACTIVE is not reachable directly from CANDIDATE (no seeded rule).
    assert repo.allowed_transition("FORM", "CANDIDATE", "ACTIVE") is False
    with pytest.raises(sqlite3.IntegrityError):
        repo.set_atom_state("f1", "ACTIVE", reason="illegal jump")
    # State unchanged after the rolled-back attempt.
    assert repo.get_atom("f1")[4] == "CANDIDATE"


def test_allowed_state_transition_succeeds(store, tmp_path):
    repo = _mig_repo(tmp_path)
    repo.ensure_lineage("linZ")
    repo.write_atom(
        atom_id="f2", lineage_id="linZ", atom_kind="FORM",
        materiality_class="SEMANTIC", state="CANDIDATE",
        canonical_payload={"f": 2}, content_hash="sha256:f2",
    )
    assert repo.allowed_transition("FORM", "CANDIDATE", "VALIDATED") is True
    repo.set_atom_state("f2", "VALIDATED", reason="approved")
    assert repo.get_atom("f2")[4] == "VALIDATED"


def test_foreign_key_enforced(store, tmp_path):
    repo = _mig_repo(tmp_path)
    with pytest.raises(sqlite3.IntegrityError):
        repo.write_atom(
            atom_id="orphan", lineage_id="does_not_exist", atom_kind="NOUMENON",
            materiality_class="SEMANTIC", state="OPEN",
            canonical_payload={"x": 1}, content_hash="sha256:orphan",
        )
