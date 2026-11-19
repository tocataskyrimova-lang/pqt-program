from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

_PROTECTED_TABLES = {
    "memory_events", "memory_atoms", "noumena", "noumenon_transitions", "hypotheses",
    "repair_pairs", "skill_candidates", "crystals", "evidence_refs", "write_plans",
    "write_audit", "probe_runs", "monitor_events", "atom_evidence",
    "memory_lifecycle_events", "repair_atom_links", "repair_crystal_links",
}
_LIFE1_STATE_TABLES = {
    "memory_atoms", "noumena", "repair_pairs", "skill_candidates", "crystals", "hypotheses",
}
_LIFE1_TABLES = {"memory_lifecycle_events", "repair_atom_links", "repair_crystal_links"}
_WRITE_RE = re.compile(r"^\s*(insert|update|delete|replace)\s+(?:or\s+\w+\s+)?(?:into\s+)?([\w_]+)", re.I)


class QVCHDatabase:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._write_authorized = 0
        self._transaction_depth = 0
        self._life1_guard_enabled = False
        self._life1_context_depth = 0
        self._life1_sandbox_path: Path | None = None
        self._life1_production_path: Path | None = None

    def init_schema(self) -> None:
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        self.conn.executescript(schema)
        self.conn.commit()

    @contextmanager
    def authorized_write(self) -> Iterator[None]:
        self._write_authorized += 1
        try:
            yield
        finally:
            self._write_authorized -= 1

    def enable_life1_sandbox_guard(self, *, sandbox_path: str | Path, production_path: str | Path) -> None:
        """Enable the LIFE1 no-mutation-without-event guard for a sandbox DB only.

        This guard is intentionally impossible to activate on the configured
        production path. It exists to verify Stage 2 sandbox invariants without
        changing production runtime behavior.
        """
        sandbox = Path(sandbox_path).resolve()
        production = Path(production_path).resolve()
        current = self.path.resolve()
        if current == production:
            raise PermissionError("LIFE1 sandbox guard cannot be enabled on production memory.db")
        if current != sandbox:
            raise PermissionError("LIFE1 sandbox guard can only be enabled on the configured sandbox DB path")
        self._life1_guard_enabled = True
        self._life1_sandbox_path = sandbox
        self._life1_production_path = production

    @contextmanager
    def life1_transition_context(self) -> Iterator[None]:
        self._life1_context_depth += 1
        try:
            yield
        finally:
            self._life1_context_depth -= 1

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self._transaction_depth:
            self._transaction_depth += 1
            try:
                yield
            finally:
                self._transaction_depth -= 1
            return
        self._transaction_depth = 1
        try:
            self.conn.execute("BEGIN")
            yield
        except Exception:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()
        finally:
            self._transaction_depth = 0

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        self._guard_sql(sql)
        cur = self.conn.execute(sql, params)
        if not self._transaction_depth:
            self.conn.commit()
        return cur.rowcount

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        row = self.conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def scalar(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        row = self.conn.execute(sql, params).fetchone()
        return row[0] if row else None

    def close(self) -> None:
        self.conn.close()

    def _guard_sql(self, sql: str) -> None:
        match = _WRITE_RE.match(sql)
        if not match:
            return
        table = match.group(2).strip('"`[]').lower()
        if table in _PROTECTED_TABLES and self._write_authorized <= 0:
            raise PermissionError(
                f"direct SQL write to protected table '{table}' is blocked; use MemoryWriteGateway or lifecycle APIs"
            )
        if self._life1_guard_enabled and table in _LIFE1_STATE_TABLES and self._life1_context_depth <= 0:
            raise PermissionError(
                f"LIFE1 sandbox guard blocked state-table mutation without lifecycle transition context: '{table}'"
            )
        if self._life1_guard_enabled and table in _LIFE1_TABLES and self._life1_context_depth <= 0:
            raise PermissionError(
                f"LIFE1 sandbox guard blocked witness-table mutation outside lifecycle transition context: '{table}'"
            )
