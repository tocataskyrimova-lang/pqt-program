"""Spanda viability scoring and FORM lifecycle transitions (brief 14.1–14.2).

Score formula (all coefficients come from :class:`SpandaPolicy`)::

    spanda_score = clamp(
        w1*applicability_health + w2*probe_success_rate
      + w3*successful_usage_rate + w4*evidence_freshness
      + w5*dependency_compatibility
      - w6*contradiction_pressure - w7*observed_failure_rate, 0, 1)

Thresholds map the score to ACTIVE / WATCH / STALE / QUARANTINED.

R3: The maintenance engine activates its Repository internally so callers
cannot supply a keyring or pass a mutate callback (R3 §2 / §3).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.manas.authority import DecisionRequest, LocalManasAuthority
from qvch_v4.manas.service import ConsumptionContext
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.policy.frozen import SpandaPolicy, VinashaPolicy
from qvch_v4.storage import QvchStore, Repository


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def compute_score(components: dict[str, float], policy: SpandaPolicy) -> float:
    """Weighted Spanda score, clamped to [0, 1]."""
    raw = (
        policy.w_applicability_health * components.get("applicability_health", 0.0)
        + policy.w_probe_success_rate * components.get("probe_success_rate", 0.0)
        + policy.w_successful_usage_rate * components.get("successful_usage_rate", 0.0)
        + policy.w_evidence_freshness * components.get("evidence_freshness", 0.0)
        + policy.w_dependency_compatibility * components.get("dependency_compatibility", 0.0)
        - policy.w_contradiction_pressure * components.get("contradiction_pressure", 0.0)
        - policy.w_observed_failure_rate * components.get("observed_failure_rate", 0.0)
    )
    return _clamp(raw)


def recommend_state(score: float, policy: SpandaPolicy) -> str:
    """Map a score onto the FORM lifecycle (brief 14.2)."""
    if score >= policy.watch_below:
        return "ACTIVE"
    if score >= policy.stale_below:
        return "WATCH"
    if score >= policy.quarantine_below:
        return "STALE"
    return "QUARANTINED"


@dataclass(frozen=True)
class SpandaAssessment:
    atom_id: str
    revision_id: str
    atom_kind: str
    current_state: str
    score: float
    components: dict[str, float] = field(default_factory=dict)
    recommended_state: str | None = None
    applied: bool = False
    needs_decision: bool = False
    policy_version: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "revision_id": self.revision_id,
            "atom_kind": self.atom_kind,
            "current_state": self.current_state,
            "score": self.score,
            "components": self.components,
            "recommended_state": self.recommended_state,
            "applied": self.applied,
            "needs_decision": self.needs_decision,
            "policy_version": self.policy_version,
        }


class Spanda:
    def __init__(self, store: QvchStore, *, policy: SpandaPolicy | None = None,
                 vinasha: VinashaPolicy | None = None) -> None:
        self._store = store
        self._policy = policy or SpandaPolicy.default()
        self._vinasha = vinasha or VinashaPolicy.default()
        # §8 maintenance authority: the signing key is created and held INSIDE
        # the maintenance engine and never exposed to callers. Every Spanda
        # downward/upward transition is authorized by this internal MANAS
        # authority and committed atomically with its consumption (R2 §8 / R3 §2).
        self._signer = DecisionSigner.ephemeral()
        self._authority = LocalManasAuthority(
            self._signer, policy_version="policy/spanda/1.0",
            service_version="spanda/1.0")
        self._repo = Repository(store)
        self._repo._activate(self._signer)

    # -- component gathering --------------------------------------------------
    def gather_components(self, atom_id: str, revision_id: str) -> dict[str, float]:
        conn = self._store._conn
        # applicability_health: latest gate decision verdict for this revision.
        row = conn.execute(
            "SELECT verdict FROM gate_decisions WHERE revision_id=? "
            "ORDER BY decided_at DESC LIMIT 1", (revision_id,)
        ).fetchone()
        if row is None:
            applicability_health = 0.5
        elif row[0] == "APPLY":
            applicability_health = 1.0
        elif row[0] == "CAUTIOUS_APPLY":
            applicability_health = 0.6
        elif row[0] in ("ESCALATE",):
            applicability_health = 0.4
        else:
            applicability_health = 0.2

        # probe_success_rate: Laplace-smoothed over recorded probe runs.
        probe_rows = conn.execute(
            "SELECT receipt_json FROM probe_runs WHERE atom_id=?", (atom_id,)
        ).fetchall()
        successes = 0
        for (rj,) in probe_rows:
            try:
                if json.loads(rj).get("success"):
                    successes += 1
            except (ValueError, TypeError):
                pass
        total_probes = len(probe_rows)
        probe_success_rate = (successes + 1) / (total_probes + 2) if total_probes else 0.5

        # successful_usage_rate: Laplace-smoothed over usage outcomes.
        usage_rows = conn.execute(
            "SELECT outcome FROM usage_outcomes WHERE atom_id=?", (atom_id,)
        ).fetchall()
        good = sum(
            1 for (o,) in usage_rows if o in ("SUCCESS", "PARTIAL_SUCCESS")
        )
        total_usage = len(usage_rows)
        successful_usage_rate = (good + 1) / (total_usage + 2) if total_usage else 0.5

        # Observed failures (used by both dependency_compatibility and pressure).
        bad_usage = sum(
            1 for (o,) in usage_rows
            if o in ("FAILURE", "UNEXPECTED_SIDE_EFFECT", "ABORTED", "CONTEXT_MISMATCH")
        )
        bad_probes = total_probes - successes

        # evidence_freshness: fraction of linked evidence younger than the
        # policy window; neutral 0.5 when the revision carries no evidence.
        evidence_freshness = self._evidence_freshness(revision_id)

        # dependency_compatibility: a contract wires the revision into an
        # environment; observed failures mean that environment/dependency has
        # drifted, so we penalise it.
        crow = conn.execute(
            "SELECT 1 FROM applicability_contracts WHERE atom_id=? AND revision_id=? LIMIT 1",
            (atom_id, revision_id),
        ).fetchone()
        if crow is None:
            dependency_compatibility = 0.3
        elif bad_probes or bad_usage:
            dependency_compatibility = 0.5
        else:
            dependency_compatibility = 1.0

        # contradiction_pressure: count of CONTRADICTS/REFUTES links inbound.
        cnt = conn.execute(
            "SELECT COUNT(*) FROM memory_links WHERE to_atom_id=? "
            "AND link_type IN ('CONTRADICTS','REFUTES')", (atom_id,)
        ).fetchone()[0]
        contradiction_pressure = min(1.0, cnt / 3.0)

        # observed_failure_rate: blended failure over usage + probe outcomes.
        denom = total_usage + total_probes
        observed_failure_rate = (
            min(1.0, (bad_usage + bad_probes) / (denom + 1)) if denom else 0.0
        )

        return {
            "applicability_health": applicability_health,
            "probe_success_rate": probe_success_rate,
            "successful_usage_rate": successful_usage_rate,
            "evidence_freshness": evidence_freshness,
            "dependency_compatibility": dependency_compatibility,
            "contradiction_pressure": contradiction_pressure,
            "observed_failure_rate": observed_failure_rate,
        }

    def _evidence_freshness(self, revision_id: str) -> float:
        """Fraction of the revision's linked evidence younger than the policy
        window. Neutral 0.5 when the revision carries no evidence refs."""
        rev = self._repo.get_revision(revision_id)
        if rev is None:
            return 0.5
        try:
            payload = json.loads(rev[4])
        except (ValueError, TypeError):
            return 0.5
        ev_ids = payload.get("migrated_evidence_refs") or payload.get("evidence_refs") or []
        if not ev_ids:
            return 0.5
        placeholders = ",".join("?" for _ in ev_ids)
        rows = self._store._conn.execute(
            f"SELECT created_at FROM evidence_refs WHERE evidence_id IN ({placeholders})",
            tuple(ev_ids),
        ).fetchall()
        if not rows:
            return 0.5
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._policy.freshness_window_days)
        fresh = 0
        for (created_at,) in rows:
            try:
                ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts >= cutoff:
                fresh += 1
        return _clamp(fresh / len(rows))

    # -- assessment -----------------------------------------------------------
    def assess(self, atom_id: str, revision_id: str) -> SpandaAssessment:
        arow = self._repo.get_atom(atom_id)
        if arow is None:
            raise ValueError(f"unknown atom {atom_id}")
        atom_kind, current_state = arow[2], arow[4]
        components = self.gather_components(atom_id, revision_id)
        score = compute_score(components, self._policy)
        recommended = recommend_state(score, self._policy)
        return SpandaAssessment(
            atom_id=atom_id, revision_id=revision_id, atom_kind=atom_kind,
            current_state=current_state, score=score, components=components,
            recommended_state=recommended, policy_version=self._policy.version,
        )

    # -- transition application ----------------------------------------------
    def _maint_write(self, operation: str, *, target_id: str, target_hash: str,
                     route: str, now: str,
                     state: dict | None = None) -> None:
        """Authorize a maintenance mutation via the internal authority (R2 §8).

        The mutation is passed as a structured payload (not a callable) so the
        caller cannot inject arbitrary SQL (R3 §3).
        """
        req = DecisionRequest(
            purpose=enums.DecisionPurpose.AUTHORIZE_STATE_TRANSITION.value,
            target_id=target_id, target_hash=target_hash, route=route,
            issued_at=now,
            expires_at=(datetime.fromisoformat(now) + timedelta(hours=1)).isoformat(),
        )
        env = self._authority.decide(req)
        ctx = ConsumptionContext(
            observed_target_hash=target_hash, observed_route=route,
            policy_version="policy/spanda/1.0", now_iso=now, ledger=None)
        self._repo.authorized_write(
            operation, env, ctx, state=state)

    def maintain(self, atom_id: str, revision_id: str, *,
                 envelope: ManasDecisionEnvelope | None = None,
                 signer: DecisionSigner | None = None,
                 now: str | None = None) -> SpandaAssessment:
        """Assess and, where policy allows, move the FORM atom along its
        lifecycle. Every transition is authorized by the internal MANAS
        maintenance authority and committed atomically with its consumption
        (brief R2 §8); the SQL state-transition trigger gates legality, so an
        illegal target state is surfaced as a no-op assessment."""
        now = now or _now_iso()
        assessment = self.assess(atom_id, revision_id)
        if assessment.atom_kind != "FORM":
            return assessment  # Spanda transitions are defined for FORM crystals
        if assessment.recommended_state == assessment.current_state:
            return assessment
        if not self._repo.allowed_transition(
                "FORM", assessment.current_state, assessment.recommended_state):
            # The SQL trigger would reject this anyway; surface it early.
            return assessment

        reason = f"spanda score={assessment.score:.3f} -> {assessment.recommended_state}"
        target_hash = sha256_hex(atom_id + revision_id + assessment.recommended_state)
        state = {
            "atom_id": atom_id,
            "to_state": assessment.recommended_state,
            "reason": reason,
        }
        self._maint_write(
            self._repo.OP_STATE_TRANSITION, target_id=atom_id,
            target_hash=target_hash, route="N", now=now,
            state=state)
        self._repo.record_maintenance_event(
            event_id=f"me_{uuid.uuid4().hex}", atom_id=atom_id,
            kind="SPANDA_TRANSITION", reason=reason, now=now)
        return replace(assessment, applied=True)


__all__ = ["Spanda", "SpandaAssessment", "compute_score", "recommend_state"]