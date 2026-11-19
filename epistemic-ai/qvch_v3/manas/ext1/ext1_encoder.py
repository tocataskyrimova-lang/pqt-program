from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .constants import C_ALIAS_NOTE, FORBIDDEN_ENCODER_FIELDS
from .contracts import EpisodeInput
from .readonly_sources import sha256_file

ENCODER_VERSION = "ext1_text_to_pqt_v1"
PROJECTION_SEED = "EXT1_DRY_ENCODER_V1"
STRUCTURAL_FEATURES = [
    "log_char_count", "log_token_count", "log_sentence_count", "question_ratio",
    "exclamation_ratio", "punctuation_ratio", "digit_ratio", "uppercase_ratio",
    "whitespace_ratio", "unique_token_ratio", "mean_token_length", "char_entropy",
]
TRIGRAM_BINS = 16
DRIVE_NAMES = ["hexad_S", "hexad_R", "hexad_A", "hexad_K", "hexad_M", "hexad_G", "center_P_L", "center_P_I", "center_E", "theta", "m_phi", "G_grey"]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _projection_value(row: int, column: int) -> float:
    raw = hashlib.sha256(f"{PROJECTION_SEED}:{row}:{column}".encode("utf-8")).digest()
    integer = int.from_bytes(raw[:8], "big")
    return 2.0 * (integer / float(2**64 - 1)) - 1.0


def fixed_projection() -> np.ndarray:
    matrix = np.array(
        [[_projection_value(row, col) for col in range(len(STRUCTURAL_FEATURES) + TRIGRAM_BINS)] for row in range(len(DRIVE_NAMES))],
        dtype=float,
    )
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0.0, 1.0, norms)


def _char_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts: dict[str, int] = {}
    for char in text:
        counts[char] = counts.get(char, 0) + 1
    total = len(text)
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    return min(1.0, entropy / 8.0)


def extract_text_features(text: str) -> np.ndarray:
    text = text or ""
    tokens = text.split()
    length = max(1, len(text))
    sentence_count = sum(text.count(mark) for mark in ".!?")
    punctuation = sum(1 for char in text if not char.isalnum() and not char.isspace())
    base = [
        min(1.0, math.log1p(len(text)) / math.log1p(4096)),
        min(1.0, math.log1p(len(tokens)) / math.log1p(512)),
        min(1.0, math.log1p(sentence_count) / math.log1p(64)),
        text.count("?") / length,
        text.count("!") / length,
        punctuation / length,
        sum(char.isdigit() for char in text) / length,
        sum(char.isupper() for char in text) / length,
        sum(char.isspace() for char in text) / length,
        len({token.casefold() for token in tokens}) / max(1, len(tokens)),
        min(1.0, (sum(map(len, tokens)) / max(1, len(tokens))) / 20.0),
        _char_entropy(text),
    ]
    bins = np.zeros(TRIGRAM_BINS, dtype=float)
    normalized = " ".join(text.casefold().split())
    for index in range(max(0, len(normalized) - 2)):
        trigram = normalized[index : index + 3].encode("utf-8")
        digest = hashlib.sha256(trigram).digest()
        bucket = int.from_bytes(digest[:2], "big") % TRIGRAM_BINS
        sign = 1.0 if digest[2] & 1 else -1.0
        bins[bucket] += sign
    norm = float(np.linalg.norm(bins))
    if norm:
        bins /= norm
    return np.concatenate([np.asarray(base, dtype=float), bins])


def _hash_tree(root: Path, pattern: str = "*.py") -> dict[str, str]:
    return {str(path.relative_to(root)).replace("\\", "/"): sha256_file(path) for path in sorted(root.rglob(pattern))}


def build_encoder_contract(pqt_math_root: Path) -> dict[str, Any]:
    core_root = pqt_math_root / "pqt_core_v03"
    defaults = pqt_math_root / "defaults.yaml"
    projection = fixed_projection()
    return {
        "contract_version": "ext1_encoder_contract_v1",
        "encoder_version": ENCODER_VERSION,
        "locked_before_historical_run": True,
        "allowed_inputs": ["raw_candidate_text", "raw_source_text", "running_pqt_state_history"],
        "forbidden_inputs": sorted(FORBIDDEN_ENCODER_FIELDS),
        "feature_names": STRUCTURAL_FEATURES + [f"signed_char_trigram_bin_{i:02d}" for i in range(TRIGRAM_BINS)],
        "projection_seed": PROJECTION_SEED,
        "projection_shape": list(projection.shape),
        "projection_matrix": projection.round(12).tolist(),
        "projection_sha256": _sha256_bytes(projection.astype("<f8").tobytes()),
        "drive_names": DRIVE_NAMES,
        "steps_per_episode": 100,
        "dt_required": 0.01,
        "rng_seed_policy": "sha256(projection_seed + episode_id), first 64 bits",
        "core_files_sha256": _hash_tree(core_root),
        "defaults_path": "defaults.yaml",
        "pqt_math_root_binding": "runtime_argument_not_part_of_contract",
        "defaults_sha256": sha256_file(defaults),
        "raw_text_artifact_policy": "read in memory only; never persist",
        "C_alias": {"source": "C_R", "output": "C_ext1_alias", "note": C_ALIAS_NOTE},
    }


def validate_encoder_payload(payload: dict[str, Any]) -> None:
    forbidden = sorted(set(payload) & FORBIDDEN_ENCODER_FIELDS)
    if forbidden:
        raise PermissionError(f"EXT1 encoder forbidden inputs: {forbidden}")


