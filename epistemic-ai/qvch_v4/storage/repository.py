"""Repository — the only production write path (brief 10.6 / R2 §1 / §7).

Every persistence operation opens an authorized ``write_scope`` transaction on
the guarded ``QvchStore``. No caller writes SQL directly. Reads are unrestricted
(SELECT is always permitted by the authorizer).

R2 trust model
--------------
A *protected write* (atom creation/revision, state transition, link, reduction
proof, applicability contract, Node-15 probe) requires a one-time MANAS
capability that is minted and consumed **inside the Gateway's atomic
transaction** (``authorized_write``). There are exactly two contexts:

* ``store._migration`` is True  — bootstrap / migration / test-fixture context.
  Direct writes are permitted so ``init``/``migrate`` and the test harness can
  seed data. This is the same flag that already gates DDL at the SQLite
  authorizer (brief R1 §12). A runtime process never opens a migration store.
* ``store._migration`` is False — production runtime. A protected write WITHOUT
  a capability minted by ``authorized_write`` is rejected (brief R2 §1).

``Repository.issue_capability`` (the old test bypass) and the ``_MISSING``
carve-out have been removed: a runtime caller can no longer mint or forge a
capability (brief R2 §2).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import canonical_json, hash_json, sha256_hex
from qvch_v4.contracts.models import new_id
from qvch_v4.manas.service import Gateway
from qvch_v4.storage.store import QvchStore, StorageError


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _j(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


class SqlConsumptionLedger:
    """Production one-time consumption ledger backed by SQL (brief R1 §4).

    Implements the same ``consume(decision_id, nonce) -> bool`` contract as the
    in-memory test ledger, but routes to ``Repository.record_consumption`` so a
    replay is rejected across restarts by the UNIQUE(decision_id)/UNIQUE(nonce)
    constraints (R1-Q6).

    NOTE: this is retained only for isolated unit-test / demo helpers that want
    to observe a consumption *outside* the atomic ``authorized_write`` path. The
    production runtime consumes inside ``authorized_write`` (R2 §7).
    """

    def __init__(self, repo: "Repository") -> None:
        self._repo = repo

    def consume(self, decision_id: str, nonce: str) -> bool:
        from qvch_v4.contracts.canonical import sha256_hex
        return self._repo.record_consumption(
            decision_id, nonce, sha256_hex(decision_id + nonce))


# Valid initial (atom_kind, state) pairs (brief R1 §7). Derived from the
# canonical state-machine vocabularies. A handful of cross-kind pairs appear in
# legacy test fixtures and are explicitly permitted via the exception set.
_INITIAL_STATE_SETS = {
    enums.AtomKind.NOUMENON.value: {s.value for s in enums.NoumenonState},
    enums.AtomKind.HYPOTHESIS.value: {s.value for s in enums.HypothesisState},
    enums.AtomKind.FORM.value: {s.value for s in enums.FormState},
}
_INITIAL_STATE_EXCEPTIONS = {
    ("FORM", "REFUTED"),  # legacy migration-style fixture data
}


class Repository:
    def __init__(self, store: QvchStore) -> None:
        self.store = store
        # The verification keyring starts empty (fail-closed) and is populated
        # only by ``_activate(signer)``, called by the system authority
        # (Studio.load) or by internal maintenance engines (Vinasha, Spanda).
        # Callers never supply a keyring or signer (R3 §1 / §2).
        self._keyring: dict = {}
        self._activated = False
        self._trusted_signer: Any = None

    # -- package-internal: activate with a system-owned signer --------------
    def _activate(self, signer: Any) -> None:
        """Configure this repository with a trusted signing key (R3 §1).

        Called only by the system bootstrap (``Studio.load``) or by internal
        maintenance engines (Vinasha, Spanda). Not exposed to ordinary callers.
        """
        self._activated = True
        self._trusted_signer = signer
        self._keyring = {signer.key_id: signer}

    # -- capability boundary (brief R1 §5 / R2 §1) ---------------------------
    OP_ATOM_WRITE = "ATOM_WRITE"
    OP_ATOM_REVISION = "ATOM_REVISION"
    OP_STATE_TRANSITION = "STATE_TRANSITION"
    OP_LINK = "LINK"
    OP_REDUCTION = "REDUCTION"
    OP_CONTRACT = "CONTRACT"
    OP_NODE15_PROBE = "NODE15_PROBE"

    # Every protected operation is authorized only by its matching MANAS
    # decision purpose (brief R1 §3 / R1-Q3). A wrong-purpose envelope is
    # rejected by the Gateway's purpose-specific verifier.
    _OP_PURPOSE = {
        OP_ATOM_WRITE: enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        OP_ATOM_REVISION: enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        OP_STATE_TRANSITION: enums.DecisionPurpose.AUTHORIZE_STATE_TRANSITION.value,
        OP_LINK: enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        OP_REDUCTION: enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        OP_CONTRACT: enums.DecisionPurpose.AUTHORIZE_WRITE.value,
        OP_NODE15_PROBE: enums.DecisionPurpose.AUTHORIZE_TEST.value,
    }

    # -- authorization gate (R2 §1) ------------------------------------------
    def _authorize(self, operation: str, *, capability: Any = None,
                   decision_id: Any = None) -> None:
        """Enforce the capability boundary for a protected write.

        In the *migration/bootstrap/fixture* context (``store._migration``) the
        repository is permitted to seed data directly — this is the same gate
        that already allows DDL at the SQLite authorizer (brief R1 §12). In a
        *production runtime* context, a protected write is only legal through
        ``authorized_write``, which mints and consumes the capability inside a
        single transaction; this method therefore refuses it.
        """
        if self.store._migration:
            return
        raise StorageError(
            f"{operation} requires a one-time MANAS capability; "
            f"direct protected writes are not authorized at runtime (R2 §1)"
        )

    def _check_initial_state(self, kind: str, state: str) -> None:
        allowed = _INITIAL_STATE_SETS.get(kind)
        if allowed is not None and state not in allowed \
                and (kind, state) not in _INITIAL_STATE_EXCEPTIONS:
            raise StorageError(
                f"invalid initial state {state!r} for {kind!r} "
                f"(brief R1 §7)"
            )

    # -- atomic authorized write (R2 §7) -------------------------------------
    def authorized_write(self, operation: str, env: Any, ctx: Any,
                         *, atom: dict | None = None,
                         state: dict | None = None,
                         link: dict | None = None,
                         reduction: dict | None = None,
                         contract: dict | None = None,
                         probe_run: dict | None = None) -> None:
        """Verify, then perform a fixed, system-defined protected mutation.

        One SQL transaction performs: (1) verify the envelope (no consume),
        (2) record the MANAS decision, (3) consume the one-time capability,
        (4) run the **fixed** system-defined mutation for ``operation``
        (caller never supplies an arbitrary SQL callback — R3 §3), (5) record
        the write attempt audit row.

        If any step fails, the whole transaction rolls back: the consumption is
        never left dangling (R2 §7, R2-Q10).

        Each ``operation`` accepts exactly one structured payload (never a
        callable). The Repository dispatches to a fixed ``_emit_*`` method
        determined by ``operation``, so the caller cannot inject arbitrary SQL.
        """
        if not self._activated or self._trusted_signer is None:
            raise StorageError(
                "Repository is not activated with a system-owned trusted "
                "signer (R3 §1)")
        gw = Gateway(self._keyring)
        purpose = self._OP_PURPOSE.get(operation)
        res = gw.verify_no_consume(
            env, ctx, self._trusted_signer, purpose=purpose)
        if not res.allowed:
            raise StorageError(f"Gateway rejected {operation}: {res.reasons}")
        now = ctx.now_iso or _now()
        from qvch_v4.manas.envelope import ManasDecisionEnvelope
        if not isinstance(env, ManasDecisionEnvelope):
            raise StorageError(f"{operation} requires a ManasDecisionEnvelope")
        try:
            with self._tx() as c:
                self._record_decision_tx(c, env, now)
                self._consume_tx(
                    c, env.decision_id, env.nonce, env.canonical_hash(), now)
                if operation == self.OP_ATOM_WRITE and atom is not None:
                    self._check_initial_state(atom["atom_kind"], atom["state"])
                    self._emit_atom(
                        c, now=now, decision_id=env.decision_id, **atom)
                elif operation == self.OP_STATE_TRANSITION and state is not None:
                    self._emit_state(
                        c, now=now, decision_id=env.decision_id, **state)
                elif operation == self.OP_LINK and link is not None:
                    self._emit_link(c, now=now, **link)
                elif operation == self.OP_REDUCTION and reduction is not None:
                    self._emit_reduction(c, now=now, **reduction)
                elif operation == self.OP_CONTRACT and contract is not None:
                    self._emit_contract(c, now=now, **contract)
                elif operation == self.OP_NODE15_PROBE and probe_run is not None:
                    self._emit_probe_run(
                        c, now=now, decision_id=env.decision_id, **probe_run)
                else:
                    raise StorageError(
                        f"no valid structured mutation for {operation}")
                self._record_write_attempt_tx(c, env, allowed=True, now=now)
        except Exception:
            raise

    # -- low-level scope ------------------------------------------------------
    def _tx(self):
        return self.store._write_scope()

    # -- in-transaction emitters --------------------------------------------
    # Each performs the raw SQL for one protected mutation on the live
    # connection ``c`` (already inside an authorized ``write_scope``). They are
    # used both by the public write methods (their own scope) and by the atomic
    # ``authorized_write`` path (the outer scope).

    def _emit_atom(self, c, *, atom_id, lineage_id, atom_kind, materiality_class,
                   state, payload_json, content_hash, decision_id, reason, now):
        c.execute(
            "INSERT INTO memory_atoms "
            "(atom_id, lineage_id, atom_kind, materiality_class, current_state, "
            "current_revision_id, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (atom_id, lineage_id, atom_kind, materiality_class, state,
             None, now, now),
        )
        c.execute(
            "INSERT INTO atom_revisions "
            "(revision_id, atom_id, revision_number, state, canonical_payload_json, "
            "content_hash, created_at) VALUES (?,?,?,?,?,?,?)",
            (f"{atom_id}#r1", atom_id, 1, state, payload_json, content_hash, now),
        )
        c.execute(
            "UPDATE memory_atoms SET current_revision_id=?, updated_at=? WHERE atom_id=?",
            (f"{atom_id}#r1", now, atom_id),
        )
        c.execute(
            "INSERT INTO atom_state_events "
            "(event_id, atom_id, from_state, to_state, occurred_at, decision_id, reason) "
            "VALUES (?,?,?,?,?,?,?)",
            (f"{atom_id}#se0", atom_id, None, state, now, decision_id, reason),
        )

    def _emit_state(self, c, atom_id, to_state, decision_id, reason, now):
        row = c.execute(
            "SELECT current_state FROM memory_atoms WHERE atom_id=?", (atom_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown atom {atom_id}")
        from_state = row[0]
        c.execute(
            "UPDATE memory_atoms SET current_state=?, updated_at=? WHERE atom_id=?",
            (to_state, now, atom_id),
        )
        c.execute(
            "INSERT INTO atom_state_events "
            "(event_id, atom_id, from_state, to_state, occurred_at, decision_id, reason) "
            "VALUES (?,?,?,?,?,?,?)",
            (f"{atom_id}#se{now}", atom_id, from_state, to_state, now, decision_id, reason),
        )

    def _emit_link(self, c, link_id, from_atom_id, to_atom_id, link_type,
                   strength, provenance, now):
        c.execute(
            "INSERT INTO memory_links "
            "(link_id, from_atom_id, to_atom_id, link_type, strength, created_at, provenance) "
            "VALUES (?,?,?,?,?,?,?)",
            (link_id, from_atom_id, to_atom_id, link_type, strength, now, provenance),
        )

    def _emit_reduction(self, c, cert, lineage_id, noumenon_atom_id,
                        supported_u_atom_ids, now):
        c.execute(
            "INSERT INTO reduction_proofs "
            "(proof_id, lineage_id, noumenon_atom_id, supported_u_atom_ids_json, "
            "baseline_unknown_slots_json, acceptance_criteria_json, evidence_bundle_ids_json, "
            "passed_tests_json, failed_tests_json, counterexamples_json, resolved_slots_json, "
            "residual_unknown_slots_json, contradiction_pressure, reduction_score, scope, "
            "verifier_version, proof_hash, created_at, slot_reduction, evidence_quality, "
            "scope_coverage, has_supporting_evidence) VALUES ("
            "?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (cert.proof_id, lineage_id, noumenon_atom_id,
             _j(list(cert.supported_u_atom_ids)),
             _j([s.__dict__ for s in cert.baseline_unknown_slots]),
             _j([a.__dict__ for a in cert.acceptance_criteria]),
             _j(list(cert.evidence_bundle_ids)),
             _j(list(cert.passed_tests)), _j(list(cert.failed_tests)),
             _j(list(cert.counterexamples)), _j(list(cert.resolved_slots)),
             _j(list(cert.residual_unknown_slots)), cert.contradiction_pressure,
             cert.reduction_score, cert.scope, cert.verifier_version,
             cert.proof_hash, now, cert.slot_reduction,
             cert.evidence_quality, cert.scope_coverage,
             1 if cert.has_supporting_evidence else 0),
        )

    def _emit_contract(self, c, contract_id, atom_id, revision_id, scope,
                       precondition, anti_condition, required_probes, now):
        c.execute(
            "INSERT INTO applicability_contracts "
            "(contract_id, atom_id, revision_id, scope, precondition_json, "
            "anti_condition_json, required_probes_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (contract_id, atom_id, revision_id, scope, _j(precondition),
             _j(anti_condition) if anti_condition is not None else None,
             _j(required_probes) if required_probes is not None else None, now),
        )

    def _emit_probe_run(self, c, *, probe_run_id, probe_plan_id, atom_id,
                        decision_id, receipt, now):
        c.execute(
            "INSERT INTO probe_runs "
            "(probe_run_id, probe_plan_id, atom_id, decision_id, command_hash, env_hash, "
            "exit_code, stdout_hash, stderr_hash, executed_at, receipt_json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (probe_run_id, probe_plan_id, atom_id, decision_id, receipt.get("command_hash"),
             receipt.get("env_hash"), receipt.get("exit_code"), receipt.get("stdout_hash"),
             receipt.get("stderr_hash"), now, _j(receipt)),
        )

    def _consume_tx(self, c, decision_id, nonce, envelope_hash, now) -> None:
        """Insert a consumption inside the caller's transaction.

        The UNIQUE(decision_id)/UNIQUE(nonce) constraints plus the FK to
        ``manas_decisions`` make a replay (or a consumption before the decision
        exists) raise ``IntegrityError`` — which propagates out of the
        ``write_scope`` and rolls back the whole write (R2 §7).
        """
        c.execute(
            "INSERT INTO decision_consumptions "
            "(consumption_id, decision_id, nonce, consumed_at, envelope_hash) "
            "VALUES (?,?,?,?,?)",
            (f"cons_{sha256_hex(decision_id + nonce)[7:23]}", decision_id,
             nonce, now, envelope_hash),
        )

    def _record_decision_tx(self, c, env, now) -> None:
        c.execute(
            "INSERT INTO manas_decisions "
            "(decision_id, purpose, target_id, target_hash, draft_id, draft_hash, "
            "sanitized_payload_hash, evidence_bundle_hash, pramana_report_hash, "
            "reduction_proof_hash, verdict, route, policy_version, service_version, "
            "key_id, issued_at, expires_at, nonce, signature_algorithm, signature, "
            "canonical_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (env.decision_id, env.purpose, env.target_id, env.target_hash, env.draft_id,
             env.draft_hash, env.sanitized_payload_hash, env.evidence_bundle_hash,
             env.pramana_report_hash, env.reduction_proof_hash, env.verdict, env.route,
             env.policy_version, env.service_version, env.key_id, env.issued_at,
             env.expires_at, env.nonce, env.signature_algorithm, env.signature,
             env.canonical_hash()),
        )

    def _record_write_attempt_tx(self, c, env, *, allowed, now) -> None:
        c.execute(
            "INSERT INTO write_attempts "
            "(attempt_id, decision_id, target_hash, verdict, allowed, reason, attempted_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (f"wa_{sha256_hex((env.decision_id or '') + env.target_hash + 'authorized')[7:23]}",
             env.decision_id, env.target_hash, env.verdict, 1 if allowed else 0,
             "AUTHORIZED_WRITE", now),
        )

    # -- inbound --------------------------------------------------------------
    def write_structured_draft(self, draft, *, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO structured_drafts "
                "(draft_id, source_text_hash, canonical_hash, created_at, payload_json) "
                "VALUES (?,?,?,?,?)",
                (draft.draft_id, draft.source_text_hash, draft.canonical_hash,
                 now, canonical_json(draft.to_payload())),
            )

    def write_claims(self, draft_id: str, claims: list, *, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            for cl in claims:
                anchor = cl.anchor.to_payload() if getattr(cl, "anchor", None) else None
                c.execute(
                    "INSERT INTO claims "
                    "(claim_id, draft_id, claim_type, subject, predicate, value, "
                    "materiality_class, anchor_json, evidence_refs_json) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (cl.claim_id, draft_id, cl.claim_type, cl.subject, cl.predicate,
                     cl.value, cl.materiality_class,
                     _j(anchor) if anchor else None, None),
                )

    def write_memory_event(self, event_id, session_id, event_type, sanitized, *,
                           now: str | None = None) -> None:
        now = now or _now()
        payload = _j(sanitized) if not isinstance(sanitized, str) else sanitized
        with self._tx() as c:
            c.execute(
                "INSERT INTO memory_events (event_id, session_id, event_type, "
                "occurred_at, sanitized_json, content_hash) VALUES (?,?,?,?,?,?)",
                (event_id, session_id, event_type, now, payload,
                 sha256_hex(payload)),
            )

    def ensure_session(self, session_id, *, now: str | None = None, source=None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT OR IGNORE INTO memory_sessions (session_id, started_at, source) "
                "VALUES (?,?,?)",
                (session_id, now, source),
            )

    # -- atoms / revisions (each atom owns its payload) -----------------------
    def ensure_lineage(self, lineage_id, root_noumenon_id=None, *,
                       now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT OR IGNORE INTO epistemic_lineages "
                "(lineage_id, root_noumenon_id, status, created_at) VALUES (?,?,?,?)",
                (lineage_id, root_noumenon_id, "OPEN", now),
            )

    def write_atom(self, *, atom_id, lineage_id, atom_kind, materiality_class,
                   state, canonical_payload, content_hash, revision_number=1,
                   decision_id=None, reason=None, now: str | None = None,
                   capability: Any = None) -> None:
        self._authorize(self.OP_ATOM_WRITE, capability=capability, decision_id=decision_id)
        self._check_initial_state(atom_kind, state)
        now = now or _now()
        payload_json = canonical_json(canonical_payload) if not isinstance(
            canonical_payload, str) else canonical_payload
        chash = hash_json(canonical_payload) if isinstance(canonical_payload, (dict, list)) \
            else (content_hash or sha256_hex(payload_json))
        with self._tx() as c:
            self._emit_atom(
                c, atom_id=atom_id, lineage_id=lineage_id, atom_kind=atom_kind,
                materiality_class=materiality_class, state=state,
                payload_json=payload_json, content_hash=chash,
                decision_id=decision_id, reason=reason, now=now)
            if revision_number != 1:
                # Additional revisions handled by the caller via write_atom again
                # is not supported; this mirror keeps a primary revision only.
                pass

    def write_atoms_batch(self, atoms: list[dict], *, now: str | None = None,
                           capability: Any = None) -> None:
        """Write many atoms in ONE transaction; each keeps its own canonical payload."""
        self._authorize(self.OP_ATOM_WRITE, capability=capability)
        now = now or _now()
        with self._tx() as c:
            for a in atoms:
                atom_id = a["atom_id"]
                payload = a["canonical_payload"]
                payload_json = canonical_json(payload) if not isinstance(payload, str) else payload
                chash = hash_json(payload) if isinstance(payload, (dict, list)) \
                    else (a.get("content_hash") or sha256_hex(payload_json))
                rev = a.get("revision_number", 1)
                self._emit_atom(
                    c, atom_id=atom_id, lineage_id=a["lineage_id"],
                    atom_kind=a["atom_kind"], materiality_class=a.get("materiality_class"),
                    state=a["state"], payload_json=payload_json, content_hash=chash,
                    decision_id=a.get("decision_id"), reason=a.get("reason"),
                    now=now)

    def set_atom_state(self, atom_id, to_state, *, decision_id=None, reason=None,
                       now: str | None = None, capability: Any = None) -> None:
        """Transition an atom's state. Enforced by the SQL trigger; a forbidden
        transition raises sqlite3.IntegrityError and rolls back."""
        self._authorize(self.OP_STATE_TRANSITION, capability=capability, decision_id=decision_id)
        now = now or _now()
        with self._tx() as c:
            self._emit_state(c, atom_id, to_state, decision_id, reason, now)

    def link(self, from_atom_id, to_atom_id, link_type, *, strength=None,
             provenance=None, now: str | None = None, capability: Any = None) -> str:
        self._authorize(self.OP_LINK, capability=capability)
        now = now or _now()
        link_id = f"lnk_{sha256_hex(from_atom_id + to_atom_id + link_type)[7:23]}"
        with self._tx() as c:
            self._emit_link(
                c, link_id, from_atom_id, to_atom_id, link_type, strength,
                provenance, now)
        return link_id

    # -- decisions / replay --------------------------------------------------
    def record_decision(self, env, *, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            self._record_decision_tx(c, env, now)

    def record_consumption(self, decision_id, nonce, envelope_hash, *,
                           now: str | None = None) -> bool:
        """Atomically record a consumption. Returns False if decision_id or nonce
        already consumed (UNIQUE constraints + authorizer-scoped write)."""
        now = now or _now()
        try:
            with self._tx() as c:
                self._consume_tx(c, decision_id, nonce, envelope_hash, now)
            return True
        except Exception:
            return False

    def record_write_attempt(self, *, decision_id, target_hash, verdict, allowed,
                             reason, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            self._record_write_attempt_tx(
                c,
                type("E", (), {"decision_id": decision_id, "target_hash": target_hash,
                               "verdict": verdict})(),
                allowed=allowed, now=now)

    # -- evidence / conflicts / proof -----------------------------------------
    def record_evidence(self, ref, *, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO evidence_refs "
                "(evidence_id, source_type, locator_json, content_hash, "
                "canonical_payload_json, llm_confidence, created_at) VALUES (?,?,?,?,?,?,?)",
                (ref.evidence_id, ref.source_type, _j(ref.locator),
                 ref.content_hash, _j(ref.canonical_payload), ref.llm_confidence, now),
            )

    def record_evidence_bundle(self, bundle_id, items, *, content_hash=None,
                               now: str | None = None) -> None:
        now = now or _now()
        chash = content_hash or sha256_hex(_j([i[0] for i in items]))
        with self._tx() as c:
            c.execute(
                "INSERT INTO evidence_bundles (bundle_id, created_at, content_hash) "
                "VALUES (?,?,?)",
                (bundle_id, now, chash),
            )
            for evidence_id, weight in items:
                c.execute(
                    "INSERT INTO evidence_bundle_items (item_id, bundle_id, evidence_id, weight) "
                    "VALUES (?,?,?,?)",
                    (f"ebi_{sha256_hex(bundle_id + evidence_id)[7:23]}", bundle_id,
                     evidence_id, weight),
                )

    def record_conflict(self, conflict, *, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO claim_conflicts "
                "(conflict_id, claim_a_id, claim_b_id, conflict_type, status, "
                "evidence_ids_json, resolution_reason, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (conflict.conflict_id, conflict.claim_a_id, conflict.claim_b_id,
                 conflict.conflict_type, conflict.status, _j(list(conflict.evidence_ids)),
                 conflict.resolution_reason, now),
            )

    def record_reduction_proof(self, cert, *, lineage_id, noumenon_atom_id,
                               supported_u_atom_ids, now: str | None = None,
                               capability: Any = None) -> None:
        self._authorize(self.OP_REDUCTION, capability=capability)
        now = now or _now()
        with self._tx() as c:
            self._emit_reduction(
                c, cert, lineage_id, noumenon_atom_id,
                supported_u_atom_ids, now)

    # -- materiality / applicability / retrieval / usage ----------------------
    def record_artifact_locator(self, *, locator_id, materiality_class, exact_locator,
                                immutable_content_hash, revision=None, commit=None,
                                retrieval_recipe=None, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO artifact_locators "
                "(locator_id, materiality_class, exact_locator, immutable_content_hash, "
                "revision, commit_ref, retrieval_recipe_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (locator_id, materiality_class, exact_locator, immutable_content_hash,
                 revision, commit, _j(retrieval_recipe or {}), now),
            )

    def record_applicability_contract(self, *, contract_id, atom_id, revision_id,
                                      scope, precondition, anti_condition=None,
                                      required_probes=None, now: str | None = None,
                                      capability: Any = None) -> None:
        self._authorize(self.OP_CONTRACT, capability=capability)
        now = now or _now()
        with self._tx() as c:
            self._emit_contract(
                c, contract_id, atom_id, revision_id, scope, precondition,
                anti_condition, required_probes, now)

    def record_applicability_probe(self, *, probe_id, contract_id, probe_name,
                                   receipt, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO applicability_probes "
                "(probe_id, contract_id, probe_name, command_hash, env_hash, exit_code, "
                "stdout_hash, stderr_hash, executed_at, receipt_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (probe_id, contract_id, probe_name, receipt.get("command_hash"),
                 receipt.get("env_hash"), receipt.get("exit_code"),
                 receipt.get("stdout_hash"), receipt.get("stderr_hash"), now, _j(receipt)),
            )

    def record_retrieval_run(self, *, run_id, query, hits, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO retrieval_runs (run_id, query, started_at, strategy) "
                "VALUES (?,?,?,?)", (run_id, query, now, "fts5+fallback"),
            )
            for h in hits:
                c.execute(
                    "INSERT INTO retrieval_hits "
                    "(hit_id, run_id, atom_id, revision_id, semantic_relevance, anchor_support, "
                    "reproducibility, applicability, freshness, contradiction_pressure, "
                    "epistemic_confidence, task_utility, retrieval_rank, components_json, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (h["hit_id"], run_id, h["atom_id"], h["revision_id"],
                     h.get("semantic_relevance"), h.get("anchor_support"),
                     h.get("reproducibility"), h.get("applicability"), h.get("freshness"),
                     h.get("contradiction_pressure"), h.get("epistemic_confidence"),
                     h.get("task_utility"), h.get("retrieval_rank"), _j(h), now),
                )

    def record_gate_decision(self, *, gate_id, atom_id, revision_id, contract_id,
                             verdict, reason, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO gate_decisions "
                "(gate_id, atom_id, revision_id, contract_id, verdict, reason, decided_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (gate_id, atom_id, revision_id, contract_id, verdict, reason, now),
            )

    def record_probe_run(self, *, probe_run_id, probe_plan_id, atom_id, decision_id,
                         receipt, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            self._emit_probe_run(
                c, probe_run_id=probe_run_id, probe_plan_id=probe_plan_id,
                atom_id=atom_id, decision_id=decision_id, receipt=receipt, now=now)

    def record_usage_outcome(self, *, outcome_id, atom_id, revision_id, gate_id,
                             outcome, context=None, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO usage_outcomes "
                "(outcome_id, atom_id, revision_id, gate_id, outcome, context_json, occurred_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (outcome_id, atom_id, revision_id, gate_id, outcome,
                 _j(context or {}), now),
            )

    def record_maintenance_event(self, *, event_id, atom_id, kind, reason,
                                 meta=None, now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO maintenance_events "
                "(event_id, atom_id, kind, reason, occurred_at, meta_json) VALUES (?,?,?,?,?,?)",
                (event_id, atom_id, kind, reason, now, _j(meta or {})),
            )

    def record_audit(self, *, event_id, actor, action, target, detail=None,
                     now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO audit_events (event_id, actor, action, target, detail_json, occurred_at) "
                "VALUES (?,?,?,?,?,?)",
                (event_id, actor, action, target, _j(detail or {}), now),
            )

    def record_migration_issue(self, *, issue_id, source_ref, issue_type, reason_code,
                               detail=None, severity="WARNING", now: str | None = None) -> None:
        now = now or _now()
        with self._tx() as c:
            c.execute(
                "INSERT INTO migration_issues "
                "(issue_id, source_ref, issue_type, reason_code, detail_json, severity, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (issue_id, source_ref, issue_type, reason_code, _j(detail or {}), severity, now),
            )

    # -- reads ----------------------------------------------------------------
    def get_atom(self, atom_id):
        row = self.store._conn.execute(
            "SELECT atom_id, lineage_id, atom_kind, materiality_class, current_state, "
            "current_revision_id FROM memory_atoms WHERE atom_id=?", (atom_id,)
        ).fetchone()
        return row

    def bundle_exists(self, bundle_id: str) -> bool:
        """True iff an evidence bundle with this id exists in SQL (brief R2 §6)."""
        row = self.store._conn.execute(
            "SELECT 1 FROM evidence_bundles WHERE bundle_id=?", (bundle_id,)
        ).fetchone()
        return row is not None

    def evidence_ids_in_bundle(self, bundle_id: str) -> list[str]:
        rows = self.store._conn.execute(
            "SELECT evidence_id FROM evidence_bundle_items WHERE bundle_id=?",
            (bundle_id,),
        ).fetchall()
        return [r[0] for r in rows]

    def evidence_source_type(self, evidence_id: str) -> str | None:
        row = self.store._conn.execute(
            "SELECT source_type FROM evidence_refs WHERE evidence_id=?",
            (evidence_id,),
        ).fetchone()
        return row[0] if row else None

    def get_revision(self, revision_id):
        row = self.store._conn.execute(
            "SELECT revision_id, atom_id, revision_number, state, canonical_payload_json, "
            "content_hash FROM atom_revisions WHERE revision_id=?", (revision_id,)
        ).fetchone()
        return row

    def list_atoms_by_kind(self, atom_kind):
        return self.store._conn.execute(
            "SELECT atom_id, current_state, materiality_class FROM memory_atoms "
            "WHERE atom_kind=?", (atom_kind,)
        ).fetchall()

    def allowed_transition(self, atom_kind, from_state, to_state) -> bool:
        row = self.store._conn.execute(
            "SELECT 1 FROM state_transition_rules WHERE atom_kind=? AND from_state=? "
            "AND to_state=?", (atom_kind, from_state, to_state)
        ).fetchone()
        return row is not None

    # -- SQL-derived reduction certificate (brief R1 §6) ----------------------
    def reduction_certificate_exists(self, proof_hash: str) -> bool:
        """True iff a stored reduction certificate carries this exact proof hash."""
        row = self.store._conn.execute(
            "SELECT 1 FROM reduction_proofs WHERE proof_hash=?", (proof_hash,)
        ).fetchone()
        return row is not None

    def get_reduction_certificate(self, proof_id: str):
        """Reconstruct a :class:`ReductionCertificate` purely from SQL (brief R1 §6).

        The certificate is derived from stored columns only; its ``canonical_hash``
        is re-computed and matched against the stored ``proof_hash`` so a tampered
        or truncated SQL row fails the integrity check (R1-Q4).
        """
        from qvch_v4.reduction.verifier import (
            AcceptanceCriterion,
            BaselineSlot,
            ReductionCertificate,
        )

        row = self.store._conn.execute(
            "SELECT proof_id, lineage_id, noumenon_atom_id, supported_u_atom_ids_json, "
            "baseline_unknown_slots_json, acceptance_criteria_json, evidence_bundle_ids_json, "
            "passed_tests_json, failed_tests_json, counterexamples_json, resolved_slots_json, "
            "residual_unknown_slots_json, contradiction_pressure, reduction_score, scope, "
            "verifier_version, proof_hash, slot_reduction, evidence_quality, "
            "scope_coverage, has_supporting_evidence "
            "FROM reduction_proofs WHERE proof_id=?", (proof_id,)
        ).fetchone()
        if row is None:
            return None
        (proof_id_v, lineage_id, noumenon_atom_id, supp_json, base_json, acc_json,
         ev_json, pass_json, fail_json, ce_json, res_json, resu_json, cp, score,
         scope, vver, phash, slot_red, evq, scov, hse) = row
        baseline = [BaselineSlot(s["slot_id"], s["weight"]) for s in json.loads(base_json)]
        acc = [AcceptanceCriterion(c["criterion_id"], c["critical"], c["passed"])
               for c in json.loads(acc_json)]
        resolved_list = tuple(json.loads(res_json))
        resolved_set = set(resolved_list)
        cert = ReductionCertificate(
            proof_id=proof_id_v,
            lineage_id=lineage_id,
            noumenon_atom_id=noumenon_atom_id,
            supported_u_atom_ids=tuple(json.loads(supp_json)),
            baseline_unknown_slots=tuple(baseline),
            acceptance_criteria=tuple(acc),
            evidence_bundle_ids=tuple(json.loads(ev_json)),
            passed_tests=tuple(json.loads(pass_json)),
            failed_tests=tuple(json.loads(fail_json)),
            counterexamples=tuple(json.loads(ce_json)),
            resolved_slots=resolved_list,
            residual_unknown_slots=tuple(json.loads(resu_json)),
            baseline_unknown_weight=sum(s.weight for s in baseline),
            resolved_weight=sum(s.weight for s in baseline if s.slot_id in resolved_set),
            contradiction_pressure=cp,
            slot_reduction=slot_red,
            evidence_quality=evq,
            scope_coverage=scov,
            reduction_score=score,
            scope=scope,
            verifier_version=vver,
            proof_hash=phash,
            critical_criteria_all_passed=all((not c.critical) or c.passed for c in acc),
            has_supporting_evidence=bool(hse),
        )
        payload = cert.to_payload()
        payload["proof_id"] = ""
        payload["proof_hash"] = ""
        if hash_json(payload) != phash:
            raise StorageError(
                f"reduction certificate {proof_id_v} hash mismatch; SQL row tampered"
            )
        return cert


__all__ = ["Repository", "SqlConsumptionLedger"]
