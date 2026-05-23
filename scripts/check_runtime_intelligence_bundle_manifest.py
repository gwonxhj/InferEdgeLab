from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich import print as rprint


EXPECTED_SCHEMA_VERSION = "inferedge.runtime-intelligence-artifact-bundle.v1"
REQUIRED_FILES = {
    "baseline_result",
    "candidate_result",
    "edgeenv_regression_report",
    "aiguard_guard_analysis",
}
REQUIRED_SOURCE_REPOSITORIES = {
    "runtime_result": "InferEdge-Runtime",
    "edgeenv_regression_report": "InferEdgeEnv",
    "orchestrator_operation_context": "InferEdgeOrchestrator",
    "aiguard_guard_analysis": "InferEdgeAIGuard",
    "lab_report_owner": "InferEdgeLab",
}
REQUIRED_ARTIFACT_ROLES = {
    "baseline_result": "runtime-lab-compatible-baseline-result",
    "candidate_result": "runtime-lab-compatible-candidate-result",
    "edgeenv_regression_report": "edgeenv-comparability-first-runtime-regression-report",
    "orchestrator_operation_context": "orchestrator-supplemental-operation-context",
    "aiguard_guard_analysis": "aiguard-deterministic-runtime-anomaly-evidence",
    "lab_report": "lab-owned-deployment-risk-report",
}
REQUIRED_PRODUCER_CONTRACTS = {
    "runtime_result_contract": "lab-compatible-runtime-result-json",
    "edgeenv_history_schema": "edgeenv.runtime-telemetry-history.v1",
    "orchestrator_feed_schema": (
        "inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1"
    ),
    "aiguard_schema": "inferedge-aiguard-diagnosis-v1",
}
REQUIRED_OWNERSHIP = {
    "runtime_result_owner": "runtime",
    "regression_owner": "edgeenv",
    "operation_context_owner": "orchestrator",
    "diagnosis_owner": "aiguard",
    "deployment_decision_owner": "lab",
}
REQUIRED_BOUNDARIES = {
    "orchestrator_context_is_verdict": False,
    "orchestrator_context_is_comparability_gate": False,
    "aiguard_is_final_decision_owner": False,
    "lab_is_final_decision_owner": True,
    "production_observability_platform": False,
}
REQUIRED_GUARD_TYPES = {
    "runtime_telemetry_context_coverage",
    "runtime_queue_overload",
    "runtime_thermal_instability",
}
REQUIRED_GUARD_EVIDENCE_FIELDS = {
    "type",
    "metric_name",
    "observed_value",
    "baseline_value",
    "threshold",
    "delta",
    "delta_pct",
    "increase_factor",
    "severity",
    "status",
    "explanation",
    "why_it_matters",
    "suspected_causes",
    "recommendation",
    "raw_context",
}
VALID_GUARD_EVIDENCE_STATUSES = {"passed", "warning", "failed", "skipped"}
VALID_GUARD_EVIDENCE_SEVERITIES = {"low", "medium", "high", "critical"}


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise typer.BadParameter(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{label} is invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise typer.BadParameter(f"{label} must be a JSON object: {path}")
    return payload


def _resolve_bundle_path(manifest_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (manifest_path.parent / candidate).resolve()


def _record(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def _validate_manifest_shape(manifest: dict[str, Any], errors: list[str]) -> None:
    _record(
        manifest.get("schema_version") == EXPECTED_SCHEMA_VERSION,
        errors,
        f"schema_version must be {EXPECTED_SCHEMA_VERSION}",
    )

    files = manifest.get("files")
    _record(isinstance(files, dict), errors, "files must be an object")
    if isinstance(files, dict):
        missing = sorted(REQUIRED_FILES - set(files))
        _record(not missing, errors, f"files is missing required keys: {missing}")

    source_repositories = manifest.get("source_repositories")
    _record(
        isinstance(source_repositories, dict),
        errors,
        "source_repositories must be an object",
    )
    if isinstance(source_repositories, dict):
        for key, expected in REQUIRED_SOURCE_REPOSITORIES.items():
            _record(
                source_repositories.get(key) == expected,
                errors,
                f"source_repositories.{key} must be {expected}",
            )

    artifact_roles = manifest.get("artifact_roles")
    _record(isinstance(artifact_roles, dict), errors, "artifact_roles must be an object")
    if isinstance(artifact_roles, dict):
        for key, expected in REQUIRED_ARTIFACT_ROLES.items():
            _record(
                artifact_roles.get(key) == expected,
                errors,
                f"artifact_roles.{key} must be {expected}",
            )

    producer_contracts = manifest.get("producer_contracts")
    _record(
        isinstance(producer_contracts, dict),
        errors,
        "producer_contracts must be an object",
    )
    if isinstance(producer_contracts, dict):
        for key, expected in REQUIRED_PRODUCER_CONTRACTS.items():
            _record(
                producer_contracts.get(key) == expected,
                errors,
                f"producer_contracts.{key} must be {expected}",
            )

    ownership = manifest.get("ownership")
    _record(isinstance(ownership, dict), errors, "ownership must be an object")
    if isinstance(ownership, dict):
        for key, expected in REQUIRED_OWNERSHIP.items():
            _record(
                ownership.get(key) == expected,
                errors,
                f"ownership.{key} must be {expected}",
            )

    boundaries = manifest.get("boundaries")
    _record(isinstance(boundaries, dict), errors, "boundaries must be an object")
    if isinstance(boundaries, dict):
        for key, expected in REQUIRED_BOUNDARIES.items():
            _record(
                boundaries.get(key) is expected,
                errors,
                f"boundaries.{key} must be {expected}",
            )


def _validate_edgeenv_report(edgeenv_report: dict[str, Any], errors: list[str]) -> None:
    _record(
        edgeenv_report.get("mode") == "same-condition",
        errors,
        "EdgeEnv report mode must be same-condition",
    )
    _record(
        edgeenv_report.get("comparable") is True,
        errors,
        "EdgeEnv report must be comparable",
    )
    context = edgeenv_report.get("runtime_telemetry_context")
    _record(
        isinstance(context, dict),
        errors,
        "EdgeEnv report must include runtime_telemetry_context",
    )
    if not isinstance(context, dict):
        return

    history = context.get("history") or {}
    _record(
        history.get("schema_version")
        == REQUIRED_PRODUCER_CONTRACTS["edgeenv_history_schema"],
        errors,
        "runtime_telemetry_context.history.schema_version must be "
        f"{REQUIRED_PRODUCER_CONTRACTS['edgeenv_history_schema']}",
    )
    summary = history.get("summary") or {}
    _record(
        summary.get("orchestrator_feed_runs") == 1,
        errors,
        "runtime_telemetry_context.history.summary.orchestrator_feed_runs must be 1",
    )
    history_coverage = history.get("telemetry_coverage")
    _record(
        isinstance(history_coverage, dict),
        errors,
        "runtime_telemetry_context.history must include telemetry_coverage",
    )
    if isinstance(history_coverage, dict):
        _validate_edgeenv_history_coverage_summary(history_coverage, errors)

    candidate = context.get("candidate") or {}
    _record(
        candidate.get("orchestrator_context_present") is True,
        errors,
        "candidate orchestrator_context_present must be true",
    )
    coverage = candidate.get("telemetry_coverage")
    _record(
        isinstance(coverage, dict),
        errors,
        "candidate must include telemetry_coverage",
    )
    if isinstance(coverage, dict):
        _record(
            coverage.get("missing_telemetry_is_failure") is False,
            errors,
            "candidate.telemetry_coverage.missing_telemetry_is_failure must be false",
        )
        missing_fields = coverage.get("missing_fields")
        _record(
            isinstance(missing_fields, list) and "queue_depth" in missing_fields,
            errors,
            "candidate.telemetry_coverage.missing_fields must include queue_depth",
        )
    operation_context = candidate.get("orchestrator_operation_context")
    _record(
        isinstance(operation_context, dict),
        errors,
        "candidate must include orchestrator_operation_context",
    )
    if not isinstance(operation_context, dict):
        return

    _record(
        operation_context.get("schema_version")
        == REQUIRED_PRODUCER_CONTRACTS["orchestrator_feed_schema"],
        errors,
        "orchestrator_operation_context.schema_version must be "
        f"{REQUIRED_PRODUCER_CONTRACTS['orchestrator_feed_schema']}",
    )
    _record(
        operation_context.get("not_a_regression_judgement") is True,
        errors,
        "orchestrator_operation_context.not_a_regression_judgement must be true",
    )
    _record(
        operation_context.get("not_a_comparability_gate") is True,
        errors,
        "orchestrator_operation_context.not_a_comparability_gate must be true",
    )
    _record(
        operation_context.get("decision_owner") == "lab",
        errors,
        "orchestrator_operation_context.decision_owner must be lab",
    )
    _record(
        operation_context.get("regression_owner") == "edgeenv",
        errors,
        "orchestrator_operation_context.regression_owner must be edgeenv",
    )


def _validate_edgeenv_history_coverage_summary(
    coverage: dict[str, Any],
    errors: list[str],
) -> None:
    _record(
        coverage.get("missing_field_run_count") == 1,
        errors,
        "runtime_telemetry_context.history.telemetry_coverage."
        "missing_field_run_count must be 1",
    )
    missing_field_runs = coverage.get("missing_field_runs")
    _record(
        isinstance(missing_field_runs, list),
        errors,
        "runtime_telemetry_context.history.telemetry_coverage."
        "missing_field_runs must be a list",
    )
    if isinstance(missing_field_runs, list):
        candidate_gap = next(
            (
                item
                for item in missing_field_runs
                if isinstance(item, dict)
                and item.get("run_id") == "edgeenv-smoke-candidate"
            ),
            None,
        )
        _record(
            isinstance(candidate_gap, dict),
            errors,
            "runtime_telemetry_context.history.telemetry_coverage."
            "missing_field_runs must include edgeenv-smoke-candidate",
        )
        if isinstance(candidate_gap, dict):
            _record(
                candidate_gap.get("missing_fields") == ["queue_depth"],
                errors,
                "runtime_telemetry_context.history.telemetry_coverage "
                "candidate missing_fields must be ['queue_depth']",
            )
    run_summaries = coverage.get("run_summaries")
    _record(
        isinstance(run_summaries, list) and len(run_summaries) >= 2,
        errors,
        "runtime_telemetry_context.history.telemetry_coverage."
        "run_summaries must include baseline and candidate runs",
    )


def _validate_guard_analysis(guard_analysis: dict[str, Any], errors: list[str]) -> None:
    _record(
        guard_analysis.get("schema_version")
        == REQUIRED_PRODUCER_CONTRACTS["aiguard_schema"],
        errors,
        "AIGuard artifact schema_version must be "
        f"{REQUIRED_PRODUCER_CONTRACTS['aiguard_schema']}",
    )
    source = guard_analysis.get("source") or {}
    _record(
        source.get("edgeenv_runtime_regression_report") is True,
        errors,
        "AIGuard source.edgeenv_runtime_regression_report must be true",
    )
    _record(
        source.get("edgeenv_mode") == "same-condition",
        errors,
        "AIGuard source.edgeenv_mode must be same-condition",
    )
    _record(
        source.get("edgeenv_comparable") is True,
        errors,
        "AIGuard source.edgeenv_comparable must be true",
    )
    _record(
        guard_analysis.get("guard_verdict") == "suspicious",
        errors,
        "AIGuard guard_verdict must be suspicious for this fixture",
    )
    evidence = guard_analysis.get("evidence")
    _record(isinstance(evidence, list), errors, "AIGuard evidence must be a list")
    if not isinstance(evidence, list):
        return
    evidence_types = {
        item.get("type")
        for item in evidence
        if isinstance(item, dict)
    }
    missing = sorted(REQUIRED_GUARD_TYPES - evidence_types)
    _record(not missing, errors, f"AIGuard evidence is missing types: {missing}")
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"AIGuard evidence[{index}] must be an object")
            continue
        missing_fields = sorted(REQUIRED_GUARD_EVIDENCE_FIELDS - set(item))
        _record(
            not missing_fields,
            errors,
            f"AIGuard evidence[{index}] is missing fields: {missing_fields}",
        )
        if missing_fields:
            continue
        _record(
            item.get("status") in VALID_GUARD_EVIDENCE_STATUSES,
            errors,
            f"AIGuard evidence[{index}].status is invalid",
        )
        _record(
            item.get("severity") in VALID_GUARD_EVIDENCE_SEVERITIES,
            errors,
            f"AIGuard evidence[{index}].severity is invalid",
        )
        _record(
            isinstance(item.get("why_it_matters"), str)
            and bool(item.get("why_it_matters")),
            errors,
            f"AIGuard evidence[{index}].why_it_matters must be a non-empty string",
        )
        _record(
            isinstance(item.get("recommendation"), str)
            and bool(item.get("recommendation")),
            errors,
            f"AIGuard evidence[{index}].recommendation must be a non-empty string",
        )
        _record(
            isinstance(item.get("suspected_causes"), list),
            errors,
            f"AIGuard evidence[{index}].suspected_causes must be a list",
        )
        _record(
            isinstance(item.get("raw_context"), dict),
            errors,
            f"AIGuard evidence[{index}].raw_context must be an object",
        )
        if item.get("type") == "runtime_telemetry_context_coverage":
            _validate_coverage_gap_evidence(item, index, errors)


def _validate_coverage_gap_evidence(
    item: dict[str, Any],
    index: int,
    errors: list[str],
) -> None:
    _record(
        item.get("status") == "warning",
        errors,
        f"AIGuard evidence[{index}] coverage status must be warning",
    )
    _record(
        item.get("observed_value") == 1.0,
        errors,
        f"AIGuard evidence[{index}] coverage observed_value must be 1.0",
    )
    suspected_causes = item.get("suspected_causes")
    _record(
        isinstance(suspected_causes, list)
        and "runtime_telemetry_field_gap" in suspected_causes,
        errors,
        f"AIGuard evidence[{index}] must include runtime_telemetry_field_gap",
    )
    edgeenv = (item.get("raw_context") or {}).get("edgeenv_regression")
    _record(
        isinstance(edgeenv, dict),
        errors,
        f"AIGuard evidence[{index}] raw_context.edgeenv_regression must be an object",
    )
    if not isinstance(edgeenv, dict):
        return
    _record(
        edgeenv.get("candidate_telemetry_coverage_missing_fields") == ["queue_depth"],
        errors,
        "AIGuard coverage evidence candidate_telemetry_coverage_missing_fields "
        "must be ['queue_depth']",
    )
    _record(
        edgeenv.get("candidate_missing_telemetry_is_failure") is False,
        errors,
        "AIGuard coverage evidence candidate_missing_telemetry_is_failure must be false",
    )


def _write_summary(path: str, *, manifest_path: Path, errors: list[str]) -> None:
    if not path:
        return
    lines = [
        "# Runtime Intelligence Bundle Manifest Gate",
        "",
        f"- Manifest: `{manifest_path}`",
        f"- Status: {'failed' if errors else 'passed'}",
        f"- Error count: {len(errors)}",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.append("")
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main(manifest: str, summary_out: str = "") -> int:
    manifest_path = Path(manifest).resolve()
    errors: list[str] = []
    manifest_payload = _load_json(manifest_path, "Runtime Intelligence bundle manifest")
    _validate_manifest_shape(manifest_payload, errors)

    files = manifest_payload.get("files") or {}
    resolved_files: dict[str, Path] = {}
    if isinstance(files, dict):
        for key in sorted(REQUIRED_FILES):
            if not isinstance(files.get(key), str):
                errors.append(f"files.{key} must be a string path")
                continue
            resolved = _resolve_bundle_path(manifest_path, files[key])
            resolved_files[key] = resolved
            if not resolved.exists():
                errors.append(f"files.{key} does not exist: {resolved}")

    if "edgeenv_regression_report" in resolved_files and resolved_files[
        "edgeenv_regression_report"
    ].exists():
        _validate_edgeenv_report(
            _load_json(
                resolved_files["edgeenv_regression_report"],
                "EdgeEnv regression report",
            ),
            errors,
        )
    if "aiguard_guard_analysis" in resolved_files and resolved_files[
        "aiguard_guard_analysis"
    ].exists():
        _validate_guard_analysis(
            _load_json(
                resolved_files["aiguard_guard_analysis"],
                "AIGuard guard_analysis",
            ),
            errors,
        )

    _write_summary(summary_out, manifest_path=manifest_path, errors=errors)
    if errors:
        rprint("[red]Runtime Intelligence bundle manifest gate failed.[/red]")
        for error in errors:
            rprint(f"[red]- {error}[/red]")
        return 2

    rprint("[green]Runtime Intelligence bundle manifest gate passed.[/green]")
    if summary_out:
        rprint(f"[cyan]Summary written[/cyan]: {summary_out}")
    return 0


def cli(
    manifest: str = typer.Option(
        ...,
        "--manifest",
        help="Runtime Intelligence bundle manifest path",
    ),
    summary_out: str = typer.Option(
        "",
        "--summary-out",
        help="Optional Markdown gate summary output path",
    ),
) -> None:
    raise typer.Exit(main(manifest=manifest, summary_out=summary_out))


if __name__ == "__main__":
    typer.run(cli)
