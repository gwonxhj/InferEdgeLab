from __future__ import annotations

from typing import Any

from inferedgelab.services.guard_analysis import guard_status, guard_verdict


REVIEW_TRADEOFF_RISKS = {"risky_tradeoff", "severe_tradeoff", "not_beneficial"}


def _decision_payload(
    *,
    decision: str,
    reason: str,
    lab_overall: Any,
    guard_status: Any,
    guard_verdict_value: Any,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "decision": decision,
        "reason": reason,
        "lab_overall": lab_overall,
        "guard_status": guard_status,
        "guard_verdict": guard_verdict_value,
        "recommended_action": recommended_action,
    }


def build_deployment_decision(judgement: dict, guard_analysis: dict | None = None) -> dict[str, Any]:
    normalized_guard_status = guard_status(guard_analysis)
    normalized_guard_verdict = guard_verdict(guard_analysis)
    lab_overall = judgement.get("overall")
    shape_match = judgement.get("shape_match")
    system_match = judgement.get("system_match")
    tradeoff_risk = judgement.get("tradeoff_risk")

    if normalized_guard_status == "error":
        return _decision_payload(
            decision="blocked",
            reason="Guard analysis reported an error-level validation issue.",
            lab_overall=lab_overall,
            guard_status=normalized_guard_status,
            guard_verdict_value=normalized_guard_verdict,
            recommended_action="Do not deploy until the Guard anomalies are resolved.",
        )

    if normalized_guard_status == "warning":
        decision = "review_required"
        reason = "Guard analysis reported warning-level validation risks."
        recommended_action = "Review Guard anomalies, suspected causes, and accuracy/provenance evidence before deployment."
    elif normalized_guard_status == "skipped":
        decision = "unknown"
        reason = "Guard analysis was skipped."
        recommended_action = "Install InferEdgeAIGuard or run validation reasoning before deployment."
    elif normalized_guard_status is None:
        decision = "unknown"
        reason = "Guard analysis is unavailable."
        recommended_action = "Run compare with --with-guard before deployment decision."
    elif normalized_guard_status == "ok":
        if lab_overall in {"improvement", "tradeoff_faster"}:
            decision = "deployable"
            reason = "Lab judgement is favorable and Guard analysis passed."
            recommended_action = "Deployment can proceed with normal rollout monitoring."
        elif lab_overall in {"neutral", "tradeoff_neutral"}:
            decision = "deployable_with_note"
            reason = "Lab judgement is neutral and Guard analysis passed."
            recommended_action = "Deployment can proceed, but keep the comparison note in release evidence."
        elif lab_overall in {"regression", "tradeoff_slower", "mismatch"}:
            decision = "review_required"
            reason = "Lab judgement indicates regression or mismatch despite Guard passing."
            recommended_action = "Review Lab comparison evidence before deployment."
        else:
            decision = "unknown"
            reason = "Lab judgement is not recognized for deployment decision."
            recommended_action = "Review the compare judgement before deployment."
    else:
        decision = "unknown"
        reason = "Guard analysis status is not recognized."
        recommended_action = "Review Guard output before deployment."

    if decision != "blocked" and shape_match is False:
        decision = "review_required"
        reason = "Input shape mismatch requires deployment review."
        recommended_action = "Resolve or explicitly approve the shape mismatch before deployment."

    if decision != "blocked" and system_match is False:
        if lab_overall in {"regression", "tradeoff_slower", "mismatch"}:
            decision = "review_required"
            reason = "System mismatch and unfavorable Lab judgement require deployment review."
            recommended_action = "Review system provenance and Lab regression evidence before deployment."
        elif decision == "deployable":
            decision = "deployable_with_note"
            reason = "System mismatch reduces deployment confidence."
            recommended_action = "Deployment can proceed only with the system mismatch noted in release evidence."

    if decision != "blocked" and tradeoff_risk in REVIEW_TRADEOFF_RISKS:
        decision = "review_required"
        reason = "Trade-off risk requires deployment review."
        recommended_action = "Review accuracy trade-off and provenance evidence before deployment."

    return _decision_payload(
        decision=decision,
        reason=reason,
        lab_overall=lab_overall,
        guard_status=normalized_guard_status,
        guard_verdict_value=normalized_guard_verdict,
        recommended_action=recommended_action,
    )
