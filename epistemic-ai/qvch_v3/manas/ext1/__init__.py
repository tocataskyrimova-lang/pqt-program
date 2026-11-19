"""EXT1-DRY read-only PQT witness for QVCH/MANAS.

This package is intentionally outside every QVCH persistence path.  Its public
surface is limited to immutable inputs, deterministic diagnostics, and the
historical-only witness sidecar.
"""

from .constants import BANNER, CLAIM_BOUNDARY

__all__ = ["BANNER", "CLAIM_BOUNDARY"]
