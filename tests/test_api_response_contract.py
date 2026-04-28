from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inferedgelab.services.api_response_contract import build_api_response_bundle


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "api_response_bundle.json"
WORKER_GUARD_FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "aiguard_worker_provenance_mismatch_guard_analysis.json"
)


def load_fixture() -> dict[str, dict[str, Any]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def load_worker_provenance_guard_fixture() -> dict[str, Any]:
    return json.loads(WORKER_GUARD_FIXTURE_PATH.read_text(encoding="utf-8"))


def assert_api_response_contract(response: dict[str, Any], *, guard_expected: bool) -> None:
    assert set(response) >= {
        "summary",
        "comparison",
        "deployment_decision",
        "provenance",
        "metadata",
        "timestamps",
        "execution_info",
    }
    assert isinstance(response["summary"], dict)
    assert isinstance(response["comparison"], dict)
    assert isinstance(response["deployment_decision"], dict)
    assert isinstance(response["provenance"], dict)
    assert isinstance(response["metadata"], dict)
    assert isinstance(response["timestamps"], dict)
    assert isinstance(response["execution_info"], dict)

    assert response["deployment_decision"]["decision"] in {
        "deployable",
        "deployable_with_note",
        "review_required",
        "blocked",
        "unknown",
    }
    assert response["summary"]["deployment_decision"] == response["deployment_decision"]["decision"]
    assert set(response["comparison"]) >= {"result", "judgement", "rendered"}
    assert set(response["comparison"]["rendered"]) >= {"markdown", "html"}
    assert "source_bundle" in response["provenance"]
    assert set(response["execution_info"]) >= {
        "base_path",
        "new_path",
        "selection_mode",
        "legacy_warning",
    }

    if guard_expected:
        assert "guard_analysis" in response
        assert isinstance(response["guard_analysis"], dict)
        assert response["guard_analysis"]["status"] in {"ok", "warning", "error", "skipped"}
        assert response["summary"]["guard_status"] == response["guard_analysis"]["status"]
    else:
        assert "guard_analysis" not in response
        assert response["summary"]["guard_status"] is None


def test_api_response_fixture_covers_required_saas_contract_cases():
    fixture = load_fixture()

    assert set(fixture) == {
        "deployable",
        "review_required",
        "blocked",
        "without_guard",
    }
    assert fixture["deployable"]["deployment_decision"]["decision"] == "deployable"
    assert fixture["review_required"]["deployment_decision"]["decision"] == "review_required"
    assert fixture["blocked"]["deployment_decision"]["decision"] == "blocked"
    assert fixture["without_guard"]["deployment_decision"]["decision"] == "unknown"

    for name, response in fixture.items():
        assert_api_response_contract(
            response,
            guard_expected=name != "without_guard",
        )


def test_api_response_contract_keeps_guard_analysis_optional():
    without_guard = load_fixture()["without_guard"]

    assert_api_response_contract(without_guard, guard_expected=False)
    assert "guard_analysis" not in without_guard


def test_build_api_response_bundle_wraps_compare_bundle_with_guard():
    bundle = {
        "meta": {
            "base_path": "results/base.json",
            "new_path": "results/new.json",
            "legacy_warning": False,
        },
        "base": {
            "timestamp": "2026-04-13T09:00:00Z",
        },
        "new": {
            "timestamp": "2026-04-13T10:00:00Z",
        },
        "result": {
            "precision": {
                "comparison_mode": "same_precision",
                "pair": "fp32_vs_fp32",
            },
            "runtime_provenance": {"new": {"runtime_artifact_path": "artifact.onnx"}},
            "shape_context": {},
            "run_config_diff": {},
        },
        "judgement": {
            "overall": "improvement",
            "comparison_mode": "same_precision",
            "precision_pair": "fp32_vs_fp32",
        },
        "markdown": "# report",
        "html": "<html></html>",
        "deployment_decision": {
            "decision": "deployable",
            "reason": "Lab judgement is favorable and Guard analysis passed.",
            "lab_overall": "improvement",
            "guard_status": "ok",
            "recommended_action": "Deployment can proceed with normal rollout monitoring.",
        },
        "guard_analysis": {
            "status": "ok",
            "anomalies": [],
            "suspected_causes": [],
            "recommendations": [],
            "confidence": 0.5,
        },
    }

    response = build_api_response_bundle(bundle)

    assert_api_response_contract(response, guard_expected=True)
    assert response["summary"] == {
        "response_type": "compare",
        "overall": "improvement",
        "comparison_mode": "same_precision",
        "precision_pair": "fp32_vs_fp32",
        "deployment_decision": "deployable",
        "guard_status": "ok",
    }
    assert response["comparison"]["result"] == bundle["result"]
    assert response["comparison"]["judgement"] == bundle["judgement"]
    assert response["deployment_decision"] == bundle["deployment_decision"]
    assert response["guard_analysis"] == bundle["guard_analysis"]
    assert response["timestamps"] == {
        "base": "2026-04-13T09:00:00Z",
        "new": "2026-04-13T10:00:00Z",
    }


def test_build_api_response_bundle_omits_guard_when_absent():
    bundle = {
        "meta": {
            "base_path": "results/base.json",
            "new_path": "results/new.json",
            "legacy_warning": False,
        },
        "result": {
            "precision": {
                "comparison_mode": "same_precision",
                "pair": "fp32_vs_fp32",
            }
        },
        "judgement": {
            "overall": "improvement",
        },
        "deployment_decision": {
            "decision": "unknown",
            "reason": "Guard analysis is unavailable.",
            "lab_overall": "improvement",
            "guard_status": None,
            "recommended_action": "Run compare with --with-guard before deployment decision.",
        },
    }

    response = build_api_response_bundle(bundle)

    assert_api_response_contract(response, guard_expected=False)
    assert response["deployment_decision"]["decision"] == "unknown"
    assert response["summary"]["guard_status"] is None


def test_build_api_response_bundle_preserves_worker_provenance_guard_evidence():
    guard_analysis = load_worker_provenance_guard_fixture()
    bundle = {
        "meta": {
            "base_path": "results/base.json",
            "new_path": "results/new.json",
            "legacy_warning": False,
        },
        "result": {
            "precision": {
                "comparison_mode": "same_precision",
                "pair": "fp16_vs_fp16",
            },
            "runtime_provenance": {
                "new": {
                    "runtime_artifact_sha256": "runtime-worker-artifact-sha256",
                    "source_model_sha256": "runtime-worker-source-sha256",
                }
            },
            "shape_context": {},
            "run_config_diff": {},
        },
        "judgement": {
            "overall": "improvement",
            "comparison_mode": "same_precision",
            "precision_pair": "fp16_vs_fp16",
        },
        "rendered": {
            "markdown": "# report\n\n## Guard Analysis",
            "html": "<html><h2>Guard Analysis</h2></html>",
        },
        "deployment_decision": {
            "decision": "blocked",
            "reason": "Guard analysis reported an error-level validation issue.",
            "lab_overall": "improvement",
            "guard_status": "error",
            "recommended_action": "Do not deploy until the guard error is resolved.",
        },
        "guard_analysis": guard_analysis,
    }

    response = build_api_response_bundle(bundle)

    assert_api_response_contract(response, guard_expected=True)
    assert response["deployment_decision"]["decision"] == "blocked"
    assert response["summary"]["guard_status"] == "error"
    assert response["guard_analysis"] == guard_analysis
    evidence = response["guard_analysis"]["anomalies"][0]["evidence"]
    assert evidence == {
        "field": "artifact_sha256",
        "expected": "forge-summary-artifact-sha256",
        "observed": "runtime-worker-artifact-sha256",
        "expected_source": "forge_worker_runtime_summary",
        "observed_source": "runtime_worker_response",
    }
