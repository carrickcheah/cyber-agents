"""Shared result type for domain checks."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CheckResult:
    """Outcome of auditing a system's response against one domain's metrics.

    ``passed`` / ``score`` are ``None`` when there isn't enough signal yet (or
    the check isn't implemented in this early release). ``bool(result)`` is True
    only when the check explicitly passed.
    """

    domain: str
    passed: bool | None = None
    score: float | None = None
    findings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed is True
