from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from qvch_v3.storage.db import QVCHDatabase

_CLAIM_RE = re.compile(
    r"(?P<subject>[A-Za-zА-Яа-я0-9_ .-]+?)\s+(?:are|is|лежит|лежат|находится|находятся)\s+(?:stored\s+)?(?:in|в)?\s*(?P<value>[A-Za-zА-Яа-я0-9_./\\:-]+)",
    re.I,
)


@dataclass(frozen=True)
class ConflictResult:
    conflict_detected: bool
    reason_codes: list[str]
    conflicts: list[dict]


def extract_storage_claim(text: str) -> tuple[str, str] | None:
    match = _CLAIM_RE.search(text or "")
    if not match:
        return None
    subject = " ".join(match.group("subject").lower().split())
    value = match.group("value").strip().rstrip(".,;:").lower().replace("\\", "/")
    if not subject or not value:
        return None
    return subject, value


def detect_conflict(db: QVCHDatabase, content: str) -> ConflictResult:
    claim = extract_storage_claim(content)
    if not claim:
        return ConflictResult(False, [], [])
    subject, value = claim
    rows = db.query(
        """
        SELECT atom_id, content_text, epistemic_status
        FROM memory_atoms
        WHERE epistemic_status IN ('F_candidate','crystal')
        """
    )
    conflicts = []
    for row in rows:
        existing = extract_storage_claim(row["content_text"])
        if not existing:
            continue
        existing_subject, existing_value = existing
        if existing_subject == subject and existing_value != value:
            conflicts.append(
                {
                    "atom_id": row["atom_id"],
                    "subject": subject,
                    "existing_value": existing_value,
                    "new_value": value,
                    "status": row["epistemic_status"],
                }
            )
    return ConflictResult(bool(conflicts), ["conflict_detected", "storage_location_mismatch"] if conflicts else [], conflicts)
