from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qvch_v3.contracts.models import (  # noqa: E402
    EvidenceRef,
    ManasReview,
    MemoryAtomDraft,
    RawExperience,
    StructuredDraft,
    ValidationResult,
    new_id,
)
from qvch_v3.core.normalizer import normalize_experience  # noqa: E402
from qvch_v3.core.planner import build_repair_plan, build_write_plan  # noqa: E402
from qvch_v3.core.structurer import structure_event  # noqa: E402
from qvch_v3.manas.review import review_draft  # noqa: E402
from qvch_v3.manas.validation import validate_candidate  # noqa: E402
from qvch_v3.retrieval.probe import run_memory_probe  # noqa: E402
from qvch_v3.retrieval.search import retrieve  # noqa: E402
from qvch_v3.safety.scanner import redact_text, scan_event  # noqa: E402
from qvch_v3.storage.db import QVCHDatabase  # noqa: E402
from qvch_v3.storage.gateway import MemoryWriteGateway  # noqa: E402

LM_STUDIO_BASE_URL = "http://100.75.52.51:1234/v1"
PREFERRED_MODELS = ("gemma-4-e4b-it", "gemma-4-e4b-it@iq4_xs", "gemma-4-e4b-it@q4_k_xl")
_KIND_VALUES = {"N", "U", "F_candidate", "literal_artifact", "secret_reference", "skill_trace", "repair_pair"}

THOUGHT_FORM_PROMPT = """You are QVCH_v3 Thought-Form Extractor for MANAS/QVCH memory intake.
Your primary task is not to prove certainty.
Your primary task is to find what is unknown, missing, ambiguous, unsupported, or requires evidence.
Unknowns are valuable: turn them into N/open questions. Unknowns do not block thought.
LLM confidence is not evidence. Do not crystallize raw model claims.
Return exactly one JSON object with this shape:
{
  "summary": "...",
  "thought_forms": [
    {
      "text": "...",
      "kind": "N|U|F_candidate|literal_artifact|secret_reference|skill_trace|repair_pair",
      "uncertainty": 0.0,
      "why_uncertain": "...",
      "open_question": "...",
      "working_assumption": "...",
      "evidence_needed": [],
      "safe_to_commit": true
    }
  ],
  "model_unknowns": [],
  "do_not_crystallize": []
}
Prefer N when evidence is missing. Mark secrets as secret_reference. Mark exact artifacts without pointer as literal_artifact.
"""


@dataclass
class Indicators:
    thought_forms_found: int = 0
    N_open_created: int = 0
    U_hypotheses_created: int = 0
    F_candidates_created: int = 0
    crystals_created: int = 0
    secrets_redacted: int = 0
    conflicts_detected: int = 0
    writes_committed: int = 0
    writes_rejected: int = 0
    probe_passed: int = 0
    probe_failed: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


