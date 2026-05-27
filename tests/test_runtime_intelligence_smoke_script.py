import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "smoke_runtime_intelligence_chain.sh"


def test_runtime_intelligence_smoke_script_help():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Runtime Intelligence local artifact smoke" in result.stdout
    assert "production control plane" in result.stdout


def test_runtime_intelligence_smoke_script_rejects_missing_output_dir_value():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--output-dir"],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "--output-dir requires a value" in result.stderr


def test_runtime_intelligence_smoke_script_runs_artifact_chain(tmp_path):
    output_dir = tmp_path / "runtime_intelligence_chain"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--output-dir", str(output_dir)],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Runtime Intelligence artifact smoke passed." in result.stdout

    expected_artifacts = [
        "runtime_intelligence_bundle_manifest_gate_summary.md",
        "aiguard_edgeenv_handoff_alignment.json",
        "aiguard_edgeenv_handoff_alignment.md",
        "edgeenv_runtime_regression.md",
        "edgeenv_runtime_regression.html",
        "runtime_anomaly_summary.md",
        "runtime_anomaly_summary.html",
        "runtime_anomaly_gate_summary.md",
        "portfolio_demo_check.json",
        "portfolio_demo_check.md",
        "deployment_risk_summary.json",
        "runtime_intelligence_ci_artifact_gate_summary.md",
    ]
    for artifact in expected_artifacts:
        assert (output_dir / artifact).is_file()

    bundle_summary = (
        output_dir / "runtime_intelligence_bundle_manifest_gate_summary.md"
    ).read_text(encoding="utf-8")
    assert "- Status: passed" in bundle_summary
    assert (
        "orchestrator_producer_markers: source_repository=InferEdgeOrchestrator"
        in bundle_summary
    )
    assert (
        "aiguard_raw_context: orchestrator_producer_markers preserved"
        in bundle_summary
    )
    assert (
        "orchestrator_downstream_guard_alignment: "
        "producer_lineage_evidence_type=edgeenv_orchestrator_producer_lineage"
        in bundle_summary
    )
    assert "aiguard_raw_context: downstream_guard_alignment preserved" in bundle_summary
    assert (
        "aiguard_raw_context: producer_lineage_guard_alignment preserved"
        in bundle_summary
    )
    assert (
        "aiguard_raw_context: missing_telemetry_orchestrator_context preserved"
        in bundle_summary
    )
    assert (
        "aiguard_handoff_alignment: external required evidence types satisfied"
        in bundle_summary
    )
    assert "edgeenv_handoff: lab_bundle_alignment validated" in bundle_summary
    assert "edgeenv_handoff: runtime_telemetry_history validated" in bundle_summary
    assert "edgeenv_handoff: remote_dispatch_boundary preserved" in bundle_summary
    assert (
        "edgeenv_handoff: external AIGuard evidence requirements declared"
        in bundle_summary
    )
    assert "edgeenv_handoff: device_local_producer_lineage validated" in bundle_summary
    assert (
        "edgeenv_handoff: producer_lineage_guard_alignment validated"
        in bundle_summary
    )
    assert (
        "edgeenv_handoff: missing_telemetry_orchestrator_context validated"
        in bundle_summary
    )

    alignment_summary = (
        output_dir / "aiguard_edgeenv_handoff_alignment.md"
    ).read_text(encoding="utf-8")
    assert "status: passed" in alignment_summary
    assert "decision_owner: lab" in alignment_summary
    assert "diagnosis_owner: aiguard" in alignment_summary
    assert (
        "handoff_producer_lineage_guard_alignment_run_ids: "
        "edgeenv-smoke-candidate, edgeenv-smoke-missing"
    ) in alignment_summary
    assert (
        "guard_analysis_producer_lineage_guard_alignment_run_ids: "
        "edgeenv-smoke-candidate, edgeenv-smoke-missing"
    ) in alignment_summary

    ci_summary = (
        output_dir / "runtime_intelligence_ci_artifact_gate_summary.md"
    ).read_text(encoding="utf-8")
    assert "- Status: passed" in ci_summary
