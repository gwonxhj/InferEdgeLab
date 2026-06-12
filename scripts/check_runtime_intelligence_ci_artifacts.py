from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_MARKDOWN_ARTIFACTS = {
    "edgeenv_runtime_regression.md",
    "runtime_anomaly_summary.md",
    "portfolio_demo_check.md",
}
REQUIRED_HTML_ARTIFACTS = {
    "edgeenv_runtime_regression.html",
    "runtime_anomaly_summary.html",
}
REQUIRED_SUMMARY_ARTIFACTS = {
    "aiguard_edgeenv_handoff_alignment.md",
    "aiguard_edgeenv_handoff_alignment_optional_present.md",
    "runtime_intelligence_source_traceability_summary.md",
    "runtime_intelligence_bundle_manifest_gate_summary.md",
    "runtime_anomaly_gate_summary.md",
}
REQUIRED_JSON_ARTIFACTS = {
    "aiguard_edgeenv_handoff_alignment.json",
    "aiguard_edgeenv_handoff_alignment_optional_present.json",
    "portfolio_demo_check.json",
    "deployment_risk_summary.json",
}
REQUIRED_BUNDLE_MANIFEST_SUMMARY_MARKERS = (
    "## Validated Contract Markers",
    "source_repositories: Runtime, EdgeEnv, Orchestrator, AIGuard, Lab",
    "producer_contracts: EdgeEnv history, Orchestrator feed, AIGuard diagnosis",
    "orchestrator_producer_markers: "
    "source_repository=InferEdgeOrchestrator,"
    "artifact_role=orchestrator-supplemental-operation-context,"
    "producer_contract=inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1",
    "ownership: regression_owner=edgeenv, deployment_decision_owner=lab",
    "orchestrator_mapping_hint: coverage_summary_owner=edgeenv",
    "orchestrator_mapping_hint: operation_context_role=supplemental",
    "orchestrator_mapping_hint: aiguard_evidence_candidates=runtime_queue_overload,runtime_thermal_instability",
    "orchestrator_downstream_guard_alignment: producer_lineage_evidence_type=edgeenv_orchestrator_producer_lineage",
    "orchestrator_device_local_producer_lineage: candidate_context.producer validated",
    "orchestrator_producer_lineage_shape: per-task source/stage/count mappings validated",
    "edgeenv_history_seed_run_config: run_config snapshots validated",
    "aiguard_evidence: edgeenv_orchestrator_producer_lineage validated",
    "aiguard_evidence: edgeenv_orchestrator_task_event_rollup validated",
    "aiguard_evidence: edgeenv_orchestrator_operation_timeline_summary validated",
    "aiguard_evidence: runtime_history_seed_run_config_traceability validated",
    "aiguard_evidence: remote_execution_recovered_by_fallback validated",
    "aiguard_raw_context: producer_lineage_shape preserved",
    "aiguard_raw_context: task_event_rollup preserved",
    "aiguard_raw_context: history_seed_run_config_traceability preserved",
    "aiguard_raw_context: remote_runtime_event_summary preserved",
    "aiguard_raw_context: remote_runtime_summary_boundary preserved",
    "aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage",
    "aiguard_raw_context: orchestrator_mapping_hint preserved",
    "aiguard_raw_context: orchestrator_producer_markers preserved",
    "aiguard_raw_context: downstream_guard_alignment preserved",
    "aiguard_raw_context: producer_lineage_guard_alignment preserved",
    "aiguard_raw_context: missing_telemetry_orchestrator_context preserved",
    "aiguard_raw_context: max_total_queue_depth traceability preserved",
    "aiguard_handoff_alignment: external required evidence types satisfied",
    "expected_report_markers: Runtime Intelligence report markers declared",
    "expected_report_markers: EdgeEnv fixture matrix coverage row declared",
    "expected_report_markers: remote fallback Lab context row declared",
    "reviewer_path_gate: README/ecosystem reviewer path gate context declared",
    "reviewer_path_local_links: local reviewer path link gate context preserved",
    "reviewer_path_anchor_fragments: reviewer path anchor gate context preserved",
    "edgeenv_handoff: lab_bundle_alignment validated",
    "edgeenv_handoff: runtime_telemetry_history validated",
    "edgeenv_handoff: external AIGuard evidence requirements declared",
    "edgeenv_handoff: device_local_producer_lineage validated",
    "edgeenv_handoff: fixture_matrix_context validated",
    "edgeenv_handoff: producer_lineage_guard_alignment validated",
    "edgeenv_handoff: orchestrator_task_event_rollup validated",
    "edgeenv_handoff: missing_telemetry_orchestrator_context validated",
    "edgeenv_handoff: optional AIGuard evidence types declared",
    "edgeenv_handoff: optional AIGuard source traceability declared",
)
REQUIRED_LAB_EXPECTED_REPORT_MARKERS = (
    "Runtime Intelligence Risk Summary",
    "Runtime replay duration scope",
    "Orchestrator operation feed context",
    "EdgeEnv fixture matrix coverage",
    "Reviewer operation quick scan",
    "Orchestrator task event rollup",
    "Lab EdgeEnv preservation context",
    "AIGuard operation risk rollup evidence",
    "AIGuard task event rollup evidence",
    "AIGuard operation timeline evidence",
    "AIGuard runtime operation anomalies",
    "AIGuard remote dispatch event summary",
    "AIGuard remote event summary consistency",
    "Remote fallback starter evidence",
    "lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback",
    "AIGuard producer-lineage guard alignment",
    "Lab remains the final deployment decision owner.",
)
REQUIRED_AIGUARD_ALIGNMENT_RUN_IDS = [
    "edgeenv-smoke-candidate",
    "edgeenv-smoke-missing",
]
REQUIRED_AIGUARD_OPTIONAL_EVIDENCE_TYPES = [
    "stale_frame_risk",
    "edgeenv_orchestrator_stale_drop_summary",
]
REQUIRED_AIGUARD_MISSING_OPTIONAL_EVIDENCE_TYPES = [
    "edgeenv_orchestrator_stale_drop_summary",
    "stale_frame_risk",
]
REQUIRED_AIGUARD_PRESENT_OPTIONAL_EVIDENCE_TYPES = [
    "edgeenv_orchestrator_stale_drop_summary",
    "stale_frame_risk",
]
REQUIRED_AIGUARD_OPTIONAL_PRESENT_SOURCE_ARTIFACT_MARKER = (
    "InferEdgeAIGuard/examples/runtime_intelligence/"
    "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
)
REQUIRED_AIGUARD_OPTIONAL_PRESENT_REPRODUCTION_COMMAND = [
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
    "examples/runtime_intelligence/remote_dispatch_fallback_recovered_result.json",
    "--orchestration-summary",
    "examples/runtime_intelligence/orchestrator_multi_workload_sustained_summary.json",
    "--save-json",
    (
        "examples/runtime_intelligence/"
        "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
    ),
]
REQUIRED_AIGUARD_OPTIONAL_PRESENT_REPRODUCTION_COMMAND_MARKER = " ".join(
    REQUIRED_AIGUARD_OPTIONAL_PRESENT_REPRODUCTION_COMMAND
)
REQUIRED_AIGUARD_OPTIONAL_PRESENT_SOURCE_ARTIFACT = {
    "repository": "InferEdgeAIGuard",
    "path": (
        "examples/runtime_intelligence/"
        "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
    ),
    "schema_version": "inferedge-aiguard-diagnosis-v1",
    "role": "aiguard-optional-stale-drop-full-evidence-source",
    "context_role": "read_only_cross_repo_traceability",
    "reproduction_command": REQUIRED_AIGUARD_OPTIONAL_PRESENT_REPRODUCTION_COMMAND,
}
REQUIRED_AIGUARD_OPTIONAL_CONTEXT_SUMMARY_MARKERS = (
    "## Validated AIGuard Optional Handoff Context",
    "aiguard_optional_context: read_only_optional_guard_context preserved",
    "aiguard_optional_requirement_boundary: optional evidence not validated as required",
    "aiguard_optional_types: stale_frame_risk, edgeenv_orchestrator_stale_drop_summary",
    "aiguard_missing_optional_types: edgeenv_orchestrator_stale_drop_summary, stale_frame_risk",
    "aiguard_optional_present_types: edgeenv_orchestrator_stale_drop_summary, stale_frame_risk",
    "aiguard_optional_present_missing_types: none",
    "aiguard_optional_present_source_artifact: "
    f"{REQUIRED_AIGUARD_OPTIONAL_PRESENT_SOURCE_ARTIFACT_MARKER}",
    "aiguard_optional_present_reproduction_command: "
    f"{REQUIRED_AIGUARD_OPTIONAL_PRESENT_REPRODUCTION_COMMAND_MARKER}",
)
REQUIRED_SOURCE_TRACEABILITY_SUMMARY_MARKERS = (
    "## Validated Source Traceability",
    "source_traceability_alignment: EdgeEnv handoff and AIGuard optional-present fixture match",
    "edgeenv_optional_source_traceability: read_only_optional_source_traceability preserved",
    "aiguard_optional_present_source_artifact: "
    f"{REQUIRED_AIGUARD_OPTIONAL_PRESENT_SOURCE_ARTIFACT_MARKER}",
    "aiguard_optional_present_reproduction_command: "
    f"{REQUIRED_AIGUARD_OPTIONAL_PRESENT_REPRODUCTION_COMMAND_MARKER}",
    "ownership: edgeenv_does_not_generate_guard_analysis=true, lab_is_final_decision_owner=true",
)
REQUIRED_DURATION_TRACEABILITY_SUMMARY_MARKERS = (
    "## Validated Duration Traceability",
    "duration_handoff_alignment: EdgeEnv/AIGuard report context preserved",
    "duration_source: source=entrypoint_requested_frames",
    "duration_scope_label: scope_label=source=entrypoint_requested_frames",
    "duration_label: short 96-frame-class replay (96 frames)",
)
REQUIRED_REVIEWER_FOCUS_SUMMARY_MARKERS = (
    "## Validated Reviewer Focus",
    "reviewer_focus_operation_quick_scan: Reviewer Focus / Operation quick scan marker validated",
    "reviewer_focus_operation_quick_scan_raw_marker: raw marker preserved in Lab report",
    "reviewer_focus_fixture_matrix: EdgeEnv fixture matrix row validated",
)
REQUIRED_REVIEW_PATH_SUMMARY_MARKERS = (
    "## Validated Review Path",
    "review_path_section: short Review Path section rendered",
    "review_path_fast_path: readable Review Path fast path rendered",
    "review_path: Reviewer Focus -> Detailed Evidence Rows guidance validated",
    "review_path_scope: comparable regression / telemetry replay / operation evidence preserved",
    "review_path_artifact_gate_summary: artifact gate summary reference row validated",
)


