"""Review routing — route by confidence, reversibility, and cost.

Ships ``route`` (the auto / human / senior decision) and a uniform ``check()``.
Early/experimental (0.1.0).
"""
from __future__ import annotations

from ..result import CheckResult

STATUS = "experimental"


def route(confidence: float, reversible: bool, high_cost: bool) -> str:
    """Return ``"auto"``, ``"human"``, or ``"senior"`` for a decision.

    - ``senior``: low confidence, or irreversible **and** high cost
    - ``human``: medium confidence, or costs real money/time, or irreversible
    - ``auto``: high confidence, reversible, low cost
    """
    if confidence < 0.5 or (not reversible and high_cost):
        return "senior"
    if confidence < 0.8 or high_cost or not reversible:
        return "human"
    return "auto"


def check(response: str) -> CheckResult:
    """Audit review-routing. Needs the decision's metadata (confidence,
    reversibility, cost) — not inferable from a response alone (planned)."""
    return CheckResult(
        "review_routing",
        findings=["needs decision metadata (confidence/reversibility/cost); not scored from a response (0.1.0)"],
    )


__all__ = ["STATUS", "route", "check"]
