"""Fairness — make unequal outcomes measurable.

Ships ``detect_language`` (a signal for per-language auditing) and a uniform
``check()``. Early/experimental (0.1.0).
"""
from __future__ import annotations

import re

from ..result import CheckResult

STATUS = "experimental"

_ZH = re.compile(r"[一-鿿]")
_MS = re.compile(r"\b(saya|nak|boleh|tak|apa|berapa|macam|ada)\b", re.IGNORECASE)


def detect_language(text: str) -> str | None:
    """Best-effort language tag (``zh`` / ``ms`` / ``en`` / ``None``).

    A sample language set — swap in the languages your own deployment serves.
    """
    if not text:
        return None
    if _ZH.search(text):
        return "zh"
    if _MS.search(text):
        return "ms"
    if re.search(r"[a-zA-Z]{2,}", text):
        return "en"
    return None


def check(response: str) -> CheckResult:
    """Audit fairness. A single response only reveals its language; genuine
    per-group fairness needs many samples (planned)."""
    lang = detect_language(response)
    return CheckResult(
        "fairness",
        findings=[f"response language={lang}; per-language fairness needs multiple samples (0.1.0)"],
    )


__all__ = ["STATUS", "detect_language", "check"]
