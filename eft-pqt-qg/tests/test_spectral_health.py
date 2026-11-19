"""Unit tests for exact eigvalsh spectral health and Lee-Wick ghost diagnostics in PQT-QG."""

from __future__ import annotations

import numpy as np
import pytest

from pqt_qg.nonlocal_memory import (
    NonlocalKernelParams,
    V1_neutral_nonlocal,
    delta_N_matrix,
    iota_inverse,
)


def test_sylvester_3x3_counterexample():
    """Verify that a 3x3 matrix with two negative eigenvalues slips past the

    legacy det(M)>0 and M_ss>0 heuristic, but is rejected by exact eigvalsh.
    """
    # Explicit eigenvalues: lambda_1 = -0.2, lambda_2 = -0.1, lambda_3 = +2.0
    # det(M) = (-0.2) * (-0.1) * (+2.0) = +0.04 > 0
    # M_ss = +2.0 > 0
    M_bad_diag = np.diag([-0.2, -0.1, 2.0])
    det_bad = float(np.linalg.det(M_bad_diag))
    M_ss_bad = float(M_bad_diag[2, 2])
    evals_bad = np.linalg.eigvalsh(M_bad_diag)
    lambda_min_bad = float(np.min(evals_bad))

    # Legacy heuristic fails: det > 0 and M_ss > 0
    legacy_passes_bad = bool(det_bad > 0 and M_ss_bad > 0)
    assert legacy_passes_bad is True, "Legacy heuristic must falsely accept M_bad"

    # Exact spectral check succeeds: minimum eigenvalue is strictly negative
    assert lambda_min_bad < 0.0, "Exact spectral check must flag negative eigenvalue"
    assert np.isclose(lambda_min_bad, -0.2), f"Expected lambda_min = -0.2, got {lambda_min_bad}"

    # Verify invariance under an arbitrary orthogonal rotation (mixing fields)
    theta = np.pi / 4.0
    c, s_val = np.cos(theta), np.sin(theta)
    R = np.array([
        [c, 0.0, s_val],
        [0.0, 1.0, 0.0],
        [-s_val, 0.0, c],
    ])
    M_bad_rot = R @ M_bad_diag @ R.T
    det_rot = float(np.linalg.det(M_bad_rot))
    evals_rot = np.linalg.eigvalsh(M_bad_rot)
    lambda_min_rot = float(np.min(evals_rot))

    assert det_rot > 0.0, "Determinant must remain invariant and positive"
    assert np.isclose(lambda_min_rot, -0.2), f"Rotated matrix eigenvalue mismatch: {lambda_min_rot}"
    assert lambda_min_rot < 0.0


def test_positive_definite_control():
    """Verify that a genuinely positive-definite matrix passes both checks."""
    # Eigenvalues: (+0.1, +0.5, +2.0)
    M_good_diag = np.diag([0.1, 0.5, 2.0])
    det_good = float(np.linalg.det(M_good_diag))
    evals_good = np.linalg.eigvalsh(M_good_diag)
    lambda_min_good = float(np.min(evals_good))

    assert det_good > 0.0
    assert np.isclose(lambda_min_good, 0.1)
    assert lambda_min_good > 0.0


