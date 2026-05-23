from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "ci" / "gitlab" / "runtime-intelligence-artifacts.yml"
DOC = REPO_ROOT / "docs" / "ci" / "runtime_intelligence_gitlab_artifacts.md"


def test_runtime_intelligence_gitlab_template_preserves_roadmap_stages():
    text = TEMPLATE.read_text(encoding="utf-8")

    for stage in (
        "test",
        "benchmark",
        "telemetry",
        "anomaly-analysis",
        "report",
        "deployment-risk",
    ):
        assert f"  - {stage}" in text

    assert "inferedge:test" in text
    assert "inferedge:benchmark-smoke" in text
    assert "inferedge:telemetry-report" in text
    assert "inferedge:deterministic-anomaly-summary" in text
    assert "inferedge:portfolio-report" in text
    assert "inferedge:deployment-risk-gate" in text


def test_runtime_intelligence_gitlab_template_keeps_local_first_artifact_contract():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "examples/edgeenv_regression/edgeenv_runtime_regression.json" in text
    assert "examples/runtime_intelligence_chain/edgeenv_regression_with_orchestrator_context.json" in text
    assert "examples/runtime_intelligence_chain/aiguard_runtime_operation_guard_analysis.json" in text
    assert "--guard-analysis" in text
    assert "check_runtime_intelligence_artifact_bundle.py" in text
    assert "runtime_anomaly_gate_summary.md" in text
    assert "reports/runtime_intelligence_ci" in text
    assert "portfolio-demo-check --format json" in text
    assert "artifacts:" in text
    assert ".gitlab-ci.yml" in text


def test_runtime_intelligence_gitlab_doc_states_ownership_boundaries():
    text = DOC.read_text(encoding="utf-8")

    assert "optional GitLab CI template" in text
    assert "Lab owns the report and deployment decision surface" in text
    assert "CI stores artifacts and applies deterministic gates" in text
    assert "does not become a production runtime control plane" in text
    assert "new InferEdge Intelligence repo" in text
    assert "ML or forecasting pipeline" in text
