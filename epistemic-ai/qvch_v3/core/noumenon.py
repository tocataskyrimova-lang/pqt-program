from __future__ import annotations

from qvch_v3.contracts.models import EvidenceRef, new_id, now_iso
from qvch_v3.storage.db import QVCHDatabase

_ALLOWED = ["N_open", "revisited", "guidance_received", "partially_resolved", "resolved_to_F_candidate", "promoted_to_F", "crystallized", "retired"]


def open_noumenon_backlog(db: QVCHDatabase) -> list[dict]:
    return db.query("SELECT * FROM noumena WHERE state NOT IN ('crystallized','retired') ORDER BY updated_at DESC")


def transition_noumenon(db: QVCHDatabase, n_id: str, to_state: str, *, evidence: EvidenceRef | None = None, note: str = "") -> str:
    if to_state not in _ALLOWED:
        raise ValueError(f"unsupported noumenon state: {to_state}")
    row = db.one("SELECT state FROM noumena WHERE n_id=?", (n_id,))
    if not row:
        raise ValueError(f"unknown noumenon: {n_id}")
    from_state = row["state"]
    with db.authorized_write():
        if evidence:
            db.execute(
                "INSERT OR IGNORE INTO evidence_refs VALUES(?,?,?,?,?,?,?)",
                (evidence.evidence_id, evidence.source_type, evidence.source_ref, evidence.summary, evidence.weight, 1 if evidence.is_llm_confidence else 0, now_iso()),
            )
        tid = new_id("ntr")
        db.execute("INSERT INTO noumenon_transitions VALUES(?,?,?,?,?,?,?)", (tid, n_id, from_state, to_state, evidence.evidence_id if evidence else None, note, now_iso()))
        db.execute("UPDATE noumena SET state=?, updated_at=? WHERE n_id=?", (to_state, now_iso(), n_id))
    return tid


def revisit_noumenon(db: QVCHDatabase, n_id: str, evidence: EvidenceRef | None = None, note: str = "revisited") -> str:
    return transition_noumenon(db, n_id, "revisited", evidence=evidence, note=note)


def receive_guidance(db: QVCHDatabase, n_id: str, evidence: EvidenceRef, note: str = "guidance received") -> str:
    return transition_noumenon(db, n_id, "guidance_received", evidence=evidence, note=note)


def partially_resolve_noumenon(db: QVCHDatabase, n_id: str, evidence: EvidenceRef, note: str = "partially resolved") -> str:
    return transition_noumenon(db, n_id, "partially_resolved", evidence=evidence, note=note)


def resolve_noumenon(db: QVCHDatabase, n_id: str, target_id: str, *, target_type: str = "F_candidate", evidence: EvidenceRef | None = None) -> str:
    state = "resolved_to_F_candidate" if target_type == "F_candidate" else "promoted_to_F"
    return transition_noumenon(db, n_id, state, evidence=evidence, note=f"resolved to {target_type}:{target_id}")
