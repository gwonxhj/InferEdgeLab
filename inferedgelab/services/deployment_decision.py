from __future__ import annotations

from typing import Any

from inferedgelab.services.guard_analysis import guard_status, guard_verdict


REVIEW_TRADEOFF_RISKS = {"risky_tradeoff", "severe_tradeoff", "not_beneficial"}
POLICY_VERSION = "inferedge-lab-decision-policy-v1"
POLICY_RULES: dict[str, dict[str, str]] = {
    "guard_error_block": {
        "effect": "blocked",
        "description": "AIGuard reported error-level diagnosis evidence.",
    },
    "guard_warning_review": {
        "effect": "review_required",
        "description": "AIGuard reported warning-level diagnosis evidence.",
    },
    "guard_skipped_unknown": {
        "effect": "unknown",
        "description": "AIGuard was skipped, so diagnosis evidence is incomplete.",
    },
    "guard_unavailable_unknown": {
        "effect": "unknown",
        "description": "AIGuard evidence is unavailable for this comparison.",
    },
    "guard_ok_lab_favorable_deployable": {
        "effect": "deployable",
        "description": "Lab comparison is favorable and AIGuard passed.",
    },
    "guard_ok_lab_neutral_deployable_note": {
        "effect": "deployable_with_note",
        "description": "Lab comparison is neutral and AIGuard passed.",
    },
    "guard_ok_lab_unfavorable_review": {
        "effect": "review_required",
        "description": "Lab comparison indicates regression or mismatch despite AIGuard passing.",
    },
    "guard_ok_lab_unknown": {
        "effect": "unknown",
        "description": "Lab comparison judgement is not recognized by the decision policy.",
    },
    "guard_status_unrecognized_unknown": {
        "effect": "unknown",
        "description": "AIGuard status is not recognized by the decision policy.",
    },
    "shape_mismatch_review": {
        "effect": "review_required",
        "description": "Input shape mismatch requires explicit deployment review.",
    },
    "system_mismatch_unfavorable_review": {
        "effect": "review_required",
        "description": "System mismatch combined with unfavorable Lab judgement requires review.",
    },
    "system_mismatch_note": {
        "effect": "deployable_with_note",
        "description": "System mismatch reduces confidence and must be noted in release evidence.",
    },
    "tradeoff_risk_review": {
        "effect": "review_required",
        "description": "Latency/accuracy trade-off risk requires deployment review.",
    },
    "worker_uncompared_unknown": {
        "effect": "unknown",
        "description": "Worker result has not been compared by Lab yet.",
    },
    "edgeenv_runtime_regression_review": {
        "effect": "review_required",
        "description": "EdgeEnv same-condition runtime regression evidence requires review.",
    },
}


def policy_summary_for_rules(triggered_rules: list[str]) -> list[dict[str, str]]:
    return [
        {
            "rule": rule,
            "effect": POLICY_RULES.get(rule, {}).get("effect", "unknown"),
            "description": POLICY_RULES.get(rule, {}).get(
                "description", "Rule is not documented in this policy version."
            ),
        }
        for rule in triggered_rules
    ]


def _decision_payload(
    *,
    decision: str,
    reason: str,
    lab_overall: Any,
    guard_status: Any,
    guard_verdict_value: Any,
    recommended_action: str,
    triggered_rules: list[str],
) -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "decision": decision,
        "reason": reason,
        "lab_overall": lab_overall,
        "guard_status": guard_status,
        "guard_verdict": guard_verdict_value,
        "recommended_action": recommended_action,
        "triggered_rules": triggered_rules,
        "policy_summary": policy_summary_for_rules(triggered_rules),
    }


