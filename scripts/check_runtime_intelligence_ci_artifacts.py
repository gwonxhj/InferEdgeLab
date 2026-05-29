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
    "runtime_intelligence_bundle_manifest_gate_summary.md",
    "runtime_anomaly_gate_summary.md",
}
REQUIRED_JSON_ARTIFACTS = {
    "aiguard_edgeenv_handoff_alignment.json",
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
    "aiguard_handoff_alignment: external required evidence types satisfied",
    "expected_report_markers: Runtime Intelligence report markers declared",
    "edgeenv_handoff: lab_bundle_alignment validated",
    "edgeenv_handoff: runtime_telemetry_history validated",
    "edgeenv_handoff: external AIGuard evidence requirements declared",
    "edgeenv_handoff: device_local_producer_lineage validated",
    "edgeenv_handoff: producer_lineage_guard_alignment validated",
    "edgeenv_handoff: orchestrator_task_event_rollup validated",
    "edgeenv_handoff: missing_telemetry_orchestrator_context validated",
)
REQUIRED_LAB_EXPECTED_REPORT_MARKERS = (
    "Runtime Intelligence Risk Summary",
    "Orchestrator operation feed context",
    "Orchestrator task event rollup",
    "Lab EdgeEnv preservation context",
    "AIGuard task event rollup evidence",
    "AIGuard runtime operation anomalies",
    "AIGuard remote dispatch event summary",
    "AIGuard remote event summary consistency",
    "AIGuard producer-lineage guard alignment",
    "Lab remains the final deployment decision owner.",
)
REQUIRED_AIGUARD_ALIGNMENT_RUN_IDS = [
    "edgeenv-smoke-candidate",
    "edgeenv-smoke-missing",
]


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


def _validate_required_files(report_dir: Path, errors: list[str]) -> None:
    for name in sorted(
        REQUIRED_MARKDOWN_ARTIFACTS
        | REQUIRED_HTML_ARTIFACTS
        | REQUIRED_SUMMARY_ARTIFACTS
        | REQUIRED_JSON_ARTIFACTS
    ):
        _record((report_dir / name).is_file(), errors, f"missing artifact: {name}")


def _validate_gate_summary(path: Path, errors: list[str], label: str) -> None:
    text = _read_text(path, errors, label)
    if text:
        _record("- Status: passed" in text, errors, f"{label} must have passed status")


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


def _validate_runtime_report(path: Path, errors: list[str]) -> None:
    text = _read_text(path, errors, "Runtime Intelligence Markdown report")
    if not text:
        return
    for marker in (
        "## Runtime Intelligence Risk Summary",
        "Lab remains the final deployment decision owner.",
        "AIGuard runtime operation anomalies",
        "runtime_queue_overload, runtime_thermal_instability",
        "AIGuard operation risk summary evidence",
        "edgeenv_orchestrator_operation_risk_summary",
        "AIGuard task event rollup evidence",
        "Lab EdgeEnv preservation context",
        "lab_report_preservation_context_present=True",
        "lab_preservation=present",
        "edgeenv_orchestrator_task_event_rollup",
        "Runtime telemetry coverage gaps",
        "AIGuard producer-lineage guard alignment",
        "edgeenv_orchestrator_producer_lineage",
        "AIGuard run_config traceability evidence",
        "runtime_history_seed_run_config_traceability",
        "AIGuard remote dispatch event summary",
        "remote_execution_recovered_by_fallback",
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
) -> None:
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
        for marker in (
            "status: passed",
            "decision_owner: lab",
            "diagnosis_owner: aiguard",
            "lab_expected_report_markers: "
            "Runtime Intelligence Risk Summary, Orchestrator operation feed context, "
            "Orchestrator task event rollup, "
            "Lab EdgeEnv preservation context, "
            "AIGuard task event rollup evidence, "
            "AIGuard runtime operation anomalies, AIGuard remote dispatch event summary, "
            "AIGuard remote event summary consistency, "
            "AIGuard producer-lineage guard alignment, "
            "Lab remains the final deployment decision owner.",
            "report_marker_context_role: lab_report_contract_context",
            "aiguard_validates_expected_report_markers: False",
            "handoff_producer_lineage_guard_alignment_run_ids: "
            "edgeenv-smoke-candidate, edgeenv-smoke-missing",
            "guard_analysis_producer_lineage_guard_alignment_run_ids: "
            "edgeenv-smoke-candidate, edgeenv-smoke-missing",
        ):
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
        _validate_gate_summary(
            report_path / "runtime_anomaly_gate_summary.md",
            errors,
            "Runtime Intelligence artifact gate summary",
        )
        _validate_aiguard_handoff_alignment(
            report_path / "aiguard_edgeenv_handoff_alignment.json",
            report_path / "aiguard_edgeenv_handoff_alignment.md",
            errors,
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