class LMStudioClient:
    def __init__(self, base_url: str = LM_STUDIO_BASE_URL, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_models(self) -> list[str]:
        with urllib.request.urlopen(f"{self.base_url}/models", timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [str(item.get("id") or item.get("name")) for item in payload.get("data", [])]

    def chat_json(self, *, model: str, system: str, user: str) -> dict[str, Any]:
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "stream": False,
            "response_format": {"type": "json_object"},
        }
        try:
            payload = self._post_chat(body)
        except urllib.error.HTTPError as exc:
            if exc.code != 400:
                raise
            fallback = dict(body)
            fallback.pop("response_format", None)
            fallback["messages"] = [
                body["messages"][0],
                {"role": "user", "content": f"{user}\n\nReturn only valid JSON. No markdown."},
            ]
            payload = self._post_chat(fallback)
        content = payload["choices"][0]["message"]["content"]
        return _loads_json_object(content)

    def _post_chat(self, body: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class QVCHStudioService:
    def __init__(
        self,
        *,
        db_path: str | Path | None = None,
        lm_client: LMStudioClient | None = None,
        preferred_models: tuple[str, ...] = PREFERRED_MODELS,
    ):
        self.root = ROOT
        self.db_path = Path(db_path) if db_path else self.root / "memory.db"
        self.db = QVCHDatabase(self.db_path)
        self.db.init_schema()
        self.gateway = MemoryWriteGateway(self.db)
        self.lm_client = lm_client or LMStudioClient()
        self.preferred_models = preferred_models
        self.selected_model: str | None = None
        self.last_receipts: list[dict[str, Any]] = []
        self.indicators = Indicators()

    def close(self) -> None:
        self.db.close()

    def health(self) -> dict[str, Any]:
        try:
            models = self.lm_client.list_models()
            selected = self._select_model(models)
            self.selected_model = selected
            return {
                "ok": selected is not None,
                "lmstudio_reachable": True,
                "models": models,
                "selected_model": selected,
                "preferred_visible": selected is not None,
            }
        except Exception as exc:
            return {
                "ok": False,
                "lmstudio_reachable": False,
                "models": [],
                "selected_model": None,
                "preferred_visible": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

    def analyze(self, text: str, *, commit: bool = False) -> dict[str, Any]:
        text = str(text or "").strip()
        if not text:
            return {"ok": False, "error": "empty_text", "analysis": _empty_analysis(), "indicators": self.indicators.to_dict()}
        health = self.health()
        if not health["ok"] or not health.get("selected_model"):
            return {"ok": False, "error": "lmstudio_model_unavailable", "health": health, "analysis": _empty_analysis(), "indicators": self.indicators.to_dict()}
        raw_analysis = self.lm_client.chat_json(model=health["selected_model"], system=THOUGHT_FORM_PROMPT, user=text)
        analysis = normalize_analysis(raw_analysis)
        self.indicators.thought_forms_found += len(analysis["thought_forms"])
        result = {"ok": True, "health": health, "analysis": analysis, "indicators": self.indicators.to_dict()}
        if commit:
            result["commit"] = self.commit(analysis["thought_forms"], source_text=text)
        return result

    def commit(self, thought_forms: list[dict[str, Any]], *, source_text: str = "") -> dict[str, Any]:
        receipts: list[dict[str, Any]] = []
        probes: list[dict[str, Any]] = []
        for form in thought_forms:
            normalized = normalize_thought_form(form)
            plan = self._plan_for_thought_form(normalized, source_text=source_text)
            receipt = self.gateway.commit(plan)
            receipt_dict = receipt.__dict__
            receipts.append(receipt_dict)
            self.last_receipts.insert(0, receipt_dict)
            self.last_receipts = self.last_receipts[:20]
            if receipt.committed:
                self.indicators.writes_committed += 1
                self._count_committed_route(plan.route, normalized)
                probe = self._probe_after_commit(normalized, plan.route)
                probes.append(probe)
                if probe.get("passed"):
                    self.indicators.probe_passed += 1
                else:
                    self.indicators.probe_failed += 1
            else:
                self.indicators.writes_rejected += 1
                if any("conflict" in reason for reason in receipt.reason_codes):
                    self.indicators.conflicts_detected += 1
        return {
            "ok": True,
            "receipts": receipts,
            "probes": probes,
            "indicators": self.indicators.to_dict(),
            "memory": self.memory_view(),
        }

    def memory_view(self) -> dict[str, Any]:
        open_n = self.db.query("SELECT n_id, content_text, state, updated_at FROM noumena ORDER BY updated_at DESC LIMIT 10")
        f_candidates = self.db.query(
            "SELECT atom_id, content_text, epistemic_status, support_count, created_at FROM memory_atoms WHERE epistemic_status='F_candidate' ORDER BY created_at DESC LIMIT 10"
        )
        crystals = self.db.query("SELECT crystal_id, invariant_text, lifecycle_state, created_at FROM crystals ORDER BY created_at DESC LIMIT 10")
        audits = self.db.query("SELECT plan_id, committed, reason_codes_json, object_ids_json, created_at FROM write_audit ORDER BY created_at DESC LIMIT 10")
        return {"open_noumena": open_n, "f_candidates": f_candidates, "crystals": crystals, "latest_write_receipts": self.last_receipts, "latest_write_audit": audits}

    def _select_model(self, models: list[str]) -> str | None:
        for preferred in self.preferred_models:
            for model in models:
                if model == preferred or model.startswith(preferred):
                    return model
        for model in models:
            if "gemma-4-e4b-it" in model:
                return model
        return None

    def _plan_for_thought_form(self, form: dict[str, Any], *, source_text: str) -> Any:
        kind = form["kind"]
        redacted_text = redact_text(str(form.get("text") or source_text or form.get("open_question") or ""))
        if kind == "secret_reference":
            question = form.get("open_question") or "What safe trace remains after secret redaction?"
            content = f"{question} Redacted trace: {redacted_text}"
            forced_route = "N"
        elif kind == "literal_artifact" and not form.get("artifact_pointer"):
            content = form.get("open_question") or f"Missing artifact pointer/evidence for literal artifact: {redacted_text}"
            forced_route = "N"
        elif kind == "skill_trace":
            content = redacted_text
            forced_route = "U"
        elif kind == "repair_pair":
            return self._repair_plan(form, source_text=source_text)
        else:
            content = form.get("open_question") if kind == "N" and form.get("open_question") else redacted_text
            forced_route = {"N": "N", "U": "U", "F_candidate": "F_candidate"}.get(kind, "N")
        raw = RawExperience(content=content, source="qvch_studio", speaker="operator", metadata={"source_text_preview": source_text[:240], "thought_form": form})
        event = normalize_experience(raw)
        safety = scan_event(event)
        draft = structure_event(event)
        atom_type = {"N": "noumenon", "U": "hypothesis", "F_candidate": "semantic_fact_candidate"}.get(forced_route, "noumenon")
        atom = MemoryAtomDraft(content=safety.redacted_content, atom_type=atom_type, route=forced_route, confidence=0.5, metadata={"thought_form_kind": kind})
        draft = StructuredDraft(new_id("draft"), event.event_id, form.get("text", "")[:160], [atom], structurer="gemma_thought_form")
        manas = ManasReview(new_id("manas"), draft.draft_id, True, forced_route, ["studio_thought_form_route", "llm_confidence_not_evidence"])
        validation = ValidationResult(new_id("val"), False, [], reason_codes=["no_non_llm_evidence", "llm_confidence_not_evidence"])
        return build_write_plan(event=event, draft=draft, manas_review=manas, safety_review=safety, validation=validation)

    def _repair_plan(self, form: dict[str, Any], *, source_text: str) -> Any:
        bad = form.get("bad_answer") or form.get("bad")
        corrected = form.get("corrected_answer") or form.get("improved_answer") or form.get("text")
        correction_source = form.get("correction_source") or "qvch_studio"
        failure = form.get("failure_reason") or form.get("why_uncertain") or "unspecified_failure"
        if not bad or not corrected:
            fallback = dict(form)
            fallback["kind"] = "N"
            fallback["open_question"] = form.get("open_question") or "Repair pair is missing bad_answer or corrected_answer fields."
            return self._plan_for_thought_form(fallback, source_text=source_text)
        event = normalize_experience(RawExperience(content=redact_text(str(corrected)), source="qvch_studio", speaker="operator", metadata={"thought_form": form}))
        safety = scan_event(event)
        return build_repair_plan(
            event=event,
            safety_review=safety,
            bad_answer=redact_text(str(bad)),
            failure_reason=redact_text(str(failure)),
            correction_source=redact_text(str(correction_source)),
            corrected_answer=redact_text(str(corrected)),
            evidence_refs=[],
        )

    def _count_committed_route(self, route: str, form: dict[str, Any]) -> None:
        if route == "N":
            self.indicators.N_open_created += 1
        elif route == "U":
            self.indicators.U_hypotheses_created += 1
        elif route == "F_candidate":
            self.indicators.F_candidates_created += 1
        elif route == "crystal":
            self.indicators.crystals_created += 1
        form_text = str(form)
        if form.get("kind") == "secret_reference" or "<REDACTED_SECRET>" in form_text or redact_text(form_text) != form_text:
            self.indicators.secrets_redacted += 1

    def _probe_after_commit(self, form: dict[str, Any], route: str) -> dict[str, Any]:
        query = str(form.get("open_question") or form.get("text") or "")[:120]
        if not query:
            query = str(form.get("kind"))
        expected = str(form.get("open_question") or form.get("text") or "")[:80]
        status = {"N": "N_open", "U": "U", "F_candidate": "F_candidate"}.get(route)
        probe = run_memory_probe(self.db, query=query, expected=expected, expected_status=status)
        return probe.__dict__


class StudioHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "QVCHStudio/0.1"

    @property
    def service(self) -> QVCHStudioService:
        return self.server.service  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/index.html"):
            self._send_file("index.html", "text/html; charset=utf-8")
        elif self.path.startswith("/static/app.js"):
            self._send_file("app.js", "application/javascript; charset=utf-8")
        elif self.path.startswith("/static/style.css"):
            self._send_file("style.css", "text/css; charset=utf-8")
        elif self.path.startswith("/api/health"):
            self._send_json(self.service.health())
        elif self.path.startswith("/api/memory"):
            self._send_json({"ok": True, "memory": self.service.memory_view(), "indicators": self.service.indicators.to_dict()})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        try:
            payload = self._read_json()
            if self.path.startswith("/api/analyze"):
                self._send_json(self.service.analyze(str(payload.get("text") or ""), commit=bool(payload.get("commit"))))
            elif self.path.startswith("/api/commit"):
                self._send_json(self.service.commit(list(payload.get("thought_forms") or []), source_text=str(payload.get("source_text") or "")))
            else:
                self.send_error(404)
        except Exception as exc:
            self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, status=500)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, name: str, content_type: str) -> None:
        path = Path(__file__).with_name("static") / name
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(*, host: str = "127.0.0.1", port: int = 8765, db_path: str | Path | None = None, lm_client: LMStudioClient | None = None) -> HTTPServer:
    service = QVCHStudioService(db_path=db_path, lm_client=lm_client)
    server = HTTPServer((host, port), StudioHTTPRequestHandler)
    server.service = service  # type: ignore[attr-defined]
    return server


def normalize_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    forms = [normalize_thought_form(item) for item in payload.get("thought_forms", []) if isinstance(item, dict)]
    return {
        "summary": str(payload.get("summary") or ""),
        "thought_forms": forms,
        "model_unknowns": [str(x) for x in payload.get("model_unknowns", [])],
        "do_not_crystallize": [str(x) for x in payload.get("do_not_crystallize", [])],
    }


def normalize_thought_form(item: dict[str, Any]) -> dict[str, Any]:
    kind = str(item.get("kind") or "N")
    if kind not in _KIND_VALUES:
        kind = "N"
    text = redact_text(str(item.get("text") or item.get("open_question") or ""))
    return {
        **item,
        "text": text,
        "kind": kind,
        "uncertainty": float(item.get("uncertainty") or 0.0),
        "why_uncertain": redact_text(str(item.get("why_uncertain") or "")),
        "open_question": redact_text(str(item.get("open_question") or "")),
        "working_assumption": redact_text(str(item.get("working_assumption") or "")),
        "evidence_needed": [redact_text(str(x)) for x in item.get("evidence_needed", [])],
        "safe_to_commit": bool(item.get("safe_to_commit", True)),
    }


def _empty_analysis() -> dict[str, Any]:
    return {"summary": "", "thought_forms": [], "model_unknowns": [], "do_not_crystallize": []}


def _loads_json_object(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))




