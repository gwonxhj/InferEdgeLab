import json
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
        "aiguard_edgeenv_handoff_alignment_optional_present.json",
        "aiguard_edgeenv_handoff_alignment_optional_present.md",
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
        "aiguard_evidence: edgeenv_orchestrator_task_event_rollup validated"
        in bundle_summary
    )
    assert (
        "aiguard_evidence: edgeenv_orchestrator_operation_timeline_summary validated"
        in bundle_summary
    )
    assert "aiguard_raw_context: task_event_rollup preserved" in bundle_summary
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
    assert "edgeenv_handoff: optional AIGuard evidence types declared" in bundle_summary
    assert (
        "edgeenv_handoff: optional AIGuard source traceability declared"
        in bundle_summary
    )
    assert "edgeenv_handoff: device_local_producer_lineage validated" in bundle_summary
    assert (
        "edgeenv_handoff: producer_lineage_guard_alignment validated"
        in bundle_summary
    )
    assert (
        "edgeenv_handoff: orchestrator_task_event_rollup validated"
        in bundle_summary
    )
    assert (
        "edgeenv_handoff: missing_telemetry_orchestrator_context validated"
        in bundle_summary
    )

    runtime_summary = (output_dir / "runtime_anomaly_summary.md").read_text(
        encoding="utf-8"
    )
    assert "Runtime replay duration scope" in runtime_summary
    assert "short 96-frame-class replay (96 frames)" in runtime_summary
    assert "class=short_96_frame_class, frames=96" in runtime_summary
    assert "source=entrypoint_requested_frames" in runtime_summary
    assert "scope_label=source=entrypoint_requested_frames" in runtime_summary

    alignment_summary = (
        output_dir / "aiguard_edgeenv_handoff_alignment.md"
    ).read_text(encoding="utf-8")
    alignment_payload = json.loads(
        (output_dir / "aiguard_edgeenv_handoff_alignment.json").read_text(
            encoding="utf-8"
        )
    )
    assert alignment_payload["optional_evidence_context_role"] == (
        "read_only_optional_guard_context"
    )
    assert alignment_payload["aiguard_validates_optional_evidence_as_required"] is False
    assert alignment_payload["optional_aiguard_evidence_types"] == [
        "stale_frame_risk",
        "edgeenv_orchestrator_stale_drop_summary",
    ]
    assert alignment_payload["optional_guard_evidence_types_present"] == []
    assert alignment_payload["missing_optional_evidence_types"] == [
        "edgeenv_orchestrator_stale_drop_summary",
        "stale_frame_risk",
    ]
    assert "status: passed" in alignment_summary
    assert "decision_owner: lab" in alignment_summary
    assert "diagnosis_owner: aiguard" in alignment_summary
    assert (
        "optional_evidence_context_role: read_only_optional_guard_context"
        in alignment_summary
    )
    assert (
        "aiguard_validates_optional_evidence_as_required: False"
        in alignment_summary
    )
    assert (
        "optional_aiguard_evidence_types: "
        "[stale_frame_risk, edgeenv_orchestrator_stale_drop_summary]"
        in alignment_summary
    )
    assert "optional_guard_evidence_types_present: []" in alignment_summary
    assert (
        "missing_optional_evidence_types: "
        "[edgeenv_orchestrator_stale_drop_summary, stale_frame_risk]"
        in alignment_summary
    )
    assert (
        "handoff_producer_lineage_guard_alignment_run_ids: "
        "[edgeenv-smoke-candidate, edgeenv-smoke-missing]"
    ) in alignment_summary
    assert (
        "guard_analysis_producer_lineage_guard_alignment_run_ids: "
        "[edgeenv-smoke-candidate, edgeenv-smoke-missing]"
    ) in alignment_summary
    optional_present_summary = (
        output_dir / "aiguard_edgeenv_handoff_alignment_optional_present.md"
    ).read_text(encoding="utf-8")
    optional_present_payload = json.loads(
        (
            output_dir / "aiguard_edgeenv_handoff_alignment_optional_present.json"
        ).read_text(encoding="utf-8")
    )
    assert optional_present_payload["optional_evidence_context_role"] == (
        "read_only_optional_guard_context"
    )
    assert (
        optional_present_payload["aiguard_validates_optional_evidence_as_required"]
        is False
    )
    assert optional_present_payload["optional_aiguard_evidence_types"] == [
        "stale_frame_risk",
        "edgeenv_orchestrator_stale_drop_summary",
    ]
    assert optional_present_payload["optional_guard_evidence_types_present"] == [
        "edgeenv_orchestrator_stale_drop_summary",
        "stale_frame_risk",
    ]
    assert optional_present_payload["missing_optional_evidence_types"] == []
    assert optional_present_payload["optional_present_source_artifact"] == {
        "repository": "InferEdgeAIGuard",
        "path": (
            "examples/runtime_intelligence/"
            "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
        ),
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "role": "aiguard-optional-stale-drop-full-evidence-source",
        "context_role": "read_only_cross_repo_traceability",
        "reproduction_command": [
            "python",
            "-m",
            "inferedge_aiguard.cli",
            "build-runtime-intelligence-optional-stale-drop",
            "--edgeenv-regression",
            (
                "examples/runtime_intelligence/"
                "edgeenv_runtime_regression_with_optional_stale_drop_context.json"
            ),
            "--remote-dispatch",
            (
                "examples/runtime_intelligence/"
                "remote_dispatch_fallback_recovered_result.json"
            ),
            "--orchestration-summary",
            (
                "examples/runtime_intelligence/"
                "orchestrator_multi_workload_sustained_summary.json"
            ),
            "--save-json",
            (
                "examples/runtime_intelligence/"
                "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
            ),
        ],
    }
    assert (
        "optional_guard_evidence_types_present: "
        "[edgeenv_orchestrator_stale_drop_summary, stale_frame_risk]"
        in optional_present_summary
    )
    assert "missing_optional_evidence_types: []" in optional_present_summary
    assert (
        "optional_present_source_artifact: "
        "InferEdgeAIGuard/examples/runtime_intelligence/"
        "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
        in optional_present_summary
    )
    assert (
        "optional_present_reproduction_command: "
        "python -m inferedge_aiguard.cli "
        "build-runtime-intelligence-optional-stale-drop "
        "--edgeenv-regression "
        "examples/runtime_intelligence/"
        "edgeenv_runtime_regression_with_optional_stale_drop_context.json "
        "--remote-dispatch "
        "examples/runtime_intelligence/remote_dispatch_fallback_recovered_result.json "
        "--orchestration-summary "
        "examples/runtime_intelligence/"
        "orchestrator_multi_workload_sustained_summary.json "
        "--save-json "
        "examples/runtime_intelligence/"
        "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
        in optional_present_summary
    )

    ci_summary = (
        output_dir / "runtime_intelligence_ci_artifact_gate_summary.md"
    ).read_text(encoding="utf-8")
    assert "- Status: passed" in ci_summary
    assert "## Validated AIGuard Optional Handoff Context" in ci_summary
    assert (
        "aiguard_optional_context: read_only_optional_guard_context preserved"
        in ci_summary
    )
    assert (
        "aiguard_optional_requirement_boundary: optional evidence not validated as required"
        in ci_summary
    )
    assert (
        "aiguard_optional_types: stale_frame_risk, edgeenv_orchestrator_stale_drop_summary"
        in ci_summary
    )
    assert (
        "aiguard_missing_optional_types: edgeenv_orchestrator_stale_drop_summary, stale_frame_risk"
        in ci_summary
    )
    assert (
        "aiguard_optional_present_types: edgeenv_orchestrator_stale_drop_summary, stale_frame_risk"
        in ci_summary
    )
    assert "aiguard_optional_present_missing_types: none" in ci_summary
    assert (
        "aiguard_optional_present_source_artifact: "
        "InferEdgeAIGuard/examples/runtime_intelligence/"
        "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
        in ci_summary
    )
    assert (
        "aiguard_optional_present_reproduction_command: "
        "python -m inferedge_aiguard.cli "
        "build-runtime-intelligence-optional-stale-drop "
        "--edgeenv-regression "
        "examples/runtime_intelligence/"
        "edgeenv_runtime_regression_with_optional_stale_drop_context.json "
        "--remote-dispatch "
        "examples/runtime_intelligence/remote_dispatch_fallback_recovered_result.json "
        "--orchestration-summary "
        "examples/runtime_intelligence/"
        "orchestrator_multi_workload_sustained_summary.json "
        "--save-json "
        "examples/runtime_intelligence/"
        "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
        in ci_summary
    )
    assert "## Validated Duration Traceability" in ci_summary
    assert (
        "duration_handoff_alignment: EdgeEnv/AIGuard report context preserved"
        in ci_summary
    )
    assert "duration_source: source=entrypoint_requested_frames" in ci_summary
    assert (
        "duration_scope_label: scope_label=source=entrypoint_requested_frames"
        in ci_summary
    )
    assert "duration_label: short 96-frame-class replay (96 frames)" in ci_summary
