from pathlib import Path

from scripts.check_runtime_intelligence_ci_artifacts import main as ci_artifact_gate


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
    assert "examples/runtime_intelligence_chain/edgeenv_lab_handoff_manifest.json" in text
    assert "examples/runtime_intelligence_chain/aiguard_runtime_operation_guard_analysis.json" in text
    assert "examples/runtime_intelligence_chain/aiguard_edgeenv_handoff_alignment.json" in text
    assert "examples/runtime_intelligence_chain/aiguard_edgeenv_handoff_alignment.md" in text
    assert "examples/runtime_intelligence_chain/bundle_manifest.json" in text
    assert "check_runtime_intelligence_bundle_manifest.py" in text
    assert "--edgeenv-handoff" in text
    assert "runtime_intelligence_bundle_manifest_gate_summary.md" in text
    assert "--guard-analysis" in text
    assert "check_runtime_intelligence_artifact_bundle.py" in text
    assert "runtime_anomaly_gate_summary.md" in text
    assert "aiguard_edgeenv_handoff_alignment.json" in text
    assert "aiguard_edgeenv_handoff_alignment.md" in text
    assert "smoke_runtime_intelligence_chain.sh --output-dir" in text
    assert "runtime_intelligence_ci_artifact_gate_summary.md" in text
    assert "deployment_risk_summary.json" in text
    assert "needs:" in text
    assert "inferedge:deterministic-anomaly-summary" in text
    assert "inferedge:portfolio-report" in text
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


