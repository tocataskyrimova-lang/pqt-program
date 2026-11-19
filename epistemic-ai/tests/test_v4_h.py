"""P0-H — Epistemic Retrieval (brief 12).

Gate P0-H:
- FACT/FORM, HYPOTHESIS, NOUMENON, STALE and REFUTED are programmatically
  distinguishable (packet fields).
- Contradictions are returned explicitly (conflicting_candidates).
- A similar-but-refuted atom is not returned as truth.
- A literal artifact is returned as a locator + hash, not paraphrased code.
- With no evidence an atom's epistemic_confidence can never be 1.0.
"""

from __future__ import annotations

from qvch_v4.applicability.matcher import PreconditionContext
from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.retrieval import compute_epistemic_confidence, compute_retrieval_rank, retrieve
from qvch_v4.retrieval.scoring import freshness_for_state
from qvch_v4.storage import QvchStore, Repository


def _build_db(path: str) -> QvchStore:
    store = QvchStore(path, migration=True)
    store.init_schema()
    repo = Repository(store)

    repo.ensure_lineage("lin_f1")
    repo.ensure_lineage("lin_f2")
    repo.ensure_lineage("lin_h1")
    repo.ensure_lineage("lin_n1")
    repo.ensure_lineage("lin_lit")

    # Real evidence (llm_confidence NULL => support-bearing).
    repo.record_evidence(_ev("ev1", "logs confirm build deterministic"))
    repo.record_evidence(_ev("ev2", "tests confirm reproducible build"))

    # FORM/FACT with evidence.
    repo.write_atom(
        atom_id="fact_1", lineage_id="lin_f1", atom_kind="FORM",
        materiality_class="SEMANTIC", state="CANDIDATE",
        canonical_payload={"form": "build deterministic", "migrated_evidence_refs": ["ev1", "ev2"]},
        content_hash=sha256_hex("fact_1"),
    )
    # Similar FORM but REFUTED and with no supporting evidence.
    repo.write_atom(
        atom_id="fact_2", lineage_id="lin_f2", atom_kind="FORM",
        materiality_class="SEMANTIC", state="REFUTED",
        canonical_payload={"form": "build deterministic", "migrated_evidence_refs": []},
        content_hash=sha256_hex("fact_2"),
    )
    # HYPOTHESIS branch.
    repo.write_atom(
        atom_id="hyp_1", lineage_id="lin_h1", atom_kind="HYPOTHESIS",
        materiality_class="SEMANTIC", state="SUPPORTED",
        canonical_payload={"u": "latency under 200ms", "migrated_evidence_refs": ["ev1"]},
        content_hash=sha256_hex("hyp_1"),
    )
    # NOUMENON.
    repo.write_atom(
        atom_id="nou_1", lineage_id="lin_n1", atom_kind="NOUMENON",
        materiality_class="SEMANTIC", state="PARTIALLY_REDUCED",
        canonical_payload={"noumenon": "unknown latency"}, content_hash=sha256_hex("nou_1"),
    )
    # LITERAL_ARTIFACT returned as locator + hash.
    repo.write_atom(
        atom_id="lit_1", lineage_id="lin_lit", atom_kind="LOCATOR",
        materiality_class="LITERAL_ARTIFACT", state="ACTIVE",
        canonical_payload={"exact_locator": "file:///src/x.py", "immutable_content_hash": "sha256:deadbeef"},
        content_hash=sha256_hex("lit_1"),
    )
    repo.record_artifact_locator(
        locator_id="loc_1", materiality_class="LITERAL_ARTIFACT",
        exact_locator="file:///src/x.py", immutable_content_hash="sha256:deadbeef",
    )
    # fact_2 REFUTES fact_1 -> visible conflicting candidate.
    repo.link("fact_2", "fact_1", "REFUTES")
    return store


def _ev(eid, summary):
    from qvch_v4.cvl.evidence_builder import EvidenceRef
    return EvidenceRef(
        evidence_id=eid, source_type="TEST_LOG",
        locator={"source_ref": summary}, canonical_payload={"summary": summary},
        content_hash=sha256_hex(summary), llm_confidence=None,
    )


def test_fts5_or_fallback_finds_matching_atoms(tmp_path):
    store = _build_db(str(tmp_path / "mem.db"))
    packets = retrieve(store, "build deterministic")
    ids = {p.atom_id for p in packets}
    assert "fact_1" in ids
    assert "fact_2" in ids
    store.close()


