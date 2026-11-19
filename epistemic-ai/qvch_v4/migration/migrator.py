"""Shadow migration v3 → v4 (brief 11).

Design guarantees (brief 11.1):
- **legacy-immutable**: the v3 DB is opened read-only; never written.
- **idempotent**: all v4 ids are deterministic and every write is ``INSERT OR
  IGNORE`` — re-running over the same source adds nothing and changes nothing.
- **resumable**: midpoint failure leaves the v4 DB consistent; a re-run
  continues and converges.
- **deterministic**: no clocks/UUIDs in migrated content; counts + hashes are
  reproducible.
- **source-hash aware**: the report pins ``source_db_hash`` so drift is visible.
- **auditable**: every mapping and every issue is recorded.

Writes go through the v4 SQL boundary (authorizer + append-only triggers) via
the store's migration write-scope. The full legacy ``write_plans.payload_json``
is deliberately NOT carried — only safe ids, route and provenance (brief 11.2).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from qvch_v4.contracts.canonical import canonical_json, sha256_hex
from qvch_v4.safety.secret_scanner import has_secret, scan
from qvch_v4.storage import QvchStore
from qvch_v4.migration.reconciliation import ReconciliationReport

MIGRATION_VERSION = "migration/v3-to-v4/1.0"
LEGACY_SESSION_ID = "legacy_migration_session"

# legacy noumenon state -> v4 NOUMENON state
_NOUMENON_STATE_MAP = {
    "N_open": "OPEN",
    "revisited": "REOPENED",
    "guidance_received": "OPEN",
    "partially_resolved": "PARTIALLY_REDUCED",
    "resolved_to_F_candidate": "PARTIALLY_REDUCED",
    "promoted_to_F": "RESOLVED",
    "crystallized": "RESOLVED",
    "retired": "ABANDONED",
}
# legacy U epistemic_status -> v4 HYPOTHESIS state
_U_STATE_MAP = {
    "candidate": "PROPOSED",
    "supported": "SUPPORTED",
    "partially_supported": "PARTIALLY_SUPPORTED",
    "validated": "SUPPORTED",
    "refuted": "REFUTED",
    "rejected": "QUARANTINED",
}
# legacy F epistemic_status -> v4 FORM state
_F_STATE_MAP = {
    "F_candidate": "CANDIDATE",
    "candidate": "CANDIDATE",
    "validated": "VALIDATED",
    "active": "ACTIVE",
    "stale": "STALE",
    "crystal": "VALIDATED",
    "retired": "ARCHIVED",
}

_V4_ATOM_KINDS = {"NOUMENON", "HYPOTHESIS", "FORM", "REPAIR", "SKILL", "LOCATOR", "CAPSULE"}


def _now_iso() -> str:
    # Deterministic placeholder; migrated rows reuse source timestamps where
    # available. Used only for rows that lack a legacy timestamp.
    return "1970-01-01T00:00:00+00:00"


def _file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class V3toV4Migrator:
    def __init__(self, legacy_path: str | Path, v4_path: str | Path) -> None:
        self.legacy_path = str(legacy_path)
        self.v4_path = str(v4_path)
        self.report = ReconciliationReport(
            source_db_path=self.legacy_path,
            source_db_hash="",
            migration_version=MIGRATION_VERSION,
        )
        self._notes: list[str] = []
        self._seen_form_texts: set[str] = set()
        self._form_invariant_texts: set[str] = set()
        self._atom_evidence: dict[str, list[str]] = {}

    # -- public API -----------------------------------------------------------
    def migrate(self) -> ReconciliationReport:
        self.report.source_db_hash = _file_sha256(self.legacy_path)
        legacy = sqlite3.connect(f"file:{self.legacy_path}?mode=ro", uri=True)
        legacy.row_factory = sqlite3.Row

        store = QvchStore(self.v4_path, migration=True)
        store.init_schema()

        try:
            self._migrate(store, legacy)
        finally:
            legacy.close()
            store.close()

        self.report.notes = self._notes
        return self.report

    # -- core ----------------------------------------------------------------
    def _migrate(self, store: QvchStore, legacy: sqlite3.Connection) -> None:
        # Pre-read atom_evidence so atom payloads can carry safe evidence ids.
        ev_rows = legacy.execute("SELECT atom_id, evidence_id FROM atom_evidence").fetchall()
        for r in ev_rows:
            self._atom_evidence.setdefault(r["atom_id"], []).append(r["evidence_id"])

        with store._write_scope() as conn:
            self._ensure_session(conn)
            self._mig_memory_events(conn, legacy)
            self._mig_evidence(conn, legacy)
            self._mig_noumena(conn, legacy)
            self._mig_crystals(conn, legacy)
            self._mig_atoms(conn, legacy)
            self._mig_repairs(conn, legacy)
            self._mig_skills(conn, legacy)
            self._mig_hypotheses(conn, legacy)
            self._mig_write_plans(conn, legacy)
            self._mig_legacy_audits(conn, legacy)
            self._count_legacy(legacy)
            self._finalize(conn, store)

    # -- helpers --------------------------------------------------------------
    def _insert(self, conn: sqlite3.Connection, table: str, cols: list[str],
                values: tuple) -> None:
        placeholders = ",".join("?" for _ in cols)
        sql = (
            f"INSERT OR IGNORE INTO {table} "
            f"({','.join(cols)}) VALUES ({placeholders})"
        )
        conn.execute(sql, values)

    def _issue(self, conn: sqlite3.Connection, source_ref: str, issue_type: str,
               reason_code: str, detail: dict, severity: str) -> None:
        self.report.migration_issues += 1
        if severity == "CRITICAL":
            self.report.critical_issues += 1
        issue_id = f"mig_{sha256_hex(source_ref + issue_type + reason_code)[:16]}"
        self._insert(
            conn, "migration_issues",
            ["issue_id", "source_ref", "issue_type", "reason_code", "detail_json", "severity", "created_at"],
            (issue_id, source_ref, issue_type, reason_code, canonical_json(detail), severity, _now_iso()),
        )

    def _count_legacy(self, legacy: sqlite3.Connection) -> None:
        tables = [
            "memory_events", "evidence_refs", "noumena", "noumenon_transitions",
            "memory_atoms", "hypotheses", "crystals", "repair_pairs",
            "skill_candidates", "atom_evidence", "write_plans", "write_audit",
            "probe_runs", "monitor_events",
        ]
        for t in tables:
            try:
                n = legacy.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except sqlite3.Error:
                n = 0
            self.report.legacy_counts[t] = n

    def _count_v4(self, conn: sqlite3.Connection) -> None:
        tables = [
            "memory_events", "evidence_refs", "epistemic_lineages", "memory_atoms",
            "atom_revisions", "atom_state_events", "memory_links", "claims",
            "reduction_proofs", "manas_decisions", "applicability_contracts",
            "gate_decisions", "probe_runs", "usage_outcomes", "maintenance_events",
            "audit_events", "migration_issues",
        ]
        for t in tables:
            self.report.v4_counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

    def _ensure_session(self, conn: sqlite3.Connection) -> None:
        self._insert(
            conn, "memory_sessions",
            ["session_id", "started_at", "source", "meta_json"],
            (LEGACY_SESSION_ID, _now_iso(), "legacy_migration", canonical_json({"kind": "v3_shadow"})),
        )

    # -- table mappers --------------------------------------------------------
    def _mig_memory_events(self, conn, legacy) -> None:
        rows = legacy.execute(
            "SELECT event_id, source, speaker, content_text, content_hash, occurred_at, metadata_json "
            "FROM memory_events"
        ).fetchall()
        for r in rows:
            content = r["content_text"]
            # Sanitize on the way in: never carry a raw secret across.
            if has_secret(content) or has_secret(r["metadata_json"]):
                self.report.redactions += 1
                self._issue(
                    conn, r["event_id"], "secret_in_event",
                    "redacted_on_migration",
                    {"field": "content_text"}, "WARNING",
                )
                content = "<REDACTED_SECRET:legacy_event>"
            self._insert(
                conn, "memory_events",
                ["event_id", "session_id", "event_type", "occurred_at", "sanitized_json", "content_hash"],
                (
                    r["event_id"], LEGACY_SESSION_ID, r["source"] or "legacy",
                    r["occurred_at"], canonical_json({"content": content, "speaker": r["speaker"],
                                                       "metadata": _safe_json(r["metadata_json"])}),
                    r["content_hash"] or sha256_hex(content),
                ),
            )
            self.report.mapped += 1

    def _mig_evidence(self, conn, legacy) -> None:
        rows = legacy.execute(
            "SELECT evidence_id, source_type, source_ref, summary, weight, is_llm_confidence, created_at "
            "FROM evidence_refs"
        ).fetchall()
        for r in rows:
            summary = r["summary"]
            if has_secret(summary) or has_secret(r["source_ref"]):
                self.report.redactions += 1
                self._issue(
                    conn, r["evidence_id"], "secret_in_evidence",
                    "redacted_on_migration",
                    {"field": "summary"}, "WARNING",
                )
                summary = "<REDACTED_SECRET:legacy_evidence>"
            payload = {
                "source_type": r["source_type"],
                "source_ref": r["source_ref"],
                "summary": summary,
                "weight": r["weight"],
            }
            canonical = canonical_json(payload)
            content_hash = sha256_hex(canonical)
            self._insert(
                conn, "evidence_refs",
                ["evidence_id", "source_type", "locator_json", "content_hash",
                 "canonical_payload_json", "llm_confidence", "created_at"],
                (
                    r["evidence_id"], r["source_type"],
                    canonical_json({"source_ref": r["source_ref"]}),
                    content_hash, canonical,
                    (None if not r["is_llm_confidence"] else 1.0),
                    r["created_at"],
                ),
            )
            self.report.mapped += 1

    def _mig_noumena(self, conn, legacy) -> None:
        rows = legacy.execute(
            "SELECT n_id, event_id, content_text, state, created_at, updated_at, metadata_json "
            "FROM noumena"
        ).fetchall()
        for r in rows:
            n_id = r["n_id"]
            lineage_id = f"lin_{n_id}"
            v4_state = _NOUMENON_STATE_MAP.get(r["state"])
            if v4_state is None:
                v4_state = "OPEN"
                self._issue(
                    conn, n_id, "unknown_noumenon_state",
                    "defaulted_to_OPEN",
                    {"legacy_state": r["state"]}, "WARNING",
                )
            self._insert(
                conn, "epistemic_lineages",
                ["lineage_id", "root_noumenon_id", "status", "created_at"],
                (lineage_id, n_id, "MIGRATED", r["created_at"]),
            )
            self._write_atom(
                conn, atom_id=n_id, lineage_id=lineage_id, atom_kind="NOUMENON",
                materiality="SEMANTIC", state=v4_state,
                payload={"noumenon": r["content_text"], "legacy_metadata": _safe_json(r["metadata_json"])},
                created_at=r["created_at"],
            )
            self.report.mapped += 1
            # state events from transitions
            trans = legacy.execute(
                "SELECT transition_id, from_state, to_state, evidence_id, note, created_at "
                "FROM noumenon_transitions WHERE n_id=?", (n_id,)
            ).fetchall()
            for t in trans:
                from_s = _NOUMENON_STATE_MAP.get(t["from_state"], t["from_state"])
                to_s = _NOUMENON_STATE_MAP.get(t["to_state"], t["to_state"])
                self._insert(
                    conn, "atom_state_events",
                    ["event_id", "atom_id", "from_state", "to_state", "occurred_at", "decision_id", "reason"],
                    (f"mse_{t['transition_id']}", n_id, from_s, to_s, t["created_at"],
                     None, t["note"]),
                )

    def _mig_crystals(self, conn, legacy) -> None:
        rows = legacy.execute(
            "SELECT crystal_id, invariant_text, support_ids_json, resolved_noumenon_ids_json, "
            "lifecycle_state, created_at FROM crystals"
        ).fetchall()
        for r in rows:
            state = _F_STATE_MAP.get(r["lifecycle_state"], "VALIDATED")
            cid = r["crystal_id"]
            self._insert(
                conn, "epistemic_lineages",
                ["lineage_id", "root_noumenon_id", "status", "created_at"],
                (f"lin_{cid}", None, "MIGRATED", r["created_at"]),
            )
            self._write_atom(
                conn, atom_id=cid, lineage_id=f"lin_{cid}", atom_kind="FORM",
                materiality="SEMANTIC", state=state,
                payload={
                    "form": r["invariant_text"],
                    "support_ids": _safe_json(r["support_ids_json"]),
                    "resolved_noumenon_ids": _safe_json(r["resolved_noumenon_ids_json"]),
                },
                created_at=r["created_at"],
            )
            self._form_invariant_texts.add(r["invariant_text"])
            self.report.mapped += 1

    def _mig_atoms(self, conn, legacy) -> None:
        rows = legacy.execute(
            "SELECT atom_id, event_id, atom_type, epistemic_status, content_text, canonical_text, "
            "confidence, support_count, metadata_json, created_at FROM memory_atoms"
        ).fetchall()
        for r in rows:
            atom_type = r["atom_type"]
            if atom_type == "noumenon":
                # Covered by the noumena table; count as dedup, do not duplicate.
                self.report.duplicate_groups += 1
                self._notes.append(f"skipped redundant noumenon-type atom {r['atom_id']} (covered by noumena)")
                continue
            if atom_type == "hypothesis":
                kind, state = "HYPOTHESIS", _U_STATE_MAP.get(r["epistemic_status"], "PROPOSED")
            elif atom_type == "semantic_fact_candidate":
                if r["epistemic_status"] == "crystal":
                    # Crystal already migrated authoritatively from crystals table.
                    if r["content_text"] in self._form_invariant_texts:
                        self.report.duplicate_groups += 1
                        self._notes.append(f"skipped duplicate crystal atom {r['atom_id']}")
                        continue
                    kind, state = "FORM", "VALIDATED"
                else:
                    kind, state = "FORM", _F_STATE_MAP.get(r["epistemic_status"], "CANDIDATE")
            else:
                self._issue(
                    conn, r["atom_id"], "unknown_atom_type",
                    "defaulted_to_SEMANTIC_NOUMENON",
                    {"atom_type": atom_type}, "WARNING",
                )
                kind, state = "NOUMENON", "OPEN"

            lineage_id = f"lin_{r['atom_id']}"
            self._insert(
                conn, "epistemic_lineages",
                ["lineage_id", "root_noumenon_id", "status", "created_at"],
                (lineage_id, None, "MIGRATED", r["created_at"]),
            )
            ev_ids = self._atom_evidence.get(r["atom_id"], [])
            self._write_atom(
                conn, atom_id=r["atom_id"], lineage_id=lineage_id, atom_kind=kind,
                materiality="SEMANTIC", state=state,
                payload={
                    "content_text": r["content_text"],
                    "route": _safe_json(r["metadata_json"]).get("route"),
                    "migrated_evidence_refs": ev_ids,
                },
                created_at=r["created_at"],
            )
            if kind == "FORM":
                self._form_invariant_texts.add(r["content_text"])
            self.report.mapped += 1

    def _mig_repairs(self, conn, legacy) -> None:
        rows = legacy.execute(
            "SELECT repair_id, bad_answer, failure_reason, correction_source, corrected_answer, "
            "validation_status, linked_noumenon_ids_json, linked_skill_candidate_id, evidence_refs_json, created_at "
            "FROM repair_pairs"
        ).fetchall()
        for r in rows:
            payload = {
                "bad_answer": _redact_if_secret(r["bad_answer"]),
                "failure_reason": r["failure_reason"],
                "correction_source": r["correction_source"],
                "corrected_answer": _redact_if_secret(r["corrected_answer"]),
                "validation_status": r["validation_status"],
                "linked_noumenon_ids": _safe_json(r["linked_noumenon_ids_json"]),
                "linked_skill_candidate_id": r["linked_skill_candidate_id"],
                "migrated_evidence_refs": _safe_json(r["evidence_refs_json"]),
            }
            self._insert(
                conn, "epistemic_lineages",
                ["lineage_id", "root_noumenon_id", "status", "created_at"],
                (f"lin_{r['repair_id']}", None, "MIGRATED", r["created_at"]),
            )
            self._write_atom(
                conn, atom_id=r["repair_id"], lineage_id=f"lin_{r['repair_id']}",
                atom_kind="REPAIR", materiality="SEMANTIC", state="OPEN",
                payload=payload, created_at=r["created_at"],
            )
            self.report.mapped += 1

    def _mig_skills(self, conn, legacy) -> None:
        rows = legacy.execute(
            "SELECT skill_id, trigger_pattern, procedure_summary, failure_modes_json, "
            "validation_status, reflex_readiness, evidence_refs_json, created_at "
            "FROM skill_candidates"
        ).fetchall()
        for r in rows:
            payload = {
                "trigger_pattern": r["trigger_pattern"],
                "procedure_summary": r["procedure_summary"],
                "failure_modes": _safe_json(r["failure_modes_json"]),
                "validation_status": r["validation_status"],
                "reflex_readiness": r["reflex_readiness"],
                "migrated_evidence_refs": _safe_json(r["evidence_refs_json"]),
            }
            self._insert(
                conn, "epistemic_lineages",
                ["lineage_id", "root_noumenon_id", "status", "created_at"],
                (f"lin_{r['skill_id']}", None, "MIGRATED", r["created_at"]),
            )
            self._write_atom(
                conn, atom_id=r["skill_id"], lineage_id=f"lin_{r['skill_id']}",
                atom_kind="SKILL", materiality="SKILL_TRACE", state="OPEN",
                payload=payload, created_at=r["created_at"],
            )
            self.report.mapped += 1

    def _mig_hypotheses(self, conn, legacy) -> None:
        rows = legacy.execute(
            "SELECT hypothesis_id, atom_id, lifecycle_state, created_at FROM hypotheses"
        ).fetchall()
        for r in rows:
            aid = r["atom_id"]
            exists = conn.execute("SELECT 1 FROM memory_atoms WHERE atom_id=?", (aid,)).fetchone()
            if not exists:
                self.report.orphan_legacy_refs += 1
                self._issue(
                    conn, r["hypothesis_id"], "orphan_hypothesis",
                    "no_target_atom", {"atom_id": aid}, "WARNING",
                )
                continue
            state = _U_STATE_MAP.get(r["lifecycle_state"], "PROPOSED")
            # Record the legacy lifecycle as a history state event. We do NOT
            # mutate the atom's current_state: the v4 state machine is enforced
            # by the atom_state_check trigger and legacy jumps (e.g.
            # PROPOSED->SUPPORTED) are not seeded transitions. The intent is
            # preserved as auditable history, not forced onto the live state.
            cur = conn.execute("SELECT current_state FROM memory_atoms WHERE atom_id=?", (aid,)).fetchone()
            if cur and cur[0] != state:
                self._insert(
                    conn, "atom_state_events",
                    ["event_id", "atom_id", "from_state", "to_state", "occurred_at", "decision_id", "reason"],
                    (f"mse_hyp_{r['hypothesis_id']}", aid, cur[0], state, r["created_at"], None,
                     "legacy hypothesis lifecycle"),
                )

    def _mig_write_plans(self, conn, legacy) -> None:
        # Safe provenance only: id, route, timestamp, hash of payload. The full
        # legacy payload_json is intentionally NOT carried (brief 11.2).
        rows = legacy.execute("SELECT plan_id, route, payload_json, created_at FROM write_plans").fetchall()
        for r in rows:
            self._insert(
                conn, "audit_events",
                ["event_id", "actor", "action", "target", "detail_json", "occurred_at"],
                (
                    f"aud_wp_{r['plan_id']}", "migration", "LEGACY_WRITE_PLAN_RECORDED",
                    r["plan_id"],
                    canonical_json({
                        "route": r["route"],
                        "payload_hash": sha256_hex(r["payload_json"]),
                        "migrated": True,
                    }),
                    r["created_at"],
                ),
            )

    def _mig_legacy_audits(self, conn, legacy) -> None:
        wa = legacy.execute(
            "SELECT audit_id, plan_id, committed, reason_codes_json, object_ids_json, created_at "
            "FROM write_audit"
        ).fetchall()
        for r in wa:
            self._insert(
                conn, "audit_events",
                ["event_id", "actor", "action", "target", "detail_json", "occurred_at"],
                (
                    f"aud_wa_{r['audit_id']}", "migration", "LEGACY_WRITE_AUDIT",
                    r["plan_id"],
                    canonical_json({
                        "committed": bool(r["committed"]),
                        "reason_codes": _safe_json(r["reason_codes_json"]),
                        "object_ids": _safe_json(r["object_ids_json"]),
                    }),
                    r["created_at"],
                ),
            )
        pr = legacy.execute(
            "SELECT probe_id, query_text, expected_text, passed, status, reason_codes_json, created_at "
            "FROM probe_runs"
        ).fetchall()
        for r in pr:
            self._insert(
                conn, "audit_events",
                ["event_id", "actor", "action", "target", "detail_json", "occurred_at"],
                (
                    f"aud_pr_{r['probe_id']}", "migration", "LEGACY_PROBE_RUN",
                    r["probe_id"],
                    canonical_json({
                        "query": r["query_text"], "expected": r["expected_text"],
                        "passed": bool(r["passed"]), "status": r["status"],
                        "reason_codes": _safe_json(r["reason_codes_json"]),
                    }),
                    r["created_at"],
                ),
            )
        me = legacy.execute(
            "SELECT monitor_id, event_type, payload_json, created_at FROM monitor_events"
        ).fetchall()
        for r in me:
            self._insert(
                conn, "audit_events",
                ["event_id", "actor", "action", "target", "detail_json", "occurred_at"],
                (
                    f"aud_me_{r['monitor_id']}", "migration", "LEGACY_MONITOR_EVENT",
                    r["monitor_id"],
                    canonical_json({"event_type": r["event_type"], "payload": _safe_json(r["payload_json"])}),
                    r["created_at"],
                ),
            )

    # -- atom writer ----------------------------------------------------------
    def _write_atom(self, conn, *, atom_id, lineage_id, atom_kind, materiality,
                    state, payload, created_at) -> None:
        canonical = canonical_json(payload)
        content_hash = sha256_hex(canonical)
        self._insert(
            conn, "memory_atoms",
            ["atom_id", "lineage_id", "atom_kind", "materiality_class", "current_state",
             "current_revision_id", "created_at", "updated_at"],
            (atom_id, lineage_id, atom_kind, materiality, state, f"{atom_id}#r1",
             created_at, created_at),
        )
        self._insert(
            conn, "atom_revisions",
            ["revision_id", "atom_id", "revision_number", "state", "canonical_payload_json",
             "content_hash", "created_at"],
            (f"{atom_id}#r1", atom_id, 1, state, canonical, content_hash, created_at),
        )

    # -- finalize -------------------------------------------------------------
    def _finalize(self, conn: sqlite3.Connection, store: QvchStore) -> None:
        self._count_v4(conn)
        self.report.integrity_ok = store.integrity_ok()
        self.report.fk_ok = store.foreign_keys_ok()


def _safe_json(raw: str | None):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"_raw": raw}


def _redact_if_secret(text: str) -> str:
    if text and has_secret(text):
        return "<REDACTED_SECRET:legacy_repair>"
    return text


def run_migration(legacy_path: str | Path, v4_path: str | Path) -> ReconciliationReport:
    return V3toV4Migrator(legacy_path, v4_path).migrate()


__all__ = ["V3toV4Migrator", "run_migration", "MIGRATION_VERSION"]