def test_runtime_intelligence_ci_artifact_gate_passes_for_expected_outputs(tmp_path):
    report_dir = tmp_path / "runtime_intelligence_ci"
    report_dir.mkdir()
    (report_dir / "edgeenv_runtime_regression.md").write_text(
        "# EdgeEnv Regression\n",
        encoding="utf-8",
    )
    (report_dir / "edgeenv_runtime_regression.html").write_text(
        "<h1>EdgeEnv Regression</h1>",
        encoding="utf-8",
    )
    (report_dir / "runtime_anomaly_summary.html").write_text(
        "<h2>Runtime Intelligence Risk Summary</h2>",
        encoding="utf-8",
    )
    (report_dir / "runtime_anomaly_summary.md").write_text(
        "\n".join(
            [
                "## Runtime Intelligence Risk Summary",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "Runtime telemetry coverage gaps",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "runtime_telemetry_field_gap",
                "Inspect telemetry coverage missing fields",
                "guard_warning_review",
                "edgeenv_runtime_regression_review",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_intelligence_bundle_manifest_gate_summary.md").write_text(
        "\n".join(
            [
                "- Status: passed",
                "## Validated Contract Markers",
                "- source_repositories: Runtime, EdgeEnv, Orchestrator, AIGuard, Lab",
                "- producer_contracts: EdgeEnv history, Orchestrator feed, AIGuard diagnosis",
                "- orchestrator_producer_markers: "
                "source_repository=InferEdgeOrchestrator,"
                "artifact_role=orchestrator-supplemental-operation-context,"
                "producer_contract=inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1",
                "- ownership: regression_owner=edgeenv, deployment_decision_owner=lab",
                "- orchestrator_mapping_hint: coverage_summary_owner=edgeenv",
                "- orchestrator_mapping_hint: operation_context_role=supplemental",
                "- orchestrator_mapping_hint: aiguard_evidence_candidates=runtime_queue_overload,runtime_thermal_instability",
                "- orchestrator_downstream_guard_alignment: producer_lineage_evidence_type=edgeenv_orchestrator_producer_lineage",
                "- orchestrator_device_local_producer_lineage: candidate_context.producer validated",
                "- orchestrator_producer_lineage_shape: per-task source/stage/count mappings validated",
                "- edgeenv_history_seed_run_config: run_config snapshots validated",
                "- aiguard_evidence: edgeenv_orchestrator_producer_lineage validated",
                "- aiguard_evidence: runtime_history_seed_run_config_traceability validated",
                "- aiguard_raw_context: producer_lineage_shape preserved",
                "- aiguard_raw_context: history_seed_run_config_traceability preserved",
                "- aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage",
                "- aiguard_raw_context: orchestrator_mapping_hint preserved",
                "- aiguard_raw_context: orchestrator_producer_markers preserved",
                "- aiguard_raw_context: downstream_guard_alignment preserved",
                "- aiguard_raw_context: producer_lineage_guard_alignment preserved",
                "- aiguard_raw_context: missing_telemetry_orchestrator_context preserved",
                "- aiguard_handoff_alignment: external required evidence types satisfied",
                "- edgeenv_handoff: lab_bundle_alignment validated",
                "- edgeenv_handoff: runtime_telemetry_history validated",
                "- edgeenv_handoff: external AIGuard evidence requirements declared",
                "- edgeenv_handoff: device_local_producer_lineage validated",
                "- edgeenv_handoff: producer_lineage_guard_alignment validated",
                "- edgeenv_handoff: missing_telemetry_orchestrator_context validated",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_anomaly_gate_summary.md").write_text(
        "- Status: passed\n",
        encoding="utf-8",
    )
    (report_dir / "aiguard_edgeenv_handoff_alignment.json").write_text(
        '{"schema_version":"inferedge-aiguard-edgeenv-handoff-alignment-v1",'
        '"status":"passed","decision_owner":"lab","diagnosis_owner":"aiguard",'
        '"handoff_producer_lineage_guard_alignment_run_ids":'
        '["edgeenv-smoke-candidate","edgeenv-smoke-missing"],'
        '"guard_analysis_producer_lineage_guard_alignment_run_ids":'
        '["edgeenv-smoke-candidate","edgeenv-smoke-missing"],'
        '"guard_alignment_summary_errors":[],"errors":[]}',
        encoding="utf-8",
    )
    (report_dir / "aiguard_edgeenv_handoff_alignment.md").write_text(
        "\n".join(
            [
                "- status: passed",
                "- decision_owner: lab",
                "- diagnosis_owner: aiguard",
                "- handoff_producer_lineage_guard_alignment_run_ids: edgeenv-smoke-candidate, edgeenv-smoke-missing",
                "- guard_analysis_producer_lineage_guard_alignment_run_ids: edgeenv-smoke-candidate, edgeenv-smoke-missing",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "portfolio_demo_check.md").write_text(
        "status: pass\n",
        encoding="utf-8",
    )
    (report_dir / "portfolio_demo_check.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    (report_dir / "deployment_risk_summary.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    summary_path = tmp_path / "ci_artifact_gate_summary.md"

    result = ci_artifact_gate(
        report_dir=str(report_dir),
        summary_out=str(summary_path),
    )

    assert result == 0
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Status: passed" in summary


def test_runtime_intelligence_ci_artifact_gate_fails_for_missing_risk_summary(
    tmp_path,
):
    report_dir = tmp_path / "runtime_intelligence_ci"
    report_dir.mkdir()
    for name in (
        "edgeenv_runtime_regression.md",
        "edgeenv_runtime_regression.html",
        "runtime_anomaly_summary.html",
        "portfolio_demo_check.md",
    ):
        (report_dir / name).write_text("placeholder\n", encoding="utf-8")
    (report_dir / "runtime_anomaly_summary.md").write_text(
        "Lab remains the final deployment decision owner.\n",
        encoding="utf-8",
    )
    for name in (
        "runtime_intelligence_bundle_manifest_gate_summary.md",
        "runtime_anomaly_gate_summary.md",
    ):
        (report_dir / name).write_text("- Status: passed\n", encoding="utf-8")
    (report_dir / "portfolio_demo_check.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    (report_dir / "deployment_risk_summary.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    summary_path = tmp_path / "ci_artifact_gate_summary.md"

    result = ci_artifact_gate(
        report_dir=str(report_dir),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "runtime report missing marker: ## Runtime Intelligence Risk Summary" in summary


def test_runtime_intelligence_ci_artifact_gate_fails_for_missing_contract_marker(
    tmp_path,
):
    report_dir = tmp_path / "runtime_intelligence_ci"
    report_dir.mkdir()
    for name in (
        "edgeenv_runtime_regression.md",
        "edgeenv_runtime_regression.html",
        "runtime_anomaly_summary.html",
        "portfolio_demo_check.md",
    ):
        (report_dir / name).write_text("placeholder\n", encoding="utf-8")
    (report_dir / "runtime_anomaly_summary.md").write_text(
        "\n".join(
            [
                "## Runtime Intelligence Risk Summary",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "Runtime telemetry coverage gaps",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "runtime_telemetry_field_gap",
                "Inspect telemetry coverage missing fields",
                "guard_warning_review",
                "edgeenv_runtime_regression_review",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_intelligence_bundle_manifest_gate_summary.md").write_text(
        "\n".join(
            [
                "- Status: passed",
                "## Validated Contract Markers",
                "- source_repositories: Runtime, EdgeEnv, Orchestrator, AIGuard, Lab",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_anomaly_gate_summary.md").write_text(
        "- Status: passed\n",
        encoding="utf-8",
    )
    (report_dir / "portfolio_demo_check.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    (report_dir / "deployment_risk_summary.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    summary_path = tmp_path / "ci_artifact_gate_summary.md"

    result = ci_artifact_gate(
        report_dir=str(report_dir),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert (
        "missing validated contract marker: "
        "orchestrator_mapping_hint: "
        "aiguard_evidence_candidates=runtime_queue_overload,runtime_thermal_instability"
    ) in summary


def test_runtime_intelligence_ci_artifact_gate_fails_for_missing_coverage_gap_marker(
    tmp_path,
):
    report_dir = tmp_path / "runtime_intelligence_ci"
    report_dir.mkdir()
    for name in (
        "edgeenv_runtime_regression.md",
        "edgeenv_runtime_regression.html",
        "runtime_anomaly_summary.html",
        "portfolio_demo_check.md",
    ):
        (report_dir / name).write_text("placeholder\n", encoding="utf-8")
    (report_dir / "runtime_anomaly_summary.md").write_text(
        "\n".join(
            [
                "## Runtime Intelligence Risk Summary",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "Runtime telemetry coverage gaps",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "guard_warning_review",
                "edgeenv_runtime_regression_review",
            ]
        ),
        encoding="utf-8",
    )
    for name in (
        "runtime_intelligence_bundle_manifest_gate_summary.md",
        "runtime_anomaly_gate_summary.md",
    ):
        (report_dir / name).write_text("- Status: passed\n", encoding="utf-8")
    (report_dir / "portfolio_demo_check.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    (report_dir / "deployment_risk_summary.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    summary_path = tmp_path / "ci_artifact_gate_summary.md"

    result = ci_artifact_gate(
        report_dir=str(report_dir),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "runtime report missing marker: runtime_telemetry_field_gap" in summary


def test_runtime_intelligence_ci_artifact_gate_fails_for_failed_deployment_risk(
    tmp_path,
):
    report_dir = tmp_path / "runtime_intelligence_ci"
    report_dir.mkdir()
    for name in (
        "edgeenv_runtime_regression.md",
        "edgeenv_runtime_regression.html",
        "runtime_anomaly_summary.html",
        "portfolio_demo_check.md",
    ):
        (report_dir / name).write_text("placeholder\n", encoding="utf-8")
    (report_dir / "runtime_anomaly_summary.md").write_text(
        "\n".join(
            [
                "## Runtime Intelligence Risk Summary",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "Runtime telemetry coverage gaps",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "runtime_telemetry_field_gap",
                "Inspect telemetry coverage missing fields",
                "guard_warning_review",
                "edgeenv_runtime_regression_review",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_intelligence_bundle_manifest_gate_summary.md").write_text(
        "\n".join(
            [
                "- Status: passed",
                "## Validated Contract Markers",
                "- source_repositories: Runtime, EdgeEnv, Orchestrator, AIGuard, Lab",
                "- producer_contracts: EdgeEnv history, Orchestrator feed, AIGuard diagnosis",
                "- orchestrator_producer_markers: "
                "source_repository=InferEdgeOrchestrator,"
                "artifact_role=orchestrator-supplemental-operation-context,"
                "producer_contract=inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1",
                "- ownership: regression_owner=edgeenv, deployment_decision_owner=lab",
                "- orchestrator_mapping_hint: coverage_summary_owner=edgeenv",
                "- orchestrator_mapping_hint: operation_context_role=supplemental",
                "- orchestrator_mapping_hint: aiguard_evidence_candidates=runtime_queue_overload,runtime_thermal_instability",
                "- orchestrator_downstream_guard_alignment: producer_lineage_evidence_type=edgeenv_orchestrator_producer_lineage",
                "- orchestrator_device_local_producer_lineage: candidate_context.producer validated",
                "- orchestrator_producer_lineage_shape: per-task source/stage/count mappings validated",
                "- edgeenv_history_seed_run_config: run_config snapshots validated",
                "- aiguard_evidence: edgeenv_orchestrator_producer_lineage validated",
                "- aiguard_evidence: runtime_history_seed_run_config_traceability validated",
                "- aiguard_raw_context: producer_lineage_shape preserved",
                "- aiguard_raw_context: history_seed_run_config_traceability preserved",
                "- aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage",
                "- aiguard_raw_context: orchestrator_mapping_hint preserved",
                "- aiguard_raw_context: orchestrator_producer_markers preserved",
                "- aiguard_raw_context: downstream_guard_alignment preserved",
                "- aiguard_raw_context: producer_lineage_guard_alignment preserved",
                "- aiguard_raw_context: missing_telemetry_orchestrator_context preserved",
                "- aiguard_handoff_alignment: external required evidence types satisfied",
                "- edgeenv_handoff: lab_bundle_alignment validated",
                "- edgeenv_handoff: runtime_telemetry_history validated",
                "- edgeenv_handoff: external AIGuard evidence requirements declared",
                "- edgeenv_handoff: device_local_producer_lineage validated",
                "- edgeenv_handoff: producer_lineage_guard_alignment validated",
                "- edgeenv_handoff: missing_telemetry_orchestrator_context validated",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_anomaly_gate_summary.md").write_text(
        "- Status: passed\n",
        encoding="utf-8",
    )
    (report_dir / "aiguard_edgeenv_handoff_alignment.json").write_text(
        '{"schema_version":"inferedge-aiguard-edgeenv-handoff-alignment-v1",'
        '"status":"passed","decision_owner":"lab","diagnosis_owner":"aiguard",'
        '"handoff_producer_lineage_guard_alignment_run_ids":'
        '["edgeenv-smoke-candidate","edgeenv-smoke-missing"],'
        '"guard_analysis_producer_lineage_guard_alignment_run_ids":'
        '["edgeenv-smoke-candidate","edgeenv-smoke-missing"],'
        '"guard_alignment_summary_errors":[],"errors":[]}',
        encoding="utf-8",
    )
    (report_dir / "aiguard_edgeenv_handoff_alignment.md").write_text(
        "\n".join(
            [
                "- status: passed",
                "- decision_owner: lab",
                "- diagnosis_owner: aiguard",
                "- handoff_producer_lineage_guard_alignment_run_ids: edgeenv-smoke-candidate, edgeenv-smoke-missing",
                "- guard_analysis_producer_lineage_guard_alignment_run_ids: edgeenv-smoke-candidate, edgeenv-smoke-missing",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "portfolio_demo_check.json").write_text(
        '{"status": "pass"}',
        encoding="utf-8",
    )
    (report_dir / "deployment_risk_summary.json").write_text(
        '{"status": "fail"}',
        encoding="utf-8",
    )
    summary_path = tmp_path / "ci_artifact_gate_summary.md"

    result = ci_artifact_gate(
        report_dir=str(report_dir),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "deployment_risk_summary.json status must be pass" in summary
