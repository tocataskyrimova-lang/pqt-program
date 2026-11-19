"""Authorized SQLite store (brief 10.5 / 10.6).

The raw connection is private. All writes flow through the repository, which
enters a ``write_scope`` that flips the connection authorizer to allow writes.
Any statement executed outside that scope (a raw ``conn.execute``, a writable
CTE, DDL, or ``executescript``) is denied by ``sqlite3.Connection.set_authorizer``
— NOT by a regex guard (brief 10.6).

History tables are append-only: UPDATE/DELETE on them is denied by the authorizer
*and* by BEFORE triggers, so a forbidden transition can never leave a partial or
mutated history row.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.storage import schema

_SQLITE_OK = sqlite3.SQLITE_OK
_SQLITE_DENY = sqlite3.SQLITE_DENY

_DDL_ACTIONS = {
    sqlite3.SQLITE_CREATE_TABLE,
    sqlite3.SQLITE_DROP_TABLE,
    sqlite3.SQLITE_ALTER_TABLE,
    sqlite3.SQLITE_CREATE_INDEX,
    sqlite3.SQLITE_DROP_INDEX,
    sqlite3.SQLITE_CREATE_TRIGGER,
    sqlite3.SQLITE_DROP_TRIGGER,
    sqlite3.SQLITE_CREATE_VIEW,
    sqlite3.SQLITE_DROP_VIEW,
    sqlite3.SQLITE_CREATE_VTABLE,
    sqlite3.SQLITE_DROP_VTABLE,
}


class StorageError(RuntimeError):
    """Raised for storage-level policy violations."""


class QvchStore:
    def __init__(self, path: str, *, migration: bool = False) -> None:
        # Private raw connection — never exposed as public API.
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._allow_writes = False
        self._migration = migration
        self._conn.set_authorizer(self._authorize)

    # -- authorization boundary ------------------------------------------------
    def _authorize(self, action, arg1, arg2, db_name, source):
        # Reads, PRAGMAs, transactions and functions are always permitted.
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_PRAGMA,
                      sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_FUNCTION,
                      sqlite3.SQLITE_READ, sqlite3.SQLITE_SAVEPOINT,
                      sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
                      sqlite3.SQLITE_ANALYZE, sqlite3.SQLITE_REINDEX,
                      sqlite3.SQLITE_RECURSIVE):
            return _SQLITE_OK
        # DDL only allowed inside the migration context.
        if action in _DDL_ACTIONS:
            return _SQLITE_OK if self._migration else _SQLITE_DENY
        # Writes to protected tables only inside an authorized write scope.
        # Internal catalog tables (sqlite_master / sqlite_sequence / ...) are
        # always permitted so DDL and schema bookkeeping work.
        if isinstance(arg1, str) and arg1.startswith("sqlite_"):
            return _SQLITE_OK
        if action == sqlite3.SQLITE_INSERT:
            if arg1 in schema.PROTECTED_TABLES and self._allow_writes:
                return _SQLITE_OK
            return _SQLITE_DENY
        if action in (sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE):
            if isinstance(arg1, str) and arg1.startswith("sqlite_"):
                return _SQLITE_OK
            # Append-only history tables can never be mutated.
            if arg1 in schema.APPEND_ONLY_TABLES:
                return _SQLITE_DENY
            if arg1 in schema.PROTECTED_TABLES and self._allow_writes:
                return _SQLITE_OK
            return _SQLITE_DENY
        return _SQLITE_DENY

    def _write_scope(self):
        return _WriteScope(self)

    def raw_connection(self) -> sqlite3.Connection:
        """Diagnostic/escape access to the guarded connection. The authorizer
        stays attached and ``_allow_writes`` stays False, so any write here is
        denied — this is the surface the SQL-boundary tests exercise."""
        return self._conn

    # -- schema bootstrap (migration context) ---------------------------------
    def init_schema(self) -> None:
        ddl = schema.SCHEMA_DDL
        triggers = self._append_only_triggers()
        seed = self._transition_seed_sql()
        prev_migration, prev_allow = self._migration, self._allow_writes
        self._migration, self._allow_writes = True, True
        try:
            # executescript manages its own transaction; the authorizer permits
            # DDL only inside this migration scope.
            self._conn.executescript(ddl)
            self._conn.executescript(triggers)
            self._conn.executescript(seed)
        finally:
            self._migration, self._allow_writes = prev_migration, prev_allow

    def _append_only_triggers(self) -> str:
        parts = []
        for t in sorted(schema.APPEND_ONLY_TABLES):
            parts.append(
                f"CREATE TRIGGER IF NOT EXISTS no_update_{t} BEFORE UPDATE ON {t} "
                f"BEGIN SELECT RAISE(ABORT, 'history table {t} is append-only'); END;"
            )
            parts.append(
                f"CREATE TRIGGER IF NOT EXISTS no_delete_{t} BEFORE DELETE ON {t} "
                f"BEGIN SELECT RAISE(ABORT, 'history table {t} is append-only'); END;"
            )
        # Forbidden state transitions are rolled back at the SQL layer.
        parts.append(
            "CREATE TRIGGER IF NOT EXISTS atom_state_check BEFORE UPDATE ON memory_atoms "
            "WHEN old.current_state IS NOT new.current_state "
            "BEGIN "
            "SELECT CASE WHEN ("
            "SELECT 1 FROM state_transition_rules "
            "WHERE atom_kind = new.atom_kind AND from_state = old.current_state "
            "AND to_state = new.current_state) IS NULL "
            "THEN RAISE(ABORT, 'forbidden state transition') END; "
            "END;"
        )
        return "\n".join(parts)

    def _transition_seed_sql(self) -> str:
        rows = ", ".join(
            f"('rule_{i}', '{k}', '{f}', '{t}')"
            for i, (k, f, t) in enumerate(schema.STATE_TRANSITION_SEED)
        )
        return (
            "INSERT OR IGNORE INTO state_transition_rules "
            "(rule_id, atom_kind, from_state, to_state) VALUES " + rows + ";"
        )

    # -- integrity gates ------------------------------------------------------
    def integrity_ok(self) -> bool:
        rows = self._conn.execute("PRAGMA integrity_check").fetchall()
        return rows == [("ok",)]

    def foreign_keys_ok(self) -> bool:
        rows = self._conn.execute("PRAGMA foreign_key_check").fetchall()
        return len(rows) == 0

    def close(self) -> None:
        self._conn.close()


class _WriteScope:
    def __init__(self, store: QvchStore) -> None:
        self._store = store

    def __enter__(self) -> sqlite3.Connection:
        self._store._allow_writes = True
        self._store._conn.execute("BEGIN IMMEDIATE")
        return self._store._conn

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self._store._conn.commit()
            else:
                self._store._conn.rollback()
        finally:
            self._store._allow_writes = False


__all__ = ["QvchStore", "StorageError"]
