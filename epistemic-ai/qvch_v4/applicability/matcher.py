"""Typed applicability precondition matcher (brief 13.1).

No arbitrary Python or ``eval`` predicates are permitted. Every precondition is
a small, enumerable, *safe* matcher evaluated against an explicit environment
context. Used by P0-H (applicability component) and extended by P0-I (the full
Applicability Gate: preconditions + anti-conditions + Node 15 probes).

Supported types: exact, platform, semver_range, dep_version, content_hash,
command, env_present (name only — value is never disclosed), feature_flag,
schema_version.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PreconditionContext:
    os_platform: str = "unknown"
    env_present: frozenset[str] = field(default_factory=frozenset)
    command_available: frozenset[str] = field(default_factory=frozenset)
    feature_flags: frozenset[str] = field(default_factory=frozenset)
    versions: dict[str, str] = field(default_factory=dict)
    file_hashes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def build(cls, *, os_platform: str = "unknown", env_present: set[str] | None = None,
              command_available: set[str] | None = None, feature_flags: set[str] | None = None,
              versions: dict[str, str] | None = None, file_hashes: dict[str, str] | None = None) -> "PreconditionContext":
        return cls(
            os_platform=os_platform,
            env_present=frozenset(env_present or set()),
            command_available=frozenset(command_available or set()),
            feature_flags=frozenset(feature_flags or set()),
            versions=dict(versions or {}),
            file_hashes=dict(file_hashes or {}),
        )


def _parse_semver(v: str) -> tuple[int, ...]:
    nums = []
    for part in v.strip().lstrip("v").split("."):
        num = ""
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break
        nums.append(int(num) if num else 0)
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def semver_satisfies(version: str, rng: str) -> bool:
    """Minimal deterministic semver range check: comma-separated comparisons
    such as '>=3.10,<4' or '==1.2.3'."""
    target = _parse_semver(version)
    for clause in rng.split(","):
        clause = clause.strip()
        if not clause:
            continue
        for op in (">=", "<=", "==", ">", "<", "!="):
            if clause.startswith(op):
                operand = clause[len(op):].strip()
                bound = _parse_semver(operand)
                break
        else:
            op, bound = "==", _parse_semver(clause)
        if op == ">=" and not (target >= bound):
            return False
        if op == "<=" and not (target <= bound):
            return False
        if op == ">" and not (target > bound):
            return False
        if op == "<" and not (target < bound):
            return False
        if op == "==" and not (target == bound):
            return False
        if op == "!=" and not (target != bound):
            return False
    return True


def _match_one(precond: dict[str, Any], ctx: PreconditionContext) -> bool:
    ptype = precond.get("type")
    if ptype == "exact":
        return str(precond.get("value")) == str(precond.get("actual", ctx.versions.get(precond.get("key", ""), "")))
    if ptype == "platform":
        return ctx.os_platform == precond.get("value")
    if ptype == "semver_range":
        pkg = precond.get("package", "")
        ver = ctx.versions.get(pkg, "0.0.0")
        return semver_satisfies(ver, precond.get("range", ""))
    if ptype == "dep_version":
        pkg = precond.get("package", "")
        return ctx.versions.get(pkg) == precond.get("version")
    if ptype == "content_hash":
        return ctx.file_hashes.get(precond.get("path", "")) == precond.get("sha256")
    if ptype == "command":
        return precond.get("value") in ctx.command_available
    if ptype == "env_present":
        return precond.get("name") in ctx.env_present
    if ptype == "feature_flag":
        return precond.get("name") in ctx.feature_flags
    if ptype == "schema_version":
        return ctx.versions.get("schema", "") == precond.get("value")
    # Unknown precondition type is treated as a hard failure, never silently
    # satisfied.
    return False


def evaluate_preconditions(preconditions: list[dict[str, Any]] | None,
                           ctx: PreconditionContext) -> float:
    """Fraction of preconditions satisfied in [0, 1]. No contract (empty list)
    means nothing to fail, so applicability is 1.0."""
    if not preconditions:
        return 1.0
    if not ctx:
        return 1.0
    ok = sum(1 for p in preconditions if _match_one(p, ctx))
    return ok / len(preconditions)


def evaluate_anti_conditions(anti_conditions: list[dict[str, Any]] | None,
                             ctx: PreconditionContext) -> bool:
    """True if ANY anti-condition matches -> the atom must be excluded."""
    if not anti_conditions:
        return False
    return any(_match_one(a, ctx) for a in anti_conditions)


__all__ = [
    "PreconditionContext",
    "semver_satisfies",
    "evaluate_preconditions",
    "evaluate_anti_conditions",
]
