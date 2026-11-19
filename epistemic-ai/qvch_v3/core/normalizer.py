from __future__ import annotations

import hashlib
from qvch_v3.contracts.models import NormalizedEvent, RawExperience, new_id


def normalize_experience(raw: RawExperience) -> NormalizedEvent:
    content = " ".join((raw.content or "").strip().split())
    return NormalizedEvent(
        event_id=new_id("evt"),
        source=raw.source,
        speaker=raw.speaker,
        content=content,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        timestamp=raw.timestamp,
        metadata={**raw.metadata, "raw_id": raw.raw_id},
    )

