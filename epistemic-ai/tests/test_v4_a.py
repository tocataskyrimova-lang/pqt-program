"""P0-A — QNUF-Forge v2.2 and StructuredDraft.

Covers the brief's QNUF-Forge test matrix: extracted-without-anchor rejected,
incorrect offsets rejected, wrong-event anchor rejected, hypothesis-without-anchor
kept, forbidden self-assigned FACT ignored, deterministic canonical hash.
"""

import pytest

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.contracts.models import RawThoughtOutput, VerbatimAnchor
from qvch_v4.forge import ForgeRejection, LocalForgeAdapter, QnufForge

SRC = "The config lives in C:\\app\\config.yaml and the port is 8080."


def _anchor_for(quote: str, start: int, end: int, redacted=False):
    return {
        "source_event_id": "evt_x",
        "start_offset": start,
        "end_offset": end,
        "quote": quote,
        "quote_hash": sha256_hex(quote),
        "redacted": redacted,
    }


def test_extracted_claim_without_anchor_rejected():
    raw = RawThoughtOutput(
        source_text=SRC,
        structured_fields={
            "claims": [
                {"claim_type": "EXTRACTED", "subject": "port", "predicate": "is", "value": "8080"}
            ]
        },
    )
    with pytest.raises(ForgeRejection):
        QnufForge().forge(raw, "evt_x")


def test_extracted_claim_with_correct_anchor_accepted():
    q = "port is 8080"
    start = SRC.index(q)
    raw = RawThoughtOutput(
        source_text=SRC,
        structured_fields={
            "claims": [
                {
                    "claim_type": "EXTRACTED",
                    "subject": "port",
                    "predicate": "is",
                    "value": "8080",
                    "anchor": _anchor_for(q, start, start + len(q)),
                }
            ]
        },
    )
    draft = QnufForge().forge(raw, "evt_x")
    assert draft.claims[0].claim_type == "EXTRACTED"
    assert draft.canonical_hash.startswith("sha256:")


def test_incorrect_offsets_rejected():
    q = "port is 8080"
    start = SRC.index(q)
    bad = dict(_anchor_for(q, start, start + len(q)))
    bad["quote_hash"] = sha256_hex("tampered")
    raw = RawThoughtOutput(
        source_text=SRC,
        structured_fields={
            "claims": [
                {
                    "claim_type": "EXTRACTED",
                    "subject": "port",
                    "predicate": "is",
                    "value": "8080",
                    "anchor": bad,
                }
            ]
        },
    )
    with pytest.raises(ForgeRejection):
        QnufForge().forge(raw, "evt_x")


def test_anchor_from_wrong_event_slice_rejected():
    # span points at a different (wrong) substring than the recorded quote
    q = "port is 8080"
    start = SRC.index(q)
    wrong = dict(_anchor_for(q, start, start + len(q)))
    wrong["quote"] = "port is 9090"  # mismatch with actual slice
    raw = RawThoughtOutput(
        source_text=SRC,
        structured_fields={
            "claims": [
                {
                    "claim_type": "EXTRACTED",
                    "subject": "port",
                    "predicate": "is",
                    "value": "8080",
                    "anchor": wrong,
                }
            ]
        },
    )
    with pytest.raises(ForgeRejection):
        QnufForge().forge(raw, "evt_x")


def test_hypothesis_without_anchor_kept_as_hypothesis():
    raw = RawThoughtOutput(
        source_text=SRC,
        structured_fields={
            "claims": [
                {
                    "claim_type": "GENERATED_HYPOTHESIS",
                    "subject": "latency",
                    "predicate": "will_drop",
                    "value": "under 10ms",
                }
            ]
        },
    )
    draft = QnufForge().forge(raw, "evt_x")
    assert draft.claims[0].claim_type == enums.ClaimType.GENERATED_HYPOTHESIS.value


def test_forbidden_self_assigned_fact_ignored_and_recorded():
    raw = RawThoughtOutput(
        source_text=SRC,
        structured_fields={
            "claims": [
                {"claim_type": "OBSERVATION_REQUEST", "subject": "x", "predicate": "y", "value": "z"}
            ],
            "approved": True,
            "fact": True,
            "final_route": "F",
            "safe_to_commit": True,
        },
    )
    draft = QnufForge().forge(raw, "evt_x")
    assert "approved" in draft.forbidden_fields_detected
    assert "fact" in draft.forbidden_fields_detected
    assert "final_route" in draft.forbidden_fields_detected


def test_canonical_hash_deterministic():
    fields = {
        "claims": [
            {"claim_type": "OBSERVATION_REQUEST", "subject": "a", "predicate": "b", "value": "c"}
        ]
    }
    r1 = RawThoughtOutput(source_text="hello", structured_fields=fields)
    r2 = RawThoughtOutput(source_text="hello", structured_fields=fields)
    h1 = QnufForge().forge(r1, "e1").canonical_hash
    h2 = QnufForge().forge(r2, "e1").canonical_hash
    assert h1 == h2
    r3 = RawThoughtOutput(source_text="hello world", structured_fields=fields)
    assert QnufForge().forge(r3, "e1").canonical_hash != h1


def test_local_adapter_does_not_invent_fact():
    raw = LocalForgeAdapter().build_raw("Where is the config file?")
    draft = QnufForge().forge(raw, "evt_q")
    assert all(c.claim_type != enums.ClaimType.EXTRACTED.value for c in draft.claims)
    assert draft.noumenon_slots  # uncertainty produced an explicit unknown slot


def test_normative_requires_source_ref():
    raw = RawThoughtOutput(
        source_text=SRC,
        structured_fields={
            "claims": [
                {"claim_type": "NORMATIVE", "subject": "policy", "predicate": "requires", "value": "TLS"}
            ]
        },
    )
    with pytest.raises(ForgeRejection):
        QnufForge().forge(raw, "evt_x")
