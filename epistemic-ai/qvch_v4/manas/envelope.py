"""ManasDecisionEnvelope — the sovereign, immutable decision record (brief 9.1).

Replaces the legacy ``ManasReview(approved: bool)``. The envelope is
cryptographically bound (HMAC-SHA256) to the exact target it authorizes; the
signature covers the canonical serialization of every field *except* the
signature itself, so any tampering invalidates verification.

``target_hash`` is the proposed write plan hash for AUTHORIZE_WRITE, or the
probe plan hash for AUTHORIZE_TEST.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qvch_v4.contracts.canonical import canonical_json, hash_json
from qvch_v4.manas.signer import DecisionSigner


@dataclass(frozen=True)
class ManasDecisionEnvelope:
    decision_id: str
    purpose: str  # enums.DecisionPurpose value
    target_id: str
    target_hash: str
    draft_id: str | None
    draft_hash: str | None
    sanitized_payload_hash: str | None
    evidence_bundle_hash: str | None
    pramana_report_hash: str | None
    reduction_proof_hash: str | None
    verdict: str  # enums.Verdict value
    route: str | None  # enums.Route value
    policy_version: str
    service_version: str
    key_id: str
    issued_at: str  # UTC ISO-8601
    expires_at: str  # UTC ISO-8601
    nonce: str
    signature_algorithm: str
    signature: str

    def to_canonical_payload(self) -> dict[str, Any]:
        """All fields except the signature — this is what gets signed."""
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

    def signing_bytes(self) -> bytes:
        return canonical_json(self.to_canonical_payload()).encode("utf-8")

    def signed_copy(self, signature: str) -> "ManasDecisionEnvelope":
        return ManasDecisionEnvelope(signature=signature, **{
            k: v for k, v in self.__dict__.items() if k != "signature"
        })


def sign_envelope(unsigned: ManasDecisionEnvelope, signer: DecisionSigner) -> ManasDecisionEnvelope:
    sig = signer.sign(unsigned.signing_bytes())
    return unsigned.signed_copy(sig)


def verify_envelope_signature(
    env: ManasDecisionEnvelope, signer: DecisionSigner
) -> bool:
    # Reconstruct the unsigned form and verify the signature over it.
    unsigned = ManasDecisionEnvelope(
        signature="", **{k: v for k, v in env.__dict__.items() if k != "signature"}
    )
    return signer.verify(unsigned.signing_bytes(), env.signature)


__all__ = ["ManasDecisionEnvelope", "sign_envelope", "verify_envelope_signature"]
