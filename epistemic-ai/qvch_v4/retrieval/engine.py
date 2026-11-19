"""Epistemic retrieval engine (brief 12).

``retrieve`` runs the search substrate, computes every scoring component
server-side, builds an :class:`EpistemicRetrievalPacket` per hit, persists the
run + hits through the repository, and returns the ranked packets. It never
hides conflicting candidates (brief 12.4) and never returns a refuted atom as
truth (its confidence is crushed by contradiction_pressure).
"""

from __future__ import annotations

import json

from qvch_v4.applicability.matcher import (
    PreconditionContext,
    evaluate_anti_conditions,
    evaluate_preconditions,
)
from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.contracts.models import new_id
from qvch_v4.retrieval.scoring import (
    EpistemicRetrievalPacket,
    compute_epistemic_confidence,
    compute_retrieval_rank,
    freshness_for_state,
)
from qvch_v4.retrieval.search import search
from qvch_v4.storage import Repository

_REFUTED = "REFUTED"
_STALE = "STALE"
_CONTRA_LINKS = ("CONTRADICTS", "REFUTES")
_SUCCESS_OUTCOMES = ("SUCCESS", "PARTIAL_SUCCESS")

_DOWNGRADE_RULE = {
    "WATCH": "downgrade to STALE then QUARANTINED on drift",
    "STALE": "QUARANTINED", "DORMANT": "REOPENED or ABANDONED",
    "QUARANTINED": "ARCHIVED or REVOKED", "ACTIVE": "WATCH on environment drift",
}


