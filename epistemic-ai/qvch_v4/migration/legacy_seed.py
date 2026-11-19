"""Build a representative QVCH v3 legacy database (brief 11.1).

This is a *fixture generator* for migration testing and the E2E demo. It does
NOT mutate any production legacy DB; its caller owns the (temporary) path.
The seed mirrors the v3 schema (`qvch_v3/storage/schema.sql`) and exercises
every mapping target listed in brief 11.2: events, evidence, noumena +
transitions, atoms (N/U/F/crystal), hypotheses, crystals, repair_pairs,
skill_candidates, atom_evidence, write_plans, write_audit, probe_runs,
monitor_events.
"""

from __future__ import annotations

import datetime
import sqlite3
import uuid

from pathlib import Path

_V3_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "qvch_v3" / "storage" / "schema.sql"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _load_v3_ddl() -> str:
    return _V3_SCHEMA_PATH.read_text(encoding="utf-8")


def seed_legacy_db(path: str | Path) -> str:
    """Create and populate a legacy v3 DB at ``path``. Returns the path.

    Deterministic IDs are used so the migration's reconciliation report is
    reproducible across runs.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript(_load_v3_ddl())
    conn.row_factory = sqlite3.Row
    now = _now()

    # --- memory_events -------------------------------------------------------
    events = [
        ("ev_1", "dialogue", "user", "Execution logs are stored in logs/runtime.",
         "sha256:ev1", now, '{"topic":"logs"}'),
        ("ev_2", "dialogue", "user", "The build passes on commit abc123.",
         "sha256:ev2", now, '{"topic":"build"}'),
        ("ev_3", "sensor", "system", "Latency under 200ms observed at peak.",
         "sha256:ev3", now, '{"topic":"latency"}'),
    ]
    conn.executemany(
        "INSERT INTO memory_events VALUES (?,?,?,?,?,?,?)", events
    )

    # --- evidence_refs -------------------------------------------------------
    evidence = [
        ("evr_1", "demo_tool_output", "logs/runtime", "logs/runtime confirmed by demo", 1.0, 0, now),
        ("evr_2", "test_log", "tests/build", "all tests green", 1.0, 0, now),
        ("evr_3", "node15_execution", "probe/commit", "manifest constant after commit", 1.0, 0, now),
    ]
    conn.executemany(
        "INSERT INTO evidence_refs VALUES (?,?,?,?,?,?,?)", evidence
    )

    # --- noumena + transitions ----------------------------------------------
    conn.execute(
        "INSERT INTO noumena VALUES (?,?,?,?,?,?,?)",
        ("n_1", "ev_1", "unknown latency", "partially_resolved", now, now, '{"src":"ev_1"}'),
    )
    conn.execute(
        "INSERT INTO noumenon_transitions VALUES (?,?,?,?,?,?,?)",
        ("nt_1", "n_1", "N_open", "partially_resolved", "evr_3", "reduced by probe", now),
    )

    # --- memory_atoms (U and F_candidate branches) --------------------------
    atoms = [
        ("a_u1", "ev_2", "hypothesis", "candidate", "build is deterministic",
         "build is deterministic", 0.6, 0, '{"route":"U"}', now),
        ("a_f1", "ev_3", "semantic_fact_candidate", "F_candidate", "latency under 200ms",
         "latency under 200ms", 0.5, 1, '{"route":"F_candidate"}', now),
        ("a_cry1", "ev_2", "semantic_fact_candidate", "crystal", "build invariant holds",
         "build invariant holds", 0.9, 2, '{"route":"crystal"}', now),
    ]
    conn.executemany(
        "INSERT INTO memory_atoms VALUES (?,?,?,?,?,?,?,?,?,?)", atoms
    )

    # --- hypotheses (state of U atoms) --------------------------------------
    conn.execute(
        "INSERT INTO hypotheses VALUES (?,?,?,?)",
        ("h_1", "a_u1", "supported", now),
    )

    # --- crystals (authoritative crystal source) ----------------------------
    conn.execute(
        "INSERT INTO crystals VALUES (?,?,?,?,?,?)",
        ("cry_1", "build invariant holds", '["a_u1"]', '["n_1"]', "promoted", now),
    )

    # --- repair_pairs --------------------------------------------------------
    conn.execute(
        "INSERT INTO repair_pairs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("rp_1", "ev_2", "old wrong answer", "off-by-one in round",
         "unit test", "corrected answer", "validated", '["n_1"]',
         None, '["evr_2"]', now),
    )

    # --- skill_candidates ----------------------------------------------------
    conn.execute(
        "INSERT INTO skill_candidates VALUES (?,?,?,?,?,?,?,?,?)",
        ("sk_1", "rounding error", '["rp_1"]', "add epsilon then floor",
         '["overflow"]', "skill_trace", 0.7, '["evr_2"]', now),
    )

    # --- atom_evidence -------------------------------------------------------
    conn.executemany(
        "INSERT INTO atom_evidence VALUES (?,?,?)",
        [("a_u1", "evr_2", now), ("a_f1", "evr_3", now), ("a_cry1", "evr_1", now)],
    )

    # --- write_plans (only safe provenance carried; no full payload) --------
    conn.execute(
        "INSERT INTO write_plans VALUES (?,?,?,?)",
        ("wp_1", "F_candidate", '{"plan":"legacy"}', now),
    )
    conn.execute(
        "INSERT INTO write_audit VALUES (?,?,?,?,?,?)",
        ("wa_1", "wp_1", 1, '["ok"]', '["a_f1"]', now),
    )

    # --- probe_runs ----------------------------------------------------------
    conn.execute(
        "INSERT INTO probe_runs VALUES (?,?,?,?,?,?,?)",
        ("pr_1", "logs/runtime", "logs/runtime", 1, "F_candidate", '["ok"]', now),
    )

    # --- monitor_events ------------------------------------------------------
    conn.execute(
        "INSERT INTO monitor_events VALUES (?,?,?,?)",
        ("me_1", "health", '{"cpu":0.3}', now),
    )

    conn.commit()
    conn.close()
    return str(path)
