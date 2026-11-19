from __future__ import annotations

from contextlib import nullcontext

from qvch_v3.contracts.models import WritePlan, WriteReceipt, new_id, now_iso, to_json
from qvch_v3.manas.conflict import detect_conflict
from qvch_v3.safety.scanner import redact_text
from qvch_v3.storage.db import QVCHDatabase


def _canon(text: str) -> str:
    return " ".join(text.lower().split())


class MemoryWriteGateway:
    """Only legal persistence boundary. Accepts WritePlan, never raw text."""

    def __init__(self, db: QVCHDatabase, life1_recorder=None):
        self.db = db
        self.life1_recorder = life1_recorder

    def commit(self, plan: WritePlan) -> WriteReceipt:
        if not isinstance(plan, WritePlan):
            raise TypeError("MemoryWriteGateway.commit accepts WritePlan only")
        object_ids: dict[str, str] = {}
        ok, fail_reasons = self._verify_plan(plan)
        if not ok:
            with self.db.authorized_write():
                self._audit(plan, False, {}, fail_reasons)
            return WriteReceipt(new_id("receipt"), plan.plan_id, False, {}, fail_reasons)

        reasons: list[str] = ["committed_via_gateway"]
        try:
            with self.db.transaction(), self.db.authorized_write(), self._life1_context():
                self._insert_event(plan)
                self.db.execute(
                    "INSERT INTO write_plans(plan_id, route, payload_json, created_at) VALUES(?,?,?,?)",
                    (plan.plan_id, plan.route, to_json(plan), plan.created_at),
                )
                self._insert_evidence_refs(plan)
                if plan.route == "N" and plan.noumenon:
                    n = plan.noumenon
                    self.db.execute(
                        "INSERT INTO noumena VALUES(?,?,?,?,?,?,?)",
                        (n.n_id, n.event_id, n.content, n.state, n.created_at, n.created_at, to_json(n.metadata)),
                    )
                    self._transition(n.n_id, "none", "N_open", None, "created open noumenon")
                    object_ids["noumenon"] = n.n_id
                    self._life1_record("noumenon", n.n_id, None, "N_open", "written", plan, "noumenon_created")
                    self._insert_atoms(plan, status="N", object_ids=object_ids)
                elif plan.route == "U":
                    self._insert_atoms(plan, status="U", object_ids=object_ids)
                    atom_id = object_ids.get("atom") or object_ids.get("duplicate_atom")
                    if atom_id and "atom" in object_ids:
                        hyp_id = new_id("hyp")
                        self.db.execute("INSERT INTO hypotheses VALUES(?,?,?,?)", (hyp_id, atom_id, "candidate", now_iso()))
                        self._life1_record("hypothesis", hyp_id, None, "candidate", "written", plan, "hypothesis_created")
                elif plan.route == "F_candidate":
                    self._insert_atoms(plan, status="F_candidate", object_ids=object_ids)
                elif plan.route == "crystal" and plan.crystal:
                    c = plan.crystal
                    self.db.execute(
                        "INSERT INTO crystals VALUES(?,?,?,?,?,?)",
                        (c.crystal_id, c.invariant_text, to_json(c.support_ids), to_json(c.resolved_noumenon_ids), c.lifecycle_state, now_iso()),
                    )
                    object_ids["crystal"] = c.crystal_id
                    self._life1_record("crystal", c.crystal_id, None, c.lifecycle_state, "written", plan, "crystal_created")
                    self._insert_atoms(plan, status="crystal", object_ids=object_ids)
                elif plan.route == "repair_pair" and plan.repair_pair:
                    r = plan.repair_pair
                    self.db.execute(
                        "INSERT INTO repair_pairs VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            r.repair_id,
                            r.event_id,
                            redact_text(r.bad_answer),
                            redact_text(r.failure_reason),
                            redact_text(r.correction_source),
                            redact_text(r.corrected_answer),
                            r.validation_status,
                            to_json(r.linked_noumenon_ids),
                            r.linked_skill_candidate_id,
                            to_json([e.__dict__ for e in r.evidence_refs]),
                            now_iso(),
                        ),
                    )
                    object_ids["repair_pair"] = r.repair_id
                    self._life1_record("repair_pair", r.repair_id, None, r.validation_status, "written", plan, "repair_pair_created")
                elif plan.route == "skill_candidate" and plan.skill_candidate:
                    s = plan.skill_candidate
                    self.db.execute(
                        "INSERT INTO skill_candidates VALUES(?,?,?,?,?,?,?,?,?)",
                        (
                            s.skill_id,
                            s.trigger_pattern,
                            to_json(s.successful_repairs),
                            s.procedure_summary,
                            to_json(s.failure_modes),
                            s.validation_status,
                            s.reflex_readiness,
                            to_json([e.__dict__ for e in s.evidence_refs]),
                            now_iso(),
                        ),
                    )
                    object_ids["skill_candidate"] = s.skill_id
                    self._life1_record("skill_candidate", s.skill_id, None, s.validation_status, "written", plan, "skill_candidate_created")
                else:
                    reasons = ["nothing_to_commit"]
                    self._audit(plan, False, object_ids, reasons)
                    return WriteReceipt(new_id("receipt"), plan.plan_id, False, object_ids, reasons)
                self._audit(plan, True, object_ids, reasons)
        except Exception as exc:
            with self.db.authorized_write():
                fail = ["gateway_transaction_rolled_back", f"{type(exc).__name__}: {exc}"]
                self._audit(plan, False, object_ids, fail)
            return WriteReceipt(new_id("receipt"), plan.plan_id, False, object_ids, fail)
        return WriteReceipt(new_id("receipt"), plan.plan_id, True, object_ids, reasons)

    def _life1_context(self):
        return self.life1_recorder.transition_context() if self.life1_recorder else nullcontext()

    def _life1_record(self, object_type: str, object_id: str, from_state: str | None, to_state: str, transition_kind: str, plan: WritePlan, reason_code: str) -> None:
        if not self.life1_recorder:
            return
        self.life1_recorder.record_lifecycle_event(
            object_type=object_type,
            object_id=object_id,
            from_state=from_state,
            to_state=to_state,
            transition_kind=transition_kind,
            occurred_at=now_iso(),
            reason_code=reason_code,
            actor_or_source="qvch_gateway",
            source_event_id=plan.event.event_id,
            idempotency_key=f"{plan.plan_id}:{object_type}:{object_id}:{transition_kind}:{to_state}",
            provenance={"source":"qvch_gateway","plan_id":plan.plan_id,"route":plan.route,"object_type":object_type,"object_id":object_id},
            provenance_source="qvch_gateway",
            metadata={"route": plan.route, "reason_code": reason_code},
            mutation_confirmed=True,
        )

    def _verify_plan(self, plan: WritePlan) -> tuple[bool, list[str]]:
        reasons = []
        if not plan.event or not plan.event.event_id:
            reasons.append("missing_normalized_event")
        if not plan.manas_review or not plan.manas_review.approved:
            reasons.append("missing_or_rejected_manas_review")
        if plan.manas_review.llm_confidence_is_evidence:
            reasons.append("llm_confidence_cannot_be_evidence")
        if not plan.safety_review or not plan.safety_review.passed:
            reasons.append("missing_or_failed_safety_review")
        if plan.route in {"N", "U", "F_candidate", "crystal"} and not plan.atoms:
            reasons.append("missing_atomization")
        if plan.route == "crystal":
            non_llm = [e for e in plan.validation.evidence_refs if not e.is_llm_confidence]
            if not plan.validation.passed or not non_llm:
                reasons.append("crystal_requires_non_llm_validation_evidence")
        if plan.route in {"F_candidate", "crystal"}:
            conflict = detect_conflict(self.db, plan.safety_review.redacted_content)
            if conflict.conflict_detected or plan.validation.conflict_detected:
                reasons.extend(conflict.reason_codes or ["conflict_detected"])
        if plan.safety_review.contains_secret and not plan.safety_review.redaction_applied:
            reasons.append("secret_without_redaction")
        return not reasons, reasons

    def _insert_event(self, plan: WritePlan) -> None:
        e = plan.event
        content = plan.safety_review.redacted_content
        self.db.execute(
            "INSERT OR IGNORE INTO memory_events VALUES(?,?,?,?,?,?,?)",
            (e.event_id, e.source, e.speaker, content, e.content_hash, e.timestamp, to_json(e.metadata)),
        )

    def _insert_evidence_refs(self, plan: WritePlan) -> None:
        for ev in plan.validation.evidence_refs:
            self.db.execute(
                "INSERT OR IGNORE INTO evidence_refs VALUES(?,?,?,?,?,?,?)",
                (ev.evidence_id, ev.source_type, ev.source_ref, ev.summary, ev.weight, 1 if ev.is_llm_confidence else 0, now_iso()),
            )

    def _insert_atoms(self, plan: WritePlan, *, status: str, object_ids: dict[str, str]) -> None:
        for atom in plan.atoms:
            atom_id = new_id("atom")
            content = plan.safety_review.redacted_content or atom.content
            support_count = self._new_support_count(plan)
            existing = self.db.one(
                "SELECT atom_id FROM memory_atoms WHERE canonical_text=? AND epistemic_status=?",
                (_canon(content), status),
            )
            if existing:
                object_ids.setdefault("duplicate_atom", existing["atom_id"])
                added = self._link_atom_evidence(existing["atom_id"], plan)
                if added:
                    self.db.execute(
                        "UPDATE memory_atoms SET support_count = support_count + ? WHERE atom_id = ?",
                        (added, existing["atom_id"]),
                    )
                    self._life1_record("memory_atom", existing["atom_id"], status, status, "evidence_accumulated", plan, "atom_evidence_accumulated")
                object_ids["evidence_accumulated"] = str(added)
                continue
            self.db.execute(
                "INSERT INTO memory_atoms VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    atom_id,
                    plan.event.event_id,
                    atom.atom_type,
                    status,
                    content,
                    _canon(content),
                    atom.confidence,
                    support_count,
                    to_json(atom.metadata),
                    now_iso(),
                ),
            )
            self._link_atom_evidence(atom_id, plan)
            object_ids.setdefault("atom", atom_id)
            self._life1_record("memory_atom", atom_id, None, status, "written", plan, "atom_created")

    def _new_support_count(self, plan: WritePlan) -> int:
        return len([e for e in plan.validation.evidence_refs if not e.is_llm_confidence])

    def _link_atom_evidence(self, atom_id: str, plan: WritePlan) -> int:
        added = 0
        for ev in plan.validation.evidence_refs:
            if ev.is_llm_confidence:
                continue
            before = self.db.scalar("SELECT COUNT(*) FROM atom_evidence WHERE atom_id=? AND evidence_id=?", (atom_id, ev.evidence_id)) or 0
            self.db.execute("INSERT OR IGNORE INTO atom_evidence VALUES(?,?,?)", (atom_id, ev.evidence_id, now_iso()))
            after = self.db.scalar("SELECT COUNT(*) FROM atom_evidence WHERE atom_id=? AND evidence_id=?", (atom_id, ev.evidence_id)) or 0
            if after > before:
                added += 1
        return added

    def _transition(self, n_id: str, from_state: str, to_state: str, evidence_id: str | None, note: str) -> str:
        tid = new_id("ntr")
        self.db.execute("INSERT INTO noumenon_transitions VALUES(?,?,?,?,?,?,?)", (tid, n_id, from_state, to_state, evidence_id, note, now_iso()))
        return tid

    def _audit(self, plan: WritePlan, committed: bool, object_ids: dict[str, str], reasons: list[str]) -> None:
        self.db.execute(
            "INSERT INTO write_audit VALUES(?,?,?,?,?,?)",
            (new_id("audit"), plan.plan_id, 1 if committed else 0, to_json(reasons), to_json(object_ids), now_iso()),
        )
