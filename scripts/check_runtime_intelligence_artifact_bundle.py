from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint


REQUIRED_MARKDOWN_MARKERS = {
    "risk_summary_section": "## Runtime Intelligence Risk Summary",
    "review_path_section": "### Review Path",
    "review_path": (
        "Review path: start with `Reviewer Focus`, then open `Detailed Evidence Rows`"
    ),
    "review_path_table": "| Step | Open | Use it for |",
    "review_path_fast_path": (
        "Fast path: `Reviewer Focus` -> `Detailed Evidence Rows` only when a quick "
        "signal needs supporting evidence."
    ),
    "review_path_artifact_gate_summary": (
        "| 3 | `Artifact Gate Summary` | Cross-check "
        "`runtime_intelligence_bundle_manifest_gate_summary.md`"
    ),
    "review_path_source_traceability_summary": (
        "`runtime_intelligence_source_traceability_summary.md`"
    ),
    "review_path_source_traceability_marker": "`source_traceability_alignment`",
    "review_path_artifact_gate_summary_markers": (
        "`reviewer_path_gate`, `reviewer_path_local_links`, and "
        "`reviewer_path_anchor_fragments`"
    ),
    "review_path_scope": (
        "only for comparable regression, telemetry/replay gaps, operation quick scan"
    ),
    "reviewer_focus_section": "### Reviewer Focus",
    "reviewer_focus_table": "| Focus | Quick signal | First read |",
    "reviewer_focus_edgeenv_gate": "| EdgeEnv regression gate |",
    "reviewer_focus_fixture_matrix": "| EdgeEnv fixture matrix |",
    "reviewer_focus_fixture_matrix_roles": "roles=6/6",
    "reviewer_focus_telemetry_quality": "| Telemetry/replay quality |",
    "reviewer_focus_operation_quick_scan": "| Operation quick scan | candidate: ",
    "reviewer_focus_operation_quick_scan_raw_marker": (
        "raw_marker=reviewer_focus_operation_quick_scan"
    ),
    "reviewer_focus_operation_quick_scan_rendered_label": (
        "rendered_label=Reviewer operation quick scan"
    ),
    "reviewer_focus_operation_context": "| Operation context |",
    "reviewer_focus_aiguard_warnings": "| AIGuard warnings |",
    "detailed_evidence_rows": "### Detailed Evidence Rows",
    "lab_decision_owner": "Lab remains the final deployment decision owner.",
    "edgeenv_comparability": "| EdgeEnv comparability | Yes / same-condition |",
    "runtime_regression": "| Runtime regression | True / mixed / high |",
    "edgeenv_fixture_matrix_coverage": "| EdgeEnv fixture matrix coverage |",
    "edgeenv_fixture_matrix_schema": (
        "schema=edgeenv-regression-replay-fixture-matrix-v1"
    ),
    "edgeenv_fixture_matrix_modes": (
        "modes=same-condition,runtime-comparison,target-comparison,protocol_mismatch"
    ),
    "edgeenv_fixture_matrix_boundary": "not_a_deployment_decision=True",
    "runtime_telemetry_coverage": (
        "| Runtime telemetry coverage gaps | baseline=none; candidate=queue_depth |"
    ),
    "aiguard_coverage_gap_reason": (
        "Runtime telemetry context has evidence gaps that require review."
    ),
    "aiguard_coverage_field_gap": "runtime_telemetry_field_gap",
    "aiguard_coverage_gap_recommendation": (
        "Inspect telemetry coverage missing fields"
    ),
    "orchestrator_feed": "| Orchestrator operation feed context | 2 |",
    "runtime_history_seed": "| Runtime telemetry history seed | 2 |",
    "runtime_history_seed_run_config": "| Runtime history seed run_config | 2 |",
    "orchestrator_attached_run": "| Orchestrator context attached runs | candidate |",
    "orchestrator_operation_risk_summary": (
        "| Orchestrator operation risk summary | candidate: "
        "queue=queue_backlog_threshold_exceeded"
    ),
    "orchestrator_queue_deadline_fallback_markers": (
        "| Orchestrator queue/deadline/fallback markers | candidate: "
        "queue_pressure_reason=queue_backlog_threshold_exceeded, "
        "max_total_queue_depth=7"
    ),
    "reviewer_operation_quick_scan": (
        "| Reviewer operation quick scan | candidate: "
        "queue_pressure_reason=queue_backlog_threshold_exceeded, "
        "max_total_queue_depth=7"
    ),
    "reviewer_operation_quick_scan_preservation": (
        "preservation=identity=jetson_device_local_preservation, "
        "path=device_local_starter, run=edgeenv-smoke-candidate"
    ),
    "runtime_replay_duration_scope": (
        "| Runtime replay duration scope | candidate: "
        "scope_label=source=entrypoint_requested_frames"
    ),
    "runtime_replay_duration_scope_label": (
        "scope_label=source=entrypoint_requested_frames"
    ),
    "jetson_edgeenv_preservation_identity": (
        "| Jetson/device-local EdgeEnv preservation run | candidate: "
        "identity=jetson_device_local_preservation, path=device_local_starter, "
        "run=edgeenv-smoke-candidate"
    ),
    "jetson_edgeenv_preservation_details": (
        "| Jetson/device-local EdgeEnv preservation details | candidate: "
        "sources=device_local_cli_override, "
        "stages=vision_agent:device_local_starter"
    ),
    "orchestrator_task_event_rollup": (
        "| Orchestrator task event rollup | candidate: "
        "vision_agent(delay=1,miss=1,max_delay_cycles=3,max_wait_ms=15,"
        "policy=queue_backlog_threshold_exceeded:1)"
    ),
    "lab_edgeenv_preservation_context": (
        "| Lab EdgeEnv preservation context | "
        "lab_report_preservation_context_present=True; "
        "lab_preservation=present; lab_context=present |"
    ),
    "aiguard_evidence": "| AIGuard deterministic evidence | warning / suspicious |",
    "aiguard_operation_anomalies": (
        "| AIGuard runtime operation anomalies | "
        "runtime_queue_overload, runtime_thermal_instability |"
    ),
    "aiguard_operation_risk_summary_evidence": (
        "| AIGuard operation risk summary evidence | "
        "status=warning, markers=4"
    ),
    "aiguard_operation_risk_summary_type": (
        "edgeenv_orchestrator_operation_risk_summary"
    ),
    "aiguard_operation_risk_rollup_evidence": (
        "| AIGuard operation risk rollup evidence | "
        "status=warning, markers=8"
    ),
    "aiguard_operation_risk_rollup_type": (
        "edgeenv_orchestrator_operation_risk_rollup"
    ),
    "aiguard_task_event_rollup_evidence": (
        "| AIGuard task event rollup evidence | "
        "status=warning, affected=2"
    ),
    "aiguard_task_event_rollup_type": "edgeenv_orchestrator_task_event_rollup",
    "aiguard_operation_timeline_evidence": (
        "| AIGuard operation timeline evidence | "
        "status=warning, markers=6"
    ),
    "aiguard_operation_timeline_type": (
        "edgeenv_orchestrator_operation_timeline_summary"
    ),
    "aiguard_scheduler_fairness_evidence": (
        "| AIGuard scheduler fairness evidence | "
        "status=warning, markers=4"
    ),
    "aiguard_scheduler_fairness_type": (
        "edgeenv_orchestrator_scheduler_fairness_summary"
    ),
    "aiguard_remote_dispatch_summary": (
        "| AIGuard remote dispatch event summary | "
        "events=3, final=succeeded, fallback_recovered=True |"
    ),
    "aiguard_remote_dispatch_consistency": (
        "| AIGuard remote event summary consistency | consistent |"
    ),
    "aiguard_remote_dispatch_boundary": (
        "| AIGuard remote summary boundary | "
        "role=remote_dispatch_runtime_event_compact_summary, "
        "boundary=remote dispatch starter evidence only, "
        "production_remote_execution=False |"
    ),
    "aiguard_remote_dispatch_evidence": "remote_execution_recovered_by_fallback",
    "remote_fallback_lab_context": (
        "| Remote fallback starter evidence | "
        "lab=Remote fallback starter evidence; "
        "evidence=remote_execution_recovered_by_fallback |"
    ),
    "aiguard_orchestrator_handoff": (
        "| AIGuard Orchestrator context handoff | feeds=2.0, candidate |"
    ),
    "aiguard_producer_lineage_handoff": (
        "| AIGuard producer lineage handoff | sources=device_local_cli_override"
    ),
    "aiguard_max_queue_traceability": (
        "| AIGuard max queue raw-context traceability | candidate: "
        "report=max_total_queue_depth=7, "
        "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7, "
        "match=True |"
    ),
    "aiguard_producer_lineage_evidence": "edgeenv_orchestrator_producer_lineage",
    "aiguard_producer_lineage_recommendation": (
        "Device-local Orchestrator producer lineage is preserved"
    ),
    "aiguard_guard_alignment": (
        "| AIGuard producer-lineage guard alignment | "
        "evidence=edgeenv_orchestrator_producer_lineage"
    ),
    "aiguard_history_seed_handoff": "| AIGuard history seed handoff | seeds=2.0",
    "aiguard_run_config_traceability": (
        "| AIGuard run_config traceability evidence | status=passed, count=2/2"
    ),
    "aiguard_run_config_traceability_evidence": (
        "runtime_history_seed_run_config_traceability"
    ),
    "guard_warning_rule": "guard_warning_review",
    "edgeenv_regression_rule": "edgeenv_runtime_regression_review",
}

