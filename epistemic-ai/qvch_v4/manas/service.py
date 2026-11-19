"""MANAS sovereign decision service and the Gateway verification boundary.

``ManasService.decide()`` is the *only* production factory of a
``ManasDecisionEnvelope`` (brief 9.4). Safety, however, is guaranteed by the
cryptographic Gateway (``Gateway.verify``), not by constructor restriction:
any hand-built envelope (a "forged approve") fails signature/expiry/hash/replay
checks.

Replay protection (brief 9.3) relies on an append-only consumption ledger with
``UNIQUE(decision_id)`` and ``UNIQUE(nonce)`` — only the first valid attempt may
create a consumption; a replay is rejected without altering memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.models import new_id
from qvch_v4.manas.envelope import (
    ManasDecisionEnvelope,
    sign_envelope,
    verify_envelope_signature,
)
from qvch_v4.manas.signer import ALGORITHM, DecisionSigner


def _parse_iso(s: str):
    return __import__("datetime").datetime.fromisoformat(s.replace("Z", "+00:00"))




class InMemoryConsumptionLedger:
    """Append-only decision/nonce ledger used by tests and as a reference
    implementation of the P0-F SQL contract (UNIQUE(decision_id)/UNIQUE(nonce))."""

    def __init__(self) -> None:
        self._decisions: set[str] = set()
        self._nonces: set[str] = set()

    def consume(self, decision_id: str, nonce: str) -> bool:
        """Atomically record a consumption. True iff this is the first valid
        attempt for both the decision_id and the nonce."""
        if decision_id in self._decisions or nonce in self._nonces:
            return False
        self._decisions.add(decision_id)
        self._nonces.add(nonce)
        return True

    def consumed(self, decision_id: str, nonce: str) -> bool:
        return decision_id in self._decisions or nonce in self._nonces


@dataclass
class ConsumptionContext:
    """What the Gateway observes at the moment it would consume a decision."""

    observed_target_hash: str | None
    observed_draft_hash: str | None = None
    observed_payload_hash: str | None = None
    observed_route: str | None = None
    policy_version: str = ""
    now_iso: str = ""
    has_reduction_proof: bool = False
    ledger: Any = None  # ConsumptionLedger with consume(decision_id, nonce)->bool
    # SQL-backed resolver: given a reduction_proof_hash, return True iff a stored
    # certificate carries that exact hash (brief R1 §6 / R1-Q4). When provided,
    # the Gateway refuses any F envelope whose proof is not found in SQL.
    reduction_proof_resolver: Any = None
    # Explicit requirement that this decision must bind a valid, SQL-resolvable
    # reduction proof. Set by the Studio *only* when the operation actually
    # commits an F / F_candidate atom (brief R1 §6). It is intentionally not
    # derived from the envelope route alone: a contract declaration or a state
    # transition may legitimately carry the F route yet must not require a proof.
    requires_reduction_proof: bool = False


@dataclass
class VerificationResult:
    allowed: bool
    reasons: tuple[str, ...]
    consumed: bool = False


class ManasService:
    """The sovereign decision issuer. ``decide()`` is the only production factory."""

    def __init__(
        self,
        signer: DecisionSigner,
        *,
        policy_version: str,
        service_version: str,
        ttl_seconds: int = 300,
    ) -> None:
        self.signer = signer
        self.policy_version = policy_version
        self.service_version = service_version
        self.ttl_seconds = ttl_seconds

    def decide(
        self,
        *,
        purpose: str,
        target_id: str,
        target_hash: str,
        verdict: str,
        route: str | None = None,
        draft_id: str | None = None,
        draft_hash: str | None = None,
        sanitized_payload_hash: str | None = None,
        evidence_bundle_hash: str | None = None,
        pramana_report_hash: str | None = None,
        reduction_proof_hash: str | None = None,
        nonce: str | None = None,
        issued_at: str | None = None,
        expires_at: str | None = None,
    ) -> ManasDecisionEnvelope:
        try:
            enums.DecisionPurpose(purpose)
        except ValueError as exc:
            raise ValueError(f"unknown purpose: {purpose!r}") from exc
        if issued_at is None or expires_at is None:
            from datetime import datetime, timedelta, timezone

            now = datetime.now(timezone.utc)
            issued_at = issued_at or now.isoformat()
            expires_at = expires_at or (now + timedelta(seconds=self.ttl_seconds)).isoformat()
        unsigned = ManasDecisionEnvelope(
            decision_id=new_id("dec"),
            purpose=purpose,
            target_id=target_id,
            target_hash=target_hash,
            draft_id=draft_id,
            draft_hash=draft_hash,
            sanitized_payload_hash=sanitized_payload_hash,
            evidence_bundle_hash=evidence_bundle_hash,
            pramana_report_hash=pramana_report_hash,
            reduction_proof_hash=reduction_proof_hash,
            verdict=verdict,
            route=route,
            policy_version=self.policy_version,
            service_version=self.service_version,
            key_id=self.signer.key_id,
            issued_at=issued_at,
            expires_at=expires_at,
            nonce=nonce or new_id("nonce"),
            signature_algorithm=ALGORITHM,
            signature="",
        )
        return sign_envelope(unsigned, self.signer)


class Gateway:
    """Cryptographic consumption boundary. Verifies a decision before any write.

    ``verify_with_signer`` takes the signer so the Gateway itself needs no key
    material — the key stays out of the DB/source/logs.

    The Gateway owns a trusted verification keyring (brief R1 §2): when a
    keyring is configured, only envelopes signed by a key in the ring are
    accepted, and the key id / algorithm / policy version are validated.
    Production commits are fail-closed and refuse to verify without a trusted
    key (the regression harness passes an ephemeral signer, so a keyring is
    only consulted when one has been explicitly configured).

    ``QUARANTINE`` and ``REJECT`` are *records*, never execution
    authorizations: every verifier requires ``verdict == APPROVE``
    (brief R1 §3 / R1-Q2).
    """

    def __init__(self, keyring: dict[str, DecisionSigner] | None = None,
                 *, caller_signer_allowed: bool = False) -> None:
        # Trusted verification keyring: key_id -> signer. When non-empty, only
        # envelopes signed by a key in the ring are accepted (brief R1 §2 / R2
        # §5). When empty, `caller_signer_allowed` must be explicitly opted in by
        # an *isolated unit-test helper* — production runtime paths must never
        # enable it (brief R2 §5: "This fallback may exist only in isolated
        # unit-test helpers, not exported runtime classes").
        self.keyring = keyring or {}
        self.caller_signer_allowed = caller_signer_allowed

    def _resolve_signer(self, env: ManasDecisionEnvelope,
                          signer: DecisionSigner | None) -> DecisionSigner | None:
        if self.keyring:
            return self.keyring.get(env.key_id)
        if self.caller_signer_allowed and signer is not None:
            return signer
        return None

    def verify_with_signer(
        self, env: ManasDecisionEnvelope, ctx: ConsumptionContext, signer: DecisionSigner | None = None
    ) -> VerificationResult:
        return self._verify(env, ctx, signer)

    def verify_no_consume(
        self, env: ManasDecisionEnvelope, ctx: ConsumptionContext,
        signer: DecisionSigner | None = None, purpose: str | None = None,
    ) -> VerificationResult:
        """Cryptographic verification *without* consuming the decision.

        Used by the atomic ``Repository.authorized_write`` path: it performs the
        pure verification here, then consumes the decision and mutates the store
        inside a *single* SQL transaction (brief R2 §7). Consuming here would be
        wrong — the consumption must roll back with the mutation if the write
        fails, which a separate consume-then-write cannot guarantee.
        """
        return self._verify(env, ctx, signer, purpose=purpose, consume=False)

    # -- purpose-specific verifiers (brief R1 §3) --------------------------
    def verify_test_authorization(
        self, env: ManasDecisionEnvelope, ctx: ConsumptionContext, signer: DecisionSigner | None = None
    ) -> VerificationResult:
        return self._verify(env, ctx, signer, purpose=enums.DecisionPurpose.AUTHORIZE_TEST.value)

    def verify_write_authorization(
        self, env: ManasDecisionEnvelope, ctx: ConsumptionContext, signer: DecisionSigner | None = None
    ) -> VerificationResult:
        return self._verify(env, ctx, signer, purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value)

    def verify_state_transition_authorization(
        self, env: ManasDecisionEnvelope, ctx: ConsumptionContext, signer: DecisionSigner | None = None
    ) -> VerificationResult:
        return self._verify(env, ctx, signer, purpose=enums.DecisionPurpose.AUTHORIZE_STATE_TRANSITION.value)

    def _verify(
        self, env: ManasDecisionEnvelope, ctx: ConsumptionContext,
        signer: DecisionSigner | None, purpose: str | None = None,
        *, consume: bool = True,
    ) -> VerificationResult:
        reasons: list[str] = []

        # 0. Trusted keyring / signature.
        real_signer = self._resolve_signer(env, signer)
        if real_signer is None:
            return VerificationResult(False, ("no verifying signer / key not in trusted keyring",))
        if not verify_envelope_signature(env, real_signer):
            return VerificationResult(False, ("wrong signature / forged envelope",))

        # 0b. Trusted key id + algorithm validation (brief R1 §2).
        if self.keyring and env.key_id not in self.keyring:
            reasons.append("envelope key_id not in trusted verification keyring")
        if env.signature_algorithm != ALGORITHM:
            reasons.append("untrusted signature algorithm")

        # 0c. Verdict: only APPROVE is an execution authorization.
        # QUARANTINE and REJECT are records, not authorizations (R1 §3 / Q2).
        if env.verdict != enums.Verdict.APPROVE.value:
            reasons.append(f"verdict {env.verdict!r} is not an execution authorization")

        # 0d. Exact purpose binding (when a purpose is requested).
        if purpose is not None and env.purpose != purpose:
            reasons.append(f"envelope purpose {env.purpose!r} != required {purpose!r}")

        # 0e. Issued-at not in the future beyond a small skew.
        try:
            skew = 5
            now = _parse_iso(ctx.now_iso) if ctx.now_iso else datetime.now(timezone.utc)
            issued = _parse_iso(env.issued_at)
            if issued > now + timedelta(seconds=skew):
                reasons.append("envelope issued in the future")
        except ValueError:
            reasons.append("malformed timestamp")

        # 1. Expiry.
        try:
            if ctx.now_iso and _parse_iso(ctx.now_iso) >= _parse_iso(env.expires_at):
                reasons.append("expired envelope")
        except ValueError:
            reasons.append("malformed timestamp")

        # 2. Target (write-plan) hash — catches a changed write plan.
        if ctx.observed_target_hash is not None and env.target_hash != ctx.observed_target_hash:
            reasons.append("changed write plan / mismatched target hash")
        if ctx.observed_target_hash is None and not env.target_hash:
            reasons.append("mandatory target hash missing")

        # 3. Draft hash.
        if (
            ctx.observed_draft_hash is not None
            and env.draft_hash is not None
            and env.draft_hash != ctx.observed_draft_hash
        ):
            reasons.append("mismatched draft hash")

        # 4. Sanitized payload hash.
        if (
            ctx.observed_payload_hash is not None
            and env.sanitized_payload_hash is not None
            and env.sanitized_payload_hash != ctx.observed_payload_hash
        ):
            reasons.append("mismatched payload hash")

        # 5. Route.
        if ctx.observed_route is not None and env.route != ctx.observed_route:
            reasons.append("mismatched route")

        # 6. Policy version.
        if ctx.policy_version and env.policy_version != ctx.policy_version:
            reasons.append("policy version mismatch")

        # 7. A decision that commits an F / F_candidate atom must bind a valid
        # reduction proof resolvable from SQL (brief R1 §6 / R1-Q4). The
        # requirement is signalled explicitly by the caller via
        # ``ctx.requires_reduction_proof`` (set only for an actual F-atom write),
        # not inferred from the route — a contract declaration or a state
        # transition may carry the F route yet must not require a proof.
        if ctx.requires_reduction_proof:
            if env.reduction_proof_hash is None:
                reasons.append("F without valid reduction proof hash")
            elif ctx.reduction_proof_resolver is not None \
                    and not ctx.reduction_proof_resolver(env.reduction_proof_hash):
                reasons.append("F reduction proof not found in SQL (R1-Q4)")
            elif ctx.reduction_proof_resolver is None and not ctx.has_reduction_proof:
                reasons.append("F without valid reduction proof")

        if reasons:
            return VerificationResult(False, tuple(reasons))

        # 8. One-time consumption: only the first valid attempt consumes.
        # Prefer the SQL ledger (production); fall back to the in-memory
        # ledger for tests that do not pass a store (R1 §4). When ``consume``
        # is False (the atomic authorized_write path), the consumption is
        # performed inside the caller's single transaction instead (R2 §7).
        if not consume:
            return VerificationResult(True, ("ok",), consumed=False)
        if ctx.ledger is None or not ctx.ledger.consume(env.decision_id, env.nonce):
            return VerificationResult(False, ("reused nonce / reused decision",))

        return VerificationResult(True, ("ok",), consumed=True)


__all__ = [
    "ManasService",
    "Gateway",
    "InMemoryConsumptionLedger",
    "ConsumptionContext",
    "VerificationResult",
]
