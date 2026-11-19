from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .constants import BANNER, CLAIM_BOUNDARY
from .contracts import EpisodeInput
from .ext1_encoder import PQTTextEncoder
from .firewall import RuntimeMutationFirewall

_FORBIDDEN_ARTIFACT_KEYS = {"raw_text", "candidate_text", "source_text", "raw_candidate_text", "raw_source_text", "private_metadata"}


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        result = set(map(str, value))
        for child in value.values():
            result |= _all_keys(child)
        return result
    if isinstance(value, (list, tuple)):
        result: set[str] = set()
        for child in value:
            result |= _all_keys(child)
        return result
    return set()


class WitnessWriter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir.resolve()
        self.output_path = self.output_dir / "pqt_witness.jsonl"

    def initialize(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8", newline=""):
            pass

    def append(self, record: dict[str, Any]) -> None:
        if self.output_path.resolve() != (self.output_dir / "pqt_witness.jsonl").resolve():
            raise PermissionError("W0 allows only pqt_witness.jsonl")
        forbidden = sorted(_all_keys(record) & _FORBIDDEN_ARTIFACT_KEYS)
        if forbidden:
            raise PermissionError(f"raw/private witness fields forbidden: {forbidden}")
        payload = {"banner": BANNER, "claim_boundary": CLAIM_BOUNDARY, "fixture_kind": "historical", **record}
        with self.output_path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def run_witness(episodes: Iterable[EpisodeInput], encoder: PQTTextEncoder, writer: WitnessWriter) -> dict[str, Any]:
    writer.initialize()
    count = 0
    with RuntimeMutationFirewall() as firewall:
        for episode in episodes:
            writer.append(encoder.encode_episode(episode))
            count += 1
    return {"historical_records_written": count, "mutation_attempts": firewall.attempts, "w0_runtime_passed": not firewall.attempts}
