from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Iterator

from qvch_v3.contracts.models import new_id, now_iso, to_json
from qvch_v3.life1.constants import (
    ALLOWED_PROVENANCE_SOURCES,
    BASELINE_UNKNOWN_HISTORY,
    FORBIDDEN_LABEL_PROVENANCE_MARKERS,
    PRODUCTION_DB_PATH,
    SANDBOX_DB_PATH,
)
from qvch_v3.storage.db import QVCHDatabase

LIFE1_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memory_lifecycle_events (
  life_event_id TEXT PRIMARY KEY,
  object_type TEXT NOT NULL CHECK(object_type IN ('memory_atom','crystal','noumenon','repair_pair','hypothesis','skill_candidate','write_plan','evidence_ref','other')),
  object_id TEXT NOT NULL,
  from_state TEXT,
  to_state TEXT NOT NULL,
  transition_kind TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  reason_code TEXT NOT NULL,
  actor_or_source TEXT NOT NULL,
  source_event_id TEXT,
  idempotency_key TEXT NOT NULL UNIQUE,
  provenance_sha256 TEXT NOT NULL,
  provenance_source TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_life_object_time ON memory_lifecycle_events(object_type, object_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_life_transition_kind ON memory_lifecycle_events(transition_kind, occurred_at);
CREATE INDEX IF NOT EXISTS idx_life_source_event ON memory_lifecycle_events(source_event_id);

CREATE TABLE IF NOT EXISTS repair_atom_links (
  link_id TEXT PRIMARY KEY,
  repair_id TEXT NOT NULL REFERENCES repair_pairs(repair_id),
  atom_id TEXT NOT NULL REFERENCES memory_atoms(atom_id),
  relation_type TEXT NOT NULL,
  linked_at TEXT NOT NULL,
  confidence TEXT NOT NULL CHECK(confidence IN ('EXACT','HIGH','MEDIUM','WEAK')),
  provenance_sha256 TEXT NOT NULL,
  provenance_source TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_repair_atom_repair ON repair_atom_links(repair_id);
CREATE INDEX IF NOT EXISTS idx_repair_atom_atom ON repair_atom_links(atom_id);

CREATE TABLE IF NOT EXISTS repair_crystal_links (
  link_id TEXT PRIMARY KEY,
  repair_id TEXT NOT NULL REFERENCES repair_pairs(repair_id),
  crystal_id TEXT NOT NULL REFERENCES crystals(crystal_id),
  relation_type TEXT NOT NULL,
  linked_at TEXT NOT NULL,
  confidence TEXT NOT NULL CHECK(confidence IN ('EXACT','HIGH','MEDIUM','WEAK')),
  provenance_sha256 TEXT NOT NULL,
  provenance_source TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_repair_crystal_repair ON repair_crystal_links(repair_id);
CREATE INDEX IF NOT EXISTS idx_repair_crystal_crystal ON repair_crystal_links(crystal_id);

CREATE TRIGGER IF NOT EXISTS trg_life_events_no_update BEFORE UPDATE ON memory_lifecycle_events
BEGIN SELECT RAISE(ABORT, 'LIFE1 append-only: UPDATE blocked on memory_lifecycle_events'); END;
CREATE TRIGGER IF NOT EXISTS trg_life_events_no_delete BEFORE DELETE ON memory_lifecycle_events
BEGIN SELECT RAISE(ABORT, 'LIFE1 append-only: DELETE blocked on memory_lifecycle_events'); END;
CREATE TRIGGER IF NOT EXISTS trg_repair_atom_links_no_update BEFORE UPDATE ON repair_atom_links
BEGIN SELECT RAISE(ABORT, 'LIFE1 append-only: UPDATE blocked on repair_atom_links'); END;
CREATE TRIGGER IF NOT EXISTS trg_repair_atom_links_no_delete BEFORE DELETE ON repair_atom_links
BEGIN SELECT RAISE(ABORT, 'LIFE1 append-only: DELETE blocked on repair_atom_links'); END;
CREATE TRIGGER IF NOT EXISTS trg_repair_crystal_links_no_update BEFORE UPDATE ON repair_crystal_links
BEGIN SELECT RAISE(ABORT, 'LIFE1 append-only: UPDATE blocked on repair_crystal_links'); END;
CREATE TRIGGER IF NOT EXISTS trg_repair_crystal_links_no_delete BEFORE DELETE ON repair_crystal_links
BEGIN SELECT RAISE(ABORT, 'LIFE1 append-only: DELETE blocked on repair_crystal_links'); END;
"""

RAW_METADATA_KEYS = {
    "raw_text", "content_text", "raw_candidate_text", "raw_source_text",
    "bad_answer", "corrected_answer", "api_key", "apikey", "token", "secret", "bearer", "auth"
}


class Life1Error(RuntimeError):
    pass


def provenance_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(to_json(payload).encode("utf-8")).hexdigest()


def _validate_provenance_source(source: str) -> None:
    low = source.lower()
    if source not in ALLOWED_PROVENANCE_SOURCES:
        raise Life1Error(f"LIFE1 provenance source is not allowlisted: {source}")
    if any(marker in low for marker in FORBIDDEN_LABEL_PROVENANCE_MARKERS):
        raise Life1Error(f"LIFE1 provenance source contains forbidden witness marker: {source}")


def _validate_metadata(metadata: dict[str, Any]) -> None:
    keys = {str(k).lower() for k in metadata.keys()}
    if keys.intersection(RAW_METADATA_KEYS):
        raise Life1Error("LIFE1 metadata contains raw/private text field")
    serialized = json.dumps(metadata, ensure_ascii=False).lower()
    forbidden_fragments = [
        "sk-", "password=", "raw_candidate_text", "raw_source_text",
        "api_key=", "token=", "bearer ", "apikey="
    ]
    if any(fragment in serialized for fragment in forbidden_fragments):
        raise Life1Error("LIFE1 metadata appears to contain raw/private payload")


class Life1Recorder:
    """Sandbox-only append-only witness writer.

    This class records memory fate. It has no routing, review, promotion, or
    rejection authority.
    """

    def __init__(self, db: QVCHDatabase, *, sandbox_path: str = SANDBOX_DB_PATH, production_path: str = PRODUCTION_DB_PATH):
        self.db = db
        self.sandbox_path = sandbox_path
        self.production_path = production_path

    def apply_schema(self) -> None:
        self.db.conn.executescript(LIFE1_SCHEMA_SQL)
        self.db.conn.commit()

    def enable_sandbox_guard(self) -> None:
        self.db.enable_life1_sandbox_guard(sandbox_path=self.sandbox_path, production_path=self.production_path)

    @contextmanager
    def transition_context(self) -> Iterator[None]:
        with self.db.life1_transition_context():
            yield

    def verify_current_state(self, *, object_type: str, object_id: str, expected_state: str) -> None:
        current = self._current_state(object_type, object_id)
        if current != expected_state:
            raise Life1Error(f"from_state mismatch for {object_type}:{object_id}: expected {expected_state}, got {current}")

    def _current_state(self, object_type: str, object_id: str) -> str | None:
        if object_type == "memory_atom":
            row = self.db.one("SELECT epistemic_status AS state FROM memory_atoms WHERE atom_id=?", (object_id,))
        elif object_type == "crystal":
            row = self.db.one("SELECT lifecycle_state AS state FROM crystals WHERE crystal_id=?", (object_id,))
        elif object_type == "noumenon":
            row = self.db.one("SELECT state FROM noumena WHERE n_id=?", (object_id,))
        elif object_type == "repair_pair":
            row = self.db.one("SELECT validation_status AS state FROM repair_pairs WHERE repair_id=?", (object_id,))
        elif object_type == "skill_candidate":
            row = self.db.one("SELECT validation_status AS state FROM skill_candidates WHERE skill_id=?", (object_id,))
        elif object_type == "hypothesis":
            row = self.db.one("SELECT lifecycle_state AS state FROM hypotheses WHERE hypothesis_id=?", (object_id,))
        else:
            row = None
        return None if not row else row["state"]

    def record_lifecycle_event(
        self,
        *,
        object_type: str,
        object_id: str,
        from_state: str | None,
        to_state: str,
        transition_kind: str,
        occurred_at: str | None = None,
        reason_code: str,
        actor_or_source: str = "qvch_gateway",
        source_event_id: str | None = None,
        idempotency_key: str,
        provenance: dict[str, Any] | None = None,
        provenance_source: str = "qvch_gateway",
        metadata: dict[str, Any] | None = None,
        mutation_confirmed: bool = False,
    ) -> str:
        if transition_kind != BASELINE_UNKNOWN_HISTORY and not mutation_confirmed:
            raise Life1Error("LIFE1 refuses phantom lifecycle event without confirmed state transition")
        _validate_provenance_source(provenance_source)
        metadata = dict(metadata or {})
        _validate_metadata(metadata)
        provenance = dict(provenance or {"source": provenance_source, "object_type": object_type, "object_id": object_id})
        _validate_metadata(provenance)
        life_event_id = new_id("life")
        with self.db.authorized_write(), self.db.life1_transition_context():
            self.db.execute(
                """
                INSERT INTO memory_lifecycle_events(
                  life_event_id, object_type, object_id, from_state, to_state, transition_kind,
                  occurred_at, reason_code, actor_or_source, source_event_id, idempotency_key,
                  provenance_sha256, provenance_source, metadata_json, created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    life_event_id,
                    object_type,
                    object_id,
                    from_state,
                    to_state,
                    transition_kind,
                    occurred_at or now_iso(),
                    reason_code,
                    actor_or_source,
                    source_event_id,
                    idempotency_key,
                    provenance_hash(provenance),
                    provenance_source,
                    to_json(metadata),
                    now_iso(),
                ),
            )
        return life_event_id

    def link_repair_to_atom(
        self,
        *,
        repair_id: str,
        atom_id: str,
        relation_type: str,
        linked_at: str | None = None,
        confidence: str = "HIGH",
        idempotency_key: str,
        provenance: dict[str, Any] | None = None,
        provenance_source: str = "qvch_gateway",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        _validate_provenance_source(provenance_source)
        _validate_metadata(dict(metadata or {}))
        link_id = new_id("ral")
        with self.db.authorized_write(), self.db.life1_transition_context():
            self.db.execute(
                "INSERT INTO repair_atom_links VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    link_id,
                    repair_id,
                    atom_id,
                    relation_type,
                    linked_at or now_iso(),
                    confidence,
                    provenance_hash(provenance or {"source": provenance_source, "repair_id": repair_id, "atom_id": atom_id}),
                    provenance_source,
                    idempotency_key,
                    to_json(metadata or {}),
                ),
            )
        return link_id

    def link_repair_to_crystal(
        self,
        *,
        repair_id: str,
        crystal_id: str,
        relation_type: str,
        linked_at: str | None = None,
        confidence: str = "HIGH",
        idempotency_key: str,
        provenance: dict[str, Any] | None = None,
        provenance_source: str = "qvch_gateway",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        _validate_provenance_source(provenance_source)
        _validate_metadata(dict(metadata or {}))
        link_id = new_id("rcl")
        with self.db.authorized_write(), self.db.life1_transition_context():
            self.db.execute(
                "INSERT INTO repair_crystal_links VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    link_id,
                    repair_id,
                    crystal_id,
                    relation_type,
                    linked_at or now_iso(),
                    confidence,
                    provenance_hash(provenance or {"source": provenance_source, "repair_id": repair_id, "crystal_id": crystal_id}),
                    provenance_source,
                    idempotency_key,
                    to_json(metadata or {}),
                ),
            )
        return link_id
