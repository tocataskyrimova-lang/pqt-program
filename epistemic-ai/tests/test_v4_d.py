"""P0-D — Proof-of-Reduction.

Gate P0-D:
  * Direct N->F is impossible.
  * An empty evidence bundle does not pass.
  * LLM confidence does not pass.
  * Partial N reduction yields only a scoped/qualified F_candidate (with residual
    unknowns), never a global FACT.
"""

import pytest

from qvch_v4.reduction import (
    AcceptanceCriterion,
    BaselineSlot,
    EvidenceItem,
    ReductionInput,
    ReductionVerifier,
)

THRESHOLD = 0.6


def _input(**over):
    base = dict(
        lineage_id="lin1",
        noumenon_atom_id="n1",
        baseline_unknown_slots=(
            BaselineSlot("u_latency", 0.6),
            BaselineSlot("u_throughput", 0.4),
        ),
        resolved_slot_ids=("u_latency", "u_throughput"),
        acceptance_criteria=(AcceptanceCriterion("ac1", True, True),),
        evidence_items=(EvidenceItem(1.0, True), EvidenceItem(0.5, True)),
        required_evidence_weight=1.5,
        scope_coverage=1.0,
        contradiction_pressure=0.0,
        supported_u_atom_ids=("u1", "u2"),
        evidence_bundle_ids=("eb1",),
    )
    base.update(over)
    return ReductionInput(**base)


def test_formula_is_deterministic_and_matches_spec():
    v = ReductionVerifier()
    inp = _input()
    cert = v.reduce(inp)
    # manual: slot_reduction=1.0, evidence_quality=(1.0+0.5)/1.5=1.0,
    # scope=1.0, (1-0)=1 -> 1.0
    assert cert.slot_reduction == 1.0
    assert cert.evidence_quality == pytest.approx(1.0)
    assert cert.reduction_score == pytest.approx(1.0)
    # determinism: equal input -> equal proof id/hash
    cert2 = v.reduce(_input())
    assert cert.proof_id == cert2.proof_id
    assert cert.proof_hash == cert2.proof_hash


def test_full_reduction_yields_global_fact():
    v = ReductionVerifier()
    verdict = v.can_crystallize(_input(), THRESHOLD)
    assert verdict.allowed is True
    assert verdict.route == "F"
    assert "global FACT" in verdict.reason


def test_direct_n_to_f_impossible():
    v = ReductionVerifier()
    verdict = v.can_crystallize(_input(resolved_slot_ids=()), THRESHOLD)
    assert verdict.allowed is False
    assert "direct N->F" in verdict.reason


def test_empty_evidence_bundle_rejected():
    v = ReductionVerifier()
    verdict = v.can_crystallize(_input(evidence_items=()), THRESHOLD)
    assert verdict.allowed is False
    assert "empty" in verdict.reason


def test_llm_confidence_only_rejected():
    v = ReductionVerifier()
    # only LLM-confidence (non-support-bearing) evidence
    verdict = v.can_crystallize(
        _input(evidence_items=(EvidenceItem(0.9, False),)), THRESHOLD
    )
    assert verdict.allowed is False
    assert "LLM confidence" in verdict.reason


def test_partial_reduction_only_scoped_candidate():
    v = ReductionVerifier()
    # resolve only one of two baseline slots
    verdict = v.can_crystallize(
        _input(resolved_slot_ids=("u_latency",)), THRESHOLD
    )
    assert verdict.allowed is True
    assert verdict.route == "F_candidate"
    # global FACT requires full resolution
    strict = v.can_crystallize(
        _input(resolved_slot_ids=("u_latency",)), THRESHOLD, allow_scoped=False
    )
    assert strict.allowed is False
    assert "residual" in strict.reason


def test_blocking_conflict_forbids_f():
    v = ReductionVerifier()
    verdict = v.can_crystallize(_input(contradiction_pressure=1.0), THRESHOLD)
    assert verdict.allowed is False
    assert "blocking conflict" in verdict.reason


def test_dummy_chain_rejected():
    v = ReductionVerifier()
    verdict = v.can_crystallize(
        _input(baseline_unknown_slots=(), resolved_slot_ids=()), THRESHOLD
    )
    assert verdict.allowed is False
    assert "no baseline unknowns" in verdict.reason


def test_critical_criterion_failure_rejected():
    v = ReductionVerifier()
    verdict = v.can_crystallize(
        _input(acceptance_criteria=(AcceptanceCriterion("ac1", True, False),)), THRESHOLD
    )
    assert verdict.allowed is False
    assert "critical" in verdict.reason


def test_below_threshold_rejected():
    v = ReductionVerifier()
    # dilute evidence quality and scope so score < threshold
    verdict = v.can_crystallize(
        _input(
            evidence_items=(EvidenceItem(0.3, True),),
            required_evidence_weight=1.5,
            scope_coverage=0.7,
        ),
        0.9,
    )
    assert verdict.allowed is False
    assert "threshold" in verdict.reason
