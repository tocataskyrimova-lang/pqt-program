"""Phase, stability, and quartic sanity classification."""

from __future__ import annotations

from math import sqrt
from typing import Mapping

import numpy as np

EPS_PHI = 1e-3
EPS_BRANCH = 1e-2
EPS_EIGEN = 1e-6


def classify_phase(phi: float, r: float, s: float, eps_phi: float = EPS_PHI, eps_branch: float = EPS_BRANCH) -> str:
    has_phi = abs(phi) > eps_phi
    has_r = abs(r) > eps_branch
    has_s = abs(s) > eps_branch
    if not has_phi and not has_r and not has_s:
        return "Symmetric"
    if has_phi and not has_r and not has_s:
        return "Prema"
    if has_phi and has_r and not has_s:
        return "Gurutva"
    if has_phi and not has_r and has_s:
        return "Tamas"
    if has_phi and has_r and has_s:
        return "Mixed"
    if not has_phi and has_r and not has_s:
        return "Rho_only"
    if not has_phi and not has_r and has_s:
        return "Iota_only"
    return "Other"


def classify_stability(eigenvalues, eps_eigen: float = EPS_EIGEN) -> str:
    vals = np.asarray(eigenvalues, dtype=float)
    if np.any(vals < -eps_eigen):
        return "unstable_saddle_or_max"
    if np.any(np.abs(vals) <= eps_eigen):
        return "flat_or_marginal"
    return "stable_minimum"


def copositivity_pairwise(params: Mapping[str, float]) -> dict:
    lam = float(params["lambdaH"])
    br = float(params["brho"])
    bi = float(params["biota"])
    ar = float(params["arho"])
    ai = float(params["aiota"])
    c = float(params["c"])
    checks = {
        "lambdaH_positive": lam > 0,
        "brho_positive": br > 0,
        "biota_positive": bi > 0,
        "arho_pairwise": ar + 2.0 * sqrt(max(lam * br, 0.0)) > 0,
        "aiota_pairwise": ai + 2.0 * sqrt(max(lam * bi, 0.0)) > 0,
        "c_pairwise": c + 2.0 * sqrt(max(br * bi, 0.0)) > 0,
    }
    return {
        "status": "pass" if all(checks.values()) else "warn",
        "checks": checks,
        "values": {
            "arho_plus_2sqrt_lambdaH_brho": ar + 2.0 * sqrt(max(lam * br, 0.0)),
            "aiota_plus_2sqrt_lambdaH_biota": ai + 2.0 * sqrt(max(lam * bi, 0.0)),
            "c_plus_2sqrt_brho_biota": c + 2.0 * sqrt(max(br * bi, 0.0)),
        },
        "note": "Pairwise quartic boundedness sanity check only; not a full three-field copositivity proof.",
    }
