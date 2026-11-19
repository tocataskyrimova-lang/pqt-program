"""Proof-of-Reduction (brief 8).

The ReductionVerifier is the *server-side* authority that decides whether an N
lineage may crystallize. The LLM never sets the final score (brief 8.1:
"LLM не задаёт итоговый score"). The score is computed by a single deterministic
formula and ``can_crystallize()`` enforces every gate before MANAS may issue an
APPROVE for FORM/CRYSTAL.

Formula (brief 8.1):

    slot_reduction   = resolved_weight / baseline_unknown_weight
    evidence_quality = weighted_valid_evidence / required_evidence_weight
    reduction_score  = clamp(
        slot_reduction * evidence_quality * scope_coverage * (1 - contradiction_pressure),
        0, 1)

Gates (brief 8.1 / Gate P0-D):
  * baseline has >= 1 real unknown weighted slot;
  * all critical acceptance criteria passed;
  * evidence is non-empty and support-bearing (LLM confidence alone fails);
  * residual unknowns enumerated explicitly;
  * no blocking conflict (contradiction_pressure < 1);
  * at least one supported U;
  * reduction_score > 0 and >= policy threshold;
  * direct N->F (nothing resolved) is impossible;
  * partial reduction yields only a scoped/qualified F_candidate, never a
    global FACT.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import hash_json, sha256_hex

VERIFIER_VERSION = "reduction-verifier/1.0"


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass(frozen=True)
class BaselineSlot:
    slot_id: str
    weight: float


@dataclass(frozen=True)
class AcceptanceCriterion:
    criterion_id: str
    critical: bool
    passed: bool


@dataclass(frozen=True)
class EvidenceItem:
    weight: float
    # False for LLM-confidence-only records, which are never support-bearing.
    support_bearing: bool


@dataclass(frozen=True)
class ReductionInput:
    lineage_id: str
    noumenon_atom_id: str
    baseline_unknown_slots: tuple[BaselineSlot, ...]
    resolved_slot_ids: tuple[str, ...]
    acceptance_criteria: tuple[AcceptanceCriterion, ...]
    evidence_items: tuple[EvidenceItem, ...]
    required_evidence_weight: float
    scope_coverage: float
    contradiction_pressure: float
    supported_u_atom_ids: tuple[str, ...]
    evidence_bundle_ids: tuple[str, ...] = ()
    counterexamples: tuple[str, ...] = ()
    failed_tests: tuple[str, ...] = ()
    passed_tests: tuple[str, ...] = ()
    scope: str = "global"
    verifier_version: str = VERIFIER_VERSION


@dataclass(frozen=True)
class ReductionCertificate:
    proof_id: str
    lineage_id: str
    noumenon_atom_id: str
    supported_u_atom_ids: tuple[str, ...]
    baseline_unknown_slots: tuple[BaselineSlot, ...]
    acceptance_criteria: tuple[AcceptanceCriterion, ...]
    evidence_bundle_ids: tuple[str, ...]
    passed_tests: tuple[str, ...]
    failed_tests: tuple[str, ...]
    counterexamples: tuple[str, ...]
    resolved_slots: tuple[str, ...]
    residual_unknown_slots: tuple[str, ...]
    baseline_unknown_weight: float
    resolved_weight: float
    contradiction_pressure: float
    slot_reduction: float
    evidence_quality: float
    scope_coverage: float
    reduction_score: float
    scope: str
    verifier_version: str
    proof_hash: str
    critical_criteria_all_passed: bool
    has_supporting_evidence: bool

    def to_payload(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "lineage_id": self.lineage_id,
            "noumenon_atom_id": self.noumenon_atom_id,
            "supported_u_atom_ids": list(self.supported_u_atom_ids),
            "baseline_unknown_slots": [s.__dict__ for s in self.baseline_unknown_slots],
            "acceptance_criteria": [c.__dict__ for c in self.acceptance_criteria],
            "evidence_bundle_ids": list(self.evidence_bundle_ids),
            "passed_tests": list(self.passed_tests),
            "failed_tests": list(self.failed_tests),
            "counterexamples": list(self.counterexamples),
            "resolved_slots": list(self.resolved_slots),
            "residual_unknown_slots": list(self.residual_unknown_slots),
            "baseline_unknown_weight": self.baseline_unknown_weight,
            "resolved_weight": self.resolved_weight,
            "contradiction_pressure": self.contradiction_pressure,
            "slot_reduction": self.slot_reduction,
            "evidence_quality": self.evidence_quality,
            "scope_coverage": self.scope_coverage,
            "reduction_score": self.reduction_score,
            "scope": self.scope,
            "verifier_version": self.verifier_version,
            "proof_hash": self.proof_hash,
            "critical_criteria_all_passed": self.critical_criteria_all_passed,
            "has_supporting_evidence": self.has_supporting_evidence,
        }

    def canonical_hash(self) -> str:
        return hash_json(self.to_payload())


@dataclass(frozen=True)
class CrystallizationVerdict:
    allowed: bool
    route: str | None  # enums.Route.F or enums.Route.F_CANDIDATE, else None
    reduction_score: float
    reason: str


@dataclass(frozen=True)
class ReductionQuery:
    """A *SQL-derived* reduction query carrying IDs only (brief R1 §6).

    No canonical payloads travel with the query; the verifier resolves the
    stored ``ReductionCertificate`` from SQL by ``proof_id`` (or by
    ``lineage_id`` + ``supported_u_atom_ids``) and re-checks its content hash.
    """

    kind: str = "reduction"
    lineage_id: str = ""
    proof_id: str = ""
    noumenon_atom_id: str = ""
    supported_u_atom_ids: tuple[str, ...] = ()


def build_reduction_query(*, lineage_id: str = "", proof_id: str = "",
                          noumenon_atom_id: str = "",
                          supported_u_atom_ids: tuple[str, ...] = ()) -> ReductionQuery:
    """Construct an IDs-only reduction query (brief R1 §6)."""
    return ReductionQuery(
        lineage_id=lineage_id, proof_id=proof_id,
        noumenon_atom_id=noumenon_atom_id,
        supported_u_atom_ids=tuple(supported_u_atom_ids),
    )


class ReductionVerifier:
    """Deterministic, server-side reduction authority (no LLM influence)."""

    def __init__(self, verifier_version: str = VERIFIER_VERSION) -> None:
        self.verifier_version = verifier_version

    def reduce(self, inp: ReductionInput) -> ReductionCertificate:
        baseline_unknown_weight = sum(s.weight for s in inp.baseline_unknown_slots)
        resolved_set = set(inp.resolved_slot_ids)
        resolved_weight = sum(
            s.weight for s in inp.baseline_unknown_slots if s.slot_id in resolved_set
        )
        residual = tuple(
            s.slot_id for s in inp.baseline_unknown_slots if s.slot_id not in resolved_set
        )

        slot_reduction = (
            resolved_weight / baseline_unknown_weight if baseline_unknown_weight > 0 else 0.0
        )
        weighted_valid = sum(
            e.weight for e in inp.evidence_items if e.support_bearing
        )
        required = inp.required_evidence_weight
        evidence_quality = weighted_valid / required if required > 0 else 0.0

        reduction_score = _clamp(
            slot_reduction
            * evidence_quality
            * inp.scope_coverage
            * (1.0 - _clamp(inp.contradiction_pressure, 0.0, 1.0))
        )

        critical_all_passed = all(
            (not c.critical) or c.passed for c in inp.acceptance_criteria
        )
        has_supporting = any(e.support_bearing for e in inp.evidence_items)

        cert = ReductionCertificate(
            proof_id="",
            lineage_id=inp.lineage_id,
            noumenon_atom_id=inp.noumenon_atom_id,
            supported_u_atom_ids=inp.supported_u_atom_ids,
            baseline_unknown_slots=inp.baseline_unknown_slots,
            acceptance_criteria=inp.acceptance_criteria,
            evidence_bundle_ids=inp.evidence_bundle_ids,
            passed_tests=inp.passed_tests,
            failed_tests=inp.failed_tests,
            counterexamples=inp.counterexamples,
            resolved_slots=tuple(sorted(resolved_set & {s.slot_id for s in inp.baseline_unknown_slots})),
            residual_unknown_slots=residual,
            baseline_unknown_weight=baseline_unknown_weight,
            resolved_weight=resolved_weight,
            contradiction_pressure=inp.contradiction_pressure,
            slot_reduction=slot_reduction,
            evidence_quality=evidence_quality,
            scope_coverage=inp.scope_coverage,
            reduction_score=reduction_score,
            scope=inp.scope,
            verifier_version=self.verifier_version,
            proof_hash="",
            critical_criteria_all_passed=critical_all_passed,
            has_supporting_evidence=has_supporting,
        )
        # Content-addressed, deterministic proof id and hash.
        payload = cert.to_payload()
        payload["proof_id"] = ""
        payload["proof_hash"] = ""
        proof_hash = hash_json(payload)
        return ReductionCertificate(
            proof_id=f"rc_{sha256_hex(proof_hash)[7:23]}",
            proof_hash=proof_hash,
            **{k: v for k, v in cert.__dict__.items() if k not in ("proof_id", "proof_hash")},
        )

    def can_crystallize(
        self,
        inp: ReductionInput,
        policy_threshold: float,
        *,
        allow_scoped: bool = True,
    ) -> CrystallizationVerdict:
        cert = self.reduce(inp)

        if cert.baseline_unknown_weight <= 0:
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                "rejected: no baseline unknowns (direct N->F / dummy chain rejected)",
            )
        if not cert.critical_criteria_all_passed:
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                "rejected: a critical acceptance criterion failed",
            )
        if (not cert.has_supporting_evidence) or cert.evidence_quality <= 0:
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                "rejected: empty or non-supporting evidence bundle (LLM confidence alone fails)",
            )
        if cert.contradiction_pressure >= 1.0:
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                "rejected: blocking conflict forbids F (Law 4)",
            )
        if not cert.supported_u_atom_ids:
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                "rejected: no supported U atom",
            )
        if cert.resolved_weight <= 0:
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                "rejected: direct N->F impossible (nothing resolved)",
            )
        if cert.reduction_score <= 0:
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                "rejected: reduction_score <= 0",
            )
        if cert.reduction_score < policy_threshold:
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                f"rejected: reduction_score {cert.reduction_score:.4f} < threshold {policy_threshold:.4f}",
            )
        if cert.residual_unknown_slots:
            if allow_scoped:
                return CrystallizationVerdict(
                    True, enums.Route.F_CANDIDATE.value, cert.reduction_score,
                    "scoped/qualified F candidate with residual unknowns",
                )
            return CrystallizationVerdict(
                False, None, cert.reduction_score,
                "rejected: residual unknowns remain; global FACT requires full resolution",
            )
        return CrystallizationVerdict(
            True, enums.Route.F.value, cert.reduction_score,
            "global FACT authorized",
        )


__all__ = [
    "ReductionVerifier",
    "ReductionCertificate",
    "ReductionInput",
    "BaselineSlot",
    "AcceptanceCriterion",
    "EvidenceItem",
    "CrystallizationVerdict",
    "VERIFIER_VERSION",
]