REQUIRED_HTML_MARKERS = {
    "risk_summary_section": "Runtime Intelligence Risk Summary",
    "review_path_panel": 'class="review-path"',
    "review_path_section": "<h3>Review Path</h3>",
    "review_path": "Review path:",
    "review_path_focus": "start with <code>Reviewer Focus</code>",
    "review_path_fast_path": (
        "<strong>Fast path:</strong> <code>Reviewer Focus</code> ->"
    ),
    "review_path_detail_step": "<strong>Detailed Evidence Rows</strong>: open only the rows needed",
    "review_path_artifact_gate_summary": (
        "<strong>Artifact Gate Summary</strong>: cross-check"
    ),
    "review_path_artifact_gate_summary_file": (
        "runtime_intelligence_bundle_manifest_gate_summary.md"
    ),
    "review_path_source_traceability_summary_file": (
        "runtime_intelligence_source_traceability_summary.md"
    ),
    "review_path_source_traceability_marker": "source_traceability_alignment",
    "review_path_artifact_gate_summary_markers": "reviewer_path_anchor_fragments",
    "review_path_scope": (
        "only for comparable regression, telemetry/replay gaps, operation quick scan"
    ),
    "reviewer_focus_section": "Reviewer Focus",
    "reviewer_focus_table": "Quick signal",
    "reviewer_focus_edgeenv_gate": "EdgeEnv regression gate",
    "reviewer_focus_fixture_matrix": "EdgeEnv fixture matrix",
    "reviewer_focus_fixture_matrix_roles": "roles=6/6",
    "reviewer_focus_telemetry_quality": "Telemetry/replay quality",
    "reviewer_focus_operation_quick_scan": "Operation quick scan",
    "reviewer_focus_operation_quick_scan_raw_marker": (
        "raw_marker=reviewer_focus_operation_quick_scan"
    ),
    "reviewer_focus_operation_quick_scan_rendered_label": (
        "rendered_label=Reviewer operation quick scan"
    ),
    "reviewer_focus_operation_context": "Operation context",
    "reviewer_focus_aiguard_warnings": "AIGuard warnings",
    "detailed_evidence_rows": "Detailed Evidence Rows",
    "lab_decision_owner": "Lab remains the final deployment decision owner.",
    "runtime_telemetry_coverage": "Runtime telemetry coverage gaps",
    "edgeenv_fixture_matrix_coverage": "EdgeEnv fixture matrix coverage",
    "edgeenv_fixture_matrix_schema": (
        "schema=edgeenv-regression-replay-fixture-matrix-v1"
    ),
    "edgeenv_fixture_matrix_modes": (
        "modes=same-condition,runtime-comparison,target-comparison,protocol_mismatch"
    ),
    "edgeenv_fixture_matrix_boundary": "not_a_deployment_decision=True",
    "aiguard_coverage_field_gap": "runtime_telemetry_field_gap",
    "aiguard_coverage_gap_recommendation": (
        "Inspect telemetry coverage missing fields"
    ),
    "aiguard_operation_anomalies": "runtime_queue_overload, runtime_thermal_instability",
    "aiguard_operation_risk_summary_evidence": (
        "AIGuard operation risk summary evidence"
    ),
    "aiguard_operation_risk_summary_type": (
        "edgeenv_orchestrator_operation_risk_summary"
    ),
    "aiguard_operation_risk_rollup_evidence": (
        "AIGuard operation risk rollup evidence"
    ),
    "aiguard_operation_risk_rollup_type": (
        "edgeenv_orchestrator_operation_risk_rollup"
    ),
    "aiguard_task_event_rollup_evidence": "AIGuard task event rollup evidence",
    "aiguard_task_event_rollup_type": "edgeenv_orchestrator_task_event_rollup",
    "aiguard_operation_timeline_evidence": "AIGuard operation timeline evidence",
    "aiguard_operation_timeline_type": (
        "edgeenv_orchestrator_operation_timeline_summary"
    ),
    "aiguard_scheduler_fairness_evidence": (
        "AIGuard scheduler fairness evidence"
    ),
    "aiguard_scheduler_fairness_type": (
        "edgeenv_orchestrator_scheduler_fairness_summary"
    ),
    "aiguard_remote_dispatch_summary": "AIGuard remote dispatch event summary",
    "aiguard_remote_dispatch_label": (
        "events=3, final=succeeded, fallback_recovered=True"
    ),
    "aiguard_remote_dispatch_consistency": "AIGuard remote event summary consistency",
    "aiguard_remote_dispatch_boundary": "AIGuard remote summary boundary",
    "aiguard_remote_dispatch_boundary_label": (
        "role=remote_dispatch_runtime_event_compact_summary, "
        "boundary=remote dispatch starter evidence only, "
        "production_remote_execution=False"
    ),
    "aiguard_remote_dispatch_evidence": "remote_execution_recovered_by_fallback",
    "remote_fallback_lab_context": "Remote fallback starter evidence",
    "remote_fallback_lab_context_marker": "lab=Remote fallback starter evidence",
    "aiguard_orchestrator_handoff": "AIGuard Orchestrator context handoff",
    "orchestrator_operation_risk_summary": "Orchestrator operation risk summary",
    "orchestrator_queue_deadline_fallback_markers": (
        "Orchestrator queue/deadline/fallback markers"
    ),
    "orchestrator_queue_deadline_fallback_values": (
        "queue_pressure_reason=queue_backlog_threshold_exceeded"
    ),
    "reviewer_operation_quick_scan": "Reviewer operation quick scan",
    "reviewer_operation_quick_scan_preservation": (
        "preservation=identity=jetson_device_local_preservation, "
        "path=device_local_starter, run=edgeenv-smoke-candidate"
    ),
    "runtime_replay_duration_scope": "Runtime replay duration scope",
    "runtime_replay_duration_label": "short 96-frame-class replay (96 frames)",
    "runtime_replay_duration_source": "source=entrypoint_requested_frames",
    "runtime_replay_duration_scope_label": (
        "scope_label=source=entrypoint_requested_frames"
    ),
    "orchestrator_task_event_rollup": "Orchestrator task event rollup",
    "lab_edgeenv_preservation_context": "Lab EdgeEnv preservation context",
    "lab_edgeenv_preservation_context_marker": (
        "lab_report_preservation_context_present=True"
    ),
    "lab_edgeenv_registry_marker": "lab_preservation=present",
    "orchestrator_operation_risk_queue": "queue=queue_backlog_threshold_exceeded",
    "aiguard_producer_lineage_handoff": "AIGuard producer lineage handoff",
    "aiguard_max_queue_traceability": (
        "AIGuard max queue raw-context traceability"
    ),
    "aiguard_max_queue_traceability_value": (
        "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7"
    ),
    "aiguard_producer_lineage_evidence": "edgeenv_orchestrator_producer_lineage",
    "aiguard_producer_lineage_recommendation": (
        "Device-local Orchestrator producer lineage is preserved"
    ),
    "aiguard_guard_alignment": "AIGuard producer-lineage guard alignment",
    "aiguard_device_local_producer_source": "device_local_cli_override",
    "jetson_edgeenv_preservation_identity": (
        "identity=jetson_device_local_preservation, path=device_local_starter, "
        "run=edgeenv-smoke-candidate"
    ),
    "jetson_edgeenv_preservation_details": (
        "Jetson/device-local EdgeEnv preservation details"
    ),
    "jetson_edgeenv_preservation_detail_source": (
        "sources=device_local_cli_override, "
        "stages=vision_agent:device_local_starter"
    ),
    "runtime_history_seed": "Runtime telemetry history seed",
    "runtime_history_seed_run_config": "Runtime history seed run_config",
    "aiguard_history_seed_handoff": "AIGuard history seed handoff",
    "aiguard_run_config_traceability": "AIGuard run_config traceability evidence",
    "aiguard_run_config_traceability_evidence": (
        "runtime_history_seed_run_config_traceability"
    ),
}

