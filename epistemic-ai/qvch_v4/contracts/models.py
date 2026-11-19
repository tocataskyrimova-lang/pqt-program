"""Immutable first-class cognitive contracts for QVCH v4.1.

These are pure data. No routing, approval, or persistence authority lives here.
The MANAS Decision Envelope (manas/service.py) is the only object that may
authorize a write; it binds cryptographically to these structures by hash.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import canonical_json, hash_json, hash_text


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


# ---------------------------------------------------------------------------
# QNUF-Forge input / output (brief 5.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RawThoughtOutput:
    """Untrusted output from an external LLM adapter.

    Raw input text stays ephemeral: it is never stored as a raw blob. Only its
    sha256 and explicit structured fields are passed to the Forge.
    """

    source_text: str
    observed_model_output: str = ""
    structured_fields: dict[str, Any] = field(default_factory=dict)
    model_id: str | None = None
    raw_id: str = field(default_factory=lambda: new_id("raw"))

    def source_text_hash(self) -> str:
        return hash_text(self.source_text)


@dataclass(frozen=True)
class VerbatimAnchor:
    """Exact span of source text backing an EXTRACTED claim (Postulate 0)."""

    source_event_id: str
    start_offset: int
    end_offset: int
    quote_hash: str
    # When the span contains a secret it is NOT stored; only a redacted marker
    # and a non-reversible fingerprint survive.
    redacted: bool = False
    fingerprint: str | None = None
    quote: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "source_event_id": self.source_event_id,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "quote_hash": self.quote_hash,
            "redacted": self.redacted,
            "fingerprint": self.fingerprint,
            "quote": self.quote,
        }


@dataclass(frozen=True)
class DraftClaim:
    claim_id: str
    claim_type: str  # enums.ClaimType value
    subject: str
    predicate: str
    value: str
    anchor: VerbatimAnchor | None = None
    normative_source_ref: str | None = None
    materiality_class: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type,
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "anchor": self.anchor.to_payload() if self.anchor else None,
            "normative_source_ref": self.normative_source_ref,
            "materiality_class": self.materiality_class,
        }


@dataclass(frozen=True)
class NoumenonSlot:
    """An explicit unknown the Forge records as a candidate N target."""

    slot_id: str
    description: str
    weight: float = 1.0
    baseline: bool = True


@dataclass(frozen=True)
class ProposedTransformation:
    transformation_id: str
    description: str
    from_state: str | None = None
    to_state: str | None = None


@dataclass(frozen=True)
class StructuredDraftCandidate:
    draft_id: str
    claims: list[DraftClaim]
    noumenon_slots: list[NoumenonSlot] = field(default_factory=list)
    transformations: list[ProposedTransformation] = field(default_factory=list)
    source_text_hash: str = ""
    model_id: str | None = None
    forbidden_fields_detected: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CanonicalStructuredDraft:
    """Validated, canonicalized, hash-bound draft the Forge emits."""

    draft_id: str
    claims: list[DraftClaim]
    noumenon_slots: list[NoumenonSlot]
    transformations: list[ProposedTransformation]
    source_text_hash: str
    model_id: str | None
    forbidden_fields_detected: tuple[str, ...]
    canonical_hash: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "claims": [c.to_payload() for c in self.claims],
            "noumenon_slots": [s.__dict__ for s in self.noumenon_slots],
            "transformations": [t.__dict__ for t in self.transformations],
            "source_text_hash": self.source_text_hash,
            "model_id": self.model_id,
            "forbidden_fields_detected": list(self.forbidden_fields_detected),
        }


# ---------------------------------------------------------------------------
# Provenance / plans
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProposedWritePlan:
    """Purpose-bound write target the MANAS envelope signs.

    Deliberately contains NO Decision Envelope, so the signature cannot be
    circular (signing an object that embeds its own signature).
    """

    plan_id: str
    source_event_id: str
    draft_id: str
    route: str  # enums.Route value
    atom_kind: str  # enums.AtomKind value
    materiality_class: str
    canonical_content: str
    sanitized_payload: dict[str, Any]
    evidence_bundle_ids: tuple[str, ...] = field(default_factory=tuple)
    pramana_report_id: str | None = None
    reduction_proof_id: str | None = None
    noumenon_slot_ids: tuple[str, ...] = field(default_factory=tuple)
    proposed_links: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "source_event_id": self.source_event_id,
            "draft_id": self.draft_id,
            "route": self.route,
            "atom_kind": self.atom_kind,
            "materiality_class": self.materiality_class,
            "canonical_content": self.canonical_content,
            "sanitized_payload": self.sanitized_payload,
            "evidence_bundle_ids": list(self.evidence_bundle_ids),
            "pramana_report_id": self.pramana_report_id,
            "reduction_proof_id": self.reduction_proof_id,
            "noumenon_slot_ids": list(self.noumenon_slot_ids),
            "proposed_links": [dict(l) for l in self.proposed_links],
        }

    def canonical_hash(self) -> str:
        return hash_json(self.to_payload())


@dataclass(frozen=True)
class ProbePlan:
    """Purpose-bound test target the MANAS AUTHORIZE_TEST envelope signs."""

    probe_plan_id: str
    noumenon_atom_id: str
    hypothesis_atom_id: str
    command_argv: tuple[str, ...]
    timeout_seconds: float
    environment_allowlist: tuple[str, ...] = field(default_factory=tuple)
    working_dir: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "probe_plan_id": self.probe_plan_id,
            "noumenon_atom_id": self.noumenon_atom_id,
            "hypothesis_atom_id": self.hypothesis_atom_id,
            "command_argv": list(self.command_argv),
            "timeout_seconds": self.timeout_seconds,
            "environment_allowlist": list(self.environment_allowlist),
            "working_dir": self.working_dir,
        }

    def canonical_hash(self) -> str:
        return hash_json(self.to_payload())


@dataclass(frozen=True)
class AuthorizedWriteRequest:
    """What the Gateway accepts: plan + separately verified envelope."""

    plan: ProposedWritePlan
    envelope: "ManasDecisionEnvelope"


# ---------------------------------------------------------------------------
# MANAS Decision Envelope (brief 9.1) — forward reference for typing only
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ManasDecisionEnvelope:
    decision_id: str
    purpose: str
    target_id: str
    target_hash: str
    draft_id: str | None
    draft_hash: str | None
    sanitized_payload_hash: str | None
    evidence_bundle_hash: str | None
    pramana_report_hash: str | None
    reduction_proof_hash: str | None
    verdict: str
    route: str | None
    policy_version: str
    service_version: str
    key_id: str
    issued_at: str
    expires_at: str
    nonce: str
    signature_algorithm: str
    signature: str

    def to_canonical_payload(self) -> dict[str, Any]:
        """All fields except the signature itself (no circular hash)."""
        return {
            "decision_id": self.decision_id,
            "purpose": self.purpose,
            "target_id": self.target_id,
            "target_hash": self.target_hash,
            "draft_id": self.draft_id,
            "draft_hash": self.draft_hash,
            "sanitized_payload_hash": self.sanitized_payload_hash,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "pramana_report_hash": self.pramana_report_hash,
            "reduction_proof_hash": self.reduction_proof_hash,
            "verdict": self.verdict,
            "route": self.route,
            "policy_version": self.policy_version,
            "service_version": self.service_version,
            "key_id": self.key_id,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "nonce": self.nonce,
            "signature_algorithm": self.signature_algorithm,
        }

    def canonical_hash(self) -> str:
        return hash_json(self.to_canonical_payload())
