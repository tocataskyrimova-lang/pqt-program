from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np

from .constants import SYNTHETIC_DISCLAIMER, SYNTHETIC_PREFIX
from .ext1_encoder import extract_text_features

SEED = 20260619


def rank_auc(y: np.ndarray, score: np.ndarray) -> float:
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    positives = int(y.sum())
    negatives = len(y) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("AUC requires both classes")
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty(len(score), dtype=float)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and score[order[end]] == score[order[index]]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        ranks[order[index:end]] = average_rank
        index = end
    return float((ranks[y == 1].sum() - positives * (positives + 1) / 2.0) / (positives * negatives))


def run_surrogate_machinery_checks() -> dict[str, Any]:
    rng = np.random.Generator(np.random.PCG64(SEED))
    n = 600
    latent = rng.normal(size=n)
    y = (latent + 0.25 * rng.normal(size=n) > 0.0).astype(int)
    planted_score = latent + 0.15 * rng.normal(size=n)
    planted_auc = rank_auc(y, planted_score)

    shuffled_auc = rank_auc(y, rng.permutation(planted_score))
    event_score = (latent > 0.15).astype(float)
    randomized_events = rng.permutation(event_score)
    random_phase_auc = rank_auc(y, randomized_events)

    time = np.linspace(-1.0, 1.0, 12)
    direction = np.where(y[:, None] == 1, 1.0, -1.0)
    histories = direction * time[None, :] + 0.15 * rng.normal(size=(n, len(time)))
    time_permuted = np.stack([row[rng.permutation(len(row))] for row in histories])
    time_permuted_score = time_permuted[:, -1] - time_permuted[:, 0]
    time_permuted_auc = rank_auc(y, time_permuted_score)
    degradation = {
        "S1_episode_shuffle": planted_auc - shuffled_auc,
        "S2_random_phase_matched_frequency": planted_auc - random_phase_auc,
        "S3_time_permuted_history": planted_auc - time_permuted_auc,
    }
    passed = planted_auc >= 0.80 and all(value >= 0.15 for value in degradation.values())
    return {
        "synthetic_banner": f"{SYNTHETIC_PREFIX}SURROGATE_VALIDATION",
        "disclaimer": SYNTHETIC_DISCLAIMER,
        "seed": SEED,
        "sample_count": n,
        "SYNTHETIC_MACHINERY_CHECK_PLANTED_AUC": planted_auc,
        "SYNTHETIC_MACHINERY_CHECK_S1_AUC": shuffled_auc,
        "SYNTHETIC_MACHINERY_CHECK_S2_AUC": random_phase_auc,
        "SYNTHETIC_MACHINERY_CHECK_S3_AUC": time_permuted_auc,
        "SYNTHETIC_MACHINERY_CHECK_DEGRADATION": degradation,
        "passed": passed,
    }


def run_encoder_laundering_check() -> dict[str, Any]:
    rng = np.random.Generator(np.random.PCG64(SEED + 1))
    n = 600
    y = rng.integers(0, 2, size=n)
    vocabulary = ["alpha", "bridge", "context", "memory", "query", "trace", "review"]
    texts = [" ".join(rng.choice(vocabulary, size=int(rng.integers(4, 20)))) for _ in range(n)]
    clean_score = np.asarray([extract_text_features(text)[0] for text in texts])
    forbidden_scalar = y + 0.03 * rng.normal(size=n)
    clean_auc = rank_auc(y, clean_score)
    laundered_auc = rank_auc(y, forbidden_scalar)
    gap = laundered_auc - clean_auc
    passed = max(clean_auc, 1.0 - clean_auc) <= 0.60 and laundered_auc >= 0.90 and gap >= 0.30
    return {
        "synthetic_banner": f"{SYNTHETIC_PREFIX}ENCODER_LAUNDERING_ABLATION",
        "disclaimer": SYNTHETIC_DISCLAIMER,
        "seed": SEED + 1,
        "sample_count": n,
        "SYNTHETIC_MACHINERY_CHECK_CLEAN_TEXT_AUC": clean_auc,
        "SYNTHETIC_MACHINERY_CHECK_FORBIDDEN_SCALAR_AUC": laundered_auc,
        "SYNTHETIC_MACHINERY_CHECK_AUC_GAP": gap,
        "passed": passed,
    }
