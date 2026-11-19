"""Nonlocal Euclidean memory kernels for PQT-QG benchmark v0.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
from scipy.special import exp1


@dataclass(frozen=True)
class NonlocalKernelParams:
    sigma0: float = 0.05
    Omega2: float = 1.0
    mu02: float = 0.0025
    M2_single_pole: float = 1.0
    Z_iota: float = 1.0
    Z_rho: float = 1.0
    kmax: float = 5.0
    num_k: int = 96
    eps_det: float = 1e-18
    nonlocal_scale: float = 1.0


def sigma_local(q, sigma0: float):
    return np.zeros_like(np.asarray(q, dtype=float)) + float(sigma0)


def sigma_single_pole(q, sigma0: float, M2: float):
    q = np.asarray(q, dtype=float)
    return float(sigma0) * float(M2) / (q + float(M2))


def sigma_exp_gap(q, sigma0: float, Omega2: float, mu02: float):
    q = np.asarray(q, dtype=float)
    x = (q + float(mu02)) / float(Omega2)
    x0 = float(mu02) / float(Omega2)
    # exp(x)*E1(x), normalized to F(0)=1.
    shape = np.exp(x) * exp1(x)
    norm = np.exp(x0) * exp1(x0)
    return float(sigma0) * shape / norm


def sigma_E(q, kernel_name: str, kp: NonlocalKernelParams):
    if kernel_name in {"local", "local_constant"}:
        return sigma_local(q, kp.sigma0)
    if kernel_name in {"single", "single_pole"}:
        return sigma_single_pole(q, kp.sigma0, kp.M2_single_pole)
    if kernel_name in {"exp", "exp_gap"}:
        return sigma_exp_gap(q, kp.sigma0, kp.Omega2, kp.mu02)
    raise ValueError(f"unknown kernel: {kernel_name!r}")


def neutral_mass_entries(phi: float, r: float, s: float, params: Mapping[str, float]) -> dict[str, float]:
    return {
        "m_hh2": -params["muH_eff2"] + 3.0 * params["lambdaH"] * phi**2 + 0.5 * params["arho"] * r**2 + 0.5 * params["aiota"] * s**2,
        "m_rr2": params["mrho2"] + 3.0 * params["brho"] * r**2 + 0.5 * params["arho"] * phi**2 + 0.5 * params["c"] * s**2,
        "m_ss_local2": params["miota2"] + 3.0 * params["biota"] * s**2 + 0.5 * params["aiota"] * phi**2 + 0.5 * params["c"] * r**2,
        "m_hr2": params["arho"] * phi * r,
        "m_hs2": params["aiota"] * phi * s,
        "m_rs2": params["c"] * r * s,
    }


def delta_N_matrix(q: float, phi: float, r: float, s: float, params: Mapping[str, float], kernel_name: str, kp: NonlocalKernelParams) -> np.ndarray:
    e = neutral_mass_entries(phi, r, s, params)
    sig = float(sigma_E(q, kernel_name, kp))
    return np.array(
        [
            [q + e["m_hh2"], e["m_hr2"], e["m_hs2"]],
            [e["m_hr2"], kp.Z_rho * q + e["m_rr2"], e["m_rs2"]],
            [e["m_hs2"], e["m_rs2"], kp.Z_iota * q + e["m_ss_local2"] - sig],
        ],
        dtype=float,
    )


def det_delta_N(q_values, phi: float, r: float, s: float, params: Mapping[str, float], kernel_name: str, kp: NonlocalKernelParams) -> np.ndarray:
    qs = np.asarray(q_values, dtype=float)
    e = neutral_mass_entries(phi, r, s, params)
    sig = sigma_E(qs, kernel_name, kp)
    a = qs + e["m_hh2"]
    d = kp.Z_rho * qs + e["m_rr2"]
    f = kp.Z_iota * qs + e["m_ss_local2"] - sig
    b = e["m_hr2"]
    c = e["m_hs2"]
    ee = e["m_rs2"]
    return a * d * f + 2.0 * b * c * ee - a * ee * ee - d * c * c - f * b * b


def iota_inverse(q_values, m_iota_local2: float, kernel_name: str, kp: NonlocalKernelParams) -> np.ndarray:
    q = np.asarray(q_values, dtype=float)
    return kp.Z_iota * q + float(m_iota_local2) - sigma_E(q, kernel_name, kp)


def quadrature_grid(kp: NonlocalKernelParams):
    # Gauss-Legendre over k in [0,kmax]
    x, w = np.polynomial.legendre.leggauss(kp.num_k)
    k = 0.5 * kp.kmax * (x + 1.0)
    weights = 0.5 * kp.kmax * w
    return k, weights, k * k


def V1_neutral_nonlocal(phi: float, r: float, s: float, params: Mapping[str, float], kernel_name: str, kp: NonlocalKernelParams) -> dict:
    k, weights, q = quadrature_grid(kp)
    det = det_delta_N(q, phi, r, s, params, kernel_name, kp)
    det_ref = det_delta_N(q, 0.0, 0.0, 0.0, params, kernel_name, kp)
    log_ratio = np.log(np.abs(det) + kp.eps_det) - np.log(np.abs(det_ref) + kp.eps_det)
    integral = np.sum(weights * k**3 * log_ratio) / (16.0 * np.pi * np.pi)
    inv_iota = iota_inverse(q, neutral_mass_entries(phi, r, s, params)["m_ss_local2"], kernel_name, kp)
    # Fast diagnostic proxy for neutral eigenvalue health; full per-k eigenscan is
    # intentionally deferred because v0.7 smoke evaluates many cells.
    min_eval = float(min(np.min(det), np.min(inv_iota)))
    return {
        "V1": float(integral),
        "determinant_negative_count": int(np.sum(det < 0)),
        "determinant_near_zero_count": int(np.sum(np.abs(det) < 1e-10)),
        "min_det": float(np.min(det)),
        "min_iota_inverse": float(np.min(inv_iota)),
        "min_neutral_eigenvalue_over_k": float(min_eval),
        "nonlocal_det_healthy": bool(np.all(det > 0) and np.all(inv_iota > 0) and min_eval > 0),
        "nonlocal_det_negative": bool(np.any(det < 0)),
        "nonlocal_det_near_zero": bool(np.any(np.abs(det) < 1e-10)),
        "nonlocal_iota_inverse_negative": bool(np.any(inv_iota < 0)),
    }


def V0_zero_mode_corrected(phi: float, r: float, s: float, params: Mapping[str, float], sigma0: float):
    # No LambdaT2_kappa0 double count; corrected bath zero-mode is -0.5*sigma0*s^2.
    return (
        -0.5 * params["muH_eff2"] * phi**2
        + 0.25 * params["lambdaH"] * phi**4
        + 0.5 * params["mrho2"] * r**2
        + 0.25 * params["brho"] * r**4
        + 0.5 * params["miota2"] * s**2
        + 0.25 * params["biota"] * s**4
        + 0.25 * params["arho"] * phi**2 * r**2
        + 0.25 * params["aiota"] * phi**2 * s**2
        + 0.25 * params["c"] * r**2 * s**2
        - 0.5 * sigma0 * s**2
    )


def Veff_nonlocal(x: Sequence[float], params: Mapping[str, float], kernel_name: str, kp: NonlocalKernelParams):
    phi, r, s = np.asarray(x, dtype=float)
    base = V0_zero_mode_corrected(phi, r, s, params, kp.sigma0)
    if kp.nonlocal_scale == 0.0 or kernel_name in {"local", "local_constant"}:
        return float(base)
    nonlocal_v1 = V1_neutral_nonlocal(phi, r, s, params, kernel_name, kp)["V1"]
    local_v1 = V1_neutral_nonlocal(phi, r, s, params, "local_constant", kp)["V1"]
    return float(base + kp.nonlocal_scale * (nonlocal_v1 - local_v1))


def kernel_sanity(kernel_name: str, kp: NonlocalKernelParams) -> dict:
    q = np.linspace(0.0, kp.kmax * kp.kmax, 512)
    sig = sigma_E(q, kernel_name, kp)
    inv = iota_inverse(q, kp.sigma0, kernel_name, kp)
    return {
        "kernel": kernel_name,
        "Sigma_E_0": float(sig[0]),
        "Sigma_E_kmax2": float(sig[-1]),
        "monotone_nonincreasing": bool(np.all(np.diff(sig) <= 1e-10)),
        "min_iota_inverse_representative": float(np.min(inv)),
    }


