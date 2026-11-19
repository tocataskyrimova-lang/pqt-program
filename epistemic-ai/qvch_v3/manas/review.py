from __future__ import annotations

from qvch_v3.contracts.models import ManasReview, StructuredDraft, new_id


def review_draft(draft: StructuredDraft, *, has_evidence: bool = False) -> ManasReview:
    route = draft.atoms[0].route if draft.atoms else "N"
    reasons: list[str] = []
    if draft.llm_confidence is not None:
        reasons.append("llm_confidence_not_evidence")
    if route == "F_candidate" and not has_evidence:
        reasons.append("fact_candidate_not_crystal")
    return ManasReview(
        review_id=new_id("manas"),
        draft_id=draft.draft_id,
        approved=bool(draft.atoms),
        route=route,
        reason_codes=reasons or ["approved_conservative_route"],
        llm_confidence_is_evidence=False,
    )
