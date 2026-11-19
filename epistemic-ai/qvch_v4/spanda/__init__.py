"""QVCH v4 Spanda viability engine (brief 14).

Spanda measures whether a live revision is still *viable* — whether it should
remain ACTIVE, or be degraded through WATCH → STALE → QUARANTINED. It is a
scoring engine only; it never deletes history and never decides policy by
itself. Downward (influence-reducing) transitions are applied automatically;
upward (re-activating) transitions require a MANAS decision envelope.
"""

from qvch_v4.spanda.engine import Spanda, SpandaAssessment, compute_score, recommend_state

__all__ = ["Spanda", "SpandaAssessment", "compute_score", "recommend_state"]
