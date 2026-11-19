"""P0-E — MANAS Decision Envelope.

Gate P0-E: the following attempts are rejected:
  forged approve; wrong signature; expired envelope; reused nonce; reused
  decision; mismatched draft hash; mismatched payload hash; mismatched route;
  changed write plan; F without valid reduction proof.
"""

import pytest

from qvch_v4.contracts import enums
from qvch_v4.manas import (
    ConsumptionContext,
    DecisionSigner,
    Gateway,
    InMemoryConsumptionLedger,
    ManasDecisionEnvelope,
    ManasService,
    MissingSigningKey,
)
from qvch_v4.manas.signer import ALGORITHM

PLAN_HASH = "sha256:plan001"
DRAFT_HASH = "sha256:draft001"
PAYLOAD_HASH = "sha256:payload001"
PROOF_HASH = "sha256:proof001"
ISSUED = "2026-07-20T10:00:00+00:00"
EXPIRES = "2026-07-20T10:05:00+00:00"
NOW = "2026-07-20T10:01:00+00:00"
NOW_LATE = "2026-07-20T10:10:00+00:00"


@pytest.fixture
def service():
    return ManasService(DecisionSigner.ephemeral(), policy_version="pv1", service_version="sv1")


def _ctx(ledger, **over):
    base = dict(
        observed_target_hash=PLAN_HASH,
        observed_draft_hash=DRAFT_HASH,
        observed_payload_hash=PAYLOAD_HASH,
        observed_route=enums.Route.F.value,
        policy_version="pv1",
        now_iso=NOW,
        has_reduction_proof=True,
        ledger=ledger,
    )
    base.update(over)
    return ConsumptionContext(**base)


def test_valid_envelope_is_allowed(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=PROOF_HASH,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    res = gw.verify_with_signer(env, _ctx(ledger), service.signer)
    assert res.allowed is True
    assert res.consumed is True


def test_forged_approve_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    forged = ManasDecisionEnvelope(
        decision_id="dec_x",
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        draft_id=None,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        evidence_bundle_hash=None,
        pramana_report_hash=None,
        reduction_proof_hash=PROOF_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        policy_version="pv1",
        service_version="sv1",
        key_id="test-ephemeral",
        issued_at=ISSUED,
        expires_at=EXPIRES,
        nonce="nonce_x",
        signature_algorithm=ALGORITHM,
        signature="deadbeef",  # bogus
    )
    res = gw.verify_with_signer(forged, _ctx(ledger), service.signer)
    assert res.allowed is False
    assert "wrong signature" in res.reasons[0]


def test_wrong_signing_key_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=PROOF_HASH,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    other = DecisionSigner.ephemeral()
    res = gw.verify_with_signer(env, _ctx(ledger), other)
    assert res.allowed is False


def test_expired_envelope_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=PROOF_HASH,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    res = gw.verify_with_signer(env, _ctx(ledger, now_iso=NOW_LATE), service.signer)
    assert res.allowed is False
    assert "expired" in res.reasons[0]


def test_reused_decision_and_nonce_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=PROOF_HASH,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    first = gw.verify_with_signer(env, _ctx(ledger), service.signer)
    assert first.allowed is True
    second = gw.verify_with_signer(env, _ctx(ledger), service.signer)
    assert second.allowed is False
    assert "reused" in second.reasons[0]


def test_mismatched_draft_hash_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=PROOF_HASH,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    res = gw.verify_with_signer(
        env, _ctx(ledger, observed_draft_hash="sha256:other"), service.signer
    )
    assert res.allowed is False
    assert "draft hash" in res.reasons[0]


def test_mismatched_payload_hash_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=PROOF_HASH,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    res = gw.verify_with_signer(
        env, _ctx(ledger, observed_payload_hash="sha256:other"), service.signer
    )
    assert res.allowed is False
    assert "payload hash" in res.reasons[0]


def test_mismatched_route_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=PROOF_HASH,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    res = gw.verify_with_signer(
        env, _ctx(ledger, observed_route=enums.Route.N.value), service.signer
    )
    assert res.allowed is False
    assert "route" in res.reasons[0]


def test_changed_write_plan_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=PROOF_HASH,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    res = gw.verify_with_signer(
        env, _ctx(ledger, observed_target_hash="sha256:tampered"), service.signer
    )
    assert res.allowed is False
    assert "write plan" in res.reasons[0]


def test_f_without_reduction_proof_rejected(service):
    gw = Gateway(caller_signer_allowed=True)
    ledger = InMemoryConsumptionLedger()
    env = service.decide(
        purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        target_id="plan1",
        target_hash=PLAN_HASH,
        verdict=enums.Verdict.APPROVE.value,
        route=enums.Route.F.value,
        draft_hash=DRAFT_HASH,
        sanitized_payload_hash=PAYLOAD_HASH,
        reduction_proof_hash=None,  # no proof
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    res = gw.verify_with_signer(
        env, _ctx(ledger, has_reduction_proof=False, requires_reduction_proof=True),
        service.signer
    )
    assert res.allowed is False
    assert "reduction proof" in res.reasons[0]


def test_missing_signing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("QVCH_MANAS_SIGNING_KEY", raising=False)
    with pytest.raises(MissingSigningKey):
        DecisionSigner.from_env()
