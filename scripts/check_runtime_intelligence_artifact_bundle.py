from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint


REQUIRED_MARKDOWN_MARKERS = {
    "risk_summary_section": "## Runtime Intelligence Risk Summary",
    "lab_decision_owner": "Lab remains the final deployment decision owner.",
    "edgeenv_comparability": "| EdgeEnv comparability | Yes / same-condition |",
    "runtime_regression": "| Runtime regression | True / mixed / high |",
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
    "aiguard_evidence": "| AIGuard deterministic evidence | warning / suspicious |",
    "aiguard_operation_anomalies": (
        "| AIGuard runtime operation anomalies | "
        "runtime_queue_overload, runtime_thermal_instability |"
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
    "aiguard_orchestrator_handoff": (
        "| AIGuard Orchestrator context handoff | feeds=2.0, candidate |"
    ),
    "aiguard_producer_lineage_handoff": (
        "| AIGuard producer lineage handoff | sources=device_local_cli_override"
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
    "lab_decision_owner": "Lab remains the final deployment decision owner.",
    "runtime_telemetry_coverage": "Runtime telemetry coverage gaps",
    "aiguard_coverage_field_gap": "runtime_telemetry_field_gap",
    "aiguard_coverage_gap_recommendation": (
        "Inspect telemetry coverage missing fields"
    ),
    "aiguard_operation_anomalies": "runtime_queue_overload, runtime_thermal_instability",
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
    "aiguard_orchestrator_handoff": "AIGuard Orchestrator context handoff",
    "orchestrator_operation_risk_summary": "Orchestrator operation risk summary",
    "orchestrator_operation_risk_queue": "queue=queue_backlog_threshold_exceeded",
    "aiguard_producer_lineage_handoff": "AIGuard producer lineage handoff",
    "aiguard_producer_lineage_evidence": "edgeenv_orchestrator_producer_lineage",
    "aiguard_producer_lineage_recommendation": (
        "Device-local Orchestrator producer lineage is preserved"
    ),
    "aiguard_guard_alignment": "AIGuard producer-lineage guard alignment",
    "aiguard_device_local_producer_source": "device_local_cli_override",
    "runtime_history_seed": "Runtime telemetry history seed",
    "runtime_history_seed_run_config": "Runtime history seed run_config",
    "aiguard_history_seed_handoff": "AIGuard history seed handoff",
    "aiguard_run_config_traceability": "AIGuard run_config traceability evidence",
    "aiguard_run_config_traceability_evidence": (
        "runtime_history_seed_run_config_traceability"
    ),
}


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
