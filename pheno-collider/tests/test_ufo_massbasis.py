"""Deterministic pytest validation suite for PQT_MemorySector_massbasis UFO package.

Zero MadGraph/Wolfram dependency: pure Python AST, compilation, and structure validation.
Validates:
1. Core UFO files exist, compile cleanly with py_compile, and import without syntax errors.
2. Model is a COMBINED Standard Model + PQT extension (not a broken PQT-only toy model).
3. Both PQT mixing parameters (MS, MH2, sint, cost) and SM electroweak parameters (MZ, MW) are defined.
4. Live VBF scalar vertices (SZZ, SWW, H2ZZ, H2WW) exist and all couplings have zero dangling references.
5. Restrict card (restrict_default.dat) defines automatic tree-level decay widths for 9000006 (S) and 9000007 (H2).
"""

from __future__ import annotations

import importlib
from pathlib import Path
import py_compile
import sys
import pytest

UFO_DIR = Path(__file__).resolve().parent.parent / "ufo" / "PQT_MemorySector_massbasis"


@pytest.fixture(scope="module")
def ufo_modules():
    """Ensure UFO_DIR is on sys.path and import core UFO modules."""
    ufo_str = str(UFO_DIR)
    if ufo_str not in sys.path:
        sys.path.insert(0, ufo_str)

    # Force clean import of UFO modules
    import object_library
    import particles
    import parameters
    import couplings
    import lorentz
    import vertices

    return {
        "object_library": object_library,
        "particles": particles,
        "parameters": parameters,
        "couplings": couplings,
        "lorentz": lorentz,
        "vertices": vertices,
    }


def test_ufo_required_files_and_python_import():
    """Confirm core UFO files exist and compile cleanly with py_compile."""
    required_files = [
        "__init__.py",
        "particles.py",
        "parameters.py",
        "couplings.py",
        "lorentz.py",
        "vertices.py",
        "object_library.py",
        "restrict_default.dat",
    ]

    assert UFO_DIR.is_dir(), f"UFO directory does not exist at {UFO_DIR}"

    for filename in required_files:
        filepath = UFO_DIR / filename
        assert filepath.is_file(), f"Required UFO file missing: {filename}"
        if filename.endswith(".py"):
            # Ensure compilation succeeds without syntax errors under current Python
            py_compile.compile(str(filepath), doraise=True)


def test_combined_sm_plus_pqt_particles(ufo_modules):
    """Guard explicitly against legacy broken toy UFOs.

    Assert that particles.py defines BOTH PQT scalars (S with PDG 9000006,
    H2 with PDG 9000007) AND core SM particles (Z, W+, W-, g, quarks, leptons).
    """
    particles_mod = ufo_modules["particles"]
    all_particles = particles_mod.all_particles
    assert len(all_particles) >= 40, f"Expected full SM+PQT particle spectrum, got {len(all_particles)}"

    pdg_by_name = {p.name: p.pdg_code for p in all_particles}
    name_by_pdg = {p.pdg_code: p.name for p in all_particles}

    # PQT Scalar assertions
    assert 9000006 in name_by_pdg, "Missing light PQT scalar PDG 9000006"
    assert name_by_pdg[9000006] == "S", f"PDG 9000006 expected name 'S', got {name_by_pdg[9000006]}"

    assert 9000007 in name_by_pdg, "Missing heavy PQT scalar PDG 9000007"
    assert name_by_pdg[9000007] == "H2", f"PDG 9000007 expected name 'H2', got {name_by_pdg[9000007]}"

    # Core SM particle assertions
    required_sm = {
        "Z": 23,
        "W+": 24,
        "W-": -24,
        "g": 21,
        "a": 22,  # photon
        "u": 2,
        "d": 1,
        "c": 4,
        "s": 3,
        "t": 6,
        "b": 5,
        "e-": 11,
        "e+": -11,
        "mu-": 13,
        "mu+": -13,
        "ta-": 15,
        "ta+": -15,
    }

    for sm_symbol, expected_pdg in required_sm.items():
        assert sm_symbol in pdg_by_name, f"Missing Standard Model particle: {sm_symbol}"
        assert pdg_by_name[sm_symbol] == expected_pdg, (
            f"Particle {sm_symbol} has PDG {pdg_by_name[sm_symbol]}, expected {expected_pdg}"
        )