def build_deployment_decision(
    judgement: dict,
    guard_analysis: dict | None = None,
    edgeenv_regression: dict | None = None,
) -> dict[str, Any]:
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
            triggered_rules=["guard_error_block"],
        )

    if normalized_guard_status == "warning":
        decision = "review_required"
        reason = "Guard analysis reported warning-level validation risks."
        recommended_action = "Review Guard anomalies, suspected causes, and accuracy/provenance evidence before deployment."
        triggered_rules = ["guard_warning_review"]
    elif normalized_guard_status == "skipped":
        decision = "unknown"
        reason = "Guard analysis was skipped."
        recommended_action = "Install InferEdgeAIGuard or run validation reasoning before deployment."
        triggered_rules = ["guard_skipped_unknown"]
    elif normalized_guard_status is None:
        decision = "unknown"
        reason = "Guard analysis is unavailable."
        recommended_action = "Run compare with --with-guard before deployment decision."
        triggered_rules = ["guard_unavailable_unknown"]
    elif normalized_guard_status == "ok":
        if lab_overall in {"improvement", "tradeoff_faster"}:
            decision = "deployable"
            reason = "Lab judgement is favorable and Guard analysis passed."
            recommended_action = "Deployment can proceed with normal rollout monitoring."
            triggered_rules = ["guard_ok_lab_favorable_deployable"]
        elif lab_overall in {"neutral", "tradeoff_neutral"}:
            decision = "deployable_with_note"
            reason = "Lab judgement is neutral and Guard analysis passed."
            recommended_action = "Deployment can proceed, but keep the comparison note in release evidence."
            triggered_rules = ["guard_ok_lab_neutral_deployable_note"]
        elif lab_overall in {"regression", "tradeoff_slower", "mismatch"}:
            decision = "review_required"
            reason = "Lab judgement indicates regression or mismatch despite Guard passing."
            recommended_action = "Review Lab comparison evidence before deployment."
            triggered_rules = ["guard_ok_lab_unfavorable_review"]
        else:
            decision = "unknown"
            reason = "Lab judgement is not recognized for deployment decision."
            recommended_action = "Review the compare judgement before deployment."
            triggered_rules = ["guard_ok_lab_unknown"]
    else:
        decision = "unknown"
        reason = "Guard analysis status is not recognized."
        recommended_action = "Review Guard output before deployment."
        triggered_rules = ["guard_status_unrecognized_unknown"]

    if decision != "blocked" and shape_match is False:
        decision = "review_required"
        reason = "Input shape mismatch requires deployment review."
        recommended_action = "Resolve or explicitly approve the shape mismatch before deployment."
        triggered_rules.append("shape_mismatch_review")

    if decision != "blocked" and system_match is False:
        if lab_overall in {"regression", "tradeoff_slower", "mismatch"}:
            decision = "review_required"
            reason = "System mismatch and unfavorable Lab judgement require deployment review."
            recommended_action = "Review system provenance and Lab regression evidence before deployment."
            triggered_rules.append("system_mismatch_unfavorable_review")
        elif decision == "deployable":
            decision = "deployable_with_note"
            reason = "System mismatch reduces deployment confidence."
            recommended_action = "Deployment can proceed only with the system mismatch noted in release evidence."
            triggered_rules.append("system_mismatch_note")

    if decision != "blocked" and tradeoff_risk in REVIEW_TRADEOFF_RISKS:
        decision = "review_required"
        reason = "Trade-off risk requires deployment review."
        recommended_action = "Review accuracy trade-off and provenance evidence before deployment."
        triggered_rules.append("tradeoff_risk_review")

    if decision != "blocked" and _edgeenv_runtime_regression_observed(
        edgeenv_regression
    ):
        decision = "review_required"
        reason = "EdgeEnv runtime regression evidence requires deployment review."
        if normalized_guard_status == "warning":
            recommended_action = (
                "Review EdgeEnv comparability judgement, latency/resource deltas, AIGuard warning evidence, and Lab comparison evidence before deployment."
            )
        else:
            recommended_action = (
                "Review EdgeEnv comparability judgement, latency/resource deltas, and Lab comparison evidence before deployment."
            )
        triggered_rules.append("edgeenv_runtime_regression_review")

    return _decision_payload(
        decision=decision,
        reason=reason,
        lab_overall=lab_overall,
        guard_status=normalized_guard_status,
        guard_verdict_value=normalized_guard_verdict,
        recommended_action=recommended_action,
        triggered_rules=triggered_rules,
    )


def _edgeenv_runtime_regression_observed(edgeenv_regression: dict | None) -> bool:
    if not isinstance(edgeenv_regression, dict):
        return False
    return bool(edgeenv_regression.get("regression_detected")) and (
        edgeenv_regression.get("mode") == "same-condition"
    )
