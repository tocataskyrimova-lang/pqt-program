from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class EpisodeInput:
    episode_id: str
    occurred_at: str
    candidate_text: str
    source_text: str = ""
    source_pointer: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


LabelValue = Literal[0, 1, "EXCLUDED"]


@dataclass(frozen=True)
class LabelResult:
    episode_id: str
    value: LabelValue
    reason_codes: tuple[str, ...]
    window_days: int
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class SourceInspection:
    data_status: str
    source_path: str | None
    source_sha256: str | None
    snapshot_path: str | None
    snapshot_sha256: str | None
    table_names: tuple[str, ...]
    eligible_episode_count: int
    source_mode: str
    notes: tuple[str, ...] = ()
