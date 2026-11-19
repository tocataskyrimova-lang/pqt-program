"""Vinasha — loss of automatic influence without loss of history (brief 14.2).

Vinasha is invoked when a previously-valid crystal degrades (a probe that used
to pass now fails, or its environment drifts). It:
  * removes the revision's right to auto-apply (state in the non-applicable
    set — the Applicability Gate already refuses those); and
  * opens a new N asking *why* applicability was lost, linked to the degraded
    revision by ''DERIVED_FROM''.

It never deletes the old content, revisions, state events, or probes. Those
stay queryable for audit indefinitely.

R3: The maintenance engine activates its Repository internally so callers
cannot supply a keyring or pass a mutate callback (R3 §2 / §3).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import canonical_json, sha256_hex
from qvch_v4.manas.authority import DecisionRequest, LocalManasAuthority
from qvch_v4.manas.service import ConsumptionContext
from qvch_v4.manas.signer import DecisionSigner
from qvch_v4.policy.frozen import VinashaPolicy
from qvch_v4.storage import QvchStore, Repository


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_blocked(state: str, policy: VinashaPolicy | None = None) -> bool:
    """A revision in a non-applicable state may not be auto-applied."""
    policy = policy or VinashaPolicy.default()
    return state in policy.non_applicable_states


@dataclass(frozen=True)
class DegradationResult:
    new_n_atom_id: str
    degraded_atom_id: str
    degraded_revision_id: str
    lineage_id: str
    link_id: str
    reason: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "new_n_atom_id": self.new_n_atom_id,
            "degraded_atom_id": self.degraded_atom_id,
            "degraded_revision_id": self.degraded_revision_id,
            "lineage_id": self.lineage_id,
            "link_id": self.link_id,
            "reason": self.reason,
        }


class Vinasha:
    def __init__(self, store: QvchStore, *,
                 policy: VinashaPolicy | None = None) -> None:
        self._store = store
        self._policy = policy or VinashaPolicy.default()
        self._signer = DecisionSigner.ephemeral()
        self._authority = LocalManasAuthority(
            self._signer, policy_version="policy/vinasha/1.0",
            service_version="vinasha/1.0")
        self._repo = Repository(store)
        self._repo._activate(self._signer)

    def blocked(self, atom_id: str) -> bool:
        arow = self._repo.get_atom(atom_id)
        if arow is None:
            raise ValueError(f"unknown atom {atom_id}")
        return is_blocked(arow[4], self._policy)

    def _maint_write(self, operation: str, *, target_id: str, target_hash: str,
                     route: str, now: str,
                     atom: dict | None = None,
                     link: dict | None = None) -> None:
        purpose = (enums.DecisionPurpose.AUTHORIZE_WRITE.value
                   if operation in (self._repo.OP_ATOM_WRITE, self._repo.OP_LINK)
                   else enums.DecisionPurpose.AUTHORIZE_STATE_TRANSITION.value)
        req = DecisionRequest(
            purpose=purpose,
            target_id=target_id, target_hash=target_hash, route=route,
            issued_at=now,
            expires_at=(datetime.fromisoformat(now) + timedelta(hours=1)).isoformat(),
        )
        env = self._authority.decide(req)
        ctx = ConsumptionContext(
            observed_target_hash=target_hash, observed_route=route,
            policy_version="policy/vinasha/1.0", now_iso=now, ledger=None)
        self._repo.authorized_write(
            operation, env, ctx, atom=atom, link=link)

    def handle_degradation(self, atom_id: str, revision_id: str, *,
                           reason: str, now: str | None = None) -> DegradationResult:
        now = now or _now_iso()
        arow = self._repo.get_atom(atom_id)
        if arow is None:
            raise ValueError(f"unknown atom {atom_id}")
        lineage_id = arow[1]

        self._repo.record_maintenance_event(
            event_id=f"me_{uuid.uuid4().hex}", atom_id=atom_id,
            kind="VINASHA_DEGRADATION", reason=reason, now=now)

        new_n_id = f"n_{uuid.uuid4().hex}"
        payload = {
            "question": self._policy.new_n_question,
            "derived_from": atom_id,
            "revision_id": revision_id,
        }
        content_hash = sha256_hex(canonical_json(payload))

        atom = {
            "atom_id": new_n_id,
            "lineage_id": lineage_id,
            "atom_kind": "NOUMENON",
            "materiality_class": "SEMANTIC",
            "state": "OPEN",
            "payload_json": canonical_json(payload),
            "content_hash": content_hash,
            "reason": reason,
        }
        self._maint_write(
            self._repo.OP_ATOM_WRITE, target_id=new_n_id,
            target_hash=content_hash,
            route=enums.Route.N.value, now=now,
            atom=atom)

        link_target = sha256_hex(
            f"{new_n_id}->{atom_id}:{self._policy.degradation_link_type}")
        link_id = f"lnk_{sha256_hex(new_n_id + atom_id + self._policy.degradation_link_type)[7:23]}"

        link = {
            "link_id": link_id,
            "from_atom_id": new_n_id,
            "to_atom_id": atom_id,
            "link_type": self._policy.degradation_link_type,
            "strength": None,
            "provenance": reason,
        }
        self._maint_write(
            self._repo.OP_LINK, target_id=f"{new_n_id}->{atom_id}",
            target_hash=link_target, route=enums.Route.N.value, now=now,
            link=link)

        return DegradationResult(
            new_n_atom_id=new_n_id, degraded_atom_id=atom_id,
            degraded_revision_id=revision_id, lineage_id=lineage_id,
            link_id=link_id, reason=reason,
        )

__all__ = ["Vinasha", "DegradationResult", "is_blocked"]
