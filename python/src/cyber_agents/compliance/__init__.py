"""Compliance — pin each obligation to a control, an owner, and evidence.

Ships the ``Control`` register row and a uniform ``check()``.
Early/experimental (0.1.0).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..result import CheckResult

STATUS = "experimental"


@dataclass(frozen=True)
class Control:
    """One row of a data-protection controls register."""

    obligation: str
    control: str
    owner: str
    evidence: str


def check(response: str) -> CheckResult:
    """Audit compliance. Mapping obligations → controls → evidence needs the
    target system's register/config, not a single response (planned)."""
    return CheckResult(
        "compliance",
        findings=["needs the system's controls register/config; not scored from a response (0.1.0)"],
    )


__all__ = ["STATUS", "Control", "check"]
