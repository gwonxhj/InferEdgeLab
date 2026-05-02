from __future__ import annotations

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


def test_guard_error_blocks_deployment():
    decision = build_deployment_decision(make_judgement(), {"status": "error"})

    assert decision["decision"] == "blocked"
    assert decision["reason"] == "Guard analysis reported an error-level validation issue."
    assert decision["recommended_action"] == "Do not deploy until the Guard anomalies are resolved."


def test_guard_warning_requires_review():
    decision = build_deployment_decision(make_judgement(), {"status": "warning"})

    assert decision["decision"] == "review_required"
    assert decision["reason"] == "Guard analysis reported warning-level validation risks."


def test_guard_skipped_is_unknown():
    decision = build_deployment_decision(make_judgement(), {"status": "skipped"})

    assert decision["decision"] == "unknown"
    assert decision["reason"] == "Guard analysis was skipped."


def test_guard_ok_with_improvement_is_deployable():
    decision = build_deployment_decision(make_judgement(overall="improvement"), {"status": "ok"})

    assert decision["decision"] == "deployable"
    assert decision["lab_overall"] == "improvement"
    assert decision["guard_status"] == "ok"
    assert decision["guard_verdict"] == "pass"


def test_guard_ok_with_neutral_is_deployable_with_note():
    decision = build_deployment_decision(make_judgement(overall="neutral"), {"status": "ok"})

    assert decision["decision"] == "deployable_with_note"


def test_guard_ok_with_regression_requires_review():
    decision = build_deployment_decision(make_judgement(overall="regression"), {"status": "ok"})

    assert decision["decision"] == "review_required"


def test_shape_mismatch_requires_review_but_guard_error_stays_blocked():
    review_decision = build_deployment_decision(make_judgement(shape_match=False), {"status": "ok"})
    blocked_decision = build_deployment_decision(make_judgement(shape_match=False), {"status": "error"})

    assert review_decision["decision"] == "review_required"
    assert blocked_decision["decision"] == "blocked"


def test_risky_tradeoff_requires_review():
    decision = build_deployment_decision(
        make_judgement(overall="tradeoff_faster", tradeoff_risk="risky_tradeoff"),
        {"status": "ok"},
    )

    assert decision["decision"] == "review_required"


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
