from __future__ import annotations

from qvch_v3.contracts.models import new_id, now_iso, to_json
from qvch_v3.storage.db import QVCHDatabase


def health_report(db: QVCHDatabase) -> dict:
    report = {
        "db_reachable": True,
        "events": db.scalar("SELECT COUNT(*) FROM memory_events") or 0,
        "atoms": db.scalar("SELECT COUNT(*) FROM memory_atoms") or 0,
        "open_n": db.scalar("SELECT COUNT(*) FROM noumena WHERE state NOT IN ('crystallized','retired')") or 0,
        "repair_pairs": db.scalar("SELECT COUNT(*) FROM repair_pairs") or 0,
        "skill_candidates": db.scalar("SELECT COUNT(*) FROM skill_candidates") or 0,
        "crystals": db.scalar("SELECT COUNT(*) FROM crystals") or 0,
        "probe_failures": db.scalar("SELECT COUNT(*) FROM probe_runs WHERE passed=0") or 0,
    }
    with db.authorized_write():
        db.execute("INSERT INTO monitor_events VALUES(?,?,?,?)", (new_id("mon"), "health_report", to_json(report), now_iso()))
    return report
