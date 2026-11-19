"""QVCH v4 Vinasha engine (brief 14.2).

Vinasha *removes the right to influence* — it does not erase. A degraded
revision loses automatic applicability and, where a previously-valid crystal
fails, a new N is opened asking why, linked to the degraded revision. The old
content and its entire causal history remain intact and auditable.
"""

from qvch_v4.vinasha.engine import Vinasha, DegradationResult, is_blocked

__all__ = ["Vinasha", "DegradationResult", "is_blocked"]
