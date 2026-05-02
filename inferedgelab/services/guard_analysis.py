from __future__ import annotations

from typing import Any


LEGACY_STATUS_TO_VERDICT = {
    "ok": "pass",
    "warning": "review_required",
    "error": "blocked",
    "skipped": "skipped",
}

VERDICT_TO_LEGACY_STATUS = {
    "pass": "ok",
    "suspicious": "warning",
    "review_required": "warning",
    "blocked": "error",
    "skipped": "skipped",
}


def guard_verdict(guard_analysis: dict[str, Any] | None) -> str | None:
    """Return the AIGuard diagnosis verdict when available.

    InferEdgeLab accepts both the older Guard reasoning shape
    (``status: ok/warning/error``) and the newer diagnosis report contract
    (``guard_verdict: pass/review_required/blocked``). This helper keeps Lab as
    the final decision owner while preserving both optional evidence contracts.
    """

    if not isinstance(guard_analysis, dict):
        return None
    verdict = guard_analysis.get("guard_verdict")
    if isinstance(verdict, str) and verdict:
        return verdict
    status = guard_analysis.get("status")
    if isinstance(status, str):
        return LEGACY_STATUS_TO_VERDICT.get(status, status)
    return None


def guard_status(guard_analysis: dict[str, Any] | None) -> str | None:
    """Return a legacy-compatible Guard status for existing Lab/API clients."""

    if not isinstance(guard_analysis, dict):
        return None
    status = guard_analysis.get("status")
    if isinstance(status, str) and status:
        return status
    verdict = guard_analysis.get("guard_verdict")
    if isinstance(verdict, str):
        return VERDICT_TO_LEGACY_STATUS.get(verdict, verdict)
    return None


def guard_primary_reason(guard_analysis: dict[str, Any] | None) -> str | None:
    if not isinstance(guard_analysis, dict):
        return None
    reason = guard_analysis.get("primary_reason") or guard_analysis.get("reason")
    return str(reason) if reason else None


def guard_evidence_items(guard_analysis: dict[str, Any] | None) -> list[Any]:
    if not isinstance(guard_analysis, dict):
        return []
    evidence = guard_analysis.get("evidence")
    if isinstance(evidence, list):
        return evidence
    anomalies = guard_analysis.get("anomalies")
    if isinstance(anomalies, list):
        return anomalies
    return []
