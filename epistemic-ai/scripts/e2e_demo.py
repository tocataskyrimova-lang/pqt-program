from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qvch_v3.contracts.models import EvidenceRef, RawExperience, new_id
from qvch_v3.core.normalizer import normalize_experience
from qvch_v3.core.planner import build_write_plan
from qvch_v3.core.structurer import structure_event
from qvch_v3.manas.review import review_draft
from qvch_v3.manas.validation import validate_candidate
from qvch_v3.retrieval.probe import run_memory_probe
from qvch_v3.retrieval.search import retrieve
from qvch_v3.safety.scanner import scan_event
from qvch_v3.storage.db import QVCHDatabase
from qvch_v3.storage.gateway import MemoryWriteGateway


def run_demo(db_path: str | Path | None = None) -> dict:
    if db_path is None:
        tmp = tempfile.TemporaryDirectory(prefix="qvch_v3_demo_")
        db_path = Path(tmp.name) / "memory.db"
    else:
        tmp = None
        db_path = Path(db_path)

    db = QVCHDatabase(db_path)
    db.init_schema()
    try:
        raw = RawExperience("Execution logs are stored in logs/runtime.")
        event = normalize_experience(raw)
        safety = scan_event(event)
        draft = structure_event(event)
        evidence = [EvidenceRef(new_id("ev"), "demo_tool_output", "demo", "logs/runtime confirmed by demo")]
        manas = review_draft(draft, has_evidence=True)
        validation = validate_candidate(evidence_refs=evidence)
        plan = build_write_plan(event=event, draft=draft, manas_review=manas, safety_review=safety, validation=validation)
        receipt = MemoryWriteGateway(db).commit(plan)
        retrieval = retrieve(db, "logs/runtime")
        probe = run_memory_probe(db, query="logs/runtime", expected="logs/runtime", expected_status="F_candidate")
        return {
            "db_path": str(db_path),
            "receipt": receipt.__dict__,
            "retrieval_status": retrieval.status,
            "retrieval_candidates": retrieval.answer_candidates,
            "probe": probe.__dict__,
        }
    finally:
        db.close()
        if tmp is not None:
            tmp.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description="QVCH_v3 end-to-end demo: raw text -> gateway commit -> retrieval -> probe")
    parser.add_argument("--db", default=None, help="Optional SQLite DB path. Defaults to a temporary DB.")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.db), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
