"""Node 15 Probe Executor (brief 13.3).

A ``ProbeExecutor`` runs *cheap* validation probes on behalf of the
Applicability Gate. It is deliberately narrow and safe:

- ``shell=False`` — only an argv list is ever executed; no shell, no string
  interpolation of untrusted input;
- an explicit environment *allowlist* (no secret env propagation);
- a temporary working directory;
- a hard timeout and output-size cap;
- network is disabled by *policy* (``network_allowed=False`` default). Real
  network isolation is the host sandbox's job; this flag is an honest
  declaration, not a simulated control;
- an immutable execution receipt (command/env hashes, exit code, stdout/stderr
  hashes, timestamps) is returned regardless of outcome.

Execution is forbidden without a valid ``AUTHORIZE_TEST`` MANAS envelope
(brief 13.3 / constraint #5). The Gate evaluates the receipt; the executor
never decides policy.

R3: The ProbeExecutor no longer accepts a caller-supplied ``keyring``. It
accepts an internal ``_trusted_signer`` set only by system code (Studio),
so an external caller cannot choose the verification key (R3 §2).
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from qvch_v4.contracts.canonical import canonical_json, sha256_hex
from qvch_v4.manas.envelope import ManasDecisionEnvelope, verify_envelope_signature
from qvch_v4.manas.signer import ALGORITHM, DecisionSigner
from qvch_v4.storage import QvchStore, Repository

OUTPUT_CAP_BYTES = 1 << 16  # 64 KiB


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ProbePlan:
    probe_name: str
    command: list[str]  # argv list — executed with shell=False
    timeout_s: float = 5.0
    env_allowlist: tuple[str, ...] = ()
    cwd: str | None = None
    output_cap_bytes: int = OUTPUT_CAP_BYTES
    network_allowed: bool = False
    required: bool = True
    target_id: str | None = None  # bound AUTHORIZE_TEST target (probe id/name)

    def command_hash(self) -> str:
        return sha256_hex(canonical_json(list(self.command)))

    def plan_hash(self) -> str:
        # Every execution-affecting field is bound into the hash so an
        # AUTHORIZE_TEST envelope authorizes exactly one plan and nothing an
        # attacker could vary post-approval (cwd, output cap, target id,
        # env allowlist) — brief R1 §9.
        return sha256_hex(canonical_json({
            "probe_name": self.probe_name,
            "command": list(self.command),
            "timeout_s": self.timeout_s,
            "env_allowlist": list(self.env_allowlist),
            "cwd": self.cwd,
            "output_cap_bytes": self.output_cap_bytes,
            "network_allowed": self.network_allowed,
            "required": self.required,
            "target_id": self.target_id,
        }))


@dataclass(frozen=True)
class ProbeReceipt:
    probe_name: str
    command_hash: str
    env_hash: str
    exit_code: int | None
    stdout_hash: str
    stderr_hash: str
    executed_at: str
    success: bool
    reason: str
    authorized: bool

    def to_payload(self) -> dict[str, Any]:
        return {
            "probe_name": self.probe_name,
            "command_hash": self.command_hash,
            "env_hash": self.env_hash,
            "exit_code": self.exit_code,
            "stdout_hash": self.stdout_hash,
            "stderr_hash": self.stderr_hash,
            "executed_at": self.executed_at,
            "success": self.success,
            "reason": self.reason,
            "authorized": self.authorized,
        }


class ProbeForbidden(Exception):
    """Raised when a probe is attempted without a valid AUTHORIZE_TEST."""


def _build_env(allowlist: tuple[str, ...]) -> dict[str, str]:
    # Explicit allowlist only — no wholesale inheritance of the caller env,
    # so secret variables are never propagated into the probe process.
    return {k: os.environ[k] for k in allowlist if k in os.environ}


def _cap(b: bytes, cap: int) -> bytes:
    return b[:cap]


def _hash(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


class ProbeExecutor:
    def __init__(self, store: QvchStore | None = None,
                 _trusted_signer: DecisionSigner | None = None) -> None:
        """Create a ProbeExecutor bound to the system's trusted signer.

        ``_trusted_signer`` is set only by internal system code (Studio).
        External callers cannot supply a keyring or signer (R3 §2).
        """
        self._store = store
        self._trusted_signer = _trusted_signer

    def _resolve_signer(self, envelope: ManasDecisionEnvelope,
                        signer: DecisionSigner | None) -> DecisionSigner | None:
        # R3: only the system's trusted signer is accepted.
        if self._trusted_signer is not None \
                and envelope.key_id == self._trusted_signer.key_id:
            return self._trusted_signer
        return None

    def _forbidden(self, plan: ProbePlan, reason: str) -> ProbeReceipt:
        # Brief 13.3: forbidden probe execution is recorded as an audit reason.
        if self._store is not None:
            Repository(self._store).record_audit(
                event_id=f"aud_probe_forbidden_{sha256_hex(plan.probe_name + reason)[:16]}",
                actor="node15", action="PROBE_EXECUTION_FORBIDDEN",
                target=plan.probe_name,
                detail={"reason": reason, "command_hash": plan.command_hash()},
            )
        return ProbeReceipt(
            probe_name=plan.probe_name, command_hash=plan.command_hash(),
            env_hash="sha256:0", exit_code=None, stdout_hash="sha256:0",
            stderr_hash="sha256:0", executed_at=_now_iso(), success=False,
            reason=reason, authorized=False,
        )

    def _authorize(self, plan: ProbePlan, envelope: ManasDecisionEnvelope | None,
                   signer: DecisionSigner | None,
                   now: str | None = None) -> str | None:
        """Return None if authorized, else a refusal reason.

        ``now`` is the logical clock against which expiry is judged. It defaults
        to the real wall clock in production so a short-TTL envelope cannot be
        replayed after it lapses; deterministic callers (E2E, tests) pass the
        same logical ``now`` the envelope was minted with so the check stays
        internally consistent (brief R1 §9)."""
        if envelope is None:
            return "missing AUTHORIZE_TEST envelope"
        if envelope.purpose != "AUTHORIZE_TEST":
            return f"envelope purpose is {envelope.purpose!r}, expected AUTHORIZE_TEST"
        # Only APPROVE is an execution authorization; QUARANTINE / REJECT are
        # records, never a licence to run a probe (brief R1 §3 / R1-Q2, R1-Q9).
        if envelope.verdict != "APPROVE":
            return f"envelope verdict is {envelope.verdict!r}, expected APPROVE"
        signer = self._resolve_signer(envelope, signer)
        if signer is None:
            return "no trusted key to verify envelope"
        if not verify_envelope_signature(envelope, signer):
            return "invalid envelope signature"
        if envelope.signature_algorithm != ALGORITHM:
            return "untrusted signature algorithm"
        # Envelope must be bound to this probe (target hash == plan hash) and
        # not expired.
        if envelope.target_hash != plan.plan_hash():
            return "envelope target_hash does not match probe plan"
        try:
            expires = datetime.fromisoformat(envelope.expires_at.replace("Z", "+00:00"))
            check = (datetime.fromisoformat(now.replace("Z", "+00:00"))
                     if now else datetime.now(timezone.utc))
            if check >= expires:
                return "expired AUTHORIZE_TEST envelope"
        except ValueError:
            return "malformed envelope timestamp"
        return None

    def execute(self, plan: ProbePlan, envelope: ManasDecisionEnvelope | None = None,
                *, signer: DecisionSigner | None = None,
                now: str | None = None) -> ProbeReceipt:
        refusal = self._authorize(plan, envelope, signer, now)
        if refusal is not None:
            return self._forbidden(plan, refusal)

        env = _build_env(plan.env_allowlist)
        env_hash = sha256_hex(canonical_json(dict(sorted(env.items()))))
        executed_at = _now_iso()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                proc = subprocess.run(
                    list(plan.command),  # shell=False, argv list only
                    shell=False,
                    cwd=plan.cwd or tmp,
                    env=env if env else {},
                    timeout=plan.timeout_s,
                    capture_output=True,
                    check=False,
                )
            stdout = _cap(proc.stdout or b"", plan.output_cap_bytes)
            stderr = _cap(proc.stderr or b"", plan.output_cap_bytes)
            return ProbeReceipt(
                probe_name=plan.probe_name, command_hash=plan.command_hash(),
                env_hash=env_hash, exit_code=proc.returncode,
                stdout_hash=_hash(stdout), stderr_hash=_hash(stderr),
                executed_at=executed_at, success=(proc.returncode == 0),
                reason="ok" if proc.returncode == 0 else f"exit_code={proc.returncode}",
                authorized=True,
            )
        except subprocess.TimeoutExpired:
            return ProbeReceipt(
                probe_name=plan.probe_name, command_hash=plan.command_hash(),
                env_hash=env_hash, exit_code=None, stdout_hash="sha256:0",
                stderr_hash="sha256:0", executed_at=executed_at, success=False,
                reason="timeout", authorized=True,
            )
        except (FileNotFoundError, OSError) as exc:
            return ProbeReceipt(
                probe_name=plan.probe_name, command_hash=plan.command_hash(),
                env_hash=env_hash, exit_code=None, stdout_hash="sha256:0",
                stderr_hash="sha256:0", executed_at=executed_at, success=False,
                reason=f"os_error:{type(exc).__name__}", authorized=True,
            )


__all__ = [
    "ProbePlan", "ProbeReceipt", "ProbeExecutor", "ProbeForbidden",
    "OUTPUT_CAP_BYTES",
]