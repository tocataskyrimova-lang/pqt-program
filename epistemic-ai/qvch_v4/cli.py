"""QVCH v4 command-line interface (brief 15.2).

Minimum commands:

    python -m qvch_v4.cli init      --db <path>
    python -m qvch_v4.cli migrate   --from <v3.db> --to <v4.db>
    python -m qvch_v4.cli reconcile --from <v3.db> --to <v4.db>
    python -m qvch_v4.cli ingest    --db <path> --text <text>
    python -m qvch_v4.cli retrieve  --db <path> --query <query>
    python -m qvch_v4.cli maintain  --db <path>

Runtime vs migration separation (brief R1 §12): only ``init`` (and the
``migrate``/``reconcile`` legacy path) open the store in the migration context
where DDL is permitted. ``ingest``/``retrieve``/``maintain`` open a *runtime*
store (``migration=False``) so arbitrary DDL is denied by the SQL authorizer
(R1-Q13); the DB must be initialised via ``init`` first.

No command bypasses MANAS/Gateway for a protected write: ``ingest`` commits an
N only under a valid ``AUTHORIZE_WRITE`` envelope minted by the sovereign
:class:`LocalManasAuthority`. The signing key is never caller-owned
(``DecisionSigner.ephemeral`` is not used in production) — R1 §2 / R1-Q1.
R3: CLI uses ``Studio.load(store)`` which reads the system signing key from
``QVCH_MANAS_SIGNING_KEY`` (R3 §1).
"""

from __future__ import annotations

import argparse
import sys

from qvch_v4.manas.authority import LocalManasAuthority
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.migration import run_migration
from qvch_v4.storage import QvchStore
from qvch_v4.studio import Studio


def _cmd_init(args) -> int:
    # Schema bootstrap is a migration context: DDL is only permitted here.
    store = QvchStore(args.db, migration=True)
    store.init_schema()
    print(f"init: schema ready at {args.db}")
    store.close()
    return 0


def _cmd_migrate(args) -> int:
    report = run_migration(args.frm, args.to)
    print(f"migrate: {report.mapped} mapped, {report.unmapped} "
          f"{report.redactions} redactions, {report.critical_issues} critical")
    return 0 if report.critical_issues == 0 else 2


def _cmd_reconcile(args) -> int:
    report = run_migration(args.frm, args.to)
    _print_safe(report.to_markdown())
    _print_safe(f"can_cutover={report.can_cutover()}")
    return 0 if report.can_cutover() else 2


def _print_safe(text: str) -> None:
    """Print, tolerating a non-UTF-8 console (e.g. Windows cp1251)."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def _cmd_ingest(args) -> int:
    # Runtime store: no DDL outside the explicit migration path (brief R1 §12 /
    # R1-Q13). The DB must already be initialised via `init`.
    store = QvchStore(args.db, migration=False)
    try:
        studio = Studio.load(store)
        atom_id = studio.ingest_observation(args.text)
        print(f"ingest: created {atom_id}")
    finally:
        store.close()
    return 0


def _cmd_retrieve(args) -> int:
    store = QvchStore(args.db, migration=False)
    try:
        packets = Studio(store).retrieve(args.query, limit=args.limit)
        for p in packets:
            print(f"{p.atom_id}\t{p.revision_id}\tkind={p.atom_kind}\t"
                  f"state={p.lifecycle_status}\tconf={p.epistemic_confidence:.3f}\t"
                  f"relevance={p.semantic_relevance:.3f}")
    finally:
        store.close()
    return 0


def _cmd_maintain(args) -> int:
    store = QvchStore(args.db, migration=False)
    try:
        results = Studio.load(store).maintain()
        if not results:
            print("maintain: no FORM atoms to assess")
        for r in results:
            tag = "applied" if r["applied"] else ("needs-decision" if r["needs_decision"] else "no-change")
            line = (f"maintain: {r['atom_id']} {r['from_state']} -> "
                    f"{r['recommended_state']} (score={r['score']:.3f}) [{tag}]")
            if r.get("new_n_atom_id"):
                line += f" new_n={r['new_n_atom_id']}"
            print(line)
    finally:
        store.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qvch_v4.cli", description="QVCH v4 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--db", required=True)
    p.set_defaults(func=_cmd_init)

    p = sub.add_parser("migrate")
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--to", required=True)
    p.set_defaults(func=_cmd_migrate)

    p = sub.add_parser("reconcile")
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--to", required=True)
    p.set_defaults(func=_cmd_reconcile)

    p = sub.add_parser("ingest")
    p.add_argument("--db", required=True)
    p.add_argument("--text", required=True)
    p.set_defaults(func=_cmd_ingest)

    p = sub.add_parser("retrieve")
    p.add_argument("--db", required=True)
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=_cmd_retrieve)

    p = sub.add_parser("maintain")
    p.add_argument("--db", required=True)
    p.set_defaults(func=_cmd_maintain)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())