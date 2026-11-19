from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from typing import Any, Literal

EpistemicRoute = Literal["N", "U", "F_candidate", "crystal", "repair_pair", "skill_candidate"]
NoumenonState = Literal[
    "N_open", "revisited", "guidance_received", "partially_resolved",
    "resolved_to_F_candidate", "promoted_to_F", "crystallized", "retired"
]
RepairValidation = Literal["candidate", "validated", "rejected", "dataset_candidate"]
SkillValidation = Literal["skill_candidate", "skill_trace", "validated_skill", "cognitive_reflex", "rejected"]
CrystalState = Literal["candidate", "promoted", "retired"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def to_json(value: Any) -> str:
    if value is None:
        return "{}"
    if is_dataclass(value):
        value = asdict(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def from_json(raw: str | None, default: Any = None) -> Any:
    if not raw:
        return {} if default is None else default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {} if default is None else default


@dataclass(frozen=True)
class RawExperience:
    content: str
    source: str = "dialogue"
    speaker: str = "user"
    raw_id: str = field(default_factory=lambda: new_id("raw"))
    timestamp: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedEvent:
    event_id: str
    source: str
    speaker: str
    content: str
    content_hash: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryAtomDraft:
    content: str
    atom_type: str
    route: EpistemicRoute
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StructuredDraft:
    draft_id: str
    event_id: str
    summary: str
    atoms: list[MemoryAtomDraft]
    structurer: str = "deterministic_v0"
    llm_confidence: float | None = None


@dataclass(frozen=True)
class ManasReview:
    review_id: str
    draft_id: str
    approved: bool
    route: EpistemicRoute
    reason_codes: list[str]
    llm_confidence_is_evidence: bool = False


@dataclass(frozen=True)
class SafetyReview:
    review_id: str
    event_id: str
    passed: bool
    contains_secret: bool
    redaction_applied: bool
    redacted_content: str
    reason_codes: list[str]


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    source_type: str
    source_ref: str
    summary: str
    weight: float = 1.0
    is_llm_confidence: bool = False


@dataclass(frozen=True)
class ValidationResult:
    validation_id: str
    passed: bool
    evidence_refs: list[EvidenceRef]
    conflict_detected: bool = False
    duplicate_of: str | None = None
    reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NoumenonRecord:
    n_id: str
    event_id: str
    content: str
    state: NoumenonState = "N_open"
    created_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NoumenonTransition:
    transition_id: str
    n_id: str
    from_state: str
    to_state: str
    evidence_id: str | None
    note: str
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class NResolutionLink:
    link_id: str
    n_id: str
    target_type: str
    target_id: str
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class RepairPair:
    repair_id: str
    event_id: str
    bad_answer: str
    failure_reason: str
    correction_source: str
    corrected_answer: str
    validation_status: RepairValidation = "candidate"
    linked_noumenon_ids: list[str] = field(default_factory=list)
    linked_skill_candidate_id: str | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


@dataclass(frozen=True)
class SkillCandidate:
    skill_id: str
    trigger_pattern: str
    successful_repairs: list[str]
    procedure_summary: str
    failure_modes: list[str]
    validation_status: SkillValidation = "skill_candidate"
    reflex_readiness: float = 0.0
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


@dataclass(frozen=True)
class CrystalRecord:
    crystal_id: str
    invariant_text: str
    support_ids: list[str]
    resolved_noumenon_ids: list[str]
    lifecycle_state: CrystalState = "candidate"


@dataclass(frozen=True)
class WritePlan:
    plan_id: str
    event: NormalizedEvent
    draft: StructuredDraft
    manas_review: ManasReview
    safety_review: SafetyReview
    validation: ValidationResult
    route: EpistemicRoute
    atoms: list[MemoryAtomDraft]
    noumenon: NoumenonRecord | None = None
    repair_pair: RepairPair | None = None
    skill_candidate: SkillCandidate | None = None
    crystal: CrystalRecord | None = None
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class WriteReceipt:
    receipt_id: str
    plan_id: str
    committed: bool
    object_ids: dict[str, str]
    reason_codes: list[str]


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    status: str
    answer_candidates: list[dict[str, Any]]
    confidence: float
    evidence: list[dict[str, Any]]
    lineage: list[dict[str, Any]]


@dataclass(frozen=True)
class MemoryProbeResult:
    probe_id: str
    passed: bool
    query: str
    expected: str
    status: str
    reason_codes: list[str]
