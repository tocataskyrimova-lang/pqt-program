"""Applicability Gate (brief 13.2 / 13.4).

Mandatory even without A2A. Flow:

    Retrieval Packet
    -> active revision
    -> static precondition check
    -> anti-condition check
    -> required cheap probes in Node 15 (needs a valid AUTHORIZE_TEST)
    -> gate verdict

Verdicts: APPLY, CAUTIOUS_APPLY, ESCALATE, QUARANTINE, REJECT.
A mismatched/unknown precondition, an anti-condition hit, a missing or failed
mandatory probe, or a revoked/stale lifecycle state all block APPLY.
The Gate records a ``gate_decision`` and, when applied, a ``usage_outcome`` is
bound to the exact revision + gate decision.

R3: The ApplicabilityGate no longer accepts a caller-supplied ``keyring``.
The ProbeExecutor receives its trusted signer internally (R3 §2).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from qvch_v4.applicability.matcher import (
    PreconditionContext,
    evaluate_anti_conditions,
    evaluate_preconditions,
)
from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.manas.envelope import ManasDecisionEnvelope
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.probes.executor import ProbeExecutor, ProbePlan, ProbeReceipt
from qvch_v4.storage import QvchStore, Repository

VERDICT_APPLY = "APPLY"
VERDICT_CAUTIOUS_APPLY = "CAUTIOUS_APPLY"
VERDICT_ESCALATE = "ESCALATE"
VERDICT_QUARANTINE = "QUARANTINE"
VERDICT_REJECT = "REJECT"

# Lifecycle states that must never be auto-applied (brief 13.4 / P0-I gate).
_NON_APPLICABLE_STATES = {
    "STALE", "REVOKED", "QUARANTINED", "ARCHIVED", "ABANDONED", "REFUTED", "SUPERSEDED",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class GateDecision:
    gate_id: str
    atom_id: str
    revision_id: str
    contract_id: str | None
    verdict: str
    reason: str
    decided_at: str
    components: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "atom_id": self.atom_id,
            "revision_id": self.revision_id,
            "contract_id": self.contract_id,
            "verdict": self.verdict,
            "reason": self.reason,
            "decided_at": self.decided_at,
            "components": self.components,
        }


class ApplicabilityGate:
    def __init__(self, store: QvchStore, *,
                 _trusted_signer: DecisionSigner | None = None) -> None:
        """Create an ApplicabilityGate bound to the system's trusted signer.

        ``_trusted_signer`` is set only by internal system code (Studio).
        External callers cannot supply a keyring or signer (R3 §2).
        """
        self._store = store
        self._repo = Repository(store)
        # The probe executor uses the system's trusted signer (R3 §2).
        self._executor = ProbeExecutor(store, _trusted_signer=_trusted_signer)

    def _get_contract(self, atom_id: str, revision_id: str):
        row = self._store._conn.execute(
            "SELECT contract_id, scope, precondition_json, anti_condition_json, required_probes_json "
            "FROM applicability_contracts WHERE atom_id=? AND revision_id=? LIMIT 1",
            (atom_id, revision_id),
        ).fetchone()
        return row

    def _atom_state(self, atom_id: str) -> str | None:
        row = self._store._conn.execute(
            "SELECT current_state FROM memory_atoms WHERE atom_id=?", (atom_id,)
        ).fetchone()
        return row[0] if row else None

    def evaluate(self, *, atom_id: str, revision_id: str,
                 ctx: PreconditionContext | dict | None = None,
                 probe_plans: list[ProbePlan] | None = None,
                 envelope: ManasDecisionEnvelope | None = None,
                 signer: DecisionSigner | None = None,
                 now: str | None = None) -> GateDecision:
        if isinstance(ctx, dict):
            ctx = PreconditionContext.build(**ctx)
        ctx = ctx or PreconditionContext.build()
        now = now or _now_iso()

        contract = self._get_contract(atom_id, revision_id)
        contract_id = contract[0] if contract else None
        pre = json.loads(contract[2]) if contract and contract[2] else []
        if isinstance(pre, dict):
            pre = [pre]
        anti = json.loads(contract[3]) if contract and contract[3] else []
        if isinstance(anti, dict):
            anti = [anti]

        state = self._atom_state(atom_id)
        probes = probe_plans or []

        reasons: list[str] = []
        pre_frac = 1.0
        anti_hit = False
        probe_results: list[ProbeReceipt] = []

        # 1. Lifecycle guard.
        if state in _NON_APPLICABLE_STATES:
            reasons.append(f"lifecycle state {state} prevents automatic apply")

        # 2. Static precondition check.
        if pre:
            pre_frac = evaluate_preconditions(pre, ctx)
            if pre_frac < 1.0:
                reasons.append("precondition not fully satisfied")

        # 3. Anti-condition check.
        if evaluate_anti_conditions(anti, ctx):
            anti_hit = True
            reasons.append("anti-condition matched")

        # 3b. Fail-closed: no contract => never APPLY (brief R1 §8 / R1-Q7).
        no_contract = contract_id is None
        if no_contract:
            reasons.append("no applicability contract; cannot grant APPLY")

        # 3c. Load required probes from the contract's required_probes_json;
        # the caller cannot omit a declared mandatory probe (R1 §8 / R1-Q8).
        contract_required = []
        if contract and contract[4]:
            try:
                contract_required = [
                    p.get("probe_name") for p in json.loads(contract[4])
                    if isinstance(p, dict) and p.get("required")
                ]
            except (json.JSONDecodeError, TypeError):
                contract_required = []
        provided_names = {p.probe_name for p in probes}
        missing_required = [n for n in contract_required if n not in provided_names]
        if missing_required:
            reasons.append(
                "mandatory probe(s) declared in contract omitted: "
                + ", ".join(missing_required)
            )

        # 4. Required cheap probes in Node 15.
        for plan in probes:
            receipt = self._executor.execute(plan, envelope, signer=signer, now=now)
            probe_results.append(receipt)
            self._persist_probe(contract_id, atom_id, plan, receipt, now)
            if plan.required and not receipt.authorized:
                reasons.append(f"mandatory probe {plan.probe_name} lacks valid AUTHORIZE_TEST")
            elif plan.required and not receipt.success:
                reasons.append(f"mandatory probe {plan.probe_name} failed: {receipt.reason}")

        # 5. Verdict.
        verdict, reason = self._verdict(
            state, anti_hit, pre_frac, probes, probe_results, reasons,
            no_contract, missing_required)

        gate_id = f"gate_{sha256_hex(atom_id + revision_id + verdict + now)[:16]}"
        decision = GateDecision(
            gate_id=gate_id, atom_id=atom_id, revision_id=revision_id,
            contract_id=contract_id, verdict=verdict, reason=reason, decided_at=now,
            components={
                "state": state, "precondition_fraction": pre_frac,
                "anti_hit": anti_hit, "probe_count": len(probe_results),
                "probes_passed": sum(1 for r in probe_results if r.success),
                "no_contract": no_contract,
                "missing_required_probes": missing_required,
            },
        )
        self._repo.record_gate_decision(
            gate_id=gate_id, atom_id=atom_id, revision_id=revision_id,
            contract_id=contract_id, verdict=verdict, reason=reason, now=now,
        )
        return decision

    def _verdict(self, state, anti_hit, pre_frac, probes, probe_results, reasons,
                 no_contract=False, missing_required=None):
        if state in _NON_APPLICABLE_STATES:
            return VERDICT_QUARANTINE, reasons[0] if reasons else "non-applicable state"
        if anti_hit:
            return VERDICT_QUARANTINE, "anti-condition matched"
        # Fail-closed: no contract and a declared mandatory probe that the
        # caller omitted both block a full APPLY (R1 §8 / Q7 / Q8).
        if no_contract:
            return VERDICT_ESCALATE, "no applicability contract; cannot grant APPLY"
        if missing_required:
            return VERDICT_QUARANTINE, (
                "mandatory probe(s) declared in contract omitted: "
                + ", ".join(missing_required)
            )
        mandatory = [p for p in probes if p.required]
        if mandatory:
            for r in probe_results:
                pass
            if any(not r.authorized for r in probe_results if r.probe_name in [p.probe_name for p in mandatory]):
                return VERDICT_QUARANTINE, "mandatory probe lacks valid AUTHORIZE_TEST"
            if any(not r.success for r in probe_results if r.probe_name in [p.probe_name for p in mandatory]):
                return VERDICT_QUARANTINE, "mandatory probe failed"
        if pre_frac < 1.0:
            # Cannot grant full APPLY without full precondition satisfaction.
            if not probes or all(r.success and r.authorized for r in probe_results):
                return VERDICT_CAUTIOUS_APPLY, "partial precondition match; apply with caution"
            return VERDICT_QUARANTINE, "precondition unsatisfied"
        if probe_results and any(not (r.success and r.authorized) for r in probe_results if not _is_required(probes, r.probe_name)):
            return VERDICT_CAUTIOUS_APPLY, "non-critical probe failed"
        return VERDICT_APPLY, "all preconditions satisfied and probes passed"

    def _persist_probe(self, contract_id, atom_id, plan, receipt, now):
        payload = receipt.to_payload()
        probe_run_id = f"pr_{sha256_hex(plan.probe_name + receipt.executed_at)[:16]}"
        self._repo.record_probe_run(
            probe_run_id=probe_run_id, probe_plan_id=plan.probe_name,
            atom_id=atom_id, decision_id=None, receipt=payload, now=now,
        )
        if contract_id is not None:
            self._repo.record_applicability_probe(
                probe_id=f"ap_{probe_run_id}", contract_id=contract_id,
                probe_name=plan.probe_name, receipt=payload,
            )

    def record_usage(self, *, atom_id, revision_id, gate_id, outcome,
                     context: dict | None = None, now: str | None = None) -> None:
        """Bind a post-application usage outcome to the exact revision + gate."""
        now = now or _now_iso()
        outcome_id = f"use_{sha256_hex(atom_id + revision_id + outcome + now)[:16]}"
        self._repo.record_usage_outcome(
            outcome_id=outcome_id, atom_id=atom_id, revision_id=revision_id,
            gate_id=gate_id, outcome=outcome, context=context or {}, now=now,
        )


def _is_required(probes: list[ProbePlan], name: str) -> bool:
    for p in probes:
        if p.probe_name == name:
            return p.required
    return False


__all__ = [
    "ApplicabilityGate", "GateDecision",
    "VERDICT_APPLY", "VERDICT_CAUTIOUS_APPLY", "VERDICT_ESCALATE",
    "VERDICT_QUARANTINE", "VERDICT_REJECT",
]