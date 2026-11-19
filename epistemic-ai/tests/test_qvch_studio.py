from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.qvch_studio.server import QVCHStudioService, normalize_analysis
from qvch_v3.contracts.models import WriteReceipt, new_id
from qvch_v3.storage.db import QVCHDatabase


class FakeLMStudioClient:
    def __init__(self, analysis: dict | None = None, models: list[str] | None = None):
        self.analysis = analysis or {
            "summary": "Unknown-oriented extraction.",
            "thought_forms": [
                {
                    "text": "Unknown execution log location.",
                    "kind": "N",
                    "uncertainty": 0.9,
                    "why_uncertain": "No evidence was provided.",
                    "open_question": "Where are execution logs stored?",
                    "working_assumption": "",
                    "evidence_needed": ["tool output or operator confirmation"],
                    "safe_to_commit": True,
                }
            ],
            "model_unknowns": ["Execution log location is unknown."],
            "do_not_crystallize": ["No non-LLM evidence yet."],
        }
        self.models = models or ["gemma-4-e4b-it@iq4_xs"]
        self.list_models_called = False
        self.chat_called = False

    def list_models(self) -> list[str]:
        self.list_models_called = True
        return self.models

    def chat_json(self, *, model: str, system: str, user: str) -> dict:
        self.chat_called = True
        assert "Your primary task is not to prove certainty" in system
        assert "LLM confidence is not evidence" in system
        assert model in self.models
        assert user
        return self.analysis


@pytest.fixture()
def service(tmp_path):
    svc = QVCHStudioService(db_path=tmp_path / "memory.db", lm_client=FakeLMStudioClient())
    yield svc
    svc.close()


def test_health_checks_lmstudio_model_list_mocked(service):
    health = service.health()
    assert health["ok"] is True
    assert health["selected_model"] == "gemma-4-e4b-it@iq4_xs"
    assert service.lm_client.list_models_called is True


def test_analyze_returns_thought_forms(service):
    result = service.analyze("Where are execution logs stored?")
    assert result["ok"] is True
    assert result["analysis"]["thought_forms"][0]["kind"] == "N"
    assert result["analysis"]["model_unknowns"]
    assert service.lm_client.chat_called is True


def test_unknown_text_creates_N_candidate(service):
    result = service.commit([
        {"text": "Unknown artifact storage.", "kind": "N", "open_question": "Where are artifacts stored?", "evidence_needed": ["tool output"]}
    ])
    assert result["receipts"][0]["committed"] is True
    assert result["indicators"]["N_open_created"] == 1
    assert service.db.scalar("SELECT COUNT(*) FROM noumena WHERE state='N_open'") == 1


def test_fact_text_creates_F_candidate_not_crystal(service):
    result = service.commit([
        {"text": "Execution logs are stored in logs/runtime.", "kind": "F_candidate", "evidence_needed": ["non-LLM confirmation"]}
    ])
    assert result["receipts"][0]["committed"] is True
    assert result["indicators"]["F_candidates_created"] == 1
    assert service.db.scalar("SELECT COUNT(*) FROM memory_atoms WHERE epistemic_status='F_candidate'") == 1
    assert service.db.scalar("SELECT COUNT(*) FROM crystals") == 0


def test_secret_text_is_redacted(service):
    service.commit([
        {"text": "api key: sk-test-123456 and logs are in logs/runtime", "kind": "secret_reference", "open_question": "What safe trace remains after redaction?"}
    ])
    combined = " ".join(row["content_text"] for row in service.db.query("SELECT content_text FROM memory_events UNION ALL SELECT content_text FROM noumena"))
    assert "sk-test" not in combined
    assert "<REDACTED_SECRET>" in combined
    assert service.indicators.secrets_redacted == 1


def test_literal_artifact_without_pointer_routes_to_N(service):
    service.commit([
        {"text": "A literal artifact was pasted but no file pointer/evidence was provided.", "kind": "literal_artifact"}
    ])
    row = service.db.one("SELECT state, content_text FROM noumena ORDER BY created_at DESC LIMIT 1")
    assert row["state"] == "N_open"
    assert "Missing artifact pointer" in row["content_text"]