def test_refuted_atom_not_returned_as_truth(tmp_path):
    store = _build_db(str(tmp_path / "mem.db"))
    packets = retrieve(store, "build deterministic")
    by_id = {p.atom_id: p for p in packets}
    assert by_id["fact_2"].is_refuted is True
    assert by_id["fact_1"].is_refuted is False
    # The refuted atom must rank below the supported one.
    assert by_id["fact_1"].retrieval_rank > by_id["fact_2"].retrieval_rank
    # And its epistemic confidence is crushed.
    assert by_id["fact_2"].epistemic_confidence < by_id["fact_1"].epistemic_confidence
    assert by_id["fact_2"].epistemic_confidence < 0.3
    store.close()


def test_contradiction_visible(tmp_path):
    store = _build_db(str(tmp_path / "mem.db"))
    packets = retrieve(store, "build deterministic")
    fact1 = next(p for p in packets if p.atom_id == "fact_1")
    assert "fact_2" in fact1.conflicting_candidates
    assert fact1.contradiction_pressure > 0.0
    store.close()


def test_no_evidence_confidence_not_one(tmp_path):
    store = _build_db(str(tmp_path / "mem.db"))
    # fact_2 has no evidence -> anchor_support 0 -> confidence 0 regardless.
    packets = retrieve(store, "build deterministic")
    fact2 = next(p for p in packets if p.atom_id == "fact_2")
    assert fact2.epistemic_confidence < 1.0
    assert fact2.epistemic_confidence == 0.0
    store.close()


def test_literal_artifact_returned_as_locator_and_hash(tmp_path):
    store = _build_db(str(tmp_path / "mem.db"))
    packets = retrieve(store, "x.py")
    lit = next((p for p in packets if p.atom_id == "lit_1"), None)
    assert lit is not None
    cap = lit.content_capsule_or_locator
    assert cap["immutable_content_hash"] == "sha256:deadbeef"
    assert cap["locator"] == "file:///src/x.py"
    # Not a paraphrased code blob.
    assert "def " not in str(cap)
    store.close()


def test_states_distinguishable_in_packet(tmp_path):
    store = _build_db(str(tmp_path / "mem.db"))
    # FTS5 MATCH is AND, so probe each kind with a term it uniquely contains.
    kinds = set()
    for q in ("build deterministic", "latency", "unknown latency", "x.py"):
        for p in retrieve(store, q):
            kinds.add(p.atom_kind)
    assert "FORM" in kinds and "HYPOTHESIS" in kinds and "NOUMENON" in kinds
    # STALE distinction: freshness map gives STALE a low value.
    assert freshness_for_state("STALE") < freshness_for_state("ACTIVE")
    # REFUTED fully flagged.
    packets = retrieve(store, "build deterministic")
    refuted = [p for p in packets if p.is_refuted]
    assert refuted and all(p.epistemic_state == "REFUTED" for p in refuted)
    store.close()


def test_retrieval_persisted(tmp_path):
    store = _build_db(str(tmp_path / "mem.db"))
    retrieve(store, "build deterministic")
    runs = store._conn.execute("SELECT COUNT(*) FROM retrieval_runs").fetchone()[0]
    hits = store._conn.execute("SELECT COUNT(*) FROM retrieval_hits").fetchone()[0]
    assert runs == 1
    assert hits >= 1
    store.close()


def test_scoring_formulas_match_spec(tmp_path):
    # epistemic_confidence = anchor*repro*appl*fresh*(1-contra)
    conf = compute_epistemic_confidence(1.0, 1.0, 1.0, 1.0, 0.0)
    assert conf == 1.0
    conf2 = compute_epistemic_confidence(0.5, 1.0, 1.0, 1.0, 0.25)
    assert abs(conf2 - 0.5 * 0.75) < 1e-9
    assert compute_epistemic_confidence(0.0, 1.0, 1.0, 1.0, 0.0) == 0.0
    # rank = semantic * confidence * task
    rank = compute_retrieval_rank(1.0, 0.5, 1.0)
    assert abs(rank - 0.5) < 1e-9
    store = QvchStore(str(tmp_path / "m.db"), migration=True)
    store.init_schema()
    store.close()


def test_applicability_typed_precondition_affects_rank(tmp_path):
    store = _build_db(str(tmp_path / "mem.db"))
    repo = Repository(store)
    repo.record_applicability_contract(
        contract_id="c1", atom_id="fact_1", revision_id="fact_1#r1",
        scope="linux", precondition=[{"type": "platform", "value": "linux"}],
        anti_condition=None, required_probes=None,
    )
    # On win32 the platform precondition fails -> applicability 0 -> confidence 0.
    packets = retrieve(store, "build deterministic", ctx={"os_platform": "win32"})
    fact1 = next(p for p in packets if p.atom_id == "fact_1")
    assert fact1.applicability == 0.0
    assert fact1.epistemic_confidence == 0.0
    store.close()
