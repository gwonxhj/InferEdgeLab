from __future__ import annotations

from pathlib import Path

from inferedgelab.services.compare_service import build_compare_bundle


FIXTURE_DIR = Path("examples/edgeenv_regression")


def test_edgeenv_regression_fixture_drives_lab_review_decision():
    bundle = build_compare_bundle(
        base_path=str(FIXTURE_DIR / "lab_baseline_result.json"),
        new_path=str(FIXTURE_DIR / "lab_candidate_result.json"),
        edgeenv_regression_path=str(FIXTURE_DIR / "edgeenv_runtime_regression.json"),
    )

    edgeenv_regression = bundle["edgeenv_runtime_regression"]
    decision = bundle["deployment_decision"]

    assert edgeenv_regression["regression_detected"] is True
    assert edgeenv_regression["mode"] == "same-condition"
    assert edgeenv_regression["evidence"]["mean_delta_pct"] == 18.0
    assert edgeenv_regression["evidence"]["p99_delta_pct"] == 32.0
    assert edgeenv_regression["runtime_telemetry_context"]["candidate"]["execution_sequence_id"] == 2
    assert decision["decision"] == "review_required"
    assert "edgeenv_runtime_regression_review" in decision["triggered_rules"]
    assert "## Runtime Regression Evidence" in bundle["markdown"]
    assert "### Runtime Telemetry Context" in bundle["markdown"]
    assert "Runtime Regression Evidence" in bundle["html"]
    assert "edgeenv.runtime-telemetry-history.v1" in bundle["html"]
    assert "p99_latency_high" in bundle["markdown"]
