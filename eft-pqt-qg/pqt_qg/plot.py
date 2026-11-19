"""Plotting helpers for PQT-QG benchmark outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .potential import V0


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def plot_phi_r_s0(params: Mapping[str, float], minima: list[dict], out_dir: Path) -> Path:
    _ensure_dir(out_dir)
    name = params["name"]
    phi = np.linspace(0.0, 2.0, 241)
    r = np.linspace(-2.0, 2.0, 321)
    P, R = np.meshgrid(phi, r, indexing="xy")
    Z = V0(P, R, 0.0, params)
    path = out_dir / f"{name}_phi_r_s0.png"
    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
    im = ax.contourf(P, R, Z, levels=80, cmap="viridis")
    ax.contour(P, R, Z, levels=20, colors="white", linewidths=0.25, alpha=0.45)
    for m in minima:
        if abs(m["s"]) < 2e-2:
            ax.scatter(m["phi"], m["r"], marker="x", s=70, c="red")
            ax.annotate(m["phase"], (m["phi"], m["r"]), color="white", fontsize=8)
    ax.set_title(f"{name}: V0(phi,r,s=0)")
    ax.set_xlabel("phi")
    ax.set_ylabel("r")
    fig.colorbar(im, ax=ax, label="V0")
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_phi_s_r0(params: Mapping[str, float], minima: list[dict], out_dir: Path) -> Path:
    _ensure_dir(out_dir)
    name = params["name"]
    phi = np.linspace(0.0, 2.0, 241)
    s = np.linspace(-2.0, 2.0, 321)
    P, S = np.meshgrid(phi, s, indexing="xy")
    Z = V0(P, 0.0, S, params)
    path = out_dir / f"{name}_phi_s_r0.png"
    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
    im = ax.contourf(P, S, Z, levels=80, cmap="magma")
    ax.contour(P, S, Z, levels=20, colors="white", linewidths=0.25, alpha=0.45)
    for m in minima:
        if abs(m["r"]) < 2e-2:
            ax.scatter(m["phi"], m["s"], marker="x", s=70, c="cyan")
            ax.annotate(m["phase"], (m["phi"], m["s"]), color="white", fontsize=8)
    ax.set_title(f"{name}: V0(phi,s,r=0)")
    ax.set_xlabel("phi")
    ax.set_ylabel("s")
    fig.colorbar(im, ax=ax, label="V0")
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_low_energy_points(params: Mapping[str, float], low_points, low_values, minima: list[dict], out_dir: Path) -> Path:
    _ensure_dir(out_dir)
    name = params["name"]
    pts = np.asarray(low_points, dtype=float)
    vals = np.asarray(low_values, dtype=float)
    path = out_dir / f"{name}_low_energy_points.png"
    fig = plt.figure(figsize=(8, 6), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    if pts.size:
        sc = ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=vals, s=8, cmap="plasma", alpha=0.75)
        fig.colorbar(sc, ax=ax, shrink=0.75, label="V0")
    for m in minima:
        ax.scatter(m["phi"], m["r"], m["s"], marker="x", s=90, c="black")
    ax.set_title(f"{name}: lowest-energy grid points")
    ax.set_xlabel("phi")
    ax.set_ylabel("r")
    ax.set_zlabel("s")
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def make_plots(result: dict, out_dir: str | Path) -> list[str]:
    out_dir = Path(out_dir)
    params = result["params"]
    minima = result["raw_minima"]
    paths = [
        plot_phi_r_s0(params, minima, out_dir),
        plot_phi_s_r0(params, minima, out_dir),
        plot_low_energy_points(params, result["low_energy_points"], result["low_energy_values"], minima, out_dir),
    ]
    return [str(p) for p in paths]
