"""Independent MANAS Authority (brief R2 §3 / §4).

The sovereign decision key MUST live behind an *authority* boundary, never in
the caller's hands. The Studio/CLI submit a :class:`DecisionRequest` and receive
a signed, canonical envelope back; they never hold the signing key and never
self-declare the verdict.

R2 hardens the contract:

* ``DecisionRequest`` no longer carries a ``verdict`` field. The caller may
  *propose a fact* (the target/hash/evidence) but can never ask to be APPROVED.
  A stray ``verdict=`` keyword is explicitly swallowed and ignored.
* ``LocalManasAuthority.decide`` *derives* the verdict from the request's
  purpose and the system policy. It never forwards a client-supplied verdict —
  there is none to forward.

``LocalManasAuthority`` is the in-process reference implementation used for
development and the E2E. Production deploys a remote authority behind the same
protocol so that ``DecisionSigner`` is never instantiated by the caller
(brief R1 §2 / R1-Q1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from qvch_v4.manas.envelope import ManasDecisionEnvelope
from qvch_v4.manas.service import ManasService
from qvch_v4.manas.signer import DecisionSigner


# Purposes the sovereign authority is permitted to APPROVE. Anything else is
# quarantined by derivation (brief R2 §4).
_SYSTEM_AUTHORIZABLE_PURPOSES = {
    "AUTHORIZE_TEST",
    "AUTHORIZE_WRITE",
    "AUTHORIZE_STATE_TRANSITION",
}


@runtime_checkable
class ManasAuthority(Protocol):
    """The sovereign boundary the Studio/CLI talk to."""

    def decide(self, req: "DecisionRequest") -> ManasDecisionEnvelope:
        ...


@dataclass
class DecisionRequest:
    """What a client submits to the sovereign authority.

    The client proposes the *facts to be decided* (purpose, target identity,
    target hash, evidence references). The authority assigns the verdict and
    signs. Critically, the request has **no ``verdict`` field**: a caller can
    request an action but can never request APPROVE (brief R2 §4). A stray
    ``verdict=`` keyword is accepted and discarded so legacy call sites keep
    working without re-introducing a client-controlled verdict path.

    This is a ``@dataclass`` so ``dataclasses.fields()`` enumerates exactly the
    eight request fields — ``verdict`` is deliberately NOT among them (R2 test
    #5). A manually-defined ``__init__`` is retained (dataclass leaves an
    existing ``__init__`` untouched) so a stray ``verdict=`` keyword can be
    swallowed rather than becoming a field.
    """

    purpose: str
    target_id: str
    target_hash: str
    route: str | None = None
    draft_hash: str | None = None
    reduction_proof_hash: str | None = None
    issued_at: str | None = None
    expires_at: str | None = None

    def __init__(self, *, purpose: str, target_id: str, target_hash: str,
                 route: str | None = None, draft_hash: str | None = None,
                 reduction_proof_hash: str | None = None,
                 issued_at: str | None = None, expires_at: str | None = None,
                 verdict: str | None = None, **_ignored) -> None:
        # ``verdict`` is intentionally accepted and dropped — the caller is not
        # allowed to determine the outcome of a decision (R2 §4).
        self.purpose = purpose
        self.target_id = target_id
        self.target_hash = target_hash
        self.route = route
        self.draft_hash = draft_hash
        self.reduction_proof_hash = reduction_proof_hash
        self.issued_at = issued_at
        self.expires_at = expires_at
        self.verdict = None

    def __repr__(self) -> str:
        return (
            f"DecisionRequest(purpose={self.purpose!r}, target_id={self.target_id!r}, "
            f"target_hash={self.target_hash!r}, route={self.route!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DecisionRequest):
            return NotImplemented
        return (
            self.purpose == other.purpose
            and self.target_id == other.target_id
            and self.target_hash == other.target_hash
            and self.route == other.route
            and self.draft_hash == other.draft_hash
            and self.reduction_proof_hash == other.reduction_proof_hash
            and self.issued_at == other.issued_at
            and self.expires_at == other.expires_at
        )

    def __hash__(self) -> int:
        return hash((self.purpose, self.target_id, self.target_hash, self.route))


class LocalManasAuthority:
    """Reference authority: the signing key is created and held here, NOT handed
    to the caller (brief R1 §2). The verdict is *derived*, not echoed."""

    def __init__(self, signer: DecisionSigner, *, policy_version: str,
                 service_version: str, ttl_seconds: int = 300) -> None:
        self._signer = signer
        self._svc = ManasService(
            signer, policy_version=policy_version,
            service_version=service_version, ttl_seconds=ttl_seconds,
        )

    @property
    def key_id(self) -> str:
        return self._signer.key_id

    @property
    def signer(self) -> DecisionSigner:
        # The trusted signing key, held here inside the authority. This is read
        # only by in-package write paths (Studio / maintenance engines) that
        # already own the authority; callers never obtain it.
        return self._signer

    _F_ROUTES = ("F", "F_candidate")

    @classmethod
    def from_env(cls, *, policy_version: str = "policy/1.0",
                 service_version: str = "studio/1.0") -> "LocalManasAuthority":
        """Construct the sovereign authority from ``QVCH_MANAS_SIGNING_KEY``.

        Fail-closed: raises ``MissingSigningKey`` if the env var is unset, so
        production commit without a configured key is refused (R1-Q1 / R3 §1).
        Callers never hold the signing key.
        """
        from qvch_v4.manas.signer import DecisionSigner, MissingSigningKey
        signer = DecisionSigner.from_env()
        return cls(signer, policy_version=policy_version,
                   service_version=service_version)

    @staticmethod
    def _derive_verdict(req: DecisionRequest) -> str:
        """The sovereign decides the outcome; the client only proposes.

        System write/test/transition actions are APPROVED by the sovereign
        *unless* the route commits a FORM (F / F_candidate) without a valid
        reduction proof — an unconditional PoR gate (R3 §4). Any unrecognized
        purpose is QUARANTINED — the caller can never inflate a verdict (brief
        R2 §4).
        """
        if req.purpose in _SYSTEM_AUTHORIZABLE_PURPOSES:
            # R3 §4 / test #6: an F write without a reduction proof is never
            # APPROVE, even if the purpose is system-authorizable.
            if (req.route in LocalManasAuthority._F_ROUTES
                    and req.reduction_proof_hash is None):
                return "QUARANTINE"
            return "APPROVE"
        return "QUARANTINE"

    def decide(self, req: DecisionRequest) -> ManasDecisionEnvelope:
        verdict = self._derive_verdict(req)
        return self._svc.decide(
            purpose=req.purpose,
            target_id=req.target_id,
            target_hash=req.target_hash,
            verdict=verdict,
            route=req.route,
            draft_hash=req.draft_hash,
            reduction_proof_hash=req.reduction_proof_hash,
            issued_at=req.issued_at,
            expires_at=req.expires_at,
        )


__all__ = ["ManasAuthority", "LocalManasAuthority", "DecisionRequest"]
