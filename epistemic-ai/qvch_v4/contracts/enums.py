"""Controlled vocabularies for QVCH v4.1.

Every value is a plain string so it can be stored directly in SQLite CHECK
constraints and serialized in canonical JSON.
"""

from enum import Enum


class ClaimType(str, Enum):
    EXTRACTED = "EXTRACTED"
    GENERATED_HYPOTHESIS = "GENERATED_HYPOTHESIS"
    NORMATIVE = "NORMATIVE"
    OBSERVATION_REQUEST = "OBSERVATION_REQUEST"


class AtomKind(str, Enum):
    NOUMENON = "NOUMENON"
    HYPOTHESIS = "HYPOTHESIS"
    FORM = "FORM"
    REPAIR = "REPAIR"
    SKILL = "SKILL"
    LOCATOR = "LOCATOR"
    CAPSULE = "CAPSULE"


class MaterialityClass(str, Enum):
    SEMANTIC = "SEMANTIC"
    LITERAL_ARTIFACT = "LITERAL_ARTIFACT"
    SKILL_TRACE = "SKILL_TRACE"
    SECRET_REF = "SECRET_REF"
    MIXED = "MIXED"


class DecisionPurpose(str, Enum):
    AUTHORIZE_TEST = "AUTHORIZE_TEST"
    AUTHORIZE_WRITE = "AUTHORIZE_WRITE"
    AUTHORIZE_STATE_TRANSITION = "AUTHORIZE_STATE_TRANSITION"


class Verdict(str, Enum):
    APPROVE = "APPROVE"
    QUARANTINE = "QUARANTINE"
    REJECT = "REJECT"


class PramanaType(str, Enum):
    PRATYAKSA = "PRATYAKSA"
    ANUMANA = "ANUMANA"
    SABDA = "SABDA"


class EvidenceSourceType(str, Enum):
    NODE15_EXECUTION = "NODE15_EXECUTION"
    TEST_LOG = "TEST_LOG"
    ARTIFACT_HASH = "ARTIFACT_HASH"
    SOURCE_ANCHOR = "SOURCE_ANCHOR"
    POLICY_CANON = "POLICY_CANON"
    EXTERNAL_SIGNED_RECEIPT = "EXTERNAL_SIGNED_RECEIPT"
    INFERENCE = "INFERENCE"


class ConflictStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED_BY_PRATYAKSA = "RESOLVED_BY_PRATYAKSA"
    CONSTRAINED_BY_SABDA = "CONSTRAINED_BY_SABDA"
    RESOLVED_BY_REFORMULATION = "RESOLVED_BY_REFORMULATION"
    QUARANTINED = "QUARANTINED"
    IRREDUCIBLE = "IRREDUCIBLE"


class LinkType(str, Enum):
    DERIVED_FROM = "DERIVED_FROM"
    TESTED_BY = "TESTED_BY"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    REFUTES = "REFUTES"
    RESOLVES = "RESOLVES"
    SPECIALIZES = "SPECIALIZES"
    SUPERSEDES = "SUPERSEDES"
    LOCATES = "LOCATES"


class ApplicabilityVerdict(str, Enum):
    APPLY = "APPLY"
    CAUTIOUS_APPLY = "CAUTIOUS_APPLY"
    ESCALATE = "ESCALATE"
    QUARANTINE = "QUARANTINE"
    REJECT = "REJECT"


class UsageOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE = "FAILURE"
    ABORTED = "ABORTED"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    UNEXPECTED_SIDE_EFFECT = "UNEXPECTED_SIDE_EFFECT"


# Route values the sovereign MANAS may authorize.
class Route(str, Enum):
    Q = "Q"
    N = "N"
    U = "U"
    F_CANDIDATE = "F_candidate"
    F = "F"
    CRYSTAL = "CRYSTAL"
    REPAIR = "REPAIR"
    SKILL = "SKILL"
    REJECT = "REJECT"
    QUARANTINE = "QUARANTINE"


# --- State machines (brief 10.4) ------------------------------------------------

class NoumenonState(str, Enum):
    OPEN = "OPEN"
    PARTIALLY_REDUCED = "PARTIALLY_REDUCED"
    RESOLVED = "RESOLVED"
    DORMANT = "DORMANT"
    ABANDONED = "ABANDONED"
    REOPENED = "REOPENED"


class HypothesisState(str, Enum):
    PROPOSED = "PROPOSED"
    QUARANTINED = "QUARANTINED"
    AUTHORIZED_FOR_TEST = "AUTHORIZED_FOR_TEST"
    TESTING = "TESTING"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    SUPERSEDED = "SUPERSEDED"


class FormState(str, Enum):
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    WATCH = "WATCH"
    STALE = "STALE"
    QUARANTINED = "QUARANTINED"
    ARCHIVED = "ARCHIVED"
    REVOKED = "REVOKED"


# Fields an untrusted LLM/Studio/client may send but QNUF-Forge must ignore.
FORBIDDEN_LLM_DECISION_FIELDS = {
    "approved",
    "fact",
    "authoritative_confidence",
    "final_route",
    "safe_to_commit",
    "manas_decision",
    "decision",
    "verify",
    "verified",
}
