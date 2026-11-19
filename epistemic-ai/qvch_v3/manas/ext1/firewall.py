from __future__ import annotations

import ast
import re
import sys
from contextlib import AbstractContextManager
from pathlib import Path
from unittest.mock import patch

from .constants import TERMINAL_W0_BREACH

_FORBIDDEN_IMPORT_PREFIXES = ("qvch_v3.storage", "apps.qvch_studio")
_FORBIDDEN_CALL_NAMES = {
    "commit", "merge", "reject", "promote", "repair", "delete",
    "authorized_write", "build_write_plan", "build_repair_plan", "build_skill_plan",
    "transition_noumenon", "resolve_noumenon", "receive_guidance",
    "partially_resolve_noumenon", "revisit_noumenon",
}
_MUTATION_SQL = re.compile(r"\b(?:insert|update|delete|replace|drop|alter|create)\b", re.I)
_RUNTIME_METHODS = {
    "commit", "execute", "authorized_write", "init_schema", "resolve_noumenon",
    "receive_guidance", "partially_resolve_noumenon", "revisit_noumenon",
    "transition_noumenon", "build_write_plan", "build_repair_plan", "build_skill_plan",
}


class W0Breach(RuntimeError):
    status = TERMINAL_W0_BREACH


def static_firewall_scan(paths: list[Path]) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(_FORBIDDEN_IMPORT_PREFIXES):
                        findings.append({"file": str(path), "line": node.lineno, "kind": "forbidden_import", "value": alias.name})
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(_FORBIDDEN_IMPORT_PREFIXES):
                    findings.append({"file": str(path), "line": node.lineno, "kind": "forbidden_import", "value": module})
            elif isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    name = node.func.id
                if name in _FORBIDDEN_CALL_NAMES:
                    findings.append({"file": str(path), "line": node.lineno, "kind": "forbidden_call", "value": name})
                if name in {"execute", "executemany", "executescript", "query"}:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and _MUTATION_SQL.search(arg.value):
                            findings.append({"file": str(path), "line": node.lineno, "kind": "mutation_sql", "value": arg.value[:80]})
    return {"passed": not findings, "findings": findings, "files_scanned": [str(path) for path in paths]}


class RuntimeMutationFirewall(AbstractContextManager["RuntimeMutationFirewall"]):
    """Patch any already-loaded QVCH mutation capability to STOP on use."""

    def __init__(self) -> None:
        self.attempts: list[str] = []
        self._patches: list[object] = []

    def _blocked(self, qualified_name: str):
        def stop(*_args: object, **_kwargs: object) -> None:
            self.attempts.append(qualified_name)
            raise W0Breach(f"W0 STOP: mutation attempt through {qualified_name}")
        return stop

    def __enter__(self) -> "RuntimeMutationFirewall":
        for module_name, module in list(sys.modules.items()):
            if module is None or not (module_name.startswith("qvch_v3") or module_name.startswith("apps.qvch_studio")):
                continue
            for object_name in dir(module):
                obj = getattr(module, object_name, None)
                if object_name in _RUNTIME_METHODS and callable(obj):
                    qualified = f"{module_name}.{object_name}"
                    patcher = patch.object(module, object_name, self._blocked(qualified))
                    patcher.start()
                    self._patches.append(patcher)
                    continue
                if not isinstance(obj, type):
                    continue
                for method_name in _RUNTIME_METHODS:
                    if hasattr(obj, method_name):
                        qualified = f"{module_name}.{object_name}.{method_name}"
                        patcher = patch.object(obj, method_name, self._blocked(qualified))
                        patcher.start()
                        self._patches.append(patcher)
        return self

    def __exit__(self, *_exc: object) -> None:
        for patcher in reversed(self._patches):
            patcher.stop()  # type: ignore[attr-defined]


def feedback_check(source_paths: list[Path], witness_path: Path) -> dict[str, object]:
    witness = witness_path.resolve()
    collisions = [str(path) for path in source_paths if path.resolve() == witness]
    return {"passed": not collisions, "collisions": collisions, "self_confirm": bool(collisions)}
