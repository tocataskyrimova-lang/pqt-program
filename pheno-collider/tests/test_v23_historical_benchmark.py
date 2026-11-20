"""Deterministic pytest validation suite for Historical Collider Benchmark v2.3.

Zero external dependencies (pure stdlib: csv, json, math, pathlib).
Execution runtime: < 0.1 second.

Validates:
1. All required historical v2.3 artifacts and gate status records exist and are non-empty.
2. The scan grid contains exactly 144 unique (window, mjj_cut, deta_cut) configurations.
3. Significance formula Z_3000 = S_3000 / sqrt(B_3000) is numerically consistent for all valid
   cells, and Z_3000 is empty for B_3000 == 0 cells (zero fabricated significance values).
4. Background starvation guardrail: confirms high starvation rate (>90% cells with B < 1)
   and verifies gate status tags are correctly set to ARCHIVED_BACKGROUND_STARVATION
   and BLOCKED_NEEDS_HIGH_STATS_REGEN.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import pytest

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent / "benchmarks"
HISTORICAL_V23_DIR = BENCHMARKS_DIR / "historical_v23"
GATE_STATUS_JSON = BENCHMARKS_DIR / "v23_gate_status.json"


def test_v23_required_artifacts_present():
    """Confirm all required historical v2.3 artifacts and gate status records exist and are non-empty."""
    required_files = [
        HISTORICAL_V23_DIR / "cut_stability_scan_v23.csv",
        HISTORICAL_V23_DIR / "cut_stability_scan_v23.json",
        HISTORICAL_V23_DIR / "plateau_metrics_v23.json",
        HISTORICAL_V23_DIR / "cut_stability_summary_v23.md",
        HISTORICAL_V23_DIR / "top_configs_v23.csv",
        HISTORICAL_V23_DIR / "README.md",
        GATE_STATUS_JSON,
    ]

    for fpath in required_files:
        assert fpath.is_file(), f"Required artifact missing: {fpath}"
        assert fpath.stat().st_size > 0, f"Artifact is empty (0 bytes): {fpath}"


def test_v23_grid_has_144_unique_configs():
    """Confirm CSV has exactly 144 rows matching 4 windows x 6 mjj x 6 deta with zero duplicates."""
    csv_path = HISTORICAL_V23_DIR / "cut_stability_scan_v23.csv"
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 144, f"Expected 144 grid rows, found {len(rows)}"

    expected_windows = {"w1", "w2", "w3", "w4"}
    expected_mjj = {"300", "400", "500", "600", "700", "800"}
    expected_deta = {"2.5", "3.0", "3.5", "4.0", "4.5", "5.0"}

    seen_configs = set()
    windows_found = set()
    mjj_found = set()
    deta_found = set()

    for r in rows:
        cfg = (r["window"], r["mjj_cut"], r["deta_cut"])
        assert cfg not in seen_configs, f"Duplicate grid point found: {cfg}"
        seen_configs.add(cfg)

        windows_found.add(r["window"])
        mjj_found.add(r["mjj_cut"])
        deta_found.add(r["deta_cut"])

    assert len(seen_configs) == 144, f"Expected 144 unique points, found {len(seen_configs)}"
    assert windows_found == expected_windows, f"Unexpected windows: {windows_found}"
    assert mjj_found == expected_mjj, f"Unexpected mjj cuts: {mjj_found}"
    assert deta_found == expected_deta, f"Unexpected deta cuts: {deta_found}"


def test_v23_significance_formula_consistency():
    """Assert Z3000 matches S3000 / sqrt(B3000) for B > 0, and is empty for B == 0."""
    csv_path = HISTORICAL_V23_DIR / "cut_stability_scan_v23.csv"
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    b_zero_count = 0
    valid_count = 0

    for r in rows:
        b3000 = float(r["B3000"])
        s3000 = float(r["S3000"])
        z3000_str = r["Z3000"].strip()

        if b3000 == 0.0:
            b_zero_count += 1
            # Must NOT fabricate a finite significance number when background is zero
            assert z3000_str == "", (
                f"Row {r['config_id']} has B3000=0 but non-empty Z3000: '{z3000_str}'"
            )
            assert r["status"] == "BG_ZERO"
        else:
            valid_count += 1
            assert z3000_str != "", f"Row {r['config_id']} has B3000>0 but empty Z3000"
            assert r["status"] == "OK"

            z3000 = float(z3000_str)
            expected_z = s3000 / math.sqrt(b3000)
            # The CSV values are printed to 4 decimal places; relative tolerance 1e-3 is robust
            assert math.isclose(z3000, expected_z, rel_tol=1e-3), (
                f"Row {r['config_id']}: Z3000={z3000} != S/sqrt(B)={expected_z}"
            )

    assert b_zero_count == 36, f"Expected exactly 36 B=0 cells, found {b_zero_count}"
    assert valid_count == 108, f"Expected exactly 108 valid cells, found {valid_count}"


def test_v23_background_starvation_guardrail():
    """Verify background starvation metrics and assert gate status classification tags."""
    # 1. Check plateau_metrics_v23.json
    metrics_path = HISTORICAL_V23_DIR / "plateau_metrics_v23.json"
    with open(metrics_path, encoding="utf-8") as f:
        metrics = json.load(f)

    assert metrics["classification"] == "BACKGROUND_STARVATION"
    assert metrics["background_starvation"] is True
    assert math.isclose(metrics["max_Z3000"], 598.362, rel_tol=1e-3)
    assert metrics["largest_component"] == 108

    # 2. Check starvation prevalence in CSV (> 90% cells with B < 1.0)
    csv_path = HISTORICAL_V23_DIR / "cut_stability_scan_v23.csv"
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    b_lt_1_count = sum(1 for r in rows if float(r["B3000"]) < 1.0)
    starvation_frac = b_lt_1_count / len(rows)
    assert starvation_frac > 0.90, f"Expected >90% starved cells, got {starvation_frac:.2%}"
    assert b_lt_1_count == 135

    # 3. Check v23_gate_status.json
    with open(GATE_STATUS_JSON, encoding="utf-8") as f:
        gate_status = json.load(f)

    assert gate_status["historical_10k_v23_status"] == "ARCHIVED_BACKGROUND_STARVATION"
    assert gate_status["statistically_valid_v23_status"] == "BLOCKED_NEEDS_HIGH_STATS_REGEN"
    assert gate_status["high_stats_requirements"]["table_interpolation_forbidden"] is True
