from __future__ import annotations

from inferedgelab.services.deployment_decision import POLICY_VERSION
from inferedgelab.services.deployment_decision import build_deployment_decision


def make_judgement(
    *,
    overall: str = "improvement",
    shape_match: bool = True,
    system_match: bool = True,
    tradeoff_risk: str = "not_applicable",
) -> dict:
    return {
        "overall": overall,
        "shape_match": shape_match,
        "system_match": system_match,
        "tradeoff_risk": tradeoff_risk,
    }


def assert_policy(decision: dict, *rules: str) -> None:
    assert decision["policy_version"] == POLICY_VERSION
    for rule in rules:
        assert rule in decision["triggered_rules"]
    assert decision["policy_summary"]
    assert decision["policy_summary"][0]["rule"] == decision["triggered_rules"][0]


def test_guard_error_blocks_deployment():
    decision = build_deployment_decision(make_judgement(), {"status": "error"})

    assert decision["decision"] == "blocked"
    assert decision["reason"] == "Guard analysis reported an error-level validation issue."
    assert decision["recommended_action"] == "Do not deploy until the Guard anomalies are resolved."
    assert_policy(decision, "guard_error_block")


def test_guard_warning_requires_review():
    decision = build_deployment_decision(make_judgement(), {"status": "warning"})

    assert decision["decision"] == "review_required"
    assert decision["reason"] == "Guard analysis reported warning-level validation risks."
    assert_policy(decision, "guard_warning_review")


def test_guard_skipped_is_unknown():
    decision = build_deployment_decision(make_judgement(), {"status": "skipped"})

    assert decision["decision"] == "unknown"
    assert decision["reason"] == "Guard analysis was skipped."
    assert_policy(decision, "guard_skipped_unknown")


def test_guard_ok_with_improvement_is_deployable():
    decision = build_deployment_decision(make_judgement(overall="improvement"), {"status": "ok"})

    assert decision["decision"] == "deployable"
    assert decision["lab_overall"] == "improvement"
    assert decision["guard_status"] == "ok"
    assert decision["guard_verdict"] == "pass"
    assert_policy(decision, "guard_ok_lab_favorable_deployable")


def test_guard_ok_with_neutral_is_deployable_with_note():
    decision = build_deployment_decision(make_judgement(overall="neutral"), {"status": "ok"})

    assert decision["decision"] == "deployable_with_note"
    assert_policy(decision, "guard_ok_lab_neutral_deployable_note")


def test_guard_ok_with_regression_requires_review():
    decision = build_deployment_decision(make_judgement(overall="regression"), {"status": "ok"})

    assert decision["decision"] == "review_required"
    assert_policy(decision, "guard_ok_lab_unfavorable_review")


def test_edgeenv_same_condition_runtime_regression_requires_review():
    decision = build_deployment_decision(
        make_judgement(overall="improvement"),
        {"status": "ok"},
        edgeenv_regression={
            "regression_detected": True,
            "regression_type": "latency",
            "severity": "high",
            "comparable": True,
            "mode": "same-condition",
            "recommendation": "review_required",
        },
    )

    assert decision["decision"] == "review_required"
    assert decision["reason"] == "EdgeEnv runtime regression evidence requires deployment review."
    assert_policy(
        decision,
        "guard_ok_lab_favorable_deployable",
        "edgeenv_runtime_regression_review",
    )


def test_edgeenv_runtime_comparison_does_not_force_review():
    decision = build_deployment_decision(
        make_judgement(overall="improvement"),
        {"status": "ok"},
        edgeenv_regression={
            "regression_detected": True,
            "regression_type": "runtime_mismatch",
            "severity": "review",
            "comparable": True,
            "mode": "runtime-comparison",
            "recommendation": "compare_as_runtime_evidence_only",
        },
    )

    assert decision["decision"] == "deployable"
    assert "edgeenv_runtime_regression_review" not in decision["triggered_rules"]


def test_edgeenv_regression_with_guard_warning_preserves_both_review_reasons():
    decision = build_deployment_decision(
        make_judgement(overall="improvement"),
        {
            "schema_version": "inferedge-aiguard-diagnosis-v1",
            "guard_verdict": "review_required",
            "severity": "medium",
            "primary_reason": "Runtime telemetry replay context should be reviewed.",
            "evidence": [
                {
                    "type": "runtime_telemetry_replay_context",
                    "metric_name": "runtime_telemetry_history_missing_run_count",
                    "observed_value": 1,
                    "baseline_value": 0,
                    "threshold": 1,
                    "severity": "medium",
                    "status": "warning",
                    "explanation": "Telemetry history replay has a missing run.",
                    "suspected_causes": ["telemetry_history_replay_gap"],
                    "recommendation": "Inspect the EdgeEnv telemetry history artifact.",
                }
            ],
        },
        edgeenv_regression={
            "regression_detected": True,
            "regression_type": "latency",
            "severity": "high",
            "comparable": True,
            "mode": "same-condition",
            "recommendation": "review_required",
        },
    )

    assert decision["decision"] == "review_required"
    assert decision["reason"] == "EdgeEnv runtime regression evidence requires deployment review."
    assert "AIGuard warning evidence" in decision["recommended_action"]
    assert_policy(
        decision,
        "guard_warning_review",
        "edgeenv_runtime_regression_review",
    )
    policy_rules = {item["rule"]: item for item in decision["policy_summary"]}
    assert policy_rules["guard_warning_review"]["effect"] == "review_required"
    assert policy_rules["edgeenv_runtime_regression_review"]["effect"] == "review_required"


def test_shape_mismatch_requires_review_but_guard_error_stays_blocked():
    review_decision = build_deployment_decision(make_judgement(shape_match=False), {"status": "ok"})
    blocked_decision = build_deployment_decision(make_judgement(shape_match=False), {"status": "error"})

    assert review_decision["decision"] == "review_required"
    assert blocked_decision["decision"] == "blocked"
    assert_policy(review_decision, "shape_mismatch_review")
    assert_policy(blocked_decision, "guard_error_block")


def test_risky_tradeoff_requires_review():
    decision = build_deployment_decision(
        make_judgement(overall="tradeoff_faster", tradeoff_risk="risky_tradeoff"),
        {"status": "ok"},
    )

    assert decision["decision"] == "review_required"
    assert_policy(decision, "tradeoff_risk_review")


def test_diagnosis_guard_verdict_blocked_blocks_deployment():
    decision = build_deployment_decision(
        make_judgement(overall="improvement"),
        {
            "schema_version": "inferedge-aiguard-diagnosis-v1",
            "guard_verdict": "blocked",
            "severity": "high",
            "primary_reason": "Temporal consistency evidence indicates deployment risk.",
            "evidence": [],
        },
    )

    assert decision["decision"] == "blocked"
    assert decision["guard_status"] == "error"
    assert decision["guard_verdict"] == "blocked"
    assert_policy(decision, "guard_error_block")


def test_diagnosis_guard_verdict_review_requires_lab_review():
    decision = build_deployment_decision(
        make_judgement(overall="improvement"),
        {
            "schema_version": "inferedge-aiguard-diagnosis-v1",
            "guard_verdict": "review_required",
            "severity": "medium",
            "primary_reason": "Temporal consistency should be reviewed before deployment.",
            "evidence": [],
        },
    )

    assert decision["decision"] == "review_required"
    assert decision["guard_status"] == "warning"
    assert decision["guard_verdict"] == "review_required"
    assert_policy(decision, "guard_warning_review")