def test_nonlocal_memory_module_spectral_check():
    """Verify that V1_neutral_nonlocal accurately reports spectral health

    across all three kernels ('local_constant', 'single_pole', 'exp_gap').
    """
    kp = NonlocalKernelParams(sigma0=0.05, kmax=5.0, num_k=48)

    # 1. Healthy physical potential
    params_healthy = {
        "muH_eff2": -0.5, "lambdaH": 0.1,
        "mrho2": 0.2, "brho": 0.1, "arho": 0.1,
        "miota2": 0.3, "biota": 0.1, "aiota": 0.1,
        "c": 0.05,
    }

    # 2. Tachyonic potential engineered with two negative mass eigenvalues
    # (m_hh2 < 0, m_rr2 < 0, m_ss2 > 0 -> det(D) > 0 at low q)
    params_tachyonic = {
        "muH_eff2": 2.0, "lambdaH": 0.01,
        "mrho2": -0.5, "brho": 0.01, "arho": 0.0,
        "miota2": 1.0, "biota": 0.1, "aiota": 0.0,
        "c": 0.0,
    }

    for kernel in ["local_constant", "single_pole", "exp_gap"]:
        # Healthy test
        res_h = V1_neutral_nonlocal(0.1, 0.1, 0.1, params_healthy, kernel, kp)
        assert res_h["nonlocal_det_healthy"] is True, f"Failed healthy check for {kernel}"
        assert res_h["min_neutral_eigenvalue_over_k"] > 0.0, f"Expected positive eigenvalue for {kernel}"

        # Tachyonic test: det > 0 must NOT fool the patched check
        res_t = V1_neutral_nonlocal(0.0, 0.0, 0.0, params_tachyonic, kernel, kp)
        assert res_t["min_neutral_eigenvalue_over_k"] < 0.0, f"Failed tachyonic detection for {kernel}"
        assert res_t["nonlocal_det_healthy"] is False, f"Declared tachyonic cell healthy for {kernel}"


def test_single_pole_residue_positivity():
    """Verify analytical continuation pole-residue check for single_pole kernel.

    D(p^2) = Z_iota * p^2 - m_ss^2 + sigma0 * M^2 / (M^2 - p^2).
    Residue derivative: D'(p^2) = Z_iota + sigma0 * M^2 / (M^2 - p^2)^2.
    For physical parameters (Z_iota > 0, sigma0 > 0), D'(p^2) >= Z_iota > 0
    guarantees strictly positive pole residues Z_res = 1 / D'(p^2) > 0 (no ghost).
    """
    def check_residue_health(m_ss2, sigma0, M2, Z_iota):
        # Discriminant of quadratic for poles p^2:
        # p^4 - (m_ss2 + M2)*p^2 + (m_ss2*M2 - sigma0*M2/Z_iota) = 0 (for Z_iota=1)
        # Using general F(p^2) = Z_iota*p^2 - m_ss2 + sigma0*M2/(M2 - p^2) = 0
        # -> -Z_iota*p^4 + (Z_iota*M2 + m_ss2)*p^2 - m_ss2*M2 + sigma0*M2 = 0
        a = -Z_iota
        b = Z_iota * M2 + m_ss2
        c_term = -m_ss2 * M2 + sigma0 * M2
        disc = b * b - 4.0 * a * c_term
        if disc < 0:
            return False, "Complex poles (Lee-Wick pair)"
        
        p2_1 = (-b + np.sqrt(disc)) / (2.0 * a)
        p2_2 = (-b - np.sqrt(disc)) / (2.0 * a)
        
        poles = [p2_1, p2_2]
        for p2 in poles:
            # Check derivative D'(p^2)
            denom = (M2 - p2)**2
            if np.isclose(denom, 0.0):
                continue
            deriv = Z_iota + (sigma0 * M2) / denom
            if deriv <= 0.0:
                return False, f"Negative residue ghost at p2={p2}: D'={deriv}"
        return True, "All real poles have positive residues"

    # Case A: Standard physical parameters (Z_iota = 1.0, sigma0 = 0.05, M2 = 1.0, m_ss2 = 0.5)
    healthy, msg = check_residue_health(m_ss2=0.5, sigma0=0.05, M2=1.0, Z_iota=1.0)
    assert healthy is True, f"Physical single_pole parameters must be ghost-free: {msg}"

    # Case B: Wrong-sign kinetic term (Z_iota = -1.0) -> Lee-Wick ghost
    healthy_ghost, msg_ghost = check_residue_health(m_ss2=0.5, sigma0=0.05, M2=1.0, Z_iota=-1.0)
    assert healthy_ghost is False, "Z_iota < 0 must be identified as negative residue ghost"
