from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from .constants import LABEL_AVAILABLE, LABEL_UNAVAILABLE
from .contracts import LabelResult

REQUIRED_SCHEMA = {
    "lifecycle_transition_log": {
        "acceptable_tables": ["crystal_transitions", "lifecycle_transitions", "object_lifecycle_transitions"],
        "required_fields": ["transition_id", "object_id", "object_type", "from_state", "to_state", "occurred_at", "reason", "actor_or_source", "source_event_id"],
        "why": "required to prove promoted-to-retired ordering",
    },
    "repair_atom_link": {
        "acceptable_tables": ["repair_atom_links"],
        "required_fields": ["repair_id", "atom_id", "relationship_type", "linked_at", "provenance"],
        "why": "required to attribute a validated repair to the repaired atom",
    },
}

OPTIONAL_COMPOSITE_SCHEMA = {
    "supersession_events": "timestamped duplicate/superseded lifecycle",
    "atom_usage_events": "timestamped usage/retrieval history",
    "evidence_quality_events": "timestamped evidence-quality history",
}


def _table_columns(schema_sql: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    pattern = re.compile(r"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+([\w_]+)\s*\((.*?)\);", re.I | re.S)
    for match in pattern.finditer(schema_sql):
        table = match.group(1).lower()
        columns: set[str] = set()
        for line in match.group(2).splitlines():
            token = line.strip().split(None, 1)[0].strip('"`[],') if line.strip() else ""
            if token and token.lower() not in {"primary", "foreign", "unique", "constraint", "check"}:
                columns.add(token.lower())
        result[table] = columns
    return result


def audit_label_capability(schema_sql: str) -> dict[str, Any]:
    tables = _table_columns(schema_sql)
    blockers: list[dict[str, Any]] = []
    channel_results: dict[str, Any] = {}
    for channel, requirement in REQUIRED_SCHEMA.items():
        candidates = [name for name in requirement["acceptable_tables"] if name in tables]
        chosen = candidates[0] if candidates else None
        missing = list(requirement["required_fields"]) if chosen is None else sorted(set(requirement["required_fields"]) - tables[chosen])
        available = chosen is not None and not missing
        channel_results[channel] = {"available": available, "table": chosen, "missing_fields": missing, "why": requirement["why"]}
        if not available:
            blockers.append({"channel": channel, "missing_table_or_fields": missing, "blocking": True})
    return {
        "label_capability_status": LABEL_AVAILABLE if not blockers else LABEL_UNAVAILABLE,
        "strong_y_bad_write_computable": not blockers,
        "channels": channel_results,
        "blockers": blockers,
        "optional_composite_requirements": OPTIONAL_COMPOSITE_SCHEMA,
        "pilot_allowed": False if blockers else True,
    }


def schema_requirements_report(capability: dict[str, Any]) -> dict[str, Any]:
    return {
        "required_before_pilot": REQUIRED_SCHEMA,
        "required_for_full_composite_label": OPTIONAL_COMPOSITE_SCHEMA,
        "current_capability": capability,
        "migration_performed": False,
        "pilot_blocked": not bool(capability["strong_y_bad_write_computable"]),
    }


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def extract_label(record: dict[str, Any], *, as_of: datetime, window_days: int = 7, evidence_floor: float = 0.5) -> LabelResult:
    episode_id = str(record["episode_id"])
    created_at = _parse_time(str(record["created_at"]))
    if as_of - created_at < timedelta(days=window_days):
        return LabelResult(episode_id, "EXCLUDED", ("immature_window",), window_days, ("created_at", "as_of"))

    reasons: list[str] = []
    provenance: list[str] = []
    if bool(record.get("validated_repair_atom_link")):
        reasons.append("validated_repair_linked_to_atom")
        provenance.append("repair_atom_links")
    promoted_at = record.get("promoted_at")
    retired_at = record.get("retired_at")
    if promoted_at and retired_at and _parse_time(str(promoted_at)) < _parse_time(str(retired_at)):
        reasons.append("promoted_then_retired")
        provenance.append("lifecycle_transition_log")
    if record.get("duplicate_or_superseded_at"):
        reasons.append("duplicate_or_superseded")
        provenance.append("supersession_events")
    usage_count = record.get("usage_count")
    evidence_quality = record.get("evidence_quality")
    if usage_count == 0 and evidence_quality is not None and float(evidence_quality) < evidence_floor:
        reasons.append("unused_low_evidence")
        provenance.extend(["atom_usage_events", "evidence_quality_events"])
    if reasons:
        return LabelResult(episode_id, 1, tuple(reasons), window_days, tuple(sorted(set(provenance))))

    explicit_clean = all(key in record for key in ("usage_count", "evidence_quality", "no_bad_lifecycle_events"))
    if explicit_clean and int(record["usage_count"]) > 0 and float(record["evidence_quality"]) >= evidence_floor and bool(record["no_bad_lifecycle_events"]):
        return LabelResult(episode_id, 0, ("mature_used_supported_survivor",), window_days, ("usage", "evidence_quality", "lifecycle"))
    return LabelResult(episode_id, "EXCLUDED", ("ambiguous_or_incomplete_lifecycle",), window_days, ())


def canonical_label_hash(labels: Iterable[LabelResult]) -> str:
    rows = [
        {"episode_id": row.episode_id, "value": row.value, "reason_codes": row.reason_codes, "window_days": row.window_days, "provenance": row.provenance}
        for row in labels
    ]
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
