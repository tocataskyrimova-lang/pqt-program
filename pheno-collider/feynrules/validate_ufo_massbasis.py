from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


def read_file_safe(filepath: Path) -> str:
    try:
        return filepath.read_text(encoding="utf-8")
    except Exception:
        return ""


def check_particle_S(ufo_dir: Path) -> bool:
    """Check particles.py contains S (pdg 9000006)"""
    particles_file = ufo_dir / "particles.py"
    content = read_file_safe(particles_file)
    if not content:
        return False
    # Look for PDG 9000006 or name 'S'
    return bool(re.search(r"9000006", content) or re.search(r"name\s*=\s*['\"]S['\"]", content))


def check_parameter_sint(ufo_dir: Path) -> bool:
    """Check parameters.py contains sint or theta"""
    params_file = ufo_dir / "parameters.py"
    content = read_file_safe(params_file)
    if not content:
        return False
    return bool(re.search(r"sint", content) or re.search(r"theta", content))


def check_vertex(vertices_content: str, particle_names: List[str]) -> bool:
    """Check if vertices.py contains a vertex with all specified particles"""
    # Vertices in UFO are lists of particle indices or names. We'll search for all particle names in a line
    # Simple approach: check if all particle names appear in the same line (crude but effective)
    lines = vertices_content.split("\n")
    for line in lines:
        if all(p in line for p in particle_names):
            return True
    return False


def check_vertices(ufo_dir: Path) -> Dict[str, bool]:
    """Check for required vertices in vertices.py"""
    vertices_file = ufo_dir / "vertices.py"
    content = read_file_safe(vertices_file)
    if not content:
        return {k: False for k in ["SZZ", "SWW", "Stt", "Sbb", "Stautau"]}
    # Particle name mappings (as they appear in UFO vertices)
    # Z is usually 'Z', W+ is 'W+', W- is 'W-', t is 't', t~ is 't~', b is 'b', b~ is 'b~', tau- is 'ta-', tau+ is 'ta+'
    results = {}
    # S Z Z
    results["SZZ"] = check_vertex(content, ["S", "Z", "Z"])
    # S W+ W-
    results["SWW"] = check_vertex(content, ["S", "W+", "W-"])
    # S t t~
    results["Stt"] = check_vertex(content, ["S", "t", "t~"])
    # S b b~
    results["Sbb"] = check_vertex(content, ["S", "b", "b~"])
    # S tau+ tau- (tau- is 'ta-', tau+ is 'ta+')
    results["Stautau"] = check_vertex(content, ["S", "ta-", "ta+"]) or check_vertex(content, ["S", "tau-", "tau+"])
    return results


def check_couplings(ufo_dir: Path) -> bool:
    """Check couplings.py contains sint or equivalent"""
    couplings_file = ufo_dir / "couplings.py"
    content = read_file_safe(couplings_file)
    if not content:
        return False
    return bool(re.search(r"sint", content) or re.search(r"sinth", content) or re.search(r"theta", content))


def check_no_iota(ufo_dir: Path) -> bool:
    """Check no old gauge-basis iota vertices remain"""
    vertices_file = ufo_dir / "vertices.py"
    content = read_file_safe(vertices_file)
    if not content:
        return True
    return "iota" not in content.lower()


def main():
    parser = argparse.ArgumentParser(description="Validate PQT Mass Basis UFO")
    parser.add_argument("--ufo", type=Path, required=True, help="UFO directory path")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON path")
    args = parser.parse_args()

    if not args.ufo.is_dir():
        print(f"Error: UFO directory {args.ufo} does not exist")
        return

    results = {
        "has_S_particle": check_particle_S(args.ufo),
        "has_sint_parameter": check_parameter_sint(args.ufo),
        "warnings": [],
    }

    # Check vertices
    vertex_checks = check_vertices(args.ufo)
    results.update(vertex_checks)

    # Check couplings
    results["has_sint_coupling"] = check_couplings(args.ufo)

    # Check no iota
    if not check_no_iota(args.ufo):
        results["warnings"].append("Old gauge-basis 'iota' found in vertices.py")

    # Overall pass
    required_checks = [
        results["has_S_particle"],
        results["has_sint_parameter"],
        results["SZZ"],
        results["SWW"],
        results["Stt"],
        results["Sbb"],
        results["Stautau"],
        results["has_sint_coupling"],
    ]
    results["passed"] = all(required_checks)

    # Write output
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("UFO Validation Results:")
    for k, v in results.items():
        if k != "warnings":
            print(f"  {k}: {v}")
    if results["warnings"]:
        print("Warnings:")
        for w in results["warnings"]:
            print(f"  - {w}")
    print(f"\nOverall passed: {results['passed']}")


if __name__ == "__main__":
    main()
