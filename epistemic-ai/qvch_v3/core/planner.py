from __future__ import annotations

from qvch_v3.contracts.models import (
    CrystalRecord, EvidenceRef, ManasReview, MemoryAtomDraft, NormalizedEvent,
    NoumenonRecord, RepairPair, SafetyReview, SkillCandidate, StructuredDraft,
    ValidationResult, WritePlan, new_id,
)


def build_write_plan(
    *,
    event: NormalizedEvent,
    draft: StructuredDraft,
    manas_review: ManasReview,
    safety_review: SafetyReview,
    validation: ValidationResult,
) -> WritePlan:
    atoms = list(draft.atoms)
    route = manas_review.route
    content = safety_review.redacted_content
    noumenon = None
    crystal = None
    if route == "N":
        noumenon = NoumenonRecord(new_id("N"), event.event_id, content)
    if route == "crystal":
        crystal = CrystalRecord(new_id("cr"), content, [e.evidence_id for e in validation.evidence_refs], [])
    return WritePlan(new_id("plan"), event, draft, manas_review, safety_review, validation, route, atoms, noumenon=noumenon, crystal=crystal)


def build_repair_plan(
    *,
    event: NormalizedEvent,
    safety_review: SafetyReview,
    bad_answer: str,
    failure_reason: str,
    correction_source: str,
    corrected_answer: str,
    linked_noumenon_ids: list[str] | None = None,
    evidence_refs: list[EvidenceRef] | None = None,
) -> WritePlan:
    evidence_refs = list(evidence_refs or [])
    repair = RepairPair(
        repair_id=new_id("repair"), event_id=event.event_id, bad_answer=bad_answer,
        failure_reason=failure_reason, correction_source=correction_source,
        corrected_answer=safety_review.redacted_content if corrected_answer == event.content else corrected_answer,
        linked_noumenon_ids=list(linked_noumenon_ids or []), evidence_refs=evidence_refs,
    )
    draft = StructuredDraft(new_id("draft"), event.event_id, "repair pair", [])
    manas = ManasReview(new_id("manas"), draft.draft_id, True, "repair_pair", ["repair_pair_lineage"])
    validation = ValidationResult(new_id("val"), bool(evidence_refs), evidence_refs, reason_codes=["repair_candidate"])
    return WritePlan(new_id("plan"), event, draft, manas, safety_review, validation, "repair_pair", [], repair_pair=repair)


def build_skill_plan(*, event: NormalizedEvent, safety_review: SafetyReview, trigger_pattern: str, repair_ids: list[str], procedure_summary: str, failure_modes: list[str] | None = None) -> WritePlan:
    skill = SkillCandidate(new_id("skill"), trigger_pattern, repair_ids, procedure_summary, list(failure_modes or []), reflex_readiness=0.0)
    draft = StructuredDraft(new_id("draft"), event.event_id, "skill candidate", [])
    manas = ManasReview(new_id("manas"), draft.draft_id, True, "skill_candidate", ["repeated_repair_pattern"])
    safety = safety_review
    validation = ValidationResult(new_id("val"), len(repair_ids) >= 2, [], reason_codes=["skill_candidate_requires_future_validation"])
    return WritePlan(new_id("plan"), event, draft, manas, safety, validation, "skill_candidate", [], skill_candidate=skill)
