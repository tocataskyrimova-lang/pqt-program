"""DecisionSigner — HMAC-SHA256 envelope signing (brief 9.2).

A thin abstraction so the signing algorithm can later be swapped for Ed25519
without changing the Gateway contract. The key is never stored in the DB,
source, or logs; only ``key_id`` travels on the envelope.

Production fail-closed: if ``QVCH_MANAS_SIGNING_KEY`` is absent, signing is
refused. Tests use an ephemeral in-memory key.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

ALGORITHM = "HMAC-SHA256"
ENV_VAR = "QVCH_MANAS_SIGNING_KEY"


class MissingSigningKey(RuntimeError):
    """Raised when a production signing key is required but unavailable."""


def _decode_key(raw: str) -> bytes:
    raw = raw.strip()
    try:
        return bytes.fromhex(raw)
    except ValueError:
        # Fall back to UTF-8 (still must meet the length floor).
        return raw.encode("utf-8")


class DecisionSigner:
    def __init__(self, key: bytes, key_id: str, algorithm: str = ALGORITHM) -> None:
        if len(key) < 32:
            raise ValueError("signing key must be at least 32 random bytes")
        self._key = key
        self.key_id = key_id
        self.algorithm = algorithm

    @classmethod
    def from_env(cls, env_name: str = ENV_VAR) -> "DecisionSigner":
        raw = os.environ.get(env_name)
        if not raw:
            raise MissingSigningKey(
                f"{env_name} is not set; production commit is fail-closed"
            )
        return cls(_decode_key(raw), key_id="prod-1", algorithm=ALGORITHM)

    @classmethod
    def ephemeral(cls) -> "DecisionSigner":
        return cls(secrets.token_bytes(32), key_id="test-ephemeral", algorithm=ALGORITHM)

    def sign(self, canonical_bytes: bytes) -> str:
        return hmac.new(self._key, canonical_bytes, hashlib.sha256).hexdigest()

    def verify(self, canonical_bytes: bytes, signature: str) -> bool:
        expected = hmac.new(self._key, canonical_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


__all__ = ["DecisionSigner", "MissingSigningKey", "ALGORITHM", "ENV_VAR"]
