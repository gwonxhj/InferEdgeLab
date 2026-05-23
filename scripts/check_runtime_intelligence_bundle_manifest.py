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
    "runtime_queue_overload",
    "runtime_thermal_instability",
}


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
    summary = history.get("summary") or {}
    _record(
        summary.get("orchestrator_feed_runs") == 1,
        errors,
        "runtime_telemetry_context.history.summary.orchestrator_feed_runs must be 1",
    )

    candidate = context.get("candidate") or {}
    _record(
        candidate.get("orchestrator_context_present") is True,
        errors,
        "candidate orchestrator_context_present must be true",
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


def _validate_guard_analysis(guard_analysis: dict[str, Any], errors: list[str]) -> None:
    _record(
        guard_analysis.get("schema_version") == "inferedge-aiguard-diagnosis-v1",
        errors,
        "AIGuard artifact schema_version must be inferedge-aiguard-diagnosis-v1",
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
