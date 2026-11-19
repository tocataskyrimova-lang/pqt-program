from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .constants import (
    BANNER,
    C_ALIAS_REPORT_NOTE,
    CLAIM_BOUNDARY,
    DATA_AVAILABLE,
    LABEL_UNAVAILABLE,
    MACHINERY_FAIL,
    MACHINERY_PASS,
    REPORT_BASE,
    SYNTHETIC_DISCLAIMER,
    SYNTHETIC_PREFIX,
    TERMINAL_HERMETIC,
    TERMINAL_INCONCLUSIVE,
    TERMINAL_LABEL_UNAVAILABLE,
    TERMINAL_NO_DATA,
    TERMINAL_SELF_CONFIRM,
    TERMINAL_SURROGATE_FAILED,
    TERMINAL_W0_BREACH,
)
from .ext1_encoder import PQTTextEncoder, build_encoder_contract
from .ext1_label_extraction import (
    audit_label_capability,
    canonical_label_hash,
    extract_label,
    schema_requirements_report,
)
from .ext1_surrogates import run_encoder_laundering_check, run_surrogate_machinery_checks
from .ext1_witness_sidecar import WitnessWriter, run_witness
from .firewall import feedback_check, static_firewall_scan
from .readonly_sources import inspect_and_load

DEFAULT_OUTPUT = Path(r"C:\AGI\PQT\outputs\ext1_dry")
DEFAULT_DB = Path(r"C:\AGI\QVCH_v3\memory.db")
DEFAULT_PQT_MATH = Path(r"C:\AGI\PQT\MATH")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _report(payload: dict[str, Any]) -> dict[str, Any]:
    return {**REPORT_BASE, **payload}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(_report(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _label_machinery_check() -> dict[str, Any]:
    as_of = datetime(2026, 6, 19, tzinfo=timezone.utc)
    base = {"created_at": "2026-05-01T00:00:00+00:00"}
    fixtures = [
        {**base, "episode_id": "repair", "validated_repair_atom_link": True},
        {**base, "episode_id": "retired", "promoted_at": "2026-05-02T00:00:00+00:00", "retired_at": "2026-05-03T00:00:00+00:00"},
        {**base, "episode_id": "duplicate", "duplicate_or_superseded_at": "2026-05-04T00:00:00+00:00"},
        {**base, "episode_id": "unused", "usage_count": 0, "evidence_quality": 0.1},
        {**base, "episode_id": "clean", "usage_count": 2, "evidence_quality": 0.9, "no_bad_lifecycle_events": True},
        {"episode_id": "immature", "created_at": "2026-06-18T00:00:00+00:00"},
        {**base, "episode_id": "ambiguous"},
    ]
    first = [extract_label(row, as_of=as_of) for row in fixtures]
    second = [extract_label(row, as_of=as_of) for row in fixtures]
    first_hash = canonical_label_hash(first)
    second_hash = canonical_label_hash(second)
    values = [row.value for row in first]
    expected = [1, 1, 1, 1, 0, "EXCLUDED", "EXCLUDED"]
    passed = values == expected and first_hash == second_hash
    return {
        "synthetic_banner": f"{SYNTHETIC_PREFIX}LABEL_EXTRACTION",
        "disclaimer": SYNTHETIC_DISCLAIMER,
        "values": values,
        "expected": expected,
        "first_hash": first_hash,
        "second_hash": second_hash,
        "reproducible": first_hash == second_hash,
        "passed": passed,
    }


def _resolve_terminal(
    *,
    static_ok: bool,
    runtime_ok: bool,
    feedback_ok: bool,
    machinery_ok: bool,
    data_status: str,
    label_status: str,
) -> str:
    if not static_ok or not runtime_ok:
        return TERMINAL_W0_BREACH
    if not feedback_ok:
        return TERMINAL_SELF_CONFIRM
    if not machinery_ok:
        return TERMINAL_SURROGATE_FAILED
    if data_status != DATA_AVAILABLE:
        return TERMINAL_NO_DATA
    if label_status == LABEL_UNAVAILABLE:
        return TERMINAL_LABEL_UNAVAILABLE
    if label_status and machinery_ok:
        return TERMINAL_HERMETIC
    return TERMINAL_INCONCLUSIVE


def run_ext1_dry(
    *,
    output_dir: Path = DEFAULT_OUTPUT,
    db_path: Path = DEFAULT_DB,
    source_mode: str = "frozen",
    pqt_math_root: Path = DEFAULT_PQT_MATH,
) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    package_dir = Path(__file__).resolve().parent
    qvch_root = Path(__file__).resolve().parents[3]
    schema_path = qvch_root / "qvch_v3" / "storage" / "schema.sql"

    contract = build_encoder_contract(pqt_math_root)
    _write_json(output_dir / "ext1_encoder_contract.json", contract)

    inspection, episodes, source_schema_sql = inspect_and_load(
        db_path, output_dir=output_dir, source_mode=source_mode
    )
    schema_sql = source_schema_sql or schema_path.read_text(encoding="utf-8")
    label_capability = audit_label_capability(schema_sql)
    schema_requirements = schema_requirements_report(label_capability)

    scan_paths = sorted(package_dir.glob("*.py"))
    static_result = static_firewall_scan(scan_paths)
    witness_path = output_dir / "pqt_witness.jsonl"
    feedback = feedback_check([db_path], witness_path)

    encoder = PQTTextEncoder(pqt_math_root=pqt_math_root, contract=contract)
    witness_result = run_witness(episodes, encoder, WitnessWriter(output_dir))
    runtime_ok = bool(witness_result["w0_runtime_passed"])

    surrogate = run_surrogate_machinery_checks()
    ablation = run_encoder_laundering_check()
    label_check = _label_machinery_check()
    machinery_ok = bool(surrogate["passed"] and ablation["passed"] and label_check["passed"])
    machinery_status = MACHINERY_PASS if machinery_ok else MACHINERY_FAIL
    terminal = _resolve_terminal(
        static_ok=bool(static_result["passed"]),
        runtime_ok=runtime_ok,
        feedback_ok=bool(feedback["passed"]),
        machinery_ok=machinery_ok,
        data_status=inspection.data_status,
        label_status=str(label_capability["label_capability_status"]),
    )

    input_inventory = {
        "inspection": asdict(inspection),
        "historical_episode_count": len(episodes),
        "synthetic_records_in_witness": 0,
        "witness_path": str(witness_path),
    }
    core_manifest = {
        "pqt_math_root": str(pqt_math_root.resolve()),
        "core_files_sha256": contract["core_files_sha256"],
        "defaults_sha256": contract["defaults_sha256"],
        "projection_sha256": contract["projection_sha256"],
        "C_alias_note": C_ALIAS_REPORT_NOTE,
    }
    run_manifest = {
        "generated_at": _now(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "source_mode": source_mode,
        "db_path": str(db_path.resolve()),
        "output_dir": str(output_dir),
        "historical_only_witness": True,
        "training_performed": False,
        "qvch_mutation_performed": False,
        "pilot_performed": False,
    }
    hermeticity = {
        "static_firewall": static_result,
        "runtime_firewall": witness_result,
        "feedback_check": feedback,
        "raw_text_persisted": False,
        "synthetic_in_witness": False,
        "w0_passed": bool(static_result["passed"] and runtime_ok and feedback["passed"]),
    }
    final = {
        "terminal_status": terminal,
        "data_status": inspection.data_status,
        "label_capability_status": label_capability["label_capability_status"],
        "machinery_status": machinery_status,
    }

    _write_json(output_dir / "ext1_input_inventory.json", input_inventory)
    _write_json(output_dir / "ext1_core_manifest.json", core_manifest)
    _write_json(output_dir / "ext1_run_manifest.json", run_manifest)
    _write_json(output_dir / "ext1_label_capability_report.json", label_capability)
    _write_json(output_dir / "ext1_qvch_schema_requirements.json", schema_requirements)
    _write_json(output_dir / "ext1_label_extraction_report.json", label_check)
    _write_json(output_dir / "ext1_dry_hermeticity_report.json", hermeticity)
    _write_json(output_dir / "ext1_surrogate_selfcheck.json", surrogate)
    _write_json(output_dir / "ext1_encoder_ablation.json", ablation)
    _write_json(output_dir / "ext1_final_classification.json", final)

    report = f"""# EXT1-DRY Report

{BANNER}

{CLAIM_BOUNDARY}

## Split status

```json
{json.dumps(final, ensure_ascii=False, indent=2)}
```

## Scope

- Historical witness records: {len(episodes)}
- Synthetic records in `pqt_witness.jsonl`: 0
- QVCH/MANAS mutation: none
- Training: none
- PILOT/HOLDOUT: not run

## Label capability

Strong `Y_bad_write` is unavailable unless QVCH supplies timestamped promoted-to-retired lifecycle transitions and an explicit repair-to-atom foreign-key link. Missing lineage is not a negative label. PILOT remains blocked.

## Synthetic machinery

All synthetic AUC values are prefixed `SYNTHETIC_MACHINERY_CHECK_` and carry the disclaimer: **{SYNTHETIC_DISCLAIMER}**. They validate detector mechanics only and are not PQT evidence.

## Alias safety

{C_ALIAS_REPORT_NOTE}
"""
    (output_dir / "EXT1_DRY_REPORT.md").write_text(report, encoding="utf-8")
    return _report(final)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EXT1-DRY hermeticity checks")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--source-mode", choices=("frozen", "live"), default="frozen")
    parser.add_argument("--pqt-math-root", type=Path, default=DEFAULT_PQT_MATH)
    args = parser.parse_args()
    result = run_ext1_dry(output_dir=args.output_dir, db_path=args.db, source_mode=args.source_mode, pqt_math_root=args.pqt_math_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
