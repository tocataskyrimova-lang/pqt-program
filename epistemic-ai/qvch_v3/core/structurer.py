from __future__ import annotations

import re
from qvch_v3.contracts.models import MemoryAtomDraft, NormalizedEvent, StructuredDraft, new_id

_QUESTION_RE = re.compile(r"\?|\b(where|what|how|unknown|не знаю|где|что|как)\b", re.I)
_HYP_RE = re.compile(r"\b(maybe|may|might|likely|possibly|plan|should|гипотез|возможно|может|план)\b", re.I)


def structure_event(event: NormalizedEvent, *, llm_confidence: float | None = None) -> StructuredDraft:
    text = event.content
    if _QUESTION_RE.search(text):
        atom_type, route = "noumenon", "N"
    elif _HYP_RE.search(text):
        atom_type, route = "hypothesis", "U"
    else:
        atom_type, route = "semantic_fact_candidate", "F_candidate"
    atom = MemoryAtomDraft(content=text, atom_type=atom_type, route=route, confidence=0.5, metadata={"source_event_id": event.event_id})
    return StructuredDraft(draft_id=new_id("draft"), event_id=event.event_id, summary=text[:160], atoms=[atom], llm_confidence=llm_confidence)