DURATION_TRACEABILITY_SUMMARY_MARKERS = (
    "duration_handoff_alignment: EdgeEnv/AIGuard report context preserved",
    "duration_source: source=entrypoint_requested_frames",
    "duration_scope_label: scope_label=source=entrypoint_requested_frames",
    "duration_label: short 96-frame-class replay (96 frames)",
)

REVIEWER_FOCUS_SUMMARY_MARKERS = (
    "reviewer_focus_operation_quick_scan: Reviewer Focus / Operation quick scan marker validated",
    "reviewer_focus_operation_quick_scan_raw_marker: raw marker preserved in Lab report",
    "reviewer_focus_fixture_matrix: EdgeEnv fixture matrix row validated",
)

REVIEW_PATH_SUMMARY_MARKERS = (
    "review_path_section: short Review Path section rendered",
    "review_path_fast_path: readable Review Path fast path rendered",
    "review_path: Reviewer Focus -> Detailed Evidence Rows guidance validated",
    "review_path_scope: comparable regression / telemetry replay / operation evidence preserved",
    "review_path_artifact_gate_summary: artifact gate summary reference row validated",
    "review_path_source_traceability_summary: source traceability summary reference row validated",
)


def _read_text(path: str, label: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"{label} not found: {path}") from exc


def _missing_markers(text: str, markers: dict[str, str]) -> list[str]:
    return [name for name, marker in markers.items() if marker not in text]