def _q(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()


def _support_bearing_evidence(conn, evidence_ids):
    support = 0
    for eid in evidence_ids:
        row = _q(conn, "SELECT llm_confidence FROM evidence_refs WHERE evidence_id=?", (eid,))
        if row is None:
            continue
        if row[0] is None:  # real evidence, not LLM confidence
            support += 1
    return support


def _anchor_support(conn, payload) -> float:
    ids = payload.get("migrated_evidence_refs") or payload.get("evidence_refs") or []
    total = len(ids)
    if total == 0:
        return 0.0
    return _support_bearing_evidence(conn, ids) / total


def _reproducibility(conn, atom_id, state) -> float:
    if state == _REFUTED:
        return 0.0
    rows = conn.execute(
        "SELECT outcome FROM usage_outcomes WHERE atom_id=?", (atom_id,)
    ).fetchall()
    total = len(rows)
    if total == 0:
        return 0.5  # Laplace uninformative prior, not 1.0
    successes = sum(1 for r in rows if r[0] in _SUCCESS_OUTCOMES)
    return (successes + 1) / (total + 2)


def _applicability(conn, atom_id, revision_id, ctx) -> float:
    row = _q(
        conn,
        "SELECT precondition_json, anti_condition_json, scope FROM applicability_contracts "
        "WHERE atom_id=? AND revision_id=? LIMIT 1",
        (atom_id, revision_id),
    )
    if row is None:
        return 1.0
    pre = json.loads(row[0]) if row[0] else []
    if isinstance(pre, dict):  # tolerate a single-condition contract
        pre = [pre]
    anti = json.loads(row[1]) if row[1] else []
    if isinstance(anti, dict):
        anti = [anti]
    if evaluate_anti_conditions(anti, ctx):
        return 0.0
    return evaluate_preconditions(pre, ctx)


def _contradiction(conn, atom_id, state, support_count=0):
    if state == _REFUTED:
        return 0.9, []
    rows = conn.execute(
        "SELECT from_atom_id FROM memory_links "
        "WHERE to_atom_id=? AND link_type IN (?, ?)",
        (atom_id, _CONTRA_LINKS[0], _CONTRA_LINKS[1]),
    ).fetchall()
    conflicting = [r[0] for r in rows]
    if not conflicting:
        return 0.0, []
    # Weighted unresolved contradictions relative to total support (brief 12.3).
    pressure = min(1.0, len(conflicting) / (support_count + 1))
    return pressure, conflicting


def _task_utility(task, kind, materiality) -> float:
    if not task:
        return 1.0
    if task.get("atom_kind") == kind:
        return 1.0
    if task.get("materiality") == materiality:
        return 0.6
    return 0.3


def _content_capsule(materiality, payload):
    if materiality == "LITERAL_ARTIFACT":
        return {
            "locator": payload.get("exact_locator"),
            "immutable_content_hash": payload.get("immutable_content_hash"),
        }
    return payload


def retrieve(store, query: str, *, task: dict | None = None,
             ctx: PreconditionContext | dict | None = None,
             limit: int = 10) -> list[EpistemicRetrievalPacket]:
    if isinstance(ctx, dict):
        ctx = PreconditionContext.build(**ctx)
    ctx = ctx or PreconditionContext.build()

    candidates = search(store, query, limit=limit)
    packets: list[EpistemicRetrievalPacket] = []
    hits: list[dict] = []
    conn = store._conn
    run_id = new_id("run")

    for cand in candidates:
        rev_id = cand["revision_id"]
        atom_id = cand["atom_id"]
        atom = _q(conn, "SELECT atom_kind, current_state, materiality_class, lineage_id "
                        "FROM memory_atoms WHERE atom_id=?", (atom_id,))
        if atom is None:
            continue
        kind, state, materiality, lineage_id = atom
        rev = _q(conn, "SELECT canonical_payload_json FROM atom_revisions WHERE revision_id=?", (rev_id,))
        if rev is None:
            continue
        payload = json.loads(rev[0])

        evidence_ids = payload.get("migrated_evidence_refs") or payload.get("evidence_refs") or []
        supporting = [e for e in evidence_ids if _is_support(conn, e)]

        anchor = _anchor_support(conn, payload)
        repro = _reproducibility(conn, atom_id, state)
        appl = _applicability(conn, atom_id, rev_id, ctx)
        fresh = freshness_for_state(state)
        cp, conflicting = _contradiction(conn, atom_id, state, len(supporting))
        conf = compute_epistemic_confidence(anchor, repro, appl, fresh, cp)
        tu = _task_utility(task, kind, materiality)
        rank = compute_retrieval_rank(cand["semantic_relevance"], conf, tu)

        contract = _q(conn,
                      "SELECT scope, precondition_json, anti_condition_json FROM applicability_contracts "
                      "WHERE atom_id=? AND revision_id=? LIMIT 1", (atom_id, rev_id))
        scope = contract[0] if contract else None
        preconds = json.loads(contract[1]) if contract and contract[1] else []
        anticonds = json.loads(contract[2]) if contract and contract[2] else []

        pkt = EpistemicRetrievalPacket(
            atom_id=atom_id, revision_id=rev_id, atom_kind=kind, epistemic_state=state,
            content_capsule_or_locator=_content_capsule(materiality, payload),
            semantic_relevance=cand["semantic_relevance"],
            anchor_support=anchor, reproducibility=repro, applicability=appl,
            freshness=fresh, contradiction_pressure=cp, epistemic_confidence=conf,
            task_utility=tu, retrieval_rank=rank,
            supporting_evidence=supporting, contradicting_evidence=[],
            conflicting_candidates=conflicting, lineage_id=lineage_id, scope=scope,
            preconditions=preconds, anti_conditions=anticonds,
            downgrade_rule=_DOWNGRADE_RULE.get(state), lifecycle_status=state,
            is_refuted=(state == _REFUTED), is_stale=(state == _STALE),
        )
        packets.append(pkt)
        hits.append({
            "hit_id": f"hit_{sha256_hex(run_id + atom_id + rev_id)[:16]}",
            "atom_id": atom_id, "revision_id": rev_id,
            "semantic_relevance": pkt.semantic_relevance,
            "anchor_support": pkt.anchor_support,
            "reproducibility": pkt.reproducibility,
            "applicability": pkt.applicability,
            "freshness": pkt.freshness,
            "contradiction_pressure": pkt.contradiction_pressure,
            "epistemic_confidence": pkt.epistemic_confidence,
            "task_utility": pkt.task_utility,
            "retrieval_rank": pkt.retrieval_rank,
            "atom_kind": kind, "epistemic_state": state,
            "supporting_evidence": supporting,
            "contradicting_evidence": [],
            "conflicting_candidates": conflicting,
            "is_refuted": pkt.is_refuted, "is_stale": pkt.is_stale,
        })

    packets.sort(key=lambda p: p.retrieval_rank, reverse=True)
    Repository(store).record_retrieval_run(run_id=run_id, query=query, hits=hits)
    return packets


def _is_support(conn, eid) -> bool:
    row = _q(conn, "SELECT llm_confidence FROM evidence_refs WHERE evidence_id=?", (eid,))
    return row is not None and row[0] is None


__all__ = ["retrieve"]