def test_pqt_and_sm_parameters(ufo_modules):
    """Assert parameters.py defines PQT parameters alongside SM electroweak parameters."""
    parameters_mod = ufo_modules["parameters"]
    all_params = parameters_mod.all_parameters
    param_dict = {p.name: p for p in all_params}

    # Required PQT parameters
    for pqt_param in ["MS", "MH2", "sint", "cost"]:
        assert pqt_param in param_dict, f"Missing required PQT parameter: {pqt_param}"

    # PQT parameter types
    assert param_dict["MS"].nature == "external"
    assert param_dict["MH2"].nature == "external"
    assert param_dict["sint"].nature == "external"
    assert param_dict["cost"].nature == "internal"

    # Required SM parameters (electroweak inputs & derived quantities)
    for sm_param in ["MZ", "MW", "aEWM1", "Gf", "aS", "vev"]:
        assert sm_param in param_dict, f"Missing standard model electroweak parameter: {sm_param}"


def test_vbf_vertices_and_coupling_integrity(ufo_modules):
    """Assert live SZZ/SWW and H2ZZ/H2WW vertices exist and all couplings have zero dangling references."""
    vertices_mod = ufo_modules["vertices"]
    couplings_mod = ufo_modules["couplings"]
    lorentz_mod = ufo_modules["lorentz"]
    particles_mod = ufo_modules["particles"]

    all_couplings_set = {c.name for c in couplings_mod.all_couplings}
    all_lorentz_set = {l.name for l in lorentz_mod.all_lorentz}
    all_particles_set = {p.name for p in particles_mod.all_particles}

    assert len(vertices_mod.all_vertices) == 157, f"Expected 157 vertices, got {len(vertices_mod.all_vertices)}"

    # 1. Zero dangling coupling references across ALL vertices
    dangling_couplings = []
    for v in vertices_mod.all_vertices:
        for coupling_key, c in v.couplings.items():
            if c.name not in all_couplings_set:
                dangling_couplings.append((v.name, c.name))
        for l in v.lorentz:
            assert l.name in all_lorentz_set, f"Vertex {v.name} references undefined lorentz structure {l.name}"
        for p in v.particles:
            assert p.name in all_particles_set, f"Vertex {v.name} references undefined particle {p.name}"

    assert len(dangling_couplings) == 0, f"Found dangling coupling references: {dangling_couplings}"

    # 2. Assert live VBF vertices for S and H2
    pqt_vertices = []
    for v in vertices_mod.all_vertices:
        p_names = [p.name for p in v.particles]
        if "S" in p_names or "H2" in p_names:
            pqt_vertices.append((v.name, p_names, [c.name for c in v.couplings.values()]))

    # Must have S-Z-Z, S-W-W, H2-Z-Z, H2-W-W
    assert len(pqt_vertices) == 4, f"Expected exactly 4 PQT scalar vertices, found {len(pqt_vertices)}"

    vertex_sigs = {tuple(sorted(pv[1])): pv[2] for pv in pqt_vertices}
    assert ("S", "Z", "Z") in vertex_sigs, "Missing S-Z-Z vertex"
    assert ("S", "W+", "W-") in vertex_sigs, "Missing S-W-W vertex"
    assert ("H2", "Z", "Z") in vertex_sigs, "Missing H2-Z-Z vertex"
    assert ("H2", "W+", "W-") in vertex_sigs, "Missing H2-W-W vertex"

    # Verify couplings have expected PQT names
    assert "GC_PQT_1" in vertex_sigs[("S", "Z", "Z")]
    assert "GC_PQT_2" in vertex_sigs[("S", "W+", "W-")]
    assert "GC_PQT_3" in vertex_sigs[("H2", "Z", "Z")]
    assert "GC_PQT_4" in vertex_sigs[("H2", "W+", "W-")]


def test_restrict_card_and_auto_width():
    """Assert restrict_default.dat is present and check DECAY 9000006/9000007 entries."""
    restrict_path = UFO_DIR / "restrict_default.dat"
    assert restrict_path.is_file(), f"restrict_default.dat not found at {restrict_path}"

    content = restrict_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]

    # Locate DECAY entries for S (9000006) and H2 (9000007)
    s_decay = [l for l in lines if l.startswith("DECAY") and "9000006" in l]
    h2_decay = [l for l in lines if l.startswith("DECAY") and "9000007" in l]

    assert len(s_decay) == 1, f"Expected exactly 1 DECAY entry for 9000006, found {s_decay}"
    assert len(h2_decay) == 1, f"Expected exactly 1 DECAY entry for 9000007, found {h2_decay}"

    # Verify both specify 'Auto' width calculation for MadGraph5
    assert "Auto" in s_decay[0], f"DECAY 9000006 is not set to Auto: {s_decay[0]}"
    assert "Auto" in h2_decay[0], f"DECAY 9000007 is not set to Auto: {h2_decay[0]}"
