"""CVL — Claim extraction and immutable evidence references."""

from qvch_v4.cvl.claim_extractor import ExtractedClaim, extract
from qvch_v4.cvl.evidence_builder import EvidenceRef, build_evidence, is_support_bearing

__all__ = [
    "ExtractedClaim",
    "extract",
    "EvidenceRef",
    "build_evidence",
    "is_support_bearing",
]
