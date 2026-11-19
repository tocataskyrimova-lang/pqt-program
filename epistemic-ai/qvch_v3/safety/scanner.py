from __future__ import annotations

import re
from qvch_v3.contracts.models import NormalizedEvent, SafetyReview, new_id

_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{6,}"),
    re.compile(r"(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*['\"]?[^\s'\"]+"),
]


def scan_event(event: NormalizedEvent) -> SafetyReview:
    text = event.content
    redacted = text
    found = False
    for pat in _PATTERNS:
        if pat.search(redacted):
            found = True
            redacted = pat.sub("<REDACTED_SECRET>", redacted)
    return SafetyReview(
        review_id=new_id("safe"),
        event_id=event.event_id,
        passed=True,
        contains_secret=found,
        redaction_applied=found,
        redacted_content=redacted,
        reason_codes=["secret_redacted"] if found else ["safety_pass"],
    )


def redact_text(text: str) -> str:
    class E: pass
    e = E(); e.content = text; e.event_id = "inline"
    return scan_event(e).redacted_content
