from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from inferedgelab.services.agent_runtime_report import (
    agent_runtime_reliability_json,
    build_agent_runtime_reliability_markdown,
    load_agent_runtime_reliability_bundle,
)


def agent_runtime_report_cmd(
    orchestration_summary: str = typer.Option(
        ...,
        "--orchestration-summary",
        help="Path to InferEdgeOrchestrator orchestration_summary JSON",
    ),
    guard_analysis: str = typer.Option(
        "",
        "--guard-analysis",
        help="Optional AIGuard runtime reliability guard_analysis JSON",
    ),
    runtime_result: str = typer.Option(
        "",
        "--runtime-result",
        help="Optional InferEdge-Runtime result JSON with runtime_health_snapshot/runtime_events",
    ),
    remote_dispatch: str = typer.Option(
        "",
        "--remote-dispatch",
        help="Optional InferEdgeOrchestrator remote dispatch result JSON",
    ),
    format: str = typer.Option("text", "--format", "-f", help="text/json/markdown"),
    output: str = typer.Option("", "--output", "-o", help="Optional output path"),
) -> None:
    report = load_agent_runtime_reliability_bundle(
        orchestration_summary_path=orchestration_summary,
        guard_analysis_path=guard_analysis or None,
        runtime_result_path=runtime_result or None,
        remote_dispatch_path=remote_dispatch or None,
    )
    normalized_format = format.strip().lower()
    if normalized_format == "json":
        text = agent_runtime_reliability_json(report)
    elif normalized_format in {"markdown", "md"}:
        text = build_agent_runtime_reliability_markdown(report)
    elif normalized_format == "text":
        text = _text_summary(report)
    else:
        raise typer.BadParameter("--format must be one of: text, json, markdown")

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        rprint(f"[green]Saved[/green]: {path}")
    else:
        print(text, end="")


def _text_summary(report: dict) -> str:
    metrics = report["agent_runtime_summary"]["metrics"]
    decision = report["agent_deployment_decision"]
    guard = report["guard_summary"]
    runtime_context = report["agent_runtime_summary"].get("runtime_result_context") or {}
    remote_context = report["agent_runtime_summary"].get("remote_dispatch_context") or {}
    remote_execution_result = remote_context.get("remote_execution_result") or {}
    fallback_execution_result = remote_context.get("fallback_execution_result") or {}
    health = runtime_context.get("runtime_health_snapshot") or {}
    error = runtime_context.get("runtime_error_classification") or {}
    operation_summary = runtime_context.get("runtime_operation_summary") or {}
    lines = [
        "InferEdge Agent Runtime Reliability Report",
        f"schema_version: {report['schema_version']}",
        f"decision: {decision['decision']}",
        f"policy_version: {decision['policy_version']}",
        f"reason: {decision['reason']}",
        f"guard_verdict: {guard.get('guard_verdict')}",
        f"drop_rate: {metrics['drop_rate']:.6g}",
        f"fallback_rate: {metrics['fallback_rate']:.6g}",
        f"deadline_miss_rate: {metrics['deadline_miss_rate']:.6g}",
        f"queue_pressure_reason: {metrics.get('queue_pressure_reason')}",
        f"device_local_event_count: {metrics.get('device_local_event_count')}",
        f"producer_sources: {', '.join(metrics.get('runtime_event_producer_sources') or [])}",
        f"runtime_health_status: {health.get('status')}",
        f"runtime_health_reason: {health.get('health_reason') or operation_summary.get('health_reason')}",
        f"runtime_error_category: {error.get('category')}",
        f"runtime_operation_recommended_action: {operation_summary.get('recommended_action')}",
        f"remote_dispatch_status: {remote_context.get('dispatch_status')}",
        f"remote_selected_worker_id: {remote_context.get('selected_worker_id')}",
        f"remote_execution_status: {remote_execution_result.get('status')}",
        f"remote_execution_transport: {remote_execution_result.get('transport')}",
        f"remote_execution_error_category: {remote_execution_result.get('error_category')}",
        f"remote_fallback_status: {fallback_execution_result.get('final_status')}",
        f"remote_fallback_workers: {', '.join(fallback_execution_result.get('attempted_worker_ids') or [])}",
        "triggered_rules:",
    ]
    lines.extend(f"- {rule}" for rule in decision["triggered_rules"])
    lines.append("")
    return "\n".join(lines)
