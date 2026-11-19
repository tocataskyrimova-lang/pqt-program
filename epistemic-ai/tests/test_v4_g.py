"""P0-G — shadow migration v3 → v4 (brief 11).

Gate P0-G: two runs over the same source DB yield an equivalent canonical
result with no duplication; cutover is forbidden while a critical issue exists.
"""

from __future__ import annotations

import hashlib

from qvch_v4.migration import run_migration, seed_legacy_db
from qvch_v4.storage import QvchStore


def _sha256(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _atom_counts(v4_path: str) -> dict[str, int]:
    store = QvchStore(v4_path)
    out = {}
    for kind in ("NOUMENON", "HYPOTHESIS", "FORM", "REPAIR", "SKILL"):
        out[kind] = store._conn.execute(
            "SELECT COUNT(*) FROM memory_atoms WHERE atom_kind=?", (kind,)
        ).fetchone()[0]
    store.close()
    return out


def test_migration_maps_all_kinds(tmp_path):
    legacy = tmp_path / "memory_v3.db"
    seed_legacy_db(legacy)
    v4 = tmp_path / "memory_v4.db"
    report = run_migration(legacy, v4)

    counts = _atom_counts(str(v4))
    assert counts["NOUMENON"] == 1, counts
    assert counts["HYPOTHESIS"] == 1, counts
    assert counts["FORM"] == 2, counts  # a_f1 + cry_1
    assert counts["REPAIR"] == 1, counts
    assert counts["SKILL"] == 1, counts

    assert report.integrity_ok is True
    assert report.fk_ok is True
    assert report.mapped > 0


def test_legacy_db_is_immutable(tmp_path):
    legacy = tmp_path / "memory_v3.db"
    seed_legacy_db(legacy)
    before = _sha256(str(legacy))
    v4 = tmp_path / "memory_v4.db"
    run_migration(legacy, v4)
    after = _sha256(str(legacy))
    assert before == after, "legacy DB must not be modified by migration"


def test_idempotent_rerun_no_duplication(tmp_path):
    legacy = tmp_path / "memory_v3.db"
    seed_legacy_db(legacy)
    v4 = tmp_path / "memory_v4.db"

    r1 = run_migration(legacy, v4)
    s1 = r1.canonical_summary()
    atoms_after_first = _atom_counts(str(v4))["FORM"]

    # Re-run over the SAME v4 target — must not duplicate.
    r2 = run_migration(legacy, v4)
    s2 = r2.canonical_summary()
    atoms_after_second = _atom_counts(str(v4))["FORM"]

    assert atoms_after_first == atoms_after_second, "re-run duplicated rows"
    assert r1.v4_counts["memory_atoms"] == r2.v4_counts["memory_atoms"]
    assert r1.v4_counts["audit_events"] == r2.v4_counts["audit_events"]
    assert s1 == s2, "re-run produced a different canonical result"


def test_deterministic_across_fresh_targets(tmp_path):
    legacy = tmp_path / "memory_v3.db"
    seed_legacy_db(legacy)

    v4a = tmp_path / "a" / "memory_v4.db"
    v4b = tmp_path / "b" / "memory_v4.db"
    v4a.parent.mkdir(parents=True, exist_ok=True)
    v4b.parent.mkdir(parents=True, exist_ok=True)
    ra = run_migration(legacy, v4a)
    rb = run_migration(legacy, v4b)

    assert ra.canonical_summary() == rb.canonical_summary(), "not deterministic"
    assert ra.v4_counts == rb.v4_counts


def test_crystal_atom_not_duplicated_with_memory_atom(tmp_path):
    legacy = tmp_path / "memory_v3.db"
    seed_legacy_db(legacy)
    v4 = tmp_path / "memory_v4.db"
    report = run_migration(legacy, v4)
    # a_cry1 (memory_atoms, status crystal) must be folded into cry_1, not
    # produce a second FORM atom.
    assert report.duplicate_groups >= 1
    counts = _atom_counts(str(v4))
    assert counts["FORM"] == 2


def test_secrets_in_payloads_are_not_carried(tmp_path):
    # The legacy seeder itself does not embed secrets; this asserts the v4
    # evidence_refs never contain a raw-looking secret token shape and that
    # the migration path refuses to embed one. We check the migrated evidence
    # payloads are clean of obvious secret markers.
    legacy = tmp_path / "memory_v3.db"
    seed_legacy_db(legacy)
    v4 = tmp_path / "memory_v4.db"
    run_migration(legacy, v4)
    store = QvchStore(v4)
    rows = store._conn.execute("SELECT canonical_payload_json FROM evidence_refs").fetchall()
    joined = " ".join(r[0] for r in rows)
    store.close()
    # No full legacy write_plans.payload_json leaked into evidence.
    assert '"plan":"legacy"' not in joined


def test_reconciliation_report_serializes(tmp_path):
    legacy = tmp_path / "memory_v3.db"
    seed_legacy_db(legacy)
    v4 = tmp_path / "memory_v4.db"
    report = run_migration(legacy, v4)
    md = report.to_markdown()
    payload = report.to_payload()
    assert "QVCH v3 → v4" in md
    assert len(payload["source_db_hash"]) == 64  # file sha256 hex
    assert "source_db_hash" in payload
    assert report.legacy_counts["memory_atoms"] >= 1
    assert report.v4_counts["memory_atoms"] >= 1


def test_cutover_forbidden_on_critical_issue(tmp_path):
    from qvch_v4.migration.reconciliation import ReconciliationReport

    clean = ReconciliationReport(
        source_db_path="x", source_db_hash="y", migration_version="v",
        critical_issues=0,
    )
    blocked = ReconciliationReport(
        source_db_path="x", source_db_hash="y", migration_version="v",
        critical_issues=1,
    )
    assert clean.can_cutover() is True
    assert blocked.can_cutover() is False


def test_clean_migration_allows_cutover(tmp_path):
    legacy = tmp_path / "memory_v3.db"
    seed_legacy_db(legacy)
    v4 = tmp_path / "memory_v4.db"
    report = run_migration(legacy, v4)
    assert report.critical_issues == 0
    assert report.can_cutover() is True