def test_commit_uses_memory_write_gateway(service, monkeypatch):
    calls = []

    class SpyGateway:
        def commit(self, plan):
            calls.append(plan)
            return WriteReceipt(new_id("receipt"), plan.plan_id, True, {"noumenon": "N_spy"}, ["spy_gateway"])

    monkeypatch.setattr(service, "gateway", SpyGateway())
    monkeypatch.setattr(service, "_probe_after_commit", lambda form, route: {"passed": True, "reason_codes": ["spy_probe"]})
    service.commit([{"text": "Unknown X", "kind": "N", "open_question": "What is X?"}])
    assert len(calls) == 1
    assert calls[0].route == "N"


def test_direct_db_write_not_used(service, monkeypatch):
    class SpyGateway:
        def commit(self, plan):
            return WriteReceipt(new_id("receipt"), plan.plan_id, True, {"noumenon": "N_spy"}, ["spy_gateway"])

    def blocked_execute(*args, **kwargs):
        raise AssertionError("service attempted direct db execute outside gateway")

    monkeypatch.setattr(service, "gateway", SpyGateway())
    monkeypatch.setattr(service, "_probe_after_commit", lambda form, route: {"passed": True})
    monkeypatch.setattr(service, "memory_view", lambda: {"ok": True})
    monkeypatch.setattr(service.db, "execute", blocked_execute)
    result = service.commit([{"text": "Unknown Y", "kind": "N", "open_question": "What is Y?"}])
    assert result["receipts"][0]["reason_codes"] == ["spy_gateway"]


def test_retrieval_probe_runs_after_commit(service):
    result = service.commit([{"text": "Where is memory.db stored?", "kind": "N", "open_question": "Where is memory.db stored?"}])
    assert result["probes"]
    assert result["probes"][0]["passed"] is True
    assert service.db.scalar("SELECT COUNT(*) FROM probe_runs") == 1


def test_indicators_count_N_U_F_secret_conflict(service):
    forms = [
        {"text": "Where are logs?", "kind": "N", "open_question": "Where are logs?"},
        {"text": "Logs may be under outputs/.", "kind": "U"},
        {"text": "Execution logs are stored in logs/runtime.", "kind": "F_candidate"},
        {"text": "token=secret999999", "kind": "secret_reference", "open_question": "Secret redacted?"},
    ]
    service.commit(forms)
    service.commit([{"text": "Execution logs are stored in output/logs.", "kind": "F_candidate"}])
    indicators = service.indicators.to_dict()
    assert indicators["N_open_created"] == 2
    assert indicators["U_hypotheses_created"] == 1
    assert indicators["F_candidates_created"] == 1
    assert indicators["secrets_redacted"] == 1
    assert indicators["conflicts_detected"] == 1
    assert indicators["crystals_created"] == 0


def test_json_response_serializable(service):
    result = service.analyze("Where is the artifact stored?")
    encoded = json.dumps(result, ensure_ascii=False)
    assert "thought_forms" in encoded


def test_no_old_qvch_dist_runtime_import():
    root = Path(__file__).resolve().parents[1]
    checked = []
    for rel in ["apps/qvch_studio/server.py", "scripts/run_qvch_studio.py"]:
        text = (root / rel).read_text(encoding="utf-8")
        checked.append(text)
    assert "qvch_dist" not in "\n".join(checked)
    assert "PQT-transformers" not in "\n".join(checked)


def test_analyze_normalizes_secret_fields():
    payload = normalize_analysis({
        "summary": "x",
        "thought_forms": [{"text": "sk-secret123456", "kind": "secret_reference", "why_uncertain": "token=abc123456"}],
        "model_unknowns": [],
        "do_not_crystallize": [],
    })
    form = payload["thought_forms"][0]
    assert "sk-secret" not in form["text"]
    assert "abc123456" not in form["why_uncertain"]
