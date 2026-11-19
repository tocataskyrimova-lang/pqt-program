"""Local one-loop Coleman-Weinberg layer for PQT-QG benchmark v0.4.

This is a synthetic local CW correction only. It uses Re[V1] with abs(m^2)
in logarithms and records negative-mass indicators instead of treating the
imaginary part. It is not a full nonlocal K_T determinant and not RG improved.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, pi
from typing import Mapping, Sequence

import numpy as np

from .potential import V0, hessian_V0


@dataclass(frozen=True)
class OneLoopParams:
    mu_ren: float = 1.0
    g_D: float = 0.65
    g_Y: float = 0.36
    y_top: float = 1.0
    n_top: int = -12
    loop_scale: float = 1.0
    eps: float = 1e-14


def cw_term(m2: float, c_const: float, mu_ren: float = 1.0, eps: float = 1e-14) -> float:
    """Real Coleman-Weinberg term m^4[log(|m^2|/mu^2)-c]."""
    m2 = float(m2)
    if abs(m2) < eps:
        return 0.0
    return (m2 * m2) * (log(abs(m2) / (mu_ren * mu_ren)) - c_const)


def mass_spectrum(phi: float, r: float, s: float, params: Mapping[str, float], loop: OneLoopParams | None = None) -> dict:
    loop = loop or OneLoopParams()
    hess = hessian_V0([phi, r, s], params)
    scalar = np.linalg.eigvalsh(hess)
    mu = float(params["muH_eff2"])
    lam = float(params["lambdaH"])
    ar = float(params["arho"])
    ai = float(params["aiota"])
    mG2 = -mu + lam * phi**2 + 0.5 * ar * r**2 + 0.5 * ai * s**2
    MW2 = loop.g_D * loop.g_D * phi**2 / 4.0
    MZ2 = (loop.g_D * loop.g_D + loop.g_Y * loop.g_Y) * phi**2 / 4.0
    mGpm2 = mG2 + MW2
    mG02 = mG2 + MZ2
    mtop2 = loop.y_top * loop.y_top * phi**2 / 2.0
    goldstones = np.array([mG02, mGpm2, mGpm2], dtype=float)
    return {
        "scalar_m2": scalar,
        "mG2": float(mG2),
        "mG02": float(mG02),
        "mGpm2": float(mGpm2),
        "goldstone_m2": goldstones,
        "MW2": float(MW2),
        "MZ2": float(MZ2),
        "mtop2": float(mtop2),
        "scalar_negative_count": int(np.sum(scalar < -loop.eps)),
        "goldstone_negative_count": int(np.sum(goldstones < -loop.eps)),
        "min_scalar_m2": float(np.min(scalar)),
        "min_goldstone_m2": float(np.min(goldstones)),
    }


def V1(phi: float, r: float, s: float, params: Mapping[str, float], loop: OneLoopParams | None = None) -> float:
    loop = loop or OneLoopParams()
    spec = mass_spectrum(phi, r, s, params, loop)
    total = 0.0
    for m2 in spec["scalar_m2"]:
        total += cw_term(float(m2), 1.5, loop.mu_ren, loop.eps)
    total += cw_term(spec["mG02"], 1.5, loop.mu_ren, loop.eps)
    total += 2.0 * cw_term(spec["mGpm2"], 1.5, loop.mu_ren, loop.eps)
    total += 6.0 * cw_term(spec["MW2"], 5.0 / 6.0, loop.mu_ren, loop.eps)
    total += 3.0 * cw_term(spec["MZ2"], 5.0 / 6.0, loop.mu_ren, loop.eps)
    total += loop.n_top * cw_term(spec["mtop2"], 1.5, loop.mu_ren, loop.eps)
    return total / (64.0 * pi * pi)


def Veff(x: Sequence[float], params: Mapping[str, float], loop: OneLoopParams | None = None) -> float:
    loop = loop or OneLoopParams()
    phi, r, s = np.asarray(x, dtype=float)
    return float(V0(phi, r, s, params) + loop.loop_scale * V1(phi, r, s, params, loop))


def cw_flags(phi: float, r: float, s: float, params: Mapping[str, float], loop: OneLoopParams | None = None) -> dict:
    spec = mass_spectrum(phi, r, s, params, loop)
    return {
        "scalar_negative_count": spec["scalar_negative_count"],
        "goldstone_negative_count": spec["goldstone_negative_count"],
        "min_scalar_m2": spec["min_scalar_m2"],
        "min_goldstone_m2": spec["min_goldstone_m2"],
        "cw_has_negative_scalar_modes": spec["scalar_negative_count"] > 0,
        "cw_has_negative_goldstone_modes": spec["goldstone_negative_count"] > 0,
        "cw_real_stable_candidate": spec["scalar_negative_count"] == 0 and spec["goldstone_negative_count"] == 0,
    }
