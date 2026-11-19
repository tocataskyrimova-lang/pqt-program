"""P0-C — CVL, Pramāṇa and conflicts.

Gate P0-C:
  * A failed execution test cannot be turned into 'passed' by inference (Law 1).
  * Policy may forbid an action but the observation stays unchanged (Law 2).
  * Contradictory execution receipts create a conflict and quarantine (Law 3).
"""

import pytest

from qvch_v4.contracts import enums
from qvch_v4.contracts.models import VerbatimAnchor
from qvch_v4.cvl import EvidenceRef, build_evidence, extract
from qvch_v4.cvl.evidence_builder import is_support_bearing
from qvch_v4.pramana import (
    PramanaAssessment,
    arbitrate,
    classify_pramana,
    law1_anumana_cannot_override_pratyaksha,
    law3_conflicting_pratyaksha_is_quarantined,
    law4_blocking_conflict_forbids_f,
)

PRATYAKSA = enums.PramanaType.PRATYAKSA.value
ANUMANA = enums.PramanaType.ANUMANA.value
SABDA = enums.PramanaType.SABDA.value


def _ev(source_type, content="artifact", **kw):
    return build_evidence(source_type, {"run_id": "r1"}, content, **kw)


def test_evidence_is_immutable_reference_and_idempotent():
    e1 = _ev(enums.EvidenceSourceType.NODE15_EXECUTION.value, "output text")
    e2 = _ev(enums.EvidenceSourceType.NODE15_EXECUTION.value, "output text")
    assert e1.evidence_id == e2.evidence_id
    assert e1.canonical_hash() == e2.canonical_hash()
    assert e1.content_hash.startswith("sha256:")


def test_llm_confidence_is_diagnostic_only():
    e = _ev(enums.EvidenceSourceType.INFERENCE.value, "guess", llm_confidence=0.97)
    assert e.is_diagnostic_only
    assert is_support_bearing(e) is False


def test_cvl_binds_extracted_claim_to_source_anchor_evidence():
    anchor = VerbatimAnchor(
        source_event_id="evt1", start_offset=0, end_offset=11,
        quote_hash="sha256:abc", quote="port is 8080",
    )
    draft = type(
        "D",
        (),
        {
            "claims": [
                type(
                    "C", (),
                    {
                        "claim_id": "c1",
                        "claim_type": enums.ClaimType.EXTRACTED.value,
                        "subject": "port",
                        "predicate": "is",
                        "value": "8080",
                        "materiality_class": None,
                        "anchor": anchor,
                    },
                )(),
                type(
                    "C", (),
                    {
                        "claim_id": "c2",
                        "claim_type": enums.ClaimType.GENERATED_HYPOTHESIS.value,
                        "subject": "x",
                        "predicate": "will",
                        "value": "drop",
                        "materiality_class": None,
                        "anchor": None,
                    },
                )(),
            ]
        },
    )()
    extracted = extract(draft)
    by_id = {c.claim_id: c for c in extracted}
    assert by_id["c1"].evidence_ids, "EXTRACTED claim must bind SOURCE_ANCHOR evidence"
    assert by_id["c2"].evidence_ids == (), "hypothesis stays a candidate, no fact promotion"


def test_classify_pramana_mapping():
    assert classify_pramana(_ev(enums.EvidenceSourceType.NODE15_EXECUTION.value)) == PRATYAKSA
    assert classify_pramana(_ev(enums.EvidenceSourceType.POLICY_CANON.value)) == SABDA
    assert classify_pramana(_ev(enums.EvidenceSourceType.INFERENCE.value)) == ANUMANA


def test_law1_failed_execution_cannot_become_passed_by_inference():
    pra = PramanaAssessment("a1", "c1", PRATYAKSA, ("e1",), assertion="svc up", outcome="fail")
    anu = PramanaAssessment("a2", "c2", ANUMANA, ("e2",), assertion="svc up", outcome="pass")
    cf = arbitrate("c1", "c2", pra, anu)
    assert cf.status == enums.ConflictStatus.RESOLVED_BY_PRATYAKSA.value
    assert "Law 1" in (cf.resolution_reason or "")
    # Resolved-by-pratyaksha is not a blocking conflict, so it must NOT forbid F
    # on its own — but the anumana claim is discarded, not used to flip the result.
    assert cf.is_blocking is False
    # Directly: the law function refuses to let inference override the failure.
    assert law1_anumana_cannot_override_pratyaksha("fail", "pass") is False
    assert law1_anumana_cannot_override_pratyaksha("fail", "fail") is True


def test_law2_policy_constrains_action_observation_unchanged():
    pra = PramanaAssessment("a1", "c1", PRATYAKSA, ("e1",), assertion="svc up", outcome="observed")
    sab = PramanaAssessment("a2", "c2", SABDA, ("e2",), assertion="svc up", outcome="forbidden")
    cf = arbitrate("c1", "c2", pra, sab)
    assert cf.status == enums.ConflictStatus.CONSTRAINED_BY_SABDA.value
    assert "Law 2" in (cf.resolution_reason or "")
    # Observation must remain unchanged (the function is invariant).
    assert pra.outcome == "observed"


def test_law3_contradictory_execution_receipts_quarantined():
    pra1 = PramanaAssessment("a1", "c1", PRATYAKSA, ("e1",), assertion="svc up", outcome="pass")
    pra2 = PramanaAssessment("a2", "c2", PRATYAKSA, ("e2",), assertion="svc up", outcome="fail")
    cf = arbitrate("c1", "c2", pra1, pra2)
    assert cf.status == enums.ConflictStatus.QUARANTINED.value
    assert "Law 3" in (cf.resolution_reason or "")
    assert cf.is_blocking is True
    assert law3_conflicting_pratyaksha_is_quarantined("pass", "fail") is True
    assert law3_conflicting_pratyaksha_is_quarantined("pass", "pass") is False


def test_law4_blocking_conflict_forbids_f():
    assert law4_blocking_conflict_forbids_f(
        [enums.ConflictStatus.QUARANTINED.value]) is False
    assert law4_blocking_conflict_forbids_f(
        [enums.ConflictStatus.OPEN.value]) is False
    assert law4_blocking_conflict_forbids_f(
        [enums.ConflictStatus.RESOLVED_BY_PRATYAKSA.value]) is True
    assert law4_blocking_conflict_forbids_f(
        [enums.ConflictStatus.CONSTRAINED_BY_SABDA.value]) is True


def test_no_linear_pramana_scale():
    # The classifier returns a type, not a rank; there is no SABDA>PRATYAKSA
    # ordering anywhere in the API.
    assert set(classify_pramana(_ev(t)) for t in (
        enums.EvidenceSourceType.POLICY_CANON.value,
        enums.EvidenceSourceType.NODE15_EXECUTION.value,
    )) == {SABDA, PRATYAKSA}
