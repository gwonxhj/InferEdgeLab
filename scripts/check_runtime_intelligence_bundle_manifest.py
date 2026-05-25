from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich import print as rprint


EXPECTED_SCHEMA_VERSION = "inferedge.runtime-intelligence-artifact-bundle.v1"
EDGEENV_HANDOFF_SCHEMA_VERSION = "edgeenv.runtime-intelligence-lab-handoff.v1"
EDGEENV_HANDOFF_ROLE = "edgeenv-runtime-intelligence-lab-handoff"
EDGEENV_HANDOFF_RUNTIME_HISTORY_KEY = "runtime_telemetry_history"
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
    "runtime_telemetry_history_seed_schema": (
        "inferedge-runtime-telemetry-history-seed-v1"
    ),
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
REQUIRED_ORCHESTRATOR_MAPPING_HINT = {
    "copy_candidate_context_to": "runtime_telemetry_context.candidate",
    "operation_context_role": "supplemental",
    "coverage_summary_owner": "edgeenv",
    "coverage_summary_path": "runtime_telemetry_context.history.telemetry_coverage",
}
REQUIRED_ORCHESTRATOR_CANDIDATE_CONTEXT_FIELDS = {
    "run_id",
    "telemetry_source",
    "operation",
    "resource",
}
REQUIRED_ORCHESTRATOR_AIGUARD_EVIDENCE_CANDIDATES = {
    "runtime_queue_overload",
    "runtime_thermal_instability",
}
REQUIRED_EDGEENV_HANDOFF_BOUNDARY_FLAGS = {
    "orchestrator_context_is_verdict": False,
    "orchestrator_context_is_comparability_gate": False,
    "aiguard_guard_analysis_is_external": True,
    "aiguard_is_final_decision_owner": False,
    "edgeenv_does_not_generate_guard_analysis": True,
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
SUMMARY_CONTRACT_MARKERS = (
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
    "aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage",
    "aiguard_raw_context: orchestrator_mapping_hint preserved",
    "aiguard_raw_context: orchestrator_producer_markers preserved",
    "aiguard_raw_context: missing_telemetry_orchestrator_context preserved",
)
EDGEENV_HANDOFF_SUMMARY_CONTRACT_MARKERS = (
    "edgeenv_handoff: lab_bundle_alignment validated",
    "edgeenv_handoff: runtime_telemetry_history validated",
    "edgeenv_handoff: missing_telemetry_orchestrator_context validated",
)


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


def _validate_edgeenv_handoff_alignment(
    handoff: dict[str, Any],
    *,
    handoff_path: Path,
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    _record(
        handoff.get("schema_version") == EDGEENV_HANDOFF_SCHEMA_VERSION,
        errors,
        f"EdgeEnv handoff schema_version must be {EDGEENV_HANDOFF_SCHEMA_VERSION}",
    )
    _record(
        handoff.get("role") == EDGEENV_HANDOFF_ROLE,
        errors,
        f"EdgeEnv handoff role must be {EDGEENV_HANDOFF_ROLE}",
    )

    handoff_files = handoff.get("files")
    _record(
        isinstance(handoff_files, dict),
        errors,
        "EdgeEnv handoff files must be an object",
    )
    manifest_files = (
        manifest.get("files") if isinstance(manifest.get("files"), dict) else {}
    )
    if isinstance(handoff_files, dict):
        for key in sorted(REQUIRED_FILES - {"aiguard_guard_analysis"}):
            _record(
                handoff_files.get(key) == manifest_files.get(key),
                errors,
                "EdgeEnv handoff files."
                f"{key} must match bundle manifest files.{key}",
            )
        _record(
            "aiguard_guard_analysis" not in handoff_files,
            errors,
            "EdgeEnv handoff files must not include aiguard_guard_analysis",
        )
        _validate_edgeenv_handoff_runtime_history_artifact(
            handoff_files,
            handoff_path=handoff_path,
            errors=errors,
        )

    alignment = handoff.get("lab_bundle_alignment")
    _record(
        isinstance(alignment, dict),
        errors,
        "EdgeEnv handoff lab_bundle_alignment must be an object",
    )
    if not isinstance(alignment, dict):
        return

    _record(
        alignment.get("bundle_schema_version") == EXPECTED_SCHEMA_VERSION,
        errors,
        "EdgeEnv handoff lab_bundle_alignment.bundle_schema_version must be "
        f"{EXPECTED_SCHEMA_VERSION}",
    )
    _record(
        set(alignment.get("required_file_keys") or []) == REQUIRED_FILES,
        errors,
        "EdgeEnv handoff lab_bundle_alignment.required_file_keys must match "
        "Lab required files",
    )
    produced_file_keys = set(alignment.get("edgeenv_produced_file_keys") or [])
    _record(
        (REQUIRED_FILES - {"aiguard_guard_analysis"}).issubset(produced_file_keys),
        errors,
        "EdgeEnv handoff lab_bundle_alignment.edgeenv_produced_file_keys "
        "must include baseline_result, candidate_result, and edgeenv_regression_report",
    )
    _record(
        produced_file_keys.isdisjoint({"aiguard_guard_analysis"}),
        errors,
        "EdgeEnv handoff lab_bundle_alignment.edgeenv_produced_file_keys "
        "must not include aiguard_guard_analysis",
    )
    _record(
        alignment.get("external_file_keys") == ["aiguard_guard_analysis"],
        errors,
        "EdgeEnv handoff lab_bundle_alignment.external_file_keys must be "
        "['aiguard_guard_analysis']",
    )

    source_repositories = alignment.get("source_repositories")
    _record(
        isinstance(source_repositories, dict),
        errors,
        "EdgeEnv handoff lab_bundle_alignment.source_repositories must be an object",
    )
    if isinstance(source_repositories, dict):
        for key, expected in REQUIRED_SOURCE_REPOSITORIES.items():
            _record(
                source_repositories.get(key) == expected,
                errors,
                "EdgeEnv handoff lab_bundle_alignment.source_repositories."
                f"{key} must be {expected}",
            )

    artifact_roles = alignment.get("artifact_roles")
    _record(
        isinstance(artifact_roles, dict),
        errors,
        "EdgeEnv handoff lab_bundle_alignment.artifact_roles must be an object",
    )
    if isinstance(artifact_roles, dict):
        for key, expected in REQUIRED_ARTIFACT_ROLES.items():
            _record(
                artifact_roles.get(key) == expected,
                errors,
                "EdgeEnv handoff lab_bundle_alignment.artifact_roles."
                f"{key} must be {expected}",
            )

    producer_contracts = alignment.get("producer_contracts")
    _record(
        isinstance(producer_contracts, dict),
        errors,
        "EdgeEnv handoff lab_bundle_alignment.producer_contracts must be an object",
    )
    if isinstance(producer_contracts, dict):
        for key, expected in REQUIRED_PRODUCER_CONTRACTS.items():
            _record(
                producer_contracts.get(key) == expected,
                errors,
                "EdgeEnv handoff lab_bundle_alignment.producer_contracts."
                f"{key} must be {expected}",
            )

    boundary_flags = alignment.get("boundary_flags")
    _record(
        isinstance(boundary_flags, dict),
        errors,
        "EdgeEnv handoff lab_bundle_alignment.boundary_flags must be an object",
    )
    if isinstance(boundary_flags, dict):
        for key, expected in REQUIRED_EDGEENV_HANDOFF_BOUNDARY_FLAGS.items():
            _record(
                boundary_flags.get(key) is expected,
                errors,
                "EdgeEnv handoff lab_bundle_alignment.boundary_flags."
                f"{key} must be {expected}",
            )


def _validate_edgeenv_handoff_runtime_history_artifact(
    handoff_files: dict[str, Any],
    *,
    handoff_path: Path,
    errors: list[str],
) -> None:
    raw_path = handoff_files.get(EDGEENV_HANDOFF_RUNTIME_HISTORY_KEY)
    _record(
        isinstance(raw_path, str),
        errors,
        "EdgeEnv handoff files.runtime_telemetry_history must be a string path",
    )
    if not isinstance(raw_path, str):
        return

    resolved = _resolve_bundle_path(handoff_path, raw_path)
    _record(
        resolved.exists(),
        errors,
        f"EdgeEnv handoff files.runtime_telemetry_history does not exist: {resolved}",
    )
    if not resolved.exists():
        return

    try:
        history = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(
            "EdgeEnv handoff files.runtime_telemetry_history is invalid JSON: "
            f"{resolved}: {exc}"
        )
        return
    except OSError as exc:
        errors.append(
            "EdgeEnv handoff files.runtime_telemetry_history could not be read: "
            f"{resolved}: {exc}"
        )
        return

    _record(
        isinstance(history, dict),
        errors,
        "EdgeEnv handoff files.runtime_telemetry_history must be a JSON object",
    )
    if not isinstance(history, dict):
        return
    _validate_edgeenv_runtime_history_artifact(history, errors)


def _validate_edgeenv_runtime_history_artifact(
    history: dict[str, Any],
    errors: list[str],
) -> None:
    _record(
        history.get("schema_version")
        == REQUIRED_PRODUCER_CONTRACTS["edgeenv_history_schema"],
        errors,
        "EdgeEnv handoff runtime_telemetry_history.schema_version must be "
        f"{REQUIRED_PRODUCER_CONTRACTS['edgeenv_history_schema']}",
    )
    summary = history.get("summary") or {}
    _record(
        summary.get("registered_runs") == 3,
        errors,
        "EdgeEnv handoff runtime_telemetry_history.summary.registered_runs must be 3",
    )
    _record(
        summary.get("telemetry_runs") == 2,
        errors,
        "EdgeEnv handoff runtime_telemetry_history.summary.telemetry_runs must be 2",
    )
    _record(
        summary.get("missing_telemetry_runs") == 1,
        errors,
        "EdgeEnv handoff runtime_telemetry_history.summary."
        "missing_telemetry_runs must be 1",
    )
    _record(
        summary.get("orchestrator_feed_runs") == 2,
        errors,
        "EdgeEnv handoff runtime_telemetry_history.summary."
        "orchestrator_feed_runs must be 2",
    )
    _record(
        summary.get("history_seed_runs") == 2,
        errors,
        "EdgeEnv handoff runtime_telemetry_history.summary.history_seed_runs must be 2",
    )
    coverage = history.get("telemetry_coverage")
    _record(
        isinstance(coverage, dict),
        errors,
        "EdgeEnv handoff runtime_telemetry_history must include telemetry_coverage",
    )
    if isinstance(coverage, dict):
        _validate_edgeenv_history_coverage_summary(coverage, errors)
    _validate_edgeenv_history_seed_runs(history, errors)
    _validate_edgeenv_missing_telemetry_orchestrator_context(
        history,
        errors,
        "EdgeEnv handoff runtime_telemetry_history",
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
        summary.get("orchestrator_feed_runs") == 2,
        errors,
        "runtime_telemetry_context.history.summary.orchestrator_feed_runs must be 2",
    )
    _record(
        summary.get("missing_telemetry_runs") == 1,
        errors,
        "runtime_telemetry_context.history.summary.missing_telemetry_runs must be 1",
    )
    _record(
        summary.get("history_seed_runs") == 2,
        errors,
        "runtime_telemetry_context.history.summary.history_seed_runs must be 2",
    )
    history_coverage = history.get("telemetry_coverage")
    _record(
        isinstance(history_coverage, dict),
        errors,
        "runtime_telemetry_context.history must include telemetry_coverage",
    )
    if isinstance(history_coverage, dict):
        _validate_edgeenv_history_coverage_summary(history_coverage, errors)
    _validate_edgeenv_history_seed_runs(history, errors)
    _validate_edgeenv_missing_telemetry_orchestrator_context(
        history,
        errors,
        "runtime_telemetry_context.history",
    )

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
    _validate_orchestrator_producer_markers(
        operation_context,
        errors,
        "orchestrator_operation_context",
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
    _validate_orchestrator_mapping_hint(operation_context, errors)


def _validate_orchestrator_producer_markers(
    operation_context: dict[str, Any],
    errors: list[str],
    prefix: str,
) -> None:
    _record(
        operation_context.get("source_repository")
        == REQUIRED_SOURCE_REPOSITORIES["orchestrator_operation_context"],
        errors,
        f"{prefix}.source_repository must be "
        f"{REQUIRED_SOURCE_REPOSITORIES['orchestrator_operation_context']}",
    )
    _record(
        operation_context.get("artifact_role")
        == REQUIRED_ARTIFACT_ROLES["orchestrator_operation_context"],
        errors,
        f"{prefix}.artifact_role must be "
        f"{REQUIRED_ARTIFACT_ROLES['orchestrator_operation_context']}",
    )
    _record(
        operation_context.get("producer_contract")
        == REQUIRED_PRODUCER_CONTRACTS["orchestrator_feed_schema"],
        errors,
        f"{prefix}.producer_contract must be "
        f"{REQUIRED_PRODUCER_CONTRACTS['orchestrator_feed_schema']}",
    )


def _validate_orchestrator_mapping_hint(
    operation_context: dict[str, Any],
    errors: list[str],
) -> None:
    mapping_hint = operation_context.get("edgeenv_mapping_hint")
    _record(
        isinstance(mapping_hint, dict),
        errors,
        "orchestrator_operation_context.edgeenv_mapping_hint must be an object",
    )
    if not isinstance(mapping_hint, dict):
        return

    for key, expected in REQUIRED_ORCHESTRATOR_MAPPING_HINT.items():
        _record(
            mapping_hint.get(key) == expected,
            errors,
            f"orchestrator_operation_context.edgeenv_mapping_hint.{key} "
            f"must be {expected}",
        )

    required_fields = mapping_hint.get("candidate_context_required_fields")
    _record(
        isinstance(required_fields, list),
        errors,
        "orchestrator_operation_context.edgeenv_mapping_hint."
        "candidate_context_required_fields must be a list",
    )
    if isinstance(required_fields, list):
        missing_fields = sorted(
            REQUIRED_ORCHESTRATOR_CANDIDATE_CONTEXT_FIELDS - set(required_fields)
        )
        _record(
            not missing_fields,
            errors,
            "orchestrator_operation_context.edgeenv_mapping_hint."
            f"candidate_context_required_fields is missing {missing_fields}",
        )

    evidence_candidates = mapping_hint.get("aiguard_evidence_candidates")
    _record(
        isinstance(evidence_candidates, list),
        errors,
        "orchestrator_operation_context.edgeenv_mapping_hint."
        "aiguard_evidence_candidates must be a list",
    )
    if isinstance(evidence_candidates, list):
        missing_candidates = sorted(
            REQUIRED_ORCHESTRATOR_AIGUARD_EVIDENCE_CANDIDATES
            - set(evidence_candidates)
        )
        _record(
            not missing_candidates,
            errors,
            "orchestrator_operation_context.edgeenv_mapping_hint."
            f"aiguard_evidence_candidates is missing {missing_candidates}",
        )

    candidate_context = operation_context.get("candidate_context")
    _record(
        isinstance(candidate_context, dict),
        errors,
        "orchestrator_operation_context.candidate_context must be an object",
    )
    if isinstance(candidate_context, dict):
        missing_context_fields = sorted(
            REQUIRED_ORCHESTRATOR_CANDIDATE_CONTEXT_FIELDS - set(candidate_context)
        )
        _record(
            not missing_context_fields,
            errors,
            "orchestrator_operation_context.candidate_context is missing "
            f"{missing_context_fields}",
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


def _validate_edgeenv_history_seed_runs(
    history: dict[str, Any],
    errors: list[str],
) -> None:
    runs = history.get("runs")
    _record(
        isinstance(runs, list),
        errors,
        "runtime_telemetry_context.history.runs must be a list",
    )
    if not isinstance(runs, list):
        return

    runs_by_id = {
        item.get("run_id"): item
        for item in runs
        if isinstance(item, dict) and isinstance(item.get("run_id"), str)
    }
    for run_id in ("edgeenv-smoke-baseline", "edgeenv-smoke-candidate"):
        run = runs_by_id.get(run_id)
        _record(
            isinstance(run, dict),
            errors,
            f"runtime_telemetry_context.history.runs must include {run_id}",
        )
        if isinstance(run, dict):
            _validate_runtime_history_seed(
                run.get("runtime_telemetry_history_seed"),
                errors,
                f"runtime_telemetry_context.history.runs[{run_id}]",
            )


def _validate_edgeenv_missing_telemetry_orchestrator_context(
    history: dict[str, Any],
    errors: list[str],
    label: str,
) -> None:
    missing_telemetry = history.get("missing_telemetry")
    _record(
        isinstance(missing_telemetry, list),
        errors,
        f"{label}.missing_telemetry must be a list",
    )
    if not isinstance(missing_telemetry, list):
        return

    missing_run = next(
        (
            item
            for item in missing_telemetry
            if isinstance(item, dict)
            and item.get("run_id") == "edgeenv-smoke-missing"
        ),
        None,
    )
    _record(
        isinstance(missing_run, dict),
        errors,
        f"{label}.missing_telemetry must include edgeenv-smoke-missing",
    )
    if not isinstance(missing_run, dict):
        return

    _record(
        missing_run.get("reason") == "runtime_telemetry_missing",
        errors,
        f"{label}.missing_telemetry[edgeenv-smoke-missing].reason "
        "must be runtime_telemetry_missing",
    )
    operation_context = missing_run.get("orchestrator_operation_context")
    _record(
        isinstance(operation_context, dict),
        errors,
        f"{label}.missing_telemetry[edgeenv-smoke-missing] must include "
        "orchestrator_operation_context",
    )
    if not isinstance(operation_context, dict):
        return

    prefix = (
        f"{label}.missing_telemetry[edgeenv-smoke-missing]."
        "orchestrator_operation_context"
    )
    _record(
        operation_context.get("schema_version")
        == REQUIRED_PRODUCER_CONTRACTS["orchestrator_feed_schema"],
        errors,
        f"{prefix}.schema_version must be "
        f"{REQUIRED_PRODUCER_CONTRACTS['orchestrator_feed_schema']}",
    )
    _validate_orchestrator_producer_markers(operation_context, errors, prefix)
    _record(
        operation_context.get("not_a_regression_judgement") is True,
        errors,
        f"{prefix}.not_a_regression_judgement must be true",
    )
    _record(
        operation_context.get("not_a_comparability_gate") is True,
        errors,
        f"{prefix}.not_a_comparability_gate must be true",
    )
    _record(
        operation_context.get("decision_owner") == "lab",
        errors,
        f"{prefix}.decision_owner must be lab",
    )
    _record(
        operation_context.get("regression_owner") == "edgeenv",
        errors,
        f"{prefix}.regression_owner must be edgeenv",
    )
    _validate_orchestrator_mapping_hint(operation_context, errors)


def _validate_runtime_history_seed(
    seed: Any,
    errors: list[str],
    path: str,
) -> None:
    _record(
        isinstance(seed, dict),
        errors,
        f"{path}.runtime_telemetry_history_seed must be an object",
    )
    if not isinstance(seed, dict):
        return
    _record(
        seed.get("schema_version")
        == REQUIRED_PRODUCER_CONTRACTS["runtime_telemetry_history_seed_schema"],
        errors,
        f"{path}.runtime_telemetry_history_seed.schema_version must be "
        f"{REQUIRED_PRODUCER_CONTRACTS['runtime_telemetry_history_seed_schema']}",
    )
    _record(
        seed.get("registry_owner") == "edgeenv",
        errors,
        f"{path}.runtime_telemetry_history_seed.registry_owner must be edgeenv",
    )
    _record(
        seed.get("decision_owner") == "lab",
        errors,
        f"{path}.runtime_telemetry_history_seed.decision_owner must be lab",
    )
    _record(
        seed.get("production_monitoring") is False,
        errors,
        f"{path}.runtime_telemetry_history_seed.production_monitoring must be false",
    )
    _record(
        seed.get("missing_telemetry_is_failure") is False,
        errors,
        f"{path}.runtime_telemetry_history_seed.missing_telemetry_is_failure must be false",
    )
    points = seed.get("points")
    _record(
        isinstance(points, list) and len(points) >= 1,
        errors,
        f"{path}.runtime_telemetry_history_seed.points must include replay points",
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
    _record(
        edgeenv.get("telemetry_coverage_source") == "history_telemetry_coverage",
        errors,
        "AIGuard coverage evidence telemetry_coverage_source must be "
        "history_telemetry_coverage",
    )
    _record(
        edgeenv.get("history_telemetry_coverage_missing_field_run_count") == 1.0,
        errors,
        "AIGuard coverage evidence history coverage missing field run count "
        "must be 1.0",
    )
    _validate_aiguard_history_seed_context(edgeenv, errors)
    missing_field_runs = edgeenv.get("history_telemetry_coverage_missing_field_runs")
    _record(
        isinstance(missing_field_runs, list),
        errors,
        "AIGuard coverage evidence history missing field runs must be a list",
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
            "AIGuard coverage evidence history missing field runs must include "
            "edgeenv-smoke-candidate",
        )
        if isinstance(candidate_gap, dict):
            _record(
                candidate_gap.get("missing_fields") == ["queue_depth"],
                errors,
                "AIGuard coverage evidence history candidate missing_fields "
                "must be ['queue_depth']",
            )
    _validate_aiguard_orchestrator_mapping_hint(edgeenv, errors)
    _validate_aiguard_missing_orchestrator_context(edgeenv, errors)


def _validate_aiguard_history_seed_context(
    edgeenv_context: dict[str, Any],
    errors: list[str],
) -> None:
    _record(
        edgeenv_context.get("history_telemetry_seed_runs") == 2.0,
        errors,
        "AIGuard coverage evidence history_telemetry_seed_runs must be 2.0",
    )
    for role in ("baseline", "candidate"):
        _record(
            edgeenv_context.get(
                f"{role}_runtime_telemetry_history_seed_schema_version"
            )
            == REQUIRED_PRODUCER_CONTRACTS["runtime_telemetry_history_seed_schema"],
            errors,
            "AIGuard coverage evidence "
            f"{role}_runtime_telemetry_history_seed_schema_version must be "
            f"{REQUIRED_PRODUCER_CONTRACTS['runtime_telemetry_history_seed_schema']}",
        )
        _record(
            edgeenv_context.get(
                f"{role}_runtime_telemetry_history_seed_registry_owner"
            )
            == "edgeenv",
            errors,
            "AIGuard coverage evidence "
            f"{role}_runtime_telemetry_history_seed_registry_owner must be edgeenv",
        )
        _record(
            edgeenv_context.get(
                f"{role}_runtime_telemetry_history_seed_decision_owner"
            )
            == "lab",
            errors,
            "AIGuard coverage evidence "
            f"{role}_runtime_telemetry_history_seed_decision_owner must be lab",
        )
    _record(
        edgeenv_context.get(
            "candidate_runtime_telemetry_history_seed_production_monitoring"
        )
        is False,
        errors,
        "AIGuard coverage evidence candidate history seed production_monitoring "
        "must be false",
    )
    _record(
        edgeenv_context.get(
            "candidate_runtime_telemetry_history_seed_missing_telemetry_is_failure"
        )
        is False,
        errors,
        "AIGuard coverage evidence candidate history seed "
        "missing_telemetry_is_failure must be false",
    )
    _record(
        edgeenv_context.get("candidate_runtime_telemetry_history_seed_point_count")
        == 1.0,
        errors,
        "AIGuard coverage evidence candidate history seed point count must be 1.0",
    )


def _validate_aiguard_orchestrator_mapping_hint(
    edgeenv_context: dict[str, Any],
    errors: list[str],
) -> None:
    _record(
        edgeenv_context.get("orchestrator_source_repository")
        == REQUIRED_SOURCE_REPOSITORIES["orchestrator_operation_context"],
        errors,
        "AIGuard coverage evidence orchestrator_source_repository must be "
        f"{REQUIRED_SOURCE_REPOSITORIES['orchestrator_operation_context']}",
    )
    _record(
        edgeenv_context.get("orchestrator_artifact_role")
        == REQUIRED_ARTIFACT_ROLES["orchestrator_operation_context"],
        errors,
        "AIGuard coverage evidence orchestrator_artifact_role must be "
        f"{REQUIRED_ARTIFACT_ROLES['orchestrator_operation_context']}",
    )
    _record(
        edgeenv_context.get("orchestrator_producer_contract")
        == REQUIRED_PRODUCER_CONTRACTS["orchestrator_feed_schema"],
        errors,
        "AIGuard coverage evidence orchestrator_producer_contract must be "
        f"{REQUIRED_PRODUCER_CONTRACTS['orchestrator_feed_schema']}",
    )

    mapping_hint = edgeenv_context.get("orchestrator_edgeenv_mapping_hint")
    _record(
        isinstance(mapping_hint, dict),
        errors,
        "AIGuard coverage evidence orchestrator_edgeenv_mapping_hint "
        "must be an object",
    )
    if not isinstance(mapping_hint, dict):
        return

    for key, expected in REQUIRED_ORCHESTRATOR_MAPPING_HINT.items():
        _record(
            mapping_hint.get(key) == expected,
            errors,
            "AIGuard coverage evidence orchestrator_edgeenv_mapping_hint."
            f"{key} must be {expected}",
        )
        _record(
            edgeenv_context.get(f"orchestrator_mapping_hint_{key}") == expected,
            errors,
            "AIGuard coverage evidence orchestrator_mapping_hint_"
            f"{key} must be {expected}",
        )

    required_fields = mapping_hint.get("candidate_context_required_fields")
    _record(
        isinstance(required_fields, list),
        errors,
        "AIGuard coverage evidence orchestrator_edgeenv_mapping_hint."
        "candidate_context_required_fields must be a list",
    )
    if isinstance(required_fields, list):
        missing_fields = sorted(
            REQUIRED_ORCHESTRATOR_CANDIDATE_CONTEXT_FIELDS - set(required_fields)
        )
        _record(
            not missing_fields,
            errors,
            "AIGuard coverage evidence orchestrator_edgeenv_mapping_hint."
            f"candidate_context_required_fields is missing {missing_fields}",
        )

    evidence_candidates = mapping_hint.get("aiguard_evidence_candidates")
    _record(
        isinstance(evidence_candidates, list),
        errors,
        "AIGuard coverage evidence orchestrator_edgeenv_mapping_hint."
        "aiguard_evidence_candidates must be a list",
    )
    if isinstance(evidence_candidates, list):
        missing_candidates = sorted(
            REQUIRED_ORCHESTRATOR_AIGUARD_EVIDENCE_CANDIDATES
            - set(evidence_candidates)
        )
        _record(
            not missing_candidates,
            errors,
            "AIGuard coverage evidence orchestrator_edgeenv_mapping_hint."
            f"aiguard_evidence_candidates is missing {missing_candidates}",
        )

    flattened_required_fields = edgeenv_context.get(
        "orchestrator_mapping_hint_candidate_context_required_fields"
    )
    _record(
        isinstance(flattened_required_fields, list),
        errors,
        "AIGuard coverage evidence "
        "orchestrator_mapping_hint_candidate_context_required_fields "
        "must be a list",
    )
    if isinstance(flattened_required_fields, list):
        missing_flattened_fields = sorted(
            REQUIRED_ORCHESTRATOR_CANDIDATE_CONTEXT_FIELDS
            - set(flattened_required_fields)
        )
        _record(
            not missing_flattened_fields,
            errors,
            "AIGuard coverage evidence "
            "orchestrator_mapping_hint_candidate_context_required_fields "
            f"is missing {missing_flattened_fields}",
        )

    flattened_evidence_candidates = edgeenv_context.get(
        "orchestrator_mapping_hint_aiguard_evidence_candidates"
    )
    _record(
        isinstance(flattened_evidence_candidates, list),
        errors,
        "AIGuard coverage evidence "
        "orchestrator_mapping_hint_aiguard_evidence_candidates "
        "must be a list",
    )
    if isinstance(flattened_evidence_candidates, list):
        missing_flattened_candidates = sorted(
            REQUIRED_ORCHESTRATOR_AIGUARD_EVIDENCE_CANDIDATES
            - set(flattened_evidence_candidates)
        )
        _record(
            not missing_flattened_candidates,
            errors,
            "AIGuard coverage evidence "
            "orchestrator_mapping_hint_aiguard_evidence_candidates "
            f"is missing {missing_flattened_candidates}",
        )

    _record(
        edgeenv_context.get("orchestrator_candidate_context_telemetry_source")
        == "inferedge_orchestrator_operation_summary",
        errors,
        "AIGuard coverage evidence "
        "orchestrator_candidate_context_telemetry_source must be "
        "inferedge_orchestrator_operation_summary",
    )


def _validate_aiguard_missing_orchestrator_context(
    edgeenv_context: dict[str, Any],
    errors: list[str],
) -> None:
    _record(
        edgeenv_context.get("history_missing_telemetry_runs") == 1.0,
        errors,
        "AIGuard coverage evidence history_missing_telemetry_runs must be 1.0",
    )
    _record(
        edgeenv_context.get("history_missing_orchestrator_context_count") == 1.0,
        errors,
        "AIGuard coverage evidence "
        "history_missing_orchestrator_context_count must be 1.0",
    )
    run_ids = edgeenv_context.get("history_missing_orchestrator_context_run_ids")
    _record(
        isinstance(run_ids, list) and "edgeenv-smoke-missing" in run_ids,
        errors,
        "AIGuard coverage evidence "
        "history_missing_orchestrator_context_run_ids must include "
        "edgeenv-smoke-missing",
    )
    _record(
        edgeenv_context.get("history_missing_orchestrator_source_repository")
        == REQUIRED_SOURCE_REPOSITORIES["orchestrator_operation_context"],
        errors,
        "AIGuard coverage evidence "
        "history_missing_orchestrator_source_repository must be "
        f"{REQUIRED_SOURCE_REPOSITORIES['orchestrator_operation_context']}",
    )
    _record(
        edgeenv_context.get("history_missing_orchestrator_artifact_role")
        == REQUIRED_ARTIFACT_ROLES["orchestrator_operation_context"],
        errors,
        "AIGuard coverage evidence history_missing_orchestrator_artifact_role "
        f"must be {REQUIRED_ARTIFACT_ROLES['orchestrator_operation_context']}",
    )
    _record(
        edgeenv_context.get("history_missing_orchestrator_producer_contract")
        == REQUIRED_PRODUCER_CONTRACTS["orchestrator_feed_schema"],
        errors,
        "AIGuard coverage evidence history_missing_orchestrator_producer_contract "
        f"must be {REQUIRED_PRODUCER_CONTRACTS['orchestrator_feed_schema']}",
    )
    _record(
        edgeenv_context.get(
            "history_missing_orchestrator_candidate_context_telemetry_source"
        )
        == "inferedge_orchestrator_operation_summary",
        errors,
        "AIGuard coverage evidence "
        "history_missing_orchestrator_candidate_context_telemetry_source must be "
        "inferedge_orchestrator_operation_summary",
    )
    mapping_hint = edgeenv_context.get(
        "history_missing_orchestrator_edgeenv_mapping_hint"
    )
    _record(
        isinstance(mapping_hint, dict),
        errors,
        "AIGuard coverage evidence "
        "history_missing_orchestrator_edgeenv_mapping_hint must be an object",
    )
    if isinstance(mapping_hint, dict):
        for key, expected in REQUIRED_ORCHESTRATOR_MAPPING_HINT.items():
            _record(
                mapping_hint.get(key) == expected,
                errors,
                "AIGuard coverage evidence "
                f"history_missing_orchestrator_edgeenv_mapping_hint.{key} "
                f"must be {expected}",
            )
    evidence_candidates = edgeenv_context.get(
        "history_missing_orchestrator_mapping_hint_aiguard_evidence_candidates"
    )
    _record(
        isinstance(evidence_candidates, list),
        errors,
        "AIGuard coverage evidence "
        "history_missing_orchestrator_mapping_hint_aiguard_evidence_candidates "
        "must be a list",
    )
    if isinstance(evidence_candidates, list):
        missing_candidates = sorted(
            REQUIRED_ORCHESTRATOR_AIGUARD_EVIDENCE_CANDIDATES
            - set(evidence_candidates)
        )
        _record(
            not missing_candidates,
            errors,
            "AIGuard coverage evidence "
            "history_missing_orchestrator_mapping_hint_aiguard_evidence_candidates "
            f"is missing {missing_candidates}",
        )


def _write_summary(
    path: str,
    *,
    manifest_path: Path,
    errors: list[str],
    edgeenv_handoff_present: bool,
) -> None:
    if not path:
        return
    contract_markers = list(SUMMARY_CONTRACT_MARKERS)
    if edgeenv_handoff_present:
        contract_markers.extend(EDGEENV_HANDOFF_SUMMARY_CONTRACT_MARKERS)
    lines = [
        "# Runtime Intelligence Bundle Manifest Gate",
        "",
        f"- Manifest: `{manifest_path}`",
        f"- Status: {'failed' if errors else 'passed'}",
        f"- Error count: {len(errors)}",
        "",
        "## Validated Contract Markers",
        "",
        *[f"- {marker}" for marker in contract_markers],
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


def main(
    manifest: str,
    summary_out: str = "",
    edgeenv_handoff: str = "",
) -> int:
    manifest_path = Path(manifest).resolve()
    errors: list[str] = []
    manifest_payload = _load_json(manifest_path, "Runtime Intelligence bundle manifest")
    _validate_manifest_shape(manifest_payload, errors)
    if edgeenv_handoff:
        edgeenv_handoff_path = Path(edgeenv_handoff).resolve()
        _validate_edgeenv_handoff_alignment(
            _load_json(edgeenv_handoff_path, "EdgeEnv handoff manifest"),
            handoff_path=edgeenv_handoff_path,
            manifest=manifest_payload,
            errors=errors,
        )

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

    _write_summary(
        summary_out,
        manifest_path=manifest_path,
        errors=errors,
        edgeenv_handoff_present=bool(edgeenv_handoff),
    )
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
    edgeenv_handoff: str = typer.Option(
        "",
        "--edgeenv-handoff",
        help="Optional EdgeEnv producer-side Runtime Intelligence handoff manifest path",
    ),
    summary_out: str = typer.Option(
        "",
        "--summary-out",
        help="Optional Markdown gate summary output path",
    ),
) -> None:
    raise typer.Exit(
        main(
            manifest=manifest,
            summary_out=summary_out,
            edgeenv_handoff=edgeenv_handoff,
        )
    )


if __name__ == "__main__":
    typer.run(cli)
