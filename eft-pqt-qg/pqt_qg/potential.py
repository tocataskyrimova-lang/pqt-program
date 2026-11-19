"""Tree-level PQT-QG observed scalar potential and derivatives.

Variables are dimensionless backgrounds:
    H_bar = (0, phi)^T / sqrt(2), rho_bar = r, iota_bar = s

The v0.1 local memory approximation K_T(k) ~= kappa0 is included as a
local iota mass shift in the potential: +0.5 * LambdaT2_kappa0 * s^2.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

Params = Mapping[str, float]


def _effective_miota2(params: Params) -> float:
    return float(params["miota2"]) + float(params.get("LambdaT2_kappa0", 0.0))


def V0(phi: float | np.ndarray, r: float | np.ndarray, s: float | np.ndarray, params: Params):
    """Evaluate canonical tree-level V0 with local memory mass shift."""
    mu = params["muH_eff2"]
    lam = params["lambdaH"]
    mr = params["mrho2"]
    br = params["brho"]
    mi_eff = _effective_miota2(params)
    bi = params["biota"]
    ar = params["arho"]
    ai = params["aiota"]
    c = params["c"]
    return (
        -0.5 * mu * phi**2
        + 0.25 * lam * phi**4
        + 0.5 * mr * r**2
        + 0.25 * br * r**4
        + 0.5 * mi_eff * s**2
        + 0.25 * bi * s**4
        + 0.25 * ar * phi**2 * r**2
        + 0.25 * ai * phi**2 * s**2
        + 0.25 * c * r**2 * s**2
    )


def V0_vec(x: Sequence[float], params: Params) -> float:
    phi, r, s = x
    return float(V0(phi, r, s, params))


def grad_V0(x: Sequence[float], params: Params) -> np.ndarray:
    """Analytic gradient dV0/d(phi,r,s)."""
    phi, r, s = np.asarray(x, dtype=float)
    mu = params["muH_eff2"]
    lam = params["lambdaH"]
    mr = params["mrho2"]
    br = params["brho"]
    mi_eff = _effective_miota2(params)
    bi = params["biota"]
    ar = params["arho"]
    ai = params["aiota"]
    c = params["c"]
    return np.array(
        [
            -mu * phi + lam * phi**3 + 0.5 * ar * phi * r**2 + 0.5 * ai * phi * s**2,
            mr * r + br * r**3 + 0.5 * ar * phi**2 * r + 0.5 * c * r * s**2,
            mi_eff * s + bi * s**3 + 0.5 * ai * phi**2 * s + 0.5 * c * r**2 * s,
        ],
        dtype=float,
    )


def hessian_V0(x: Sequence[float], params: Params) -> np.ndarray:
    """Analytic Hessian with canonical a/2 diagonal portal normalization."""
    phi, r, s = np.asarray(x, dtype=float)
    mu = params["muH_eff2"]
    lam = params["lambdaH"]
    mr = params["mrho2"]
    br = params["brho"]
    mi_eff = _effective_miota2(params)
    bi = params["biota"]
    ar = params["arho"]
    ai = params["aiota"]
    c = params["c"]

    m_hh2 = -mu + 3.0 * lam * phi**2 + 0.5 * ar * r**2 + 0.5 * ai * s**2
    m_rr2 = mr + 3.0 * br * r**2 + 0.5 * ar * phi**2 + 0.5 * c * s**2
    m_ss2 = mi_eff + 3.0 * bi * s**2 + 0.5 * ai * phi**2 + 0.5 * c * r**2
    m_hr2 = ar * phi * r
    m_hs2 = ai * phi * s
    m_rs2 = c * r * s
    return np.array(
        [[m_hh2, m_hr2, m_hs2], [m_hr2, m_rr2, m_rs2], [m_hs2, m_rs2, m_ss2]],
        dtype=float,
    )


def hessian_eigenvalues(x: Sequence[float], params: Params) -> np.ndarray:
    return np.linalg.eigvalsh(hessian_V0(x, params))
