"""QNUF-Forge v2.2 — untrusted compiler of LLM output into a structured draft.

The Forge does NOT:
  * assign FACT or any epistemic route;
  * approve or reject a write;
  * decide safe_to_commit;
  * invent claims that the source does not support.

It validates, canonicalizes and hash-binds. Sovereign decisions belong to
MANAS (manas/service.py). See docs/QNUF_FORGE_V2_2_CONTRACT.md.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json, sha256_hex
from qvch_v4.contracts.models import (
    CanonicalStructuredDraft,
    DraftClaim,
    NoumenonSlot,
    ProposedTransformation,
    RawThoughtOutput,
    VerbatimAnchor,
    new_id,
)
from qvch_v4.forge.anchor_verifier import verify_anchor

_UNCERTAINTY_RE = re.compile(
    r"\?|\b(unknown|uncertain|не знаю|неизвестно|where|what|how|unknown|unsure)\b", re.I
)


class ForgeRejection(Exception):
    """The candidate draft violates a Forge invariant (e.g. Postulate 0)."""


def _stable_id(prefix: str, *parts: Any) -> str:
    """Content-derived id so the canonical hash is deterministic for equal input."""
    h = sha256_hex("|".join(str(p) for p in parts))[7:23]
    return f"{prefix}_{h}"


def _coerce_claim(raw: dict[str, Any]) -> DraftClaim:
    claim_id = raw.get("claim_id") or _stable_id(
        "claim",
        raw.get("claim_type"),
        raw.get("subject"),
        raw.get("predicate"),
        raw.get("value"),
        raw.get("normative_source_ref"),
    )
    return DraftClaim(
        claim_id=claim_id,
        claim_type=str(raw.get("claim_type") or "OBSERVATION_REQUEST"),
        subject=str(raw.get("subject", "")),
        predicate=str(raw.get("predicate", "")),
        value=str(raw.get("value", "")),
        anchor=_coerce_anchor(raw.get("anchor")) if raw.get("anchor") else None,
        normative_source_ref=raw.get("normative_source_ref"),
        materiality_class=raw.get("materiality_class"),
    )


def _coerce_anchor(raw: dict[str, Any]) -> VerbatimAnchor:
    return VerbatimAnchor(
        source_event_id=str(raw.get("source_event_id", "")),
        start_offset=int(raw.get("start_offset", -1)),
        end_offset=int(raw.get("end_offset", -1)),
        quote_hash=str(raw.get("quote_hash", "")),
        redacted=bool(raw.get("redacted", False)),
        fingerprint=raw.get("fingerprint"),
        quote=raw.get("quote"),
    )


class QnufForge:
    """Validation/canonicalization service for externally produced candidates."""

    def forge(
        self,
        raw: RawThoughtOutput,
        source_event_id: str,
        draft_id: str | None = None,
    ) -> CanonicalStructuredDraft:
        fields = dict(raw.structured_fields or {})
        if raw.observed_model_output:
            try:
                parsed = json.loads(raw.observed_model_output)
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        fields.setdefault(k, v)
            except (json.JSONDecodeError, TypeError):
                pass
        # Forbidden LLM self-assertion fields must be detected AFTER merging
        # the structured fields with the observed (untrusted) model JSON, so a
        # model cannot smuggle an "approved"/"final_route" decision past the
        # Forge by hiding it in the JSON blob (brief R1 §10 / R1-Q11).
        forbidden = tuple(
            f for f in enums.FORBIDDEN_LLM_DECISION_FIELDS if f in fields
        )

        raw_claims = fields.get("claims") or []
        if not isinstance(raw_claims, list):
            raw_claims = []

        claims: list[DraftClaim] = []
        for rc in raw_claims:
            if not isinstance(rc, dict):
                continue
            claim = _coerce_claim(rc)
            self._validate_claim(claim, raw.source_text, source_event_id)
            claims.append(claim)

        slots = [
            NoumenonSlot(
                slot_id=s.get("slot_id")
                or _stable_id("slot", s.get("description"), s.get("weight"), s.get("baseline")),
                description=str(s.get("description", "")),
                weight=float(s.get("weight", 1.0)),
                baseline=bool(s.get("baseline", True)),
            )
            for s in (fields.get("noumenon_slots") or [])
            if isinstance(s, dict)
        ]
        transformations = [
            ProposedTransformation(
                transformation_id=t.get("transformation_id")
                or _stable_id("tx", t.get("description"), t.get("from_state"), t.get("to_state")),
                description=str(t.get("description", "")),
                from_state=t.get("from_state"),
                to_state=t.get("to_state"),
            )
            for t in (fields.get("transformations") or [])
            if isinstance(t, dict)
        ]

        if draft_id is None:
            did = _stable_id(
                "draft",
                raw.source_text_hash(),
                [c.claim_id for c in claims],
                [s.slot_id for s in slots],
                [t.transformation_id for t in transformations],
            )
        else:
            did = draft_id
        canonical = CanonicalStructuredDraft(
            draft_id=did,
            claims=claims,
            noumenon_slots=slots,
            transformations=transformations,
            source_text_hash=raw.source_text_hash(),
            model_id=raw.model_id,
            forbidden_fields_detected=forbidden,
            canonical_hash="",
        )
        return replace(canonical, canonical_hash=hash_json(canonical.to_payload()))

    def _validate_claim(self, claim: DraftClaim, source_text: str,
                        source_event_id: str) -> None:
        try:
            enums.ClaimType(claim.claim_type)
        except ValueError:
            raise ForgeRejection(f"unknown claim_type: {claim.claim_type!r}")

        if claim.claim_type == enums.ClaimType.EXTRACTED.value:
            # Postulate 0: an EXTRACTED claim without a verified verbatim anchor
            # does not exist.
            if claim.anchor is None:
                raise ForgeRejection(
                    "EXTRACTED claim without anchor violates Postulate 0"
                )
            # The anchor must be bound to the CURRENT source event; an anchor
            # carried from a different event is a provenance forgery
            # (brief R1 §10 / R1-Q12).
            if claim.anchor.source_event_id != source_event_id:
                raise ForgeRejection(
                    f"EXTRACTED anchor bound to source_event_id "
                    f"{claim.anchor.source_event_id!r} but current event is "
                    f"{source_event_id!r}"
                )
            if not verify_anchor(source_text, claim.anchor):
                raise ForgeRejection(
                    "EXTRACTED anchor failed verification against source text"
                )
        elif claim.claim_type == enums.ClaimType.NORMATIVE.value:
            if not claim.normative_source_ref:
                raise ForgeRejection("NORMATIVE claim requires normative_source_ref")
        # GENERATED_HYPOTHESIS / OBSERVATION_REQUEST may exist without an anchor.


class LocalForgeAdapter:
    """Deterministic, claim-free adapter for tests and Studio.

    It proposes an observation (and, when uncertainty is detected, an explicit
    unknown slot) but never invents EXTRACTED/FACT claims or assigns a route.
    """

    def build_raw(self, text: str, model_id: str | None = None) -> RawThoughtOutput:
        fields: dict[str, Any] = {
            "claims": [
                {
                    "claim_type": enums.ClaimType.OBSERVATION_REQUEST.value,
                    "subject": "observation",
                    "predicate": "observed_text",
                    "value": text[:240],
                }
            ],
        }
        if _UNCERTAINTY_RE.search(text):
            fields["noumenon_slots"] = [
                {
                    "slot_id": _stable_id("slot", text[:160]),
                    "description": f"open unknown raised by: {text[:160]}",
                    "weight": 1.0,
                    "baseline": True,
                }
            ]
        return RawThoughtOutput(
            source_text=text, structured_fields=fields, model_id=model_id
        )
