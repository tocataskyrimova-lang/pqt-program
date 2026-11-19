"""QVCH v4 lifecycle policy (brief 14).

Versioned, frozen weights & thresholds for Spanda (viability scoring) and
Vinasha (loss-of-influence handling). Nothing here is a hard-coded magic
number scattered through the engine — the engine reads every coefficient from
a policy object so it can be versioned, audited, and replaced.
"""

from qvch_v4.policy.frozen import SpandaPolicy, VinashaPolicy

__all__ = ["SpandaPolicy", "VinashaPolicy"]
