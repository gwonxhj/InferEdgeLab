from pathlib import Path

from scripts.check_runtime_intelligence_ci_artifacts import main as ci_artifact_gate


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "ci" / "gitlab" / "runtime-intelligence-artifacts.yml"
DOC = REPO_ROOT / "docs" / "ci" / "runtime_intelligence_gitlab_artifacts.md"
DURATION_TRACEABILITY_SUMMARY = "\n".join(
    [
        "- Status: passed",
        "## Validated Duration Traceability",
        "- duration_handoff_alignment: EdgeEnv/AIGuard report context preserved",
        "- duration_source: source=entrypoint_requested_frames",
        "- duration_scope_label: scope_label=source=entrypoint_requested_frames",
        "- duration_label: short 96-frame-class replay (96 frames)",
        "## Validated Reviewer Focus",
        "- reviewer_focus_operation_quick_scan: Reviewer Focus / Operation quick scan marker validated",
        "- reviewer_focus_operation_quick_scan_raw_marker: raw marker preserved in Lab report",
        "- reviewer_focus_fixture_matrix: EdgeEnv fixture matrix row validated",
        "## Validated EdgeEnv Fixture Matrix",
        "- edgeenv_fixture_matrix_coverage: EdgeEnv fixture matrix coverage row validated",
        "- edgeenv_fixture_matrix_boundary: comparability-first EdgeEnv boundary preserved",
        "## Validated Review Path",
        "- review_path_section: short Review Path section rendered",
        "- review_path_fast_path: readable Review Path fast path rendered",
        "- review_path: Reviewer Focus -> Detailed Evidence Rows guidance validated",
        "- review_path_scope: comparable regression / telemetry replay / operation evidence preserved",
        "- review_path_artifact_gate_summary: artifact gate summary reference row validated",
    ]
) + "\n"
RUNTIME_REPORT_REVIEW_PATH_MARKERS = [
    "### Review Path",
    "Review path: start with `Reviewer Focus`, then open `Detailed Evidence Rows`",
    "Fast path: `Reviewer Focus` -> `Detailed Evidence Rows` only when a quick signal needs supporting evidence.",
    "| Step | Open | Use it for |",
    "| 3 | `Artifact Gate Summary` | Cross-check `runtime_intelligence_bundle_manifest_gate_summary.md`",
    "`reviewer_path_gate`, `reviewer_path_local_links`, and `reviewer_path_anchor_fragments`",
    "only for comparable regression, telemetry/replay gaps, operation quick scan",
]


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
    assert "lab_expected_report_markers" in text
    assert "lab_report_contract_context" in text
    assert "aiguard_validates_expected_report_markers" in text
    assert "Validated Duration Traceability" in text
    assert "duration_handoff_alignment" in text
    assert "Validated Review Path" in text
    assert "Review path" in text
    assert "runtime_intelligence_ci_artifact_gate_summary.md" in text


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
                *RUNTIME_REPORT_REVIEW_PATH_MARKERS,
                "Runtime replay duration scope",
                "EdgeEnv fixture matrix coverage",
                "schema=edgeenv-regression-replay-fixture-matrix-v1",
                "modes=same-condition,runtime-comparison,target-comparison,protocol_mismatch",
                "not_a_deployment_decision=True",
                "short 96-frame-class replay (96 frames)",
                "source=entrypoint_requested_frames",
                "scope_label=source=entrypoint_requested_frames",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "AIGuard operation risk summary evidence",
                "edgeenv_orchestrator_operation_risk_summary",
                "AIGuard operation risk rollup evidence",
                "edgeenv_orchestrator_operation_risk_rollup",
                "AIGuard task event rollup evidence",
                "edgeenv_orchestrator_task_event_rollup",
                "AIGuard operation timeline evidence",
                "edgeenv_orchestrator_operation_timeline_summary",
                "Lab EdgeEnv preservation context",
                "lab_report_preservation_context_present=True",
                "lab_preservation=present",
                "Runtime telemetry coverage gaps",
                "Operation quick scan",
                "Reviewer operation quick scan",
                "rendered_label=Reviewer operation quick scan",
                "raw_marker=reviewer_focus_operation_quick_scan",
                "Orchestrator queue/deadline/fallback markers",
                "queue_pressure_reason=queue_backlog_threshold_exceeded",
                "max_total_queue_depth=7",
                "preservation=identity=jetson_device_local_preservation",
                "AIGuard max queue raw-context traceability",
                "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "AIGuard remote dispatch event summary",
                "remote_execution_recovered_by_fallback",
                "Remote fallback starter evidence",
                "lab=Remote fallback starter evidence",
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
                "- aiguard_evidence: edgeenv_orchestrator_operation_risk_rollup validated",
                "- aiguard_evidence: edgeenv_orchestrator_task_event_rollup validated",
                "- aiguard_evidence: edgeenv_orchestrator_operation_timeline_summary validated",
                "- aiguard_evidence: runtime_history_seed_run_config_traceability validated",
                "- aiguard_evidence: remote_execution_recovered_by_fallback validated",
                "- aiguard_raw_context: producer_lineage_shape preserved",
                "- aiguard_raw_context: task_event_rollup preserved",
                "- aiguard_raw_context: history_seed_run_config_traceability preserved",
                "- aiguard_raw_context: remote_runtime_event_summary preserved",
                "- aiguard_raw_context: remote_runtime_summary_boundary preserved",
                "- aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage",
                "- aiguard_raw_context: orchestrator_mapping_hint preserved",
                "- aiguard_raw_context: orchestrator_producer_markers preserved",
                "- aiguard_raw_context: downstream_guard_alignment preserved",
                "- aiguard_raw_context: producer_lineage_guard_alignment preserved",
                "- aiguard_raw_context: missing_telemetry_orchestrator_context preserved",
                "- aiguard_raw_context: max_total_queue_depth traceability preserved",
                "- aiguard_handoff_alignment: external required evidence types satisfied",
                "- expected_report_markers: Runtime Intelligence report markers declared",
                "- expected_report_markers: EdgeEnv fixture matrix coverage row declared",
                "- expected_report_markers: remote fallback Lab context row declared",
                "- reviewer_path_gate: README/ecosystem reviewer path gate context declared",
                "- reviewer_path_local_links: local reviewer path link gate context preserved",
                "- reviewer_path_anchor_fragments: reviewer path anchor gate context preserved",
                "- edgeenv_handoff: lab_bundle_alignment validated",
                "- edgeenv_handoff: runtime_telemetry_history validated",
                "- edgeenv_handoff: remote_dispatch_boundary preserved",
                "- edgeenv_handoff: external AIGuard evidence requirements declared",
                "- edgeenv_handoff: optional AIGuard evidence types declared",
                "- edgeenv_handoff: optional AIGuard source traceability declared",
                "- edgeenv_handoff: device_local_producer_lineage validated",
                "- edgeenv_handoff: fixture_matrix_context validated",
                "- edgeenv_handoff: producer_lineage_guard_alignment validated",
                "- edgeenv_handoff: orchestrator_task_event_rollup validated",
                "- edgeenv_handoff: missing_telemetry_orchestrator_context validated",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_anomaly_gate_summary.md").write_text(
        DURATION_TRACEABILITY_SUMMARY,
        encoding="utf-8",
    )
    (report_dir / "aiguard_edgeenv_handoff_alignment.json").write_text(
        '{"schema_version":"inferedge-aiguard-edgeenv-handoff-alignment-v1",'
        '"status":"passed","decision_owner":"lab","diagnosis_owner":"aiguard",'
        '"lab_expected_report_marker_count":17,'
        '"lab_expected_report_markers":['
        '"Runtime Intelligence Risk Summary",'
        '"Runtime replay duration scope",'
        '"Orchestrator operation feed context",'
        '"EdgeEnv fixture matrix coverage",'
        '"Reviewer operation quick scan",'
        '"Orchestrator task event rollup",'
        '"Lab EdgeEnv preservation context",'
        '"AIGuard operation risk rollup evidence",'
        '"AIGuard task event rollup evidence",'
        '"AIGuard operation timeline evidence",'
        '"AIGuard runtime operation anomalies",'
        '"AIGuard remote dispatch event summary",'
        '"AIGuard remote event summary consistency",'
        '"Remote fallback starter evidence",'
        '"lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback",'
        '"AIGuard producer-lineage guard alignment",'
        '"Lab remains the final deployment decision owner."],'
        '"lab_report_marker_owner":"lab",'
        '"report_marker_context_role":"lab_report_contract_context",'
        '"aiguard_validates_expected_report_markers":false,'
        '"optional_evidence_context_role":"read_only_optional_guard_context",'
        '"aiguard_validates_optional_evidence_as_required":false,'
        '"optional_evidence_type_count":2,'
        '"optional_aiguard_evidence_types":'
        '["stale_frame_risk","edgeenv_orchestrator_stale_drop_summary"],'
        '"optional_guard_evidence_types_present":[],'
        '"missing_optional_evidence_types":'
        '["edgeenv_orchestrator_stale_drop_summary","stale_frame_risk"],'
        '"invalid_optional_evidence_types":[],'
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
                "- lab_expected_report_markers: [Runtime Intelligence Risk Summary, Runtime replay duration scope, Orchestrator operation feed context, EdgeEnv fixture matrix coverage, Reviewer operation quick scan, Orchestrator task event rollup, Lab EdgeEnv preservation context, AIGuard operation risk rollup evidence, AIGuard task event rollup evidence, AIGuard operation timeline evidence, AIGuard runtime operation anomalies, AIGuard remote dispatch event summary, AIGuard remote event summary consistency, Remote fallback starter evidence, lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback, AIGuard producer-lineage guard alignment, Lab remains the final deployment decision owner.]",
                "- report_marker_context_role: lab_report_contract_context",
                "- aiguard_validates_expected_report_markers: False",
                "- optional_evidence_context_role: read_only_optional_guard_context",
                "- aiguard_validates_optional_evidence_as_required: False",
                "- optional_aiguard_evidence_types: [stale_frame_risk, edgeenv_orchestrator_stale_drop_summary]",
                "- optional_guard_evidence_types_present: []",
                "- missing_optional_evidence_types: [edgeenv_orchestrator_stale_drop_summary, stale_frame_risk]",
                "- handoff_producer_lineage_guard_alignment_run_ids: [edgeenv-smoke-candidate, edgeenv-smoke-missing]",
                "- guard_analysis_producer_lineage_guard_alignment_run_ids: [edgeenv-smoke-candidate, edgeenv-smoke-missing]",
            ]
        ),
        encoding="utf-8",
    )
    (
        report_dir / "aiguard_edgeenv_handoff_alignment_optional_present.json"
    ).write_text(
        '{"schema_version":"inferedge-aiguard-edgeenv-handoff-alignment-v1",'
        '"status":"passed","decision_owner":"lab","diagnosis_owner":"aiguard",'
        '"lab_expected_report_marker_count":17,'
        '"lab_expected_report_markers":['
        '"Runtime Intelligence Risk Summary",'
        '"Runtime replay duration scope",'
        '"Orchestrator operation feed context",'
        '"EdgeEnv fixture matrix coverage",'
        '"Reviewer operation quick scan",'
        '"Orchestrator task event rollup",'
        '"Lab EdgeEnv preservation context",'
        '"AIGuard operation risk rollup evidence",'
        '"AIGuard task event rollup evidence",'
        '"AIGuard operation timeline evidence",'
        '"AIGuard runtime operation anomalies",'
        '"AIGuard remote dispatch event summary",'
        '"AIGuard remote event summary consistency",'
        '"Remote fallback starter evidence",'
        '"lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback",'
        '"AIGuard producer-lineage guard alignment",'
        '"Lab remains the final deployment decision owner."],'
        '"lab_report_marker_owner":"lab",'
        '"report_marker_context_role":"lab_report_contract_context",'
        '"aiguard_validates_expected_report_markers":false,'
        '"optional_evidence_context_role":"read_only_optional_guard_context",'
        '"aiguard_validates_optional_evidence_as_required":false,'
        '"optional_evidence_type_count":2,'
        '"optional_aiguard_evidence_types":'
        '["stale_frame_risk","edgeenv_orchestrator_stale_drop_summary"],'
        '"optional_guard_evidence_types_present":'
        '["edgeenv_orchestrator_stale_drop_summary","stale_frame_risk"],'
        '"missing_optional_evidence_types":[],'
        '"optional_present_source_artifact":{'
        '"repository":"InferEdgeAIGuard",'
        '"path":"examples/runtime_intelligence/aiguard_runtime_operation_guard_analysis_optional_stale_drop.json",'
        '"schema_version":"inferedge-aiguard-diagnosis-v1",'
        '"role":"aiguard-optional-stale-drop-full-evidence-source",'
        '"context_role":"read_only_cross_repo_traceability",'
        '"reproduction_command":['
        '"python","-m","inferedge_aiguard.cli",'
        '"build-runtime-intelligence-optional-stale-drop",'
        '"--edgeenv-regression",'
        '"examples/runtime_intelligence/edgeenv_runtime_regression_with_optional_stale_drop_context.json",'
        '"--remote-dispatch",'
        '"examples/runtime_intelligence/remote_dispatch_fallback_recovered_result.json",'
        '"--orchestration-summary",'
        '"examples/runtime_intelligence/orchestrator_multi_workload_sustained_summary.json",'
        '"--save-json",'
        '"examples/runtime_intelligence/aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"]},'
        '"invalid_optional_evidence_types":[],'
        '"handoff_producer_lineage_guard_alignment_run_ids":'
        '["edgeenv-smoke-candidate","edgeenv-smoke-missing"],'
        '"guard_analysis_producer_lineage_guard_alignment_run_ids":'
        '["edgeenv-smoke-candidate","edgeenv-smoke-missing"],'
        '"guard_alignment_summary_errors":[],"errors":[]}',
        encoding="utf-8",
    )
    (
        report_dir / "aiguard_edgeenv_handoff_alignment_optional_present.md"
    ).write_text(
        "\n".join(
            [
                "- status: passed",
                "- decision_owner: lab",
                "- diagnosis_owner: aiguard",
                "- lab_expected_report_markers: [Runtime Intelligence Risk Summary, Runtime replay duration scope, Orchestrator operation feed context, EdgeEnv fixture matrix coverage, Reviewer operation quick scan, Orchestrator task event rollup, Lab EdgeEnv preservation context, AIGuard operation risk rollup evidence, AIGuard task event rollup evidence, AIGuard operation timeline evidence, AIGuard runtime operation anomalies, AIGuard remote dispatch event summary, AIGuard remote event summary consistency, Remote fallback starter evidence, lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback, AIGuard producer-lineage guard alignment, Lab remains the final deployment decision owner.]",
                "- report_marker_context_role: lab_report_contract_context",
                "- aiguard_validates_expected_report_markers: False",
                "- optional_evidence_context_role: read_only_optional_guard_context",
                "- aiguard_validates_optional_evidence_as_required: False",
                "- optional_aiguard_evidence_types: [stale_frame_risk, edgeenv_orchestrator_stale_drop_summary]",
                "- optional_guard_evidence_types_present: [edgeenv_orchestrator_stale_drop_summary, stale_frame_risk]",
                "- missing_optional_evidence_types: []",
                "- optional_present_source_artifact: InferEdgeAIGuard/examples/runtime_intelligence/aiguard_runtime_operation_guard_analysis_optional_stale_drop.json",
                "- optional_present_reproduction_command: python -m inferedge_aiguard.cli build-runtime-intelligence-optional-stale-drop --edgeenv-regression examples/runtime_intelligence/edgeenv_runtime_regression_with_optional_stale_drop_context.json --remote-dispatch examples/runtime_intelligence/remote_dispatch_fallback_recovered_result.json --orchestration-summary examples/runtime_intelligence/orchestrator_multi_workload_sustained_summary.json --save-json examples/runtime_intelligence/aiguard_runtime_operation_guard_analysis_optional_stale_drop.json",
                "- handoff_producer_lineage_guard_alignment_run_ids: [edgeenv-smoke-candidate, edgeenv-smoke-missing]",
                "- guard_analysis_producer_lineage_guard_alignment_run_ids: [edgeenv-smoke-candidate, edgeenv-smoke-missing]",
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
    assert "## Validated Duration Traceability" in summary
    assert (
        "duration_handoff_alignment: EdgeEnv/AIGuard report context preserved"
        in summary
    )
    assert "duration_source: source=entrypoint_requested_frames" in summary
    assert (
        "duration_scope_label: scope_label=source=entrypoint_requested_frames"
        in summary
    )
    assert "duration_label: short 96-frame-class replay (96 frames)" in summary
    assert "## Validated Reviewer Focus" in summary
    assert (
        "reviewer_focus_operation_quick_scan: Reviewer Focus / "
        "Operation quick scan marker validated"
    ) in summary
    assert (
        "reviewer_focus_operation_quick_scan_raw_marker: "
        "raw marker preserved in Lab report"
    ) in summary
    assert "## Validated Review Path" in summary
    assert "review_path_section: short Review Path section rendered" in summary
    assert "review_path_fast_path: readable Review Path fast path rendered" in summary
    assert (
        "review_path: Reviewer Focus -> Detailed Evidence Rows guidance validated"
        in summary
    )
    assert (
        "review_path_scope: comparable regression / telemetry replay / "
        "operation evidence preserved"
    ) in summary
    assert (
        "review_path_artifact_gate_summary: artifact gate summary reference row validated"
        in summary
    )
    assert "## Validated AIGuard Optional Handoff Context" in summary
    assert (
        "aiguard_optional_context: read_only_optional_guard_context preserved"
        in summary
    )
    assert (
        "aiguard_optional_requirement_boundary: optional evidence not validated as required"
        in summary
    )
    assert (
        "aiguard_missing_optional_types: edgeenv_orchestrator_stale_drop_summary, stale_frame_risk"
        in summary
    )
    assert (
        "aiguard_optional_present_types: edgeenv_orchestrator_stale_drop_summary, stale_frame_risk"
        in summary
    )
    assert "aiguard_optional_present_missing_types: none" in summary
    assert (
        "aiguard_optional_present_source_artifact: "
        "InferEdgeAIGuard/examples/runtime_intelligence/"
        "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
        in summary
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
        in summary
    )

    (report_dir / "runtime_anomaly_gate_summary.md").write_text(
        "- Status: passed\n",
        encoding="utf-8",
    )
    missing_duration_summary = tmp_path / "ci_artifact_gate_missing_duration.md"

    result = ci_artifact_gate(
        report_dir=str(report_dir),
        summary_out=str(missing_duration_summary),
    )

    assert result == 2
    missing_summary = missing_duration_summary.read_text(encoding="utf-8")
    assert (
        "Runtime Intelligence artifact gate summary missing duration "
        "traceability marker: ## Validated Duration Traceability"
    ) in missing_summary
    assert (
        "Runtime Intelligence artifact gate summary missing reviewer focus "
        "marker: ## Validated Reviewer Focus"
    ) in missing_summary
    assert (
        "Runtime Intelligence artifact gate summary missing review path "
        "marker: ## Validated Review Path"
    ) in missing_summary


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


def test_runtime_intelligence_ci_artifact_gate_fails_for_missing_lab_marker_context(
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
                *RUNTIME_REPORT_REVIEW_PATH_MARKERS,
                "Runtime replay duration scope",
                "EdgeEnv fixture matrix coverage",
                "schema=edgeenv-regression-replay-fixture-matrix-v1",
                "modes=same-condition,runtime-comparison,target-comparison,protocol_mismatch",
                "not_a_deployment_decision=True",
                "short 96-frame-class replay (96 frames)",
                "source=entrypoint_requested_frames",
                "scope_label=source=entrypoint_requested_frames",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "AIGuard operation risk summary evidence",
                "edgeenv_orchestrator_operation_risk_summary",
                "AIGuard operation risk rollup evidence",
                "edgeenv_orchestrator_operation_risk_rollup",
                "AIGuard task event rollup evidence",
                "edgeenv_orchestrator_task_event_rollup",
                "AIGuard operation timeline evidence",
                "edgeenv_orchestrator_operation_timeline_summary",
                "Lab EdgeEnv preservation context",
                "lab_report_preservation_context_present=True",
                "lab_preservation=present",
                "Runtime telemetry coverage gaps",
                "Operation quick scan",
                "Reviewer operation quick scan",
                "rendered_label=Reviewer operation quick scan",
                "raw_marker=reviewer_focus_operation_quick_scan",
                "Orchestrator queue/deadline/fallback markers",
                "queue_pressure_reason=queue_backlog_threshold_exceeded",
                "max_total_queue_depth=7",
                "preservation=identity=jetson_device_local_preservation",
                "AIGuard max queue raw-context traceability",
                "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "AIGuard remote dispatch event summary",
                "remote_execution_recovered_by_fallback",
                "Remote fallback starter evidence",
                "lab=Remote fallback starter evidence",
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
                "- aiguard_evidence: edgeenv_orchestrator_operation_risk_rollup validated",
                "- aiguard_evidence: edgeenv_orchestrator_task_event_rollup validated",
                "- aiguard_evidence: edgeenv_orchestrator_operation_timeline_summary validated",
                "- aiguard_evidence: runtime_history_seed_run_config_traceability validated",
                "- aiguard_evidence: remote_execution_recovered_by_fallback validated",
                "- aiguard_raw_context: producer_lineage_shape preserved",
                "- aiguard_raw_context: task_event_rollup preserved",
                "- aiguard_raw_context: history_seed_run_config_traceability preserved",
                "- aiguard_raw_context: remote_runtime_event_summary preserved",
                "- aiguard_raw_context: remote_runtime_summary_boundary preserved",
                "- aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage",
                "- aiguard_raw_context: orchestrator_mapping_hint preserved",
                "- aiguard_raw_context: orchestrator_producer_markers preserved",
                "- aiguard_raw_context: downstream_guard_alignment preserved",
                "- aiguard_raw_context: producer_lineage_guard_alignment preserved",
                "- aiguard_raw_context: missing_telemetry_orchestrator_context preserved",
                "- aiguard_raw_context: max_total_queue_depth traceability preserved",
                "- aiguard_handoff_alignment: external required evidence types satisfied",
                "- expected_report_markers: Runtime Intelligence report markers declared",
                "- expected_report_markers: EdgeEnv fixture matrix coverage row declared",
                "- expected_report_markers: remote fallback Lab context row declared",
                "- reviewer_path_gate: README/ecosystem reviewer path gate context declared",
                "- reviewer_path_local_links: local reviewer path link gate context preserved",
                "- reviewer_path_anchor_fragments: reviewer path anchor gate context preserved",
                "- edgeenv_handoff: lab_bundle_alignment validated",
                "- edgeenv_handoff: runtime_telemetry_history validated",
                "- edgeenv_handoff: remote_dispatch_boundary preserved",
                "- edgeenv_handoff: external AIGuard evidence requirements declared",
                "- edgeenv_handoff: optional AIGuard evidence types declared",
                "- edgeenv_handoff: optional AIGuard source traceability declared",
                "- edgeenv_handoff: device_local_producer_lineage validated",
                "- edgeenv_handoff: fixture_matrix_context validated",
                "- edgeenv_handoff: producer_lineage_guard_alignment validated",
                "- edgeenv_handoff: orchestrator_task_event_rollup validated",
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
        "aiguard_edgeenv_handoff_alignment.json lab_expected_report_markers "
        "must match Lab report contract"
    ) in summary


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
                *RUNTIME_REPORT_REVIEW_PATH_MARKERS,
                "Runtime replay duration scope",
                "EdgeEnv fixture matrix coverage",
                "schema=edgeenv-regression-replay-fixture-matrix-v1",
                "modes=same-condition,runtime-comparison,target-comparison,protocol_mismatch",
                "not_a_deployment_decision=True",
                "short 96-frame-class replay (96 frames)",
                "source=entrypoint_requested_frames",
                "scope_label=source=entrypoint_requested_frames",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "AIGuard operation risk summary evidence",
                "edgeenv_orchestrator_operation_risk_summary",
                "AIGuard operation risk rollup evidence",
                "edgeenv_orchestrator_operation_risk_rollup",
                "AIGuard task event rollup evidence",
                "edgeenv_orchestrator_task_event_rollup",
                "AIGuard operation timeline evidence",
                "edgeenv_orchestrator_operation_timeline_summary",
                "Lab EdgeEnv preservation context",
                "lab_report_preservation_context_present=True",
                "lab_preservation=present",
                "Runtime telemetry coverage gaps",
                "Operation quick scan",
                "Reviewer operation quick scan",
                "rendered_label=Reviewer operation quick scan",
                "raw_marker=reviewer_focus_operation_quick_scan",
                "Orchestrator queue/deadline/fallback markers",
                "queue_pressure_reason=queue_backlog_threshold_exceeded",
                "max_total_queue_depth=7",
                "preservation=identity=jetson_device_local_preservation",
                "AIGuard max queue raw-context traceability",
                "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "AIGuard remote dispatch event summary",
                "remote_execution_recovered_by_fallback",
                "Remote fallback starter evidence",
                "lab=Remote fallback starter evidence",
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
                *RUNTIME_REPORT_REVIEW_PATH_MARKERS,
                "Runtime replay duration scope",
                "EdgeEnv fixture matrix coverage",
                "schema=edgeenv-regression-replay-fixture-matrix-v1",
                "modes=same-condition,runtime-comparison,target-comparison,protocol_mismatch",
                "not_a_deployment_decision=True",
                "short 96-frame-class replay (96 frames)",
                "source=entrypoint_requested_frames",
                "scope_label=source=entrypoint_requested_frames",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "AIGuard operation risk summary evidence",
                "edgeenv_orchestrator_operation_risk_summary",
                "AIGuard operation risk rollup evidence",
                "edgeenv_orchestrator_operation_risk_rollup",
                "AIGuard task event rollup evidence",
                "edgeenv_orchestrator_task_event_rollup",
                "AIGuard operation timeline evidence",
                "edgeenv_orchestrator_operation_timeline_summary",
                "Lab EdgeEnv preservation context",
                "lab_report_preservation_context_present=True",
                "lab_preservation=present",
                "Runtime telemetry coverage gaps",
                "Operation quick scan",
                "Reviewer operation quick scan",
                "rendered_label=Reviewer operation quick scan",
                "raw_marker=reviewer_focus_operation_quick_scan",
                "Orchestrator queue/deadline/fallback markers",
                "queue_pressure_reason=queue_backlog_threshold_exceeded",
                "max_total_queue_depth=7",
                "preservation=identity=jetson_device_local_preservation",
                "AIGuard max queue raw-context traceability",
                "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "AIGuard remote dispatch event summary",
                "remote_execution_recovered_by_fallback",
                "Remote fallback starter evidence",
                "lab=Remote fallback starter evidence",
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
                *RUNTIME_REPORT_REVIEW_PATH_MARKERS,
                "Runtime replay duration scope",
                "EdgeEnv fixture matrix coverage",
                "schema=edgeenv-regression-replay-fixture-matrix-v1",
                "modes=same-condition,runtime-comparison,target-comparison,protocol_mismatch",
                "not_a_deployment_decision=True",
                "short 96-frame-class replay (96 frames)",
                "source=entrypoint_requested_frames",
                "scope_label=source=entrypoint_requested_frames",
                "Lab remains the final deployment decision owner.",
                "AIGuard runtime operation anomalies",
                "runtime_queue_overload, runtime_thermal_instability",
                "AIGuard operation risk summary evidence",
                "edgeenv_orchestrator_operation_risk_summary",
                "AIGuard operation risk rollup evidence",
                "edgeenv_orchestrator_operation_risk_rollup",
                "AIGuard task event rollup evidence",
                "edgeenv_orchestrator_task_event_rollup",
                "AIGuard operation timeline evidence",
                "edgeenv_orchestrator_operation_timeline_summary",
                "Lab EdgeEnv preservation context",
                "lab_report_preservation_context_present=True",
                "lab_preservation=present",
                "Runtime telemetry coverage gaps",
                "Operation quick scan",
                "Reviewer operation quick scan",
                "rendered_label=Reviewer operation quick scan",
                "raw_marker=reviewer_focus_operation_quick_scan",
                "Orchestrator queue/deadline/fallback markers",
                "queue_pressure_reason=queue_backlog_threshold_exceeded",
                "max_total_queue_depth=7",
                "preservation=identity=jetson_device_local_preservation",
                "AIGuard max queue raw-context traceability",
                "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7",
                "AIGuard producer-lineage guard alignment",
                "edgeenv_orchestrator_producer_lineage",
                "AIGuard run_config traceability evidence",
                "runtime_history_seed_run_config_traceability",
                "AIGuard remote dispatch event summary",
                "remote_execution_recovered_by_fallback",
                "Remote fallback starter evidence",
                "lab=Remote fallback starter evidence",
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
                "- aiguard_evidence: edgeenv_orchestrator_operation_risk_rollup validated",
                "- aiguard_evidence: edgeenv_orchestrator_task_event_rollup validated",
                "- aiguard_evidence: edgeenv_orchestrator_operation_timeline_summary validated",
                "- aiguard_evidence: runtime_history_seed_run_config_traceability validated",
                "- aiguard_evidence: remote_execution_recovered_by_fallback validated",
                "- aiguard_raw_context: producer_lineage_shape preserved",
                "- aiguard_raw_context: task_event_rollup preserved",
                "- aiguard_raw_context: history_seed_run_config_traceability preserved",
                "- aiguard_raw_context: remote_runtime_event_summary preserved",
                "- aiguard_raw_context: remote_runtime_summary_boundary preserved",
                "- aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage",
                "- aiguard_raw_context: orchestrator_mapping_hint preserved",
                "- aiguard_raw_context: orchestrator_producer_markers preserved",
                "- aiguard_raw_context: downstream_guard_alignment preserved",
                "- aiguard_raw_context: producer_lineage_guard_alignment preserved",
                "- aiguard_raw_context: missing_telemetry_orchestrator_context preserved",
                "- aiguard_raw_context: max_total_queue_depth traceability preserved",
                "- aiguard_handoff_alignment: external required evidence types satisfied",
                "- expected_report_markers: Runtime Intelligence report markers declared",
                "- expected_report_markers: EdgeEnv fixture matrix coverage row declared",
                "- expected_report_markers: remote fallback Lab context row declared",
                "- reviewer_path_gate: README/ecosystem reviewer path gate context declared",
                "- reviewer_path_local_links: local reviewer path link gate context preserved",
                "- reviewer_path_anchor_fragments: reviewer path anchor gate context preserved",
                "- edgeenv_handoff: lab_bundle_alignment validated",
                "- edgeenv_handoff: runtime_telemetry_history validated",
                "- edgeenv_handoff: remote_dispatch_boundary preserved",
                "- edgeenv_handoff: external AIGuard evidence requirements declared",
                "- edgeenv_handoff: optional AIGuard evidence types declared",
                "- edgeenv_handoff: optional AIGuard source traceability declared",
                "- edgeenv_handoff: device_local_producer_lineage validated",
                "- edgeenv_handoff: fixture_matrix_context validated",
                "- edgeenv_handoff: producer_lineage_guard_alignment validated",
                "- edgeenv_handoff: orchestrator_task_event_rollup validated",
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
        '"lab_expected_report_marker_count":17,'
        '"lab_expected_report_markers":['
        '"Runtime Intelligence Risk Summary",'
        '"Runtime replay duration scope",'
        '"Orchestrator operation feed context",'
        '"EdgeEnv fixture matrix coverage",'
        '"Reviewer operation quick scan",'
        '"Orchestrator task event rollup",'
        '"Lab EdgeEnv preservation context",'
        '"AIGuard operation risk rollup evidence",'
        '"AIGuard task event rollup evidence",'
        '"AIGuard operation timeline evidence",'
        '"AIGuard runtime operation anomalies",'
        '"AIGuard remote dispatch event summary",'
        '"AIGuard remote event summary consistency",'
        '"Remote fallback starter evidence",'
        '"lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback",'
        '"AIGuard producer-lineage guard alignment",'
        '"Lab remains the final deployment decision owner."],'
        '"lab_report_marker_owner":"lab",'
        '"report_marker_context_role":"lab_report_contract_context",'
        '"aiguard_validates_expected_report_markers":false,'
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
                "- lab_expected_report_markers: Runtime Intelligence Risk Summary, Runtime replay duration scope, Orchestrator operation feed context, EdgeEnv fixture matrix coverage, Reviewer operation quick scan, Orchestrator task event rollup, Lab EdgeEnv preservation context, AIGuard operation risk rollup evidence, AIGuard task event rollup evidence, AIGuard operation timeline evidence, AIGuard runtime operation anomalies, AIGuard remote dispatch event summary, AIGuard remote event summary consistency, Remote fallback starter evidence, lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback, AIGuard producer-lineage guard alignment, Lab remains the final deployment decision owner.",
                "- report_marker_context_role: lab_report_contract_context",
                "- aiguard_validates_expected_report_markers: False",
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
