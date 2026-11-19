"""Studio orchestration over the v4 engines (brief 15.1 / R2 §3 / §4 / §7).

This is the *operational* surface the CLI and (if present) the Studio UI call.
It wires the engines together but never decides truth on its own: the only
authority to turn a candidate into a committed atom is a valid MANAS Decision
Envelope, verified by the Gateway. The Studio may propose; the authority
authorizes one exact transaction.

R2 hardening
------------
* The Studio holds a :class:`LocalManasAuthority` (brief R2 §3). It never holds
  a raw ``DecisionSigner`` for minting, and it never forwards a client-supplied
  verdict — the verdict is *derived* by the authority from the purpose (R2 §4).
* Every protected mutation travels through
  :meth:`Repository.authorized_write`, which verifies the envelope and consumes
  the one-time capability *inside a single SQL transaction* (R2 §7). A runtime
  Studio with no trusted keyring is fail-closed (R2 §5 / test #4).
* R3: the Studio is constructed via ``Studio.load(store)`` which reads the
  system signing key from ``QVCH_MANAS_SIGNING_KEY``. Public methods accept
  **no ``signer``, ``keyring``, or ``Gateway``** parameters — the caller cannot
  choose the trust root (R3 §1 / §2).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from qvch_v4.applicability import ApplicabilityGate, VERDICT_APPLY, VERDICT_CAUTIOUS_APPLY
from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import canonical_json, hash_json, sha256_hex
from qvch_v4.cvl import build_evidence, extract
from qvch_v4.forge import LocalForgeAdapter, QnufForge
from qvch_v4.manas.authority import DecisionRequest, LocalManasAuthority
from qvch_v4.manas.service import ConsumptionContext, Gateway
from qvch_v4.probes import ProbePlan, ProbeExecutor, ProbeReceipt
from qvch_v4.retrieval import EpistemicRetrievalPacket, retrieve
from qvch_v4.safety import classify_materiality, sanitize_and_hash
from qvch_v4.spanda import Spanda
from qvch_v4.storage import QvchStore, Repository
from qvch_v4.storage.store import StorageError
from qvch_v4.vinasha import Vinasha

# Client flags that must NEVER reach the sovereign write path.
_FORBIDDEN_CLIENT_FLAGS = ("approved", "safe_to_commit", "verdict", "approved_by")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _guard_no_client_approval(**kwargs: Any) -> None:
    bad = [k for k in kwargs if k in _FORBIDDEN_CLIENT_FLAGS]
    if bad:
        raise ValueError(
            f"Studio refuses client-supplied approval flags {bad}; "
            "the verifier verdict is derived by the system, not the client."
        )


class Studio:
    """Thin orchestration surface over the v4 engines."""

    def __init__(self, store: QvchStore) -> None:
        """Private constructor — use ``Studio.load(store)`` to create an
        activated Studio with the system signing key."""
        self._store = store
        self._repo = Repository(store)
        self._forge = QnufForge()
        self._adapter = LocalForgeAdapter()
        self._policy_version = "policy/1.0"
        self._service_version = "studio/1.0"
        # Fail-closed: no authority until .load() activates with the system key.
        self._authority: LocalManasAuthority | None = None
        self._activated = False

    @classmethod
    def load(cls, store: QvchStore) -> "Studio":
        """Create a fully-activated Studio with the system signing key.

        Reads ``QVCH_MANAS_SIGNING_KEY``, creates the sovereign authority,
        and activates the Repository's trusted keyring. Raises
        :class:`MissingSigningKey` if the env var is unset (fail-closed,
        R3 §1).
        """
        from qvch_v4.manas.signer import DecisionSigner
        studio = cls(store)
        signer = DecisionSigner.from_env()
        studio._repo._activate(signer)
        studio._authority = LocalManasAuthority(
            signer,
            policy_version=studio._policy_version,
            service_version=studio._service_version,
        )
        studio._activated = True
        return studio

    def _authority_for(self) -> LocalManasAuthority:
        if not self._activated or self._authority is None:
            raise StorageError(
                "Studio is fail-closed: not activated. Use Studio.load(store) "
                "with QVCH_MANAS_SIGNING_KEY set (R3 §1)")
        return self._authority

    # -- analysis (read-only) ------------------------------------------------
    def analyze(self, text: str) -> dict[str, Any]:
        event_id = f"ev_{uuid.uuid4().hex}"
        draft = self._forge.forge(self._adapter.build_raw(text), source_event_id=event_id)
        claims = extract(draft)
        claim_types = sorted({c.claim_type for c in claims})
        return {
            "source_event_id": event_id,
            "draft_id": draft.draft_id,
            "draft_hash": draft.canonical_hash,
            "forbidden_fields_detected": list(draft.forbidden_fields_detected),
            "noumenon_slots": [s.slot_id for s in draft.noumenon_slots],
            "claim_count": len(claims),
            "claim_types": claim_types,
        }

    # -- atomic authorized write helper (R2 §7 / R3 §3) ----------------------
    def _authorize_write(self, operation: str, *, purpose: str, target_id: str,
                         target_hash: str, route: str, now: str,
                         draft_hash: str | None = None,
                         reduction_proof_hash: str | None = None,
                         requires_reduction_proof: bool = False,
                         resolver=None,
                         atom: dict | None = None,
                         state: dict | None = None,
                         link: dict | None = None,
                         reduction: dict | None = None,
                         contract: dict | None = None,
                         probe_run: dict | None = None) -> None:
        """Mint a verdict-derived envelope via the sovereign authority and commit
        it atomically with its one-time consumption (R2 §4 / §7 / R3 §3).

        The mutation is passed as a **structured payload** (``atom``, ``state``,
        ``link``, etc.) — never a callable — so the caller cannot inject arbitrary
        SQL (R3 §3).
        """
        if not self._activated or self._authority is None:
            raise StorageError("Studio not activated with system signing key")
        auth = self._authority
        req = DecisionRequest(
            purpose=purpose, target_id=target_id, target_hash=target_hash,
            route=route, draft_hash=draft_hash,
            reduction_proof_hash=reduction_proof_hash,
            issued_at=now,
            expires_at=(datetime.fromisoformat(now) + timedelta(hours=1)).isoformat(),
        )
        # The authority *derives* the verdict; it never echoes a client verdict
        # (R2 §4). DecisionRequest has no ``verdict`` field.
        env = auth.decide(req)
        ctx = ConsumptionContext(
            observed_target_hash=target_hash, observed_route=route,
            policy_version=self._policy_version, now_iso=now,
            requires_reduction_proof=requires_reduction_proof,
            reduction_proof_resolver=resolver, ledger=None,
        )
        self._repo.authorized_write(
            operation, env, ctx,
            atom=atom, state=state, link=link,
            reduction=reduction, contract=contract,
            probe_run=probe_run,
        )

    # -- ingest (protected write via MANAS + Gateway) ------------------------
    def ingest_observation(self, text: str, *, now: str | None = None) -> str:
        """Ingest an observation + uncertainty as a NOUMENON atom.

        The atom is committed only under a valid ``AUTHORIZE_WRITE`` Decision
        Envelope whose target hash binds the exact canonical content, minted by
        the sovereign authority (verdict derived, never client-supplied).
        """
        _guard_no_client_approval()
        now = now or _now_iso()
        event_id = f"ev_{uuid.uuid4().hex}"
        draft = self._forge.forge(self._adapter.build_raw(text), source_event_id=event_id)
        claims = extract(draft)

        # Trusted Forge provenance: the canonical draft and its extracted hard
        # claims are system-recorded audit rows on the authorized ingest path.
        self._repo.write_structured_draft(draft)
        self._repo.write_claims(draft.draft_id, claims)

        # Materiality: deterministic detection is authoritative. Secrets are
        # sanitized to opaque markers before anything is stored (constraint #7);
        # if a secret survives the scan, ingestion is refused (brief R1 §10).
        sres = sanitize_and_hash(text)
        if not sres.clean:
            raise ValueError(
                "ingest rejected: a secret survived sanitization (constraint #7)")
        stored_text = sres.sanitized if isinstance(sres.sanitized, str) else text
        materiality = (
            enums.MaterialityClass.SECRET_REF.value if sres.first_findings
            else classify_materiality(text))

        atom_id = f"n_{uuid.uuid4().hex}"
        lineage_id = f"ln_{uuid.uuid4().hex}"
        self._repo.ensure_lineage(lineage_id, root_noumenon_id=atom_id, now=now)

        payload = {
            "kind": "NOUMENON",
            "observation": stored_text,
            "lineage_id": lineage_id,
            "draft_id": draft.draft_id,
            "claim_types": sorted({c.claim_type for c in claims}),
            "raised_unknown": bool(draft.noumenon_slots),
        }
        content_hash = hash_json(payload)

        ev = build_evidence(
            source_type=enums.EvidenceSourceType.SOURCE_ANCHOR.value,
            locator={"source_event_id": event_id, "text_hash": sha256_hex(text)},
            content=text[:512],
        )
        self._repo.record_evidence(ev, now=now)

        atom = {
            "atom_id": atom_id,
            "lineage_id": lineage_id,
            "atom_kind": "NOUMENON",
            "materiality_class": materiality,
            "state": "OPEN",
            "payload_json": canonical_json(payload),
            "content_hash": content_hash,
            "reason": "AUTHORIZE_WRITE",
        }
        self._authorize_write(
            self._repo.OP_ATOM_WRITE,
            purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
            target_id=atom_id, target_hash=content_hash,
            route=enums.Route.N.value, now=now,
            atom=atom,
        )
        return atom_id

    # -- production API: every protected write goes through a MANAS capability
    #    created and consumed inside the Gateway's atomic transaction (R2 §7).
    def commit_understanding(self, *, atom_id, lineage_id, payload, now,
                             materiality_class="SEMANTIC") -> str:
        """Create a HYPOTHESIS/U atom under an AUTHORIZE_WRITE capability."""
        content_hash = hash_json(payload)
        now = now or _now_iso()

        atom = {
            "atom_id": atom_id,
            "lineage_id": lineage_id,
            "atom_kind": "HYPOTHESIS",
            "materiality_class": materiality_class,
            "state": "PROPOSED",
            "payload_json": canonical_json(payload),
            "content_hash": content_hash,
            "reason": "AUTHORIZE_WRITE",
        }
        self._authorize_write(
            self._repo.OP_ATOM_WRITE,
            purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
            target_id=atom_id, target_hash=content_hash,
            route=enums.Route.U.value, now=now,
            atom=atom,
        )
        return atom_id

    def commit_form(self, *, atom_id, lineage_id, payload, now,
                    state="CANDIDATE",
                    reduction_proof_hash: str) -> str:
        """Create a FORM/F crystal under an AUTHORIZE_WRITE capability.

        ``reduction_proof_hash`` is **required** — R3 §4 mandates a valid
        proof-of-reduction for every FORM commitment. The Gateway resolves it
        against the SQL-stored reduction certificate (brief R1 §6 / R1-Q4).
        """
        content_hash = hash_json(payload)
        now = now or _now_iso()
        requires_proof = bool(reduction_proof_hash)
        resolver = self._repo.reduction_certificate_exists if requires_proof else None

        atom = {
            "atom_id": atom_id,
            "lineage_id": lineage_id,
            "atom_kind": "FORM",
            "materiality_class": "SEMANTIC",
            "state": state,
            "payload_json": canonical_json(payload),
            "content_hash": content_hash,
            "reason": "AUTHORIZE_WRITE",
        }
        self._authorize_write(
            self._repo.OP_ATOM_WRITE,
            purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
            target_id=atom_id, target_hash=content_hash,
            route=enums.Route.F_CANDIDATE.value,
            reduction_proof_hash=reduction_proof_hash,
            requires_reduction_proof=requires_proof, resolver=resolver,
            now=now,
            atom=atom,
        )
        return atom_id

    def transition(self, atom_id, to_state, *, now, reason=None,
                   route=None) -> None:
        """Authorize a state transition via AUTHORIZE_STATE_TRANSITION."""
        now = now or _now_iso()

        state = {
            "atom_id": atom_id,
            "to_state": to_state,
            "reason": reason or "AUTHORIZE_STATE_TRANSITION",
        }
        self._authorize_write(
            self._repo.OP_STATE_TRANSITION,
            purpose=enums.DecisionPurpose.AUTHORIZE_STATE_TRANSITION.value,
            target_id=atom_id, target_hash=atom_id,
            route=route or enums.Route.N.value, now=now,
            state=state,
        )

    def bind_link(self, from_atom_id, to_atom_id, link_type, *, now) -> str:
        """Create an atom link under an AUTHORIZE_WRITE capability."""
        now = now or _now_iso()
        target_hash = sha256_hex(f"{from_atom_id}->{to_atom_id}:{link_type}")
        link_id = f"lnk_{sha256_hex(from_atom_id + to_atom_id + link_type)[7:23]}"

        link = {
            "link_id": link_id,
            "from_atom_id": from_atom_id,
            "to_atom_id": to_atom_id,
            "link_type": link_type,
            "strength": None,
            "provenance": None,
        }
        self._authorize_write(
            self._repo.OP_LINK,
            purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
            target_id=f"{from_atom_id}->{to_atom_id}", target_hash=target_hash,
            route=enums.Route.N.value, now=now,
            link=link,
        )
        return link_id

    def record_reduction(self, cert, *, lineage_id, noumenon_atom_id,
                         supported_u_atom_ids, now) -> None:
        """Persist a SQL-grounded reduction certificate under AUTHORIZE_WRITE.

        §6 causal check: every U-atom and evidence bundle the certificate
        claims to rest on must actually exist in SQL, else the proof is not
        real (R2 test #7). The atomic write also requires the certificate to be
        content-addressed and stored verbatim (R1 §6)."""
        now = now or _now_iso()
        # §6 causal grounding: every U-atom and evidence bundle the
        # certificate claims to rest on must actually exist in SQL and
        # satisfy the causal constraints, else the proof is not real
        # (R2 test #7 / R2-Q8 / brief R2 §6).
        _supported_states = {
            enums.HypothesisState.SUPPORTED.value,
            enums.HypothesisState.PARTIALLY_SUPPORTED.value,
        }
        for u in supported_u_atom_ids:
            row = self._repo.get_atom(u)
            if row is None:
                raise ValueError(
                    f"reduction proof references unknown U-atom {u} (R2 §6)")
            if row[1] != lineage_id:
                raise ValueError(
                    f"U-atom {u} is not in reduction lineage {lineage_id} (R2 §6)")
            if row[2] != enums.AtomKind.HYPOTHESIS.value:
                raise ValueError(f"U-atom {u} is not a HYPOTHESIS (R2 §6)")
            if row[4] not in _supported_states:
                raise ValueError(
                    f"U-atom {u} in state {row[4]} cannot support an F (R2 §6)")
        for b in cert.evidence_bundle_ids:
            if not self._repo.bundle_exists(b):
                raise ValueError(
                    f"reduction proof references unknown evidence bundle {b} (R2 §6)")
            for ev_id in self._repo.evidence_ids_in_bundle(b):
                if self._repo.evidence_source_type(ev_id) == \
                        enums.EvidenceSourceType.INFERENCE.value:
                    raise ValueError(
                        f"evidence {ev_id} is LLM-inference only; "
                        f"cannot ground an F (R2 §6)")

        reduction = {
            "cert": cert,
            "lineage_id": lineage_id,
            "noumenon_atom_id": noumenon_atom_id,
            "supported_u_atom_ids": supported_u_atom_ids,
        }
        self._authorize_write(
            self._repo.OP_REDUCTION,
            purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
            target_id=cert.proof_id, target_hash=cert.proof_hash,
            route=enums.Route.CRYSTAL.value, now=now,
            reduction=reduction,
        )

    def declare_applicability(self, *, contract_id, atom_id, revision_id, scope,
                              precondition, anti_condition=None, required_probes=None,
                              now=None) -> None:
        """Declare an applicability contract under an AUTHORIZE_WRITE capability."""
        now = now or _now_iso()
        target_hash = sha256_hex(f"{atom_id}:{revision_id}:{contract_id}")

        contract = {
            "contract_id": contract_id,
            "atom_id": atom_id,
            "revision_id": revision_id,
            "scope": scope,
            "precondition": precondition,
            "anti_condition": anti_condition,
            "required_probes": required_probes,
        }
        self._authorize_write(
            self._repo.OP_CONTRACT,
            purpose=enums.DecisionPurpose.AUTHORIZE_WRITE.value,
            target_id=contract_id, target_hash=target_hash,
            route=enums.Route.F.value, now=now,
            contract=contract,
        )

    def run_node15_probe(self, plan, *, atom_id, now) -> object:
        """Execute a Node 15 probe under a one-time AUTHORIZE_TEST envelope and
        record the receipt (with the consumed decision id) atomically."""
        now = now or _now_iso()
        target_hash = plan.plan_hash()
        auth = self._authority_for()
        # Probe executor uses the system's trusted signer (R3 §2).
        executor = ProbeExecutor(self._store, _trusted_signer=auth.signer)
        env = auth.decide(DecisionRequest(
            purpose=enums.DecisionPurpose.AUTHORIZE_TEST.value,
            target_id=plan.probe_name, target_hash=target_hash,
            route=enums.Route.N.value, issued_at=now,
            expires_at=(datetime.fromisoformat(now) + timedelta(hours=1)).isoformat(),
        ))
        receipt = executor.execute(plan, env, now=now)
        probe_run_id = f"pr_{sha256_hex(plan.probe_name + now)[7:23]}"

        probe_run = {
            "probe_run_id": probe_run_id,
            "probe_plan_id": plan.probe_name,
            "atom_id": atom_id,
            "receipt": receipt.to_payload(),
        }
        self._authorize_write(
            self._repo.OP_NODE15_PROBE,
            purpose=enums.DecisionPurpose.AUTHORIZE_TEST.value,
            target_id=plan.probe_name, target_hash=target_hash,
            route=enums.Route.N.value, now=now,
            probe_run=probe_run,
        )
        return receipt

    # -- retrieval -----------------------------------------------------------
    def retrieve(self, query: str, *, task: str | None = None,
                 ctx: dict | None = None, limit: int = 10) -> list[EpistemicRetrievalPacket]:
        return retrieve(self._store, query, task=task, ctx=ctx, limit=limit)

    # -- crystal application (Applicability Gate) ----------------------------
    def apply_crystal(self, atom_id: str, revision_id: str, ctx: dict | None,
                      *, probe_plans: list[ProbePlan] | None = None,
                      envelope: Any = None,
                      now: str | None = None):
        """Run the Applicability Gate and bind the usage outcome.

        Returns ``(gate_decision, usage_outcome)``. A non-APPLY verdict is not
        forced; the outcome is recorded honestly (SUCCESS only when the gate
        actually passed)."""
        _guard_no_client_approval()
        now = now or _now_iso()
        auth = self._authority_for()
        gate = ApplicabilityGate(self._store, _trusted_signer=auth.signer)
        d = gate.evaluate(
            atom_id=atom_id, revision_id=revision_id, ctx=ctx,
            probe_plans=probe_plans or [], envelope=envelope, now=now)
        if d.verdict in (VERDICT_APPLY, VERDICT_CAUTIOUS_APPLY):
            outcome = "SUCCESS"
        elif d.verdict == "ESCALATE":
            outcome = "PARTIAL_SUCCESS"
        else:
            outcome = "CONTEXT_MISMATCH"
        gate.record_usage(
            atom_id=atom_id, revision_id=revision_id, gate_id=d.gate_id,
            outcome=outcome, now=now)
        return d, outcome

    # -- maintenance (Spanda + Vinasha) --------------------------------------
    def maintain(self, *, now: str | None = None) -> list[dict[str, Any]]:
        """Run Spanda viability transitions; where a previously-valid crystal
        degrades, let Vinasha open a new N asking why.

        Both engines own their own internal MANAS maintenance authority and
        commit their mutations atomically with a capability (brief R2 §8).

        Returns a list of per-atom transition summaries.
        """
        now = now or _now_iso()
        sp = Spanda(self._store)
        vin = Vinasha(self._store)
        out: list[dict[str, Any]] = []
        for atom_id, state, _mat in self._repo.list_atoms_by_kind("FORM"):
            arow = self._repo.get_atom(atom_id)
            rev = arow[5]  # current_revision_id
            if not rev:
                continue
            before = arow[4]
            res = sp.maintain(atom_id, rev, now=now)
            entry = {
                "atom_id": atom_id, "from_state": before,
                "recommended_state": res.recommended_state,
                "score": res.score, "applied": res.applied,
                "needs_decision": res.needs_decision,
            }
            if res.applied and res.recommended_state in ("STALE", "QUARANTINED"):
                dr = vin.handle_degradation(
                    atom_id, rev, reason=f"spanda:{res.recommended_state}", now=now)
                entry["new_n_atom_id"] = dr.new_n_atom_id
            out.append(entry)
        return out


__all__ = ["Studio", "ProbePlan", "ProbeReceipt"]