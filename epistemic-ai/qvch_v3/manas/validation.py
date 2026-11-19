from __future__ import annotations

from qvch_v3.contracts.models import EvidenceRef, ValidationResult, new_id


def validate_candidate(*, evidence_refs: list[EvidenceRef] | None = None, conflict_detected: bool = False, duplicate_of: str | None = None) -> ValidationResult:
    refs = list(evidence_refs or [])
    non_llm = [e for e in refs if not e.is_llm_confidence]
    passed = bool(non_llm) and not conflict_detected
    reasons = []
    if not non_llm:
        reasons.append("no_non_llm_evidence")
    if conflict_detected:
        reasons.append("conflict_detected")
    if duplicate_of:
        reasons.append("duplicate_detected")
    if passed:
        reasons.append("validation_passed")
    return ValidationResult(new_id("val"), passed, refs, conflict_detected, duplicate_of, reasons)
