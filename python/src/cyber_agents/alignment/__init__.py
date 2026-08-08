"""Alignment — enforce *your* rules in code, not just the prompt.

Ships ``resolve_account_id`` (reject any model-supplied tenant override) and a
uniform ``check()`` for auditing a system. Early/experimental (0.1.0).
"""
from __future__ import annotations

from ..result import CheckResult

STATUS = "experimental"


class TenantMismatch(Exception):
    """Raised when a model-supplied tenant id disagrees with the verified one."""


def resolve_account_id(*, verified: str, model_supplied: str | None = None) -> str:
    """Return the VERIFIED account id and reject any LLM-supplied override.

    Tenant identity must never come from model output. Pass the id you resolved
    from the request/session as ``verified``; a mismatching ``model_supplied``
    raises :class:`TenantMismatch` rather than silently trusting it.
    """
    if model_supplied is not None and str(model_supplied) != str(verified):
        raise TenantMismatch("model-supplied account id must never override the verified one")
    return verified


def check(response: str) -> CheckResult:
    """Audit alignment. Not scorable from a single response — needs the target
    system's auth/tenant configuration (planned)."""
    return CheckResult(
        "alignment",
        findings=["needs the system's auth/tenant config; not scored from a response alone (0.1.0)"],
    )


__all__ = ["STATUS", "TenantMismatch", "resolve_account_id", "check"]
