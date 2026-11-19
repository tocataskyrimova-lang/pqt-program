from __future__ import annotations

from qvch_v3.contracts.models import MemoryProbeResult, new_id, now_iso, to_json
from qvch_v3.retrieval.search import retrieve
from qvch_v3.storage.db import QVCHDatabase


def run_memory_probe(db: QVCHDatabase, *, query: str, expected: str, expected_status: str | None = None) -> MemoryProbeResult:
    result = retrieve(db, query)
    found = any(expected.lower() in str(item.get("content_text", "")).lower() for item in result.answer_candidates)
    status_ok = expected_status is None or result.status == expected_status
    passed = found and status_ok
    reasons = []
    if not found:
        reasons.append("expected_meaning_not_retrieved")
    if not status_ok:
        reasons.append("unexpected_epistemic_status")
    if passed:
        reasons.append("probe_passed")
    probe = MemoryProbeResult(new_id("probe"), passed, query, expected, result.status, reasons)
    with db.authorized_write():
        db.execute("INSERT INTO probe_runs VALUES(?,?,?,?,?,?,?)", (probe.probe_id, query, expected, 1 if passed else 0, result.status, to_json(reasons), now_iso()))
    return probe
