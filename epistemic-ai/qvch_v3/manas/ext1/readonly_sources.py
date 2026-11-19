from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from .constants import DATA_AVAILABLE, DATA_EMPTY_DB, DATA_NO_DB, DATA_NO_EPISODES
from .contracts import EpisodeInput, SourceInspection


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite_uri(path: Path, *, immutable: bool) -> str:
    encoded = quote(path.resolve().as_posix(), safe="/:" )
    suffix = "mode=ro&immutable=1" if immutable else "mode=ro"
    return f"file:{encoded}?{suffix}"


class ReadOnlySQLite:
    """Narrow SELECT-only SQLite capability.

    Frozen snapshots are immutable. Live databases are opened read-only solely
    long enough to make a consistent SQLite backup; the resulting snapshot is
    then reopened immutable.
    """

    def __init__(self, path: Path, *, immutable: bool):
        self.path = path.resolve()
        self.immutable = bool(immutable)
        self.conn = sqlite3.connect(_sqlite_uri(self.path, immutable=immutable), uri=True)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA query_only=ON")

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        first = sql.lstrip().split(None, 1)[0].lower() if sql.strip() else ""
        if first not in {"select", "pragma", "with", "explain"}:
            raise PermissionError("EXT1 read-only source accepts SELECT/PRAGMA/WITH/EXPLAIN only")
        return [dict(row) for row in self.conn.execute(sql, tuple(params)).fetchall()]

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ReadOnlySQLite":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def snapshot_live_database(source: Path, output_dir: Path) -> tuple[Path, str]:
    """Create a consistent read-only snapshot without immutable access to WAL source."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    snapshot = output_dir / f"ext1_readonly_snapshot_{stamp}.sqlite"
    source_conn = sqlite3.connect(_sqlite_uri(source, immutable=False), uri=True)
    source_conn.execute("PRAGMA query_only=ON")
    destination = sqlite3.connect(snapshot)
    try:
        source_conn.backup(destination)
    finally:
        destination.close()
        source_conn.close()
    return snapshot, sha256_file(snapshot)


def _tables(db: ReadOnlySQLite) -> tuple[str, ...]:
    rows = db.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return tuple(row["name"] for row in rows if not str(row["name"]).startswith("sqlite_"))


def _episode_rows(db: ReadOnlySQLite, tables: tuple[str, ...]) -> list[dict[str, Any]]:
    if "memory_events" not in tables:
        return []
    return db.query(
        "SELECT event_id, occurred_at, content_text, source FROM memory_events "
        "WHERE event_id IS NOT NULL AND occurred_at IS NOT NULL AND content_text IS NOT NULL "
        "ORDER BY occurred_at, event_id"
    )


def inspect_and_load(
    source: Path,
    *,
    output_dir: Path,
    source_mode: str,
) -> tuple[SourceInspection, list[EpisodeInput], str]:
    """Inspect a frozen snapshot or copy a live DB, never creating the source."""
    source = source.resolve()
    if not source.exists():
        inspection = SourceInspection(
            DATA_NO_DB, str(source), None, None, None, (), 0, source_mode,
            ("source database does not exist; no placeholder was created",),
        )
        return inspection, [], ""

    source_hash = sha256_file(source)
    if source_mode == "frozen":
        snapshot = source
        snapshot_hash = source_hash
    elif source_mode == "live":
        snapshot, snapshot_hash = snapshot_live_database(source, output_dir)
    else:
        raise ValueError("source_mode must be 'frozen' or 'live'")

    with ReadOnlySQLite(snapshot, immutable=True) as db:
        tables = _tables(db)
        rows = _episode_rows(db, tables)
        schema_rows = db.query("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")
    schema_sql = "\n".join(str(row.get("sql") or "") for row in schema_rows)

    if not tables:
        data_status = DATA_EMPTY_DB
    elif not rows:
        data_status = DATA_NO_EPISODES
    else:
        data_status = DATA_AVAILABLE
    episodes = [
        EpisodeInput(
            episode_id=str(row["event_id"]),
            occurred_at=str(row["occurred_at"]),
            candidate_text=str(row["content_text"]),
            source_pointer=f"sqlite://memory_events/{row['event_id']}",
            metadata={"source_kind": str(row.get("source") or "unknown")},
        )
        for row in rows
    ]
    inspection = SourceInspection(
        data_status=data_status,
        source_path=str(source),
        source_sha256=source_hash,
        snapshot_path=str(snapshot),
        snapshot_sha256=snapshot_hash,
        table_names=tables,
        eligible_episode_count=len(episodes),
        source_mode=source_mode,
        notes=("live source copied through SQLite backup API" if source_mode == "live" else "frozen snapshot opened immutable",),
    )
    return inspection, episodes, schema_sql
