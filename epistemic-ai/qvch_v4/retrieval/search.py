"""Search substrate for epistemic retrieval (brief 12.1).

Primary: SQLite FTS5 with ``bm25`` ranking, indexed over a *transient*
in-memory connection (never the protected v4 store, so no DDL touches the
authorizer-guarded schema). Deterministic fallback: token-overlap scoring when
FTS5 is unavailable. No external vector DB (brief 12.1).
"""

from __future__ import annotations

import re
import sqlite3

_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is",
    "are", "was", "were", "be", "by", "as", "at", "it", "this", "that", "from",
}


def _tokenize(text: str) -> list[str]:
    return [w for w in re.split(r"\W+", (text or "").lower()) if w and w not in _STOP]


def fts5_available() -> bool:
    try:
        c = sqlite3.connect(":memory:")
        c.execute("CREATE VIRTUAL TABLE _fts_probe USING fts5(content)")
        c.close()
        return True
    except sqlite3.OperationalError:
        return False


def _fallback_scores(query: str, docs: dict[str, str]) -> dict[str, float]:
    q = set(_tokenize(query))
    out: dict[str, float] = {}
    if not q:
        return out
    for did, text in docs.items():
        toks = set(_tokenize(text))
        overlap = sum(1 for t in q if t in toks)
        out[did] = overlap / len(q)
    return out


def _fts5_scores(query: str, docs: dict[str, str]) -> dict[str, float] | None:
    try:
        c = sqlite3.connect(":memory:")
        c.execute("CREATE VIRTUAL TABLE fts USING fts5(rev_id UNINDEXED, content)")
        c.executemany(
            "INSERT INTO fts (rev_id, content) VALUES (?, ?)",
            [(k, v) for k, v in docs.items()],
        )
        q = " ".join(f'"{t}"' for t in _tokenize(query))
        if not q:
            c.close()
            return {}
        rows = c.execute(
            "SELECT rev_id, bm25(fts) AS score FROM fts WHERE fts MATCH ? ORDER BY score",
            (q,),
        ).fetchall()
        c.close()
    except sqlite3.OperationalError:
        return None
    if not rows:
        return {}
    # bm25: more negative == better match. Map to a strictly positive relevance
    # in (0, 1] so every matched revision survives the caller's s > 0 filter,
    # even when bm25 length-normalization rates two equally-relevant docs
    # differently (a min-max normalization would force the weaker one to 0.0).
    out: dict[str, float] = {}
    for rid, score in rows:
        raw = -score
        if raw <= 0:
            out[rid] = 1e-6
        else:
            out[rid] = raw / (1.0 + raw)
    return out


def search(store, query: str, limit: int = 10) -> list[dict[str, object]]:
    """Return ranked candidate revisions for ``query``.

    Each item: ``{"revision_id", "atom_id", "semantic_relevance"}`` sorted by
    relevance descending. Only revisions with a positive match are returned.
    """
    rows = store._conn.execute(
        "SELECT r.revision_id, r.atom_id, r.canonical_payload_json "
        "FROM atom_revisions r JOIN memory_atoms a ON a.atom_id = r.atom_id"
    ).fetchall()
    docs = {r[0]: r[2] for r in rows}
    atom_of = {r[0]: r[1] for r in rows}

    if fts5_available():
        scores = _fts5_scores(query, docs)
        if scores is None:
            scores = _fallback_scores(query, docs)
    else:
        scores = _fallback_scores(query, docs)

    candidates = [
        {"revision_id": rid, "atom_id": atom_of[rid], "semantic_relevance": round(s, 6)}
        for rid, s in scores.items() if s > 0
    ]
    candidates.sort(key=lambda c: c["semantic_relevance"], reverse=True)
    return candidates[:limit]


__all__ = ["search", "fts5_available"]
