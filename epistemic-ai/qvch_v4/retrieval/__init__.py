"""QVCH v4 epistemic retrieval subsystem (brief 12)."""

from qvch_v4.retrieval.engine import retrieve
from qvch_v4.retrieval.scoring import (
    EpistemicRetrievalPacket,
    compute_epistemic_confidence,
    compute_retrieval_rank,
    freshness_for_state,
)
from qvch_v4.retrieval.search import fts5_available, search

__all__ = [
    "retrieve",
    "EpistemicRetrievalPacket",
    "compute_epistemic_confidence",
    "compute_retrieval_rank",
    "freshness_for_state",
    "search",
    "fts5_available",
]
