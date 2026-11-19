"""Reconciliation report for the v3→v4 shadow migration (brief 11.3).

The report is fully deterministic: given the same source DB, two migrations
produce byte-identical canonical summaries (row counts, hashes, tallies).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


def _canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass
class ReconciliationReport:
    source_db_path: str
    source_db_hash: str
    migration_version: str
    legacy_counts: dict[str, int] = field(default_factory=dict)
    v4_counts: dict[str, int] = field(default_factory=dict)
    mapped: int = 0
    unmapped: int = 0
    quarantined: int = 0
    duplicate_groups: int = 0
    orphan_legacy_refs: int = 0
    redactions: int = 0
    migration_issues: int = 0
    critical_issues: int = 0
    fk_ok: bool = False
    integrity_ok: bool = False
    deterministic_rerun_match: bool = False
    notes: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "source_db_path": self.source_db_path,
            "source_db_hash": self.source_db_hash,
            "migration_version": self.migration_version,
            "legacy_counts": self.legacy_counts,
            "v4_counts": self.v4_counts,
            "mapped": self.mapped,
            "unmapped": self.unmapped,
            "quarantined": self.quarantined,
            "duplicate_groups": self.duplicate_groups,
            "orphan_legacy_refs": self.orphan_legacy_refs,
            "redactions": self.redactions,
            "migration_issues": self.migration_issues,
            "critical_issues": self.critical_issues,
            "fk_ok": self.fk_ok,
            "integrity_ok": self.integrity_ok,
            "deterministic_rerun_match": self.deterministic_rerun_match,
            "notes": self.notes,
        }

    def canonical_summary(self) -> str:
        """Deterministic fingerprint of the mapping outcome — excludes the
        source path so two runs over the same bytes compare equal."""
        summary = {
            "source_db_hash": self.source_db_hash,
            "migration_version": self.migration_version,
            "legacy_counts": self.legacy_counts,
            "v4_counts": self.v4_counts,
            "mapped": self.mapped,
            "unmapped": self.unmapped,
            "quarantined": self.quarantined,
            "duplicate_groups": self.duplicate_groups,
            "orphan_legacy_refs": self.orphan_legacy_refs,
            "redactions": self.redactions,
            "migration_issues": self.migration_issues,
            "critical_issues": self.critical_issues,
            "fk_ok": self.fk_ok,
            "integrity_ok": self.integrity_ok,
        }
        return _canon(summary)

    def can_cutover(self) -> bool:
        """Gate P0-G: controlled cutover is forbidden while any critical
        migration issue remains unresolved (brief 11)."""
        return self.critical_issues == 0

    def to_markdown(self) -> str:
        lines = [
            "# QVCH v3 → v4 Migration Reconciliation Report",
            "",
            f"- **source_db**: `{self.source_db_path}`",
            f"- **source_db_hash**: `{self.source_db_hash}`",
            f"- **migration_version**: `{self.migration_version}`",
            f"- **deterministic_rerun_match**: {self.deterministic_rerun_match}",
            f"- **fk_ok**: {self.fk_ok} | **integrity_ok**: {self.integrity_ok}",
            "",
            "## Row counts (AS-IS, v3)",
            "",
        ]
        for k, v in sorted(self.legacy_counts.items()):
            lines.append(f"- {k}: {v}")
        lines += ["", "## Row counts (v4)", ""]
        for k, v in sorted(self.v4_counts.items()):
            lines.append(f"- {k}: {v}")
        lines += [
            "",
            "## Outcome",
            "",
            f"- mapped: {self.mapped}",
            f"- unmapped: {self.unmapped}",
            f"- quarantined: {self.quarantined}",
            f"- duplicate_groups: {self.duplicate_groups}",
            f"- orphan_legacy_refs: {self.orphan_legacy_refs}",
            f"- redactions: {self.redactions}",
            f"- migration_issues: {self.migration_issues} (critical: {self.critical_issues})",
            "",
        ]
        if self.notes:
            lines.append("## Notes")
            lines.append("")
            for n in self.notes:
                lines.append(f"- {n}")
            lines.append("")
        return "\n".join(lines)