class PQTTextEncoder:
    def __init__(self, *, pqt_math_root: Path, contract: dict[str, Any]):
        self.pqt_math_root = pqt_math_root.resolve()
        self.contract = contract
        if str(self.pqt_math_root) not in sys.path:
            sys.path.insert(0, str(self.pqt_math_root))
        from pqt_core_v03.params import load_params

        self.params = load_params(self.pqt_math_root / "defaults.yaml")
        if abs(float(self.params.dt) - float(contract["dt_required"])) > 1e-12:
            raise ValueError("PQT dt differs from locked EXT1 contract")
        self.state = self.params.initial_state()
        self.projection = np.asarray(contract["projection_matrix"], dtype=float)

    def _drive(self, features: np.ndarray) -> None:
        from pqt_core_v03.integrator import project_simplex, wrap_theta

        drive = np.tanh(self.projection @ features)
        hexad_names = ["S", "R", "A", "K", "M", "G"]
        old_mass = sum(float(getattr(self.state, name)) for name in hexad_names)
        values = np.asarray([float(getattr(self.state, name)) for name in hexad_names])
        values *= np.exp(0.02 * drive[:6])
        values *= old_mass / float(values.sum())
        for name, value in zip(hexad_names, values):
            setattr(self.state, name, float(value))
        center_names = ["P_L", "P_I", "E"]
        center = np.asarray([max(1e-12, float(getattr(self.state, name))) for name in center_names])
        center = np.exp(np.log(center) + 0.10 * drive[6:9])
        for name, value in zip(center_names, center):
            setattr(self.state, name, float(value))
        project_simplex(self.state)
        self.state.theta = wrap_theta(float(self.state.theta) + 0.10 * float(drive[9]))
        self.state.m_phi = max(0.0, float(self.state.m_phi) + 0.02 * max(0.0, float(drive[10])))
        self.state.G_grey = max(0.0, float(self.state.G_grey) + 0.02 * max(0.0, float(drive[11])))

    def encode_episode(self, episode: EpisodeInput) -> dict[str, Any]:
        from pqt_core_v03.integrator import diagnostics_row, step, wrap_theta
        from pqt_core_v03.gates import compute_flows, compute_gates

        validate_encoder_payload({"raw_candidate_text": episode.candidate_text, "raw_source_text": episode.source_text})
        combined = f"{episode.candidate_text}\n{episode.source_text}".strip()
        features = extract_text_features(combined)
        input_hash = _sha256_bytes(combined.encode("utf-8"))
        feature_hash = _sha256_bytes(features.astype("<f8").tobytes())
        initial_theta = float(self.state.theta)
        self._drive(features)
        seed_bytes = hashlib.sha256(f"{PROJECTION_SEED}:{episode.episode_id}".encode("utf-8")).digest()
        seed = int.from_bytes(seed_bytes[:8], "big")
        rng = np.random.Generator(np.random.PCG64(seed))
        events: list[dict[str, Any]] = []
        prema_hits = 0
        maya_hits = 0
        history: list[dict[str, float]] = []
        for index in range(int(self.contract["steps_per_episode"])):
            self.state, flows, step_events = step(self.state, self.params, rng, index * self.params.dt)
            events.extend(step_events)
            prema_hits += int(self.state.P_L > 0.99)
            maya_hits += int(self.state.P_I > 0.99)
            history.append(diagnostics_row((index + 1) * self.params.dt, self.state, flows, self.params))
        if not history:
            flows = compute_flows(self.state, self.params, compute_gates(self.state, self.params))
            history.append(diagnostics_row(0.0, self.state, flows, self.params))
        event_types = [str(event.get("type")) for event in events]
        agni_times = [float(event["t"]) for event in events if event.get("type") == "Agni"]
        laya_times = [float(event["t"]) for event in events if event.get("type") == "Prem_Laya"]
        stabilization_window = float(self.params.T_W + self.params.laya_tail_margin)
        premature_laya = any(not any(0.0 <= laya - agni <= stabilization_window for agni in agni_times) for laya in laya_times)
        steps = int(self.contract["steps_per_episode"])
        return {
            "episode_id": episode.episode_id,
            "occurred_at": episode.occurred_at,
            "input_hash": input_hash,
            "text_length": len(combined),
            "feature_hash": feature_hash,
            "redacted_preview_if_already_safe": None,
            "source_pointer": episode.source_pointer,
            "encoder_version": ENCODER_VERSION,
            "witness_write_authority": False,
            "C_R": float(self.state.C_R),
            "C_ext1_alias": float(self.state.C_R),
            "C_alias_note": C_ALIAS_NOTE,
            "H": float(self.state.H),
            "G_grey": float(self.state.G_grey),
            "m_phi": float(self.state.m_phi),
            "P_L": float(self.state.P_L),
            "P_I": float(self.state.P_I),
            "E": float(self.state.E),
            "delta_phi": wrap_theta(float(self.state.theta) - initial_theta),
            "B_edge": float(np.clip(1.0 - 3.0 * min(self.state.P_L, self.state.P_I, self.state.E), 0.0, 1.0)),
            "prema_boundary": prema_hits / max(1, steps),
            "maya_collapse": maya_hits / max(1, steps),
            "agni_event": "Agni" in event_types,
            "om_event": "Om_Nada" in event_types,
            "laya_event": "Prem_Laya" in event_types,
            "premature_laya": premature_laya,
            "event_counts": {name: event_types.count(name) for name in sorted(set(event_types))},
            "Q": float(history[-1]["Q"]),
            "F_tot": float(history[-1]["F_tot"]),
            "Lambda": float(history[-1]["Lambda"]),
        }