def _record(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def _read_text(path: Path, errors: list[str], label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        errors.append(f"{label} not found: {path}")
        return ""


def _load_json(path: Path, errors: list[str], label: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        errors.append(f"{label} not found: {path}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is invalid JSON: {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{label} must be a JSON object: {path}")
        return {}
    return payload


def _format_markdown_inline_list(values: list[str]) -> str:
    return f"[{', '.join(values)}]" if values else "[]"


def _validate_required_files(report_dir: Path, errors: list[str]) -> None:
    for name in sorted(
        REQUIRED_MARKDOWN_ARTIFACTS
        | REQUIRED_HTML_ARTIFACTS
        | REQUIRED_SUMMARY_ARTIFACTS
        | REQUIRED_JSON_ARTIFACTS
    ):
        _record((report_dir / name).is_file(), errors, f"missing artifact: {name}")


def _validate_runtime_artifact_gate_summary(path: Path, errors: list[str]) -> None:
    label = "Runtime Intelligence artifact gate summary"
    text = _read_text(path, errors, label)
    if not text:
        return
    _record("- Status: passed" in text, errors, f"{label} must have passed status")
    for marker in REQUIRED_DURATION_TRACEABILITY_SUMMARY_MARKERS:
        _record(
            marker in text,
            errors,
            f"{label} missing duration traceability marker: {marker}",
        )
    for marker in REQUIRED_REVIEWER_FOCUS_SUMMARY_MARKERS:
        _record(
            marker in text,
            errors,
            f"{label} missing reviewer focus marker: {marker}",
        )
    for marker in REQUIRED_REVIEW_PATH_SUMMARY_MARKERS:
        _record(
            marker in text,
            errors,
            f"{label} missing review path marker: {marker}",
        )


def _validate_bundle_manifest_gate_summary(path: Path, errors: list[str]) -> None:
    label = "Runtime Intelligence bundle manifest gate summary"
    text = _read_text(path, errors, label)
    if not text:
        return
    _record("- Status: passed" in text, errors, f"{label} must have passed status")
    for marker in REQUIRED_BUNDLE_MANIFEST_SUMMARY_MARKERS:
        _record(
            marker in text,
            errors,
            f"{label} missing validated contract marker: {marker}",
        )


def _validate_source_traceability_summary(path: Path, errors: list[str]) -> None:
    label = "Runtime Intelligence source traceability summary"
    text = _read_text(path, errors, label)
    if not text:
        return
    _record("- Status: passed" in text, errors, f"{label} must have passed status")
    for marker in REQUIRED_SOURCE_TRACEABILITY_SUMMARY_MARKERS:
        _record(
            marker in text,
            errors,
            f"{label} missing source traceability marker: {marker}",
        )


def _validate_runtime_report(path: Path, errors: list[str]) -> None:
    text = _read_text(path, errors, "Runtime Intelligence Markdown report")
    if not text:
        return
    for marker in (
        "## Runtime Intelligence Risk Summary",
        "### Review Path",
        "Review path: start with `Reviewer Focus`, then open `Detailed Evidence Rows`",
        "Fast path: `Reviewer Focus` -> `Detailed Evidence Rows` only when a quick signal needs supporting evidence.",
        "| Step | Open | Use it for |",
        "| 3 | `Artifact Gate Summary` | Cross-check `runtime_intelligence_bundle_manifest_gate_summary.md`",
        "`reviewer_path_gate`, `reviewer_path_local_links`, and `reviewer_path_anchor_fragments`",
        "only for comparable regression, telemetry/replay gaps, operation quick scan",
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
        "Lab EdgeEnv preservation context",
        "lab_report_preservation_context_present=True",
        "lab_preservation=present",
        "edgeenv_orchestrator_task_event_rollup",
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
    ):
        _record(marker in text, errors, f"runtime report missing marker: {marker}")


def _validate_portfolio_status(path: Path, errors: list[str]) -> None:
    payload = _load_json(path, errors, "Portfolio demo check JSON")
    if payload:
        _record(
            payload.get("status") == "pass",
            errors,
            "portfolio_demo_check.json status must be pass",
        )


def _validate_deployment_risk_status(path: Path, errors: list[str]) -> None:
    payload = _load_json(path, errors, "Deployment risk summary JSON")
    if payload:
        _record(
            payload.get("status") == "pass",
            errors,
            "deployment_risk_summary.json status must be pass",
        )


def _validate_aiguard_handoff_alignment(
    json_path: Path,
    markdown_path: Path,
    errors: list[str],
    *,
    expected_optional_guard_evidence_types_present: list[str] | None = None,
    expected_missing_optional_evidence_types: list[str] | None = None,
    expected_optional_present_source_artifact: dict[str, str] | None = None,
) -> None:
    expected_optional_guard_evidence_types_present = (
        expected_optional_guard_evidence_types_present
        if expected_optional_guard_evidence_types_present is not None
        else []
    )
    expected_missing_optional_evidence_types = (
        expected_missing_optional_evidence_types
        if expected_missing_optional_evidence_types is not None
        else REQUIRED_AIGUARD_MISSING_OPTIONAL_EVIDENCE_TYPES
    )
    payload = _load_json(json_path, errors, "AIGuard EdgeEnv handoff alignment JSON")
    if payload:
        _record(
            payload.get("schema_version")
            == "inferedge-aiguard-edgeenv-handoff-alignment-v1",
            errors,
            "aiguard_edgeenv_handoff_alignment.json schema_version is invalid",
        )
        _record(
            payload.get("status") == "passed",
            errors,
            "aiguard_edgeenv_handoff_alignment.json status must be passed",
        )
        _record(
            payload.get("decision_owner") == "lab",
            errors,
            "aiguard_edgeenv_handoff_alignment.json decision_owner must be lab",
        )
        _record(
            payload.get("diagnosis_owner") == "aiguard",
            errors,
            "aiguard_edgeenv_handoff_alignment.json diagnosis_owner must be aiguard",
        )
        _record(
            payload.get("lab_report_marker_owner") == "lab",
            errors,
            "aiguard_edgeenv_handoff_alignment.json lab_report_marker_owner must be lab",
        )
        _record(
            payload.get("report_marker_context_role") == "lab_report_contract_context",
            errors,
            "aiguard_edgeenv_handoff_alignment.json report_marker_context_role must be lab_report_contract_context",
        )
        _record(
            payload.get("aiguard_validates_expected_report_markers") is False,
            errors,
            "aiguard_edgeenv_handoff_alignment.json must not claim AIGuard validates Lab report markers",
        )
        _record(
            payload.get("optional_evidence_context_role")
            == "read_only_optional_guard_context",
            errors,
            "aiguard_edgeenv_handoff_alignment.json optional_evidence_context_role must be read_only_optional_guard_context",
        )
        _record(
            payload.get("aiguard_validates_optional_evidence_as_required") is False,
            errors,
            "aiguard_edgeenv_handoff_alignment.json must not validate optional evidence as required",
        )
        _record(
            payload.get("optional_evidence_type_count")
            == len(REQUIRED_AIGUARD_OPTIONAL_EVIDENCE_TYPES),
            errors,
            "aiguard_edgeenv_handoff_alignment.json optional_evidence_type_count is invalid",
        )
        _record(
            payload.get("optional_aiguard_evidence_types")
            == REQUIRED_AIGUARD_OPTIONAL_EVIDENCE_TYPES,
            errors,
            "aiguard_edgeenv_handoff_alignment.json optional evidence types must match EdgeEnv handoff context",
        )
        _record(
            payload.get("optional_guard_evidence_types_present")
            == expected_optional_guard_evidence_types_present,
            errors,
            "aiguard_edgeenv_handoff_alignment.json optional evidence present list must reflect the bundled guard artifact",
        )
        _record(
            payload.get("missing_optional_evidence_types")
            == expected_missing_optional_evidence_types,
            errors,
            "aiguard_edgeenv_handoff_alignment.json missing optional evidence types must remain read-only context",
        )
        _record(
            payload.get("invalid_optional_evidence_types") == [],
            errors,
            "aiguard_edgeenv_handoff_alignment.json invalid_optional_evidence_types must be empty",
        )
        if expected_optional_present_source_artifact is not None:
            _record(
                payload.get("optional_present_source_artifact")
                == expected_optional_present_source_artifact,
                errors,
                "aiguard_edgeenv_handoff_alignment.json optional-present source artifact must point to the AIGuard full evidence example",
            )
        _record(
            payload.get("lab_expected_report_marker_count")
            == len(REQUIRED_LAB_EXPECTED_REPORT_MARKERS),
            errors,
            "aiguard_edgeenv_handoff_alignment.json lab_expected_report_marker_count is invalid",
        )
        _record(
            payload.get("lab_expected_report_markers")
            == list(REQUIRED_LAB_EXPECTED_REPORT_MARKERS),
            errors,
            "aiguard_edgeenv_handoff_alignment.json lab_expected_report_markers must match Lab report contract",
        )
        _record(
            payload.get("handoff_producer_lineage_guard_alignment_run_ids")
            == REQUIRED_AIGUARD_ALIGNMENT_RUN_IDS,
            errors,
            "AIGuard alignment handoff run IDs must match EdgeEnv summary",
        )
        _record(
            payload.get("guard_analysis_producer_lineage_guard_alignment_run_ids")
            == REQUIRED_AIGUARD_ALIGNMENT_RUN_IDS,
            errors,
            "AIGuard alignment guard_analysis run IDs must match EdgeEnv summary",
        )
        _record(
            payload.get("guard_alignment_summary_errors") == [],
            errors,
            "AIGuard alignment guard_alignment_summary_errors must be empty",
        )
        _record(
            payload.get("errors") == [],
            errors,
            "AIGuard alignment errors must be empty",
        )

    text = _read_text(
        markdown_path,
        errors,
        "AIGuard EdgeEnv handoff alignment Markdown",
    )
    if text:
        expected_present_marker = _format_markdown_inline_list(
            expected_optional_guard_evidence_types_present
        )
        expected_missing_marker = _format_markdown_inline_list(
            expected_missing_optional_evidence_types
        )
        expected_markers = [
            "status: passed",
            "decision_owner: lab",
            "diagnosis_owner: aiguard",
            "lab_expected_report_markers: ["
            "Runtime Intelligence Risk Summary, Runtime replay duration scope, "
            "Orchestrator operation feed context, "
            "EdgeEnv fixture matrix coverage, "
            "Reviewer operation quick scan, "
            "Orchestrator task event rollup, "
            "Lab EdgeEnv preservation context, "
            "AIGuard operation risk rollup evidence, "
            "AIGuard task event rollup evidence, "
            "AIGuard operation timeline evidence, "
            "AIGuard runtime operation anomalies, AIGuard remote dispatch event summary, "
            "AIGuard remote event summary consistency, "
            "Remote fallback starter evidence, "
            "lab=Remote fallback starter evidence; "
            "evidence=remote_execution_recovered_by_fallback, "
            "AIGuard producer-lineage guard alignment, "
            "Lab remains the final deployment decision owner.]",
            "report_marker_context_role: lab_report_contract_context",
            "aiguard_validates_expected_report_markers: False",
            "optional_evidence_context_role: read_only_optional_guard_context",
            "aiguard_validates_optional_evidence_as_required: False",
            "optional_aiguard_evidence_types: "
            "[stale_frame_risk, edgeenv_orchestrator_stale_drop_summary]",
            f"optional_guard_evidence_types_present: {expected_present_marker}",
            f"missing_optional_evidence_types: {expected_missing_marker}",
            "handoff_producer_lineage_guard_alignment_run_ids: "
            "[edgeenv-smoke-candidate, edgeenv-smoke-missing]",
            "guard_analysis_producer_lineage_guard_alignment_run_ids: "
            "[edgeenv-smoke-candidate, edgeenv-smoke-missing]",
        ]
        if expected_optional_present_source_artifact is not None:
            expected_markers.append(
                "optional_present_source_artifact: "
                f"{REQUIRED_AIGUARD_OPTIONAL_PRESENT_SOURCE_ARTIFACT_MARKER}"
            )
            expected_markers.append(
                "optional_present_reproduction_command: "
                f"{REQUIRED_AIGUARD_OPTIONAL_PRESENT_REPRODUCTION_COMMAND_MARKER}"
            )
        for marker in expected_markers:
            _record(
                marker in text,
                errors,
                f"AIGuard alignment Markdown missing marker: {marker}",
            )


def _write_summary(path: Path, report_dir: Path, errors: list[str]) -> None:
    lines = [
        "# Runtime Intelligence CI Artifact Gate",
        "",
        f"- Report dir: `{report_dir}`",
        f"- Status: {'failed' if errors else 'passed'}",
        f"- Error count: {len(errors)}",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.append("")
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    else:
        lines.append("## Validated Duration Traceability")
        lines.append("")
        lines.extend(
            f"- {marker}"
            for marker in REQUIRED_DURATION_TRACEABILITY_SUMMARY_MARKERS
            if not marker.startswith("## ")
        )
        lines.append("")
        lines.append("## Validated Reviewer Focus")
        lines.append("")
        lines.extend(
            f"- {marker}"
            for marker in REQUIRED_REVIEWER_FOCUS_SUMMARY_MARKERS
            if not marker.startswith("## ")
        )
        lines.append("")
        lines.append("## Validated Review Path")
        lines.append("")
        lines.extend(
            f"- {marker}"
            for marker in REQUIRED_REVIEW_PATH_SUMMARY_MARKERS
            if not marker.startswith("## ")
        )
        lines.append("")
        lines.append("## Validated AIGuard Optional Handoff Context")
        lines.append("")
        lines.extend(
            f"- {marker}"
            for marker in REQUIRED_AIGUARD_OPTIONAL_CONTEXT_SUMMARY_MARKERS
            if not marker.startswith("## ")
        )
        lines.append("")
        lines.append("## Validated Source Traceability")
        lines.append("")
        lines.extend(
            f"- {marker}"
            for marker in REQUIRED_SOURCE_TRACEABILITY_SUMMARY_MARKERS
            if not marker.startswith("## ")
        )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(report_dir: str, summary_out: str = "") -> int:
    report_path = Path(report_dir)
    errors: list[str] = []
    _record(report_path.is_dir(), errors, f"report dir not found: {report_path}")
    if report_path.is_dir():
        _validate_required_files(report_path, errors)
        _validate_bundle_manifest_gate_summary(
            report_path / "runtime_intelligence_bundle_manifest_gate_summary.md",
            errors,
        )
        _validate_source_traceability_summary(
            report_path / "runtime_intelligence_source_traceability_summary.md",
            errors,
        )
        _validate_runtime_artifact_gate_summary(
            report_path / "runtime_anomaly_gate_summary.md",
            errors,
        )
        _validate_aiguard_handoff_alignment(
            report_path / "aiguard_edgeenv_handoff_alignment.json",
            report_path / "aiguard_edgeenv_handoff_alignment.md",
            errors,
        )
        _validate_aiguard_handoff_alignment(
            report_path / "aiguard_edgeenv_handoff_alignment_optional_present.json",
            report_path / "aiguard_edgeenv_handoff_alignment_optional_present.md",
            errors,
            expected_optional_guard_evidence_types_present=(
                REQUIRED_AIGUARD_PRESENT_OPTIONAL_EVIDENCE_TYPES
            ),
            expected_missing_optional_evidence_types=[],
            expected_optional_present_source_artifact=(
                REQUIRED_AIGUARD_OPTIONAL_PRESENT_SOURCE_ARTIFACT
            ),
        )
        _validate_runtime_report(report_path / "runtime_anomaly_summary.md", errors)
        _validate_portfolio_status(report_path / "portfolio_demo_check.json", errors)
        _validate_deployment_risk_status(
            report_path / "deployment_risk_summary.json",
            errors,
        )

    if summary_out:
        _write_summary(Path(summary_out), report_path, errors)
    return 2 if errors else 0


def cli() -> int:
    parser = argparse.ArgumentParser(
        description="Validate optional Runtime Intelligence GitLab artifact outputs.",
    )
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--summary-out", default="")
    args = parser.parse_args()
    return main(report_dir=args.report_dir, summary_out=args.summary_out)


if __name__ == "__main__":
    raise SystemExit(cli())
