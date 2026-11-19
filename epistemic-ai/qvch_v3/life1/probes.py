from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

FORBIDDEN_EXT1_LIFE1_SYMBOLS = {
    "Life1Recorder",
    "record_lifecycle_event",
    "link_repair_to_atom",
    "link_repair_to_crystal",
    "memory_lifecycle_events",
    "repair_atom_links",
    "repair_crystal_links",
}
FORBIDDEN_PROVENANCE_MODULE_MARKERS = {
    "qvch_v3.manas.ext1",
    "ext1_encoder",
    "ext1_witness_sidecar",
    "ext1_surrogates",
    "pqt",
    "synthetic",
    "replay_future",
}


def scan_ext1_for_life1_insert_routes(root: Path) -> dict[str, Any]:
    manas_dir = root / "qvch_v3" / "manas"
    findings: list[dict[str, Any]] = []
    for path in sorted(manas_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("qvch_v3.life1"):
                    findings.append({"file": str(path), "kind": "forbidden_import", "module": module})
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("qvch_v3.life1"):
                        findings.append({"file": str(path), "kind": "forbidden_import", "module": alias.name})
            elif isinstance(node, ast.Name) and node.id in FORBIDDEN_EXT1_LIFE1_SYMBOLS:
                findings.append({"file": str(path), "kind": "forbidden_symbol", "symbol": node.id})
            elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_EXT1_LIFE1_SYMBOLS:
                findings.append({"file": str(path), "kind": "forbidden_call", "symbol": node.attr})
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "getattr":
                    if len(node.args) >= 2:
                        arg2 = node.args[1]
                        val = None
                        if isinstance(arg2, ast.Constant):
                            val = arg2.value
                        if val in FORBIDDEN_EXT1_LIFE1_SYMBOLS:
                            findings.append({"file": str(path), "kind": "forbidden_getattr", "symbol": val})
    return {"probe": "P2_EXT1_NO_LIFE1_INSERT_ROUTE", "passed": not findings, "findings": findings}


def structural_provenance_scan(root: Path) -> dict[str, Any]:
    """Prove label-chain provenance cannot import witness/PQT inputs.

    This is a static construction check, not a sample check. It scans the LIFE1
    label/provenance modules and rejects imports or symbol references to EXT1,
    witness, encoder, synthetic, replay-future, or PQT paths.
    """
    files = [root / "qvch_v3" / "life1" / "labels.py", root / "qvch_v3" / "life1" / "recorder.py"]
    findings: list[dict[str, Any]] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").lower()
                if any(marker in module for marker in FORBIDDEN_PROVENANCE_MODULE_MARKERS):
                    findings.append({"file": str(path), "kind": "forbidden_import", "module": module})
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.lower()
                    if any(marker in name for marker in FORBIDDEN_PROVENANCE_MODULE_MARKERS):
                        findings.append({"file": str(path), "kind": "forbidden_import", "module": name})
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value.lower()
                if any(marker in value for marker in {"ext1_encoder", "ext1_witness_sidecar", "pqt_input"}):
                    findings.append({"file": str(path), "kind": "forbidden_literal", "value": node.value})
    return {
        "probe": "P3_STRUCTURAL_PROVENANCE_PROOF",
        "status": "P3_STRUCTURAL_PASS" if not findings else "P3_STRUCTURAL_FAIL",
        "passed": not findings,
        "sample_only": False,
        "findings": findings,
    }
