"""P0 — End-to-end v4 sovereignty cycle (brief 16).

Drives ``scripts/e2e_v4_demo.py`` as a pytest case so the full
N -> U branches -> F -> use -> degrade -> new N cycle is part of the
qualification matrix. The script asserts every one of the 23 steps (14 brief + 4 R1 gates +
5 R2 gates); this test fails if any step (or the script's own assertions) fails.

Run standalone:  python scripts/e2e_v4_demo.py
"""

from __future__ import annotations

import importlib.util
import os

import pytest

_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "scripts", "e2e_v4_demo.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("e2e_v4_demo", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e2e_full_v4_cycle():
    mod = _load_module()
    # main() returns 0 on success and raises AssertionError on any failed step.
    assert mod.main() == 0


__all__ = ["test_e2e_full_v4_cycle"]
