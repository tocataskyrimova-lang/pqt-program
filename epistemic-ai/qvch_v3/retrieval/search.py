from __future__ import annotations

from qvch_v3.contracts.models import RetrievalResult, from_json
from qvch_v3.storage.db import QVCHDatabase


def retrieve(db: QVCHDatabase, query: str, limit: int = 5) -> RetrievalResult:
    q = "%" + query.lower() + "%"
    rows = db.query(
        """
        SELECT atom_id as id, 'atom' as kind, epistemic_status as status, content_text, event_id
        FROM memory_atoms WHERE lower(content_text) LIKE ?
        UNION ALL
        SELECT n_id as id, 'noumenon' as kind, state as status, content_text, event_id
        FROM noumena WHERE lower(content_text) LIKE ?
        UNION ALL
        SELECT repair_id as id, 'repair_pair' as kind, validation_status as status, corrected_answer as content_text, event_id
        FROM repair_pairs WHERE lower(bad_answer) LIKE ? OR lower(corrected_answer) LIKE ? OR lower(failure_reason) LIKE ?
        UNION ALL
        SELECT skill_id as id, 'skill_candidate' as kind, validation_status as status, procedure_summary as content_text, '' as event_id
        FROM skill_candidates WHERE lower(trigger_pattern) LIKE ? OR lower(procedure_summary) LIKE ?
        LIMIT ?
        """,
        (q, q, q, q, q, q, q, limit),
    )
    status = next((r["status"] for r in rows if r["kind"] == "noumenon"), rows[0]["status"] if rows else "not_found")
    lineage = []
    evidence = []
    for r in rows:
        lineage.append({"kind": r["kind"], "id": r["id"], "status": r["status"], "event_id": r.get("event_id")})
        if r["kind"] == "noumenon":
            lineage.extend(db.query("SELECT transition_id as id, 'noumenon_transition' as kind, to_state as status, note FROM noumenon_transitions WHERE n_id=?", (r["id"],)))
    return RetrievalResult(query, status, rows, 1.0 if rows else 0.0, evidence, lineage)