def _write_summary(
    path: str,
    *,
    missing_markdown: list[str],
    missing_html: list[str],
) -> None:
    if not path:
        return
    lines = [
        "# Runtime Intelligence Artifact Bundle Gate",
        "",
        f"- Status: {'failed' if missing_markdown or missing_html else 'passed'}",
        f"- Missing Markdown markers: {len(missing_markdown)}",
        f"- Missing HTML markers: {len(missing_html)}",
        "",
    ]
    if missing_markdown:
        lines.append("## Missing Markdown Markers")
        lines.append("")
        lines.extend(f"- `{name}`" for name in missing_markdown)
        lines.append("")
    if missing_html:
        lines.append("## Missing HTML Markers")
        lines.append("")
        lines.extend(f"- `{name}`" for name in missing_html)
        lines.append("")
    if not missing_markdown and not missing_html:
        lines.append("## Validated Duration Traceability")
        lines.append("")
        lines.extend(f"- {marker}" for marker in DURATION_TRACEABILITY_SUMMARY_MARKERS)
        lines.append("")
        lines.append("## Validated Reviewer Focus")
        lines.append("")
        lines.extend(f"- {marker}" for marker in REVIEWER_FOCUS_SUMMARY_MARKERS)
        lines.append("")
        lines.append("## Validated EdgeEnv Fixture Matrix")
        lines.append("")
        lines.append(
            "- edgeenv_fixture_matrix_coverage: EdgeEnv fixture matrix coverage row validated"
        )
        lines.append(
            "- edgeenv_fixture_matrix_boundary: comparability-first EdgeEnv boundary preserved"
        )
        lines.append("")
        lines.append("## Validated Review Path")
        lines.append("")
        lines.extend(f"- {marker}" for marker in REVIEW_PATH_SUMMARY_MARKERS)
        lines.append("")

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main(markdown: str, html: str = "", summary_out: str = "") -> int:
    markdown_text = _read_text(markdown, "Markdown report")
    html_text = _read_text(html, "HTML report") if html else ""

    missing_markdown = _missing_markers(markdown_text, REQUIRED_MARKDOWN_MARKERS)
    missing_html = _missing_markers(html_text, REQUIRED_HTML_MARKERS) if html else []
    _write_summary(
        summary_out,
        missing_markdown=missing_markdown,
        missing_html=missing_html,
    )

    if missing_markdown or missing_html:
        rprint("[red]Runtime Intelligence artifact bundle gate failed.[/red]")
        for name in missing_markdown:
            rprint(f"[red]Missing Markdown marker[/red]: {name}")
        for name in missing_html:
            rprint(f"[red]Missing HTML marker[/red]: {name}")
        return 2

    rprint("[green]Runtime Intelligence artifact bundle gate passed.[/green]")
    if summary_out:
        rprint(f"[cyan]Summary written[/cyan]: {summary_out}")
    return 0


def cli(
    markdown: str = typer.Option(
        ...,
        "--markdown",
        help="Runtime Intelligence Markdown report path",
    ),
    html: str = typer.Option(
        "",
        "--html",
        help="Optional Runtime Intelligence HTML report path",
    ),
    summary_out: str = typer.Option(
        "",
        "--summary-out",
        help="Optional Markdown gate summary output path",
    ),
) -> None:
    raise typer.Exit(main(markdown=markdown, html=html, summary_out=summary_out))


if __name__ == "__main__":
    typer.run(cli)
