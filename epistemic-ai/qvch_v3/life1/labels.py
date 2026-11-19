from __future__ import annotations

from datetime import datetime
from typing import Any

from qvch_v3.storage.db import QVCHDatabase

STRONG_LINK_CONFIDENCE = {"EXACT", "HIGH"}
VALIDATED_REPAIR_STATUSES = {"validated", "validated_repair", "repair_validated"}
WRITTEN_TRANSITIONS = {"written", "promoted"}


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _base_result(label_id: str) -> dict[str, Any]:
    return {
        "label_id": label_id,
        "eligible": False,
        "strong_y_bad_write_evidence": False,
        "reason_codes": [],
        "provenance_policy": "QVCH_LIFE1_ONLY_NO_PQT_EXT1_INPUTS",
    }


def _validated_repair(db: QVCHDatabase, repair_id: str, result: dict[str, Any]) -> bool:
    row = db.one("SELECT validation_status FROM repair_pairs WHERE repair_id=?", (repair_id,))
    if not row:
        result["reason_codes"].append("missing_repair_pair")
        return False
    if row["validation_status"] not in VALIDATED_REPAIR_STATUSES:
        result["reason_codes"].append("repair_pair_not_validated")
        return False
    return True


def _prior_written_event(db: QVCHDatabase, *, object_type: str, object_id: str) -> dict[str, Any] | None:
    rows = db.query(
        """
        SELECT * FROM memory_lifecycle_events
        WHERE object_type=? AND object_id=? AND transition_kind IN ('written','promoted')
        ORDER BY occurred_at ASC
        """,
        (object_type, object_id),
    )
    return rows[0] if rows else None


def audit_repair_atom_label(db: QVCHDatabase, *, repair_id: str, atom_id: str) -> dict[str, Any]:
    result = _base_result("Y_BAD_WRITE_REPAIR_TO_ATOM")
    if not _validated_repair(db, repair_id, result):
        return result
    link = db.one(
        "SELECT * FROM repair_atom_links WHERE repair_id=? AND atom_id=? ORDER BY linked_at ASC",
        (repair_id, atom_id),
    )
    if not link:
        result["reason_codes"].append("missing_repair_atom_link")
        return result
    if link["confidence"] not in STRONG_LINK_CONFIDENCE:
        result["reason_codes"].append("repair_atom_link_confidence_too_weak")
        return result
    prior = _prior_written_event(db, object_type="memory_atom", object_id=atom_id)
    if not prior:
        result["reason_codes"].append("missing_prior_written_or_promoted_lifecycle_event")
        return result
    if _parse_iso(link["linked_at"]) <= _parse_iso(prior["occurred_at"]):
        result["reason_codes"].append("temporal_order_invalid")
        return result
    result.update({
        "eligible": True,
        "strong_y_bad_write_evidence": True,
        "reason_codes": ["validated_repair_linked_to_prior_written_atom"],
        "prior_lifecycle_event_id": prior["life_event_id"],
        "link_id": link["link_id"],
    })
    return result


def audit_repair_crystal_label(db: QVCHDatabase, *, repair_id: str, crystal_id: str) -> dict[str, Any]:
    result = _base_result("Y_BAD_WRITE_REPAIR_TO_CRYSTAL")
    if not _validated_repair(db, repair_id, result):
        return result
    link = db.one(
        "SELECT * FROM repair_crystal_links WHERE repair_id=? AND crystal_id=? ORDER BY linked_at ASC",
        (repair_id, crystal_id),
    )
    if not link:
        result["reason_codes"].append("missing_repair_crystal_link")
        return result
    if link["confidence"] not in STRONG_LINK_CONFIDENCE:
        result["reason_codes"].append("repair_crystal_link_confidence_too_weak")
        return result
    prior = _prior_written_event(db, object_type="crystal", object_id=crystal_id)
    if not prior:
        result["reason_codes"].append("missing_prior_written_or_promoted_lifecycle_event")
        return result
    if _parse_iso(link["linked_at"]) <= _parse_iso(prior["occurred_at"]):
        result["reason_codes"].append("temporal_order_invalid")
        return result
    result.update({
        "eligible": True,
        "strong_y_bad_write_evidence": True,
        "reason_codes": ["validated_repair_linked_to_prior_written_crystal"],
        "prior_lifecycle_event_id": prior["life_event_id"],
        "link_id": link["link_id"],
    })
    return result
