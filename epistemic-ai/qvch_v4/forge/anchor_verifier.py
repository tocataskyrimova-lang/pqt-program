"""Verbatim anchor verification (Postulate 0).

An EXTRACTED claim must reference an exact, hash-verified span of the source
text. The raw input stays ephemeral; only the quote hash (or, for secrets, a
non-reversible fingerprint) is retained.
"""

from __future__ import annotations

from qvch_v4.contracts.canonical import sha256_hex
from qvch_v4.contracts.models import VerbatimAnchor


class ForgeAnchorError(ValueError):
    """Anchor verification failed."""


def compute_quote_hash(quote: str) -> str:
    return sha256_hex(quote)


def verify_anchor(source_text: str, anchor: VerbatimAnchor) -> bool:
    if anchor.start_offset < 0 or anchor.end_offset > len(source_text):
        return False
    if anchor.start_offset >= anchor.end_offset:
        return False
    span = source_text[anchor.start_offset : anchor.end_offset]
    if anchor.redacted:
        # Secret span: only a non-reversible fingerprint may survive.
        if anchor.fingerprint is None:
            return False
        return anchor.fingerprint == sha256_hex(span)
    if anchor.quote is None:
        return False
    return anchor.quote == span and anchor.quote_hash == sha256_hex(span)
