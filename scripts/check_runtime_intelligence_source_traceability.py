from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_HANDOFF_SCHEMA_VERSION = "edgeenv.runtime-intelligence-lab-handoff.v1"
EXPECTED_AIGUARD_ALIGNMENT_SCHEMA_VERSION = (
    "inferedge-aiguard-edgeenv-handoff-alignment-v1"
)
EXPECTED_EDGEENV_TRACEABILITY_CONTEXT_ROLE = (
    "read_only_optional_source_traceability"
)
EXPECTED_AIGUARD_SOURCE_ARTIFACT_MARKER = (
    "InferEdgeAIGuard/examples/runtime_intelligence/"
    "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
)
EXPECTED_AIGUARD_REPRODUCTION_COMMAND = [
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
EXPECTED_AIGUARD_REPRODUCTION_COMMAND_MARKER = " ".join(
    EXPECTED_AIGUARD_REPRODUCTION_COMMAND
)
EXPECTED_AIGUARD_SOURCE_ARTIFACT = {
    "repository": "InferEdgeAIGuard",
    "path": (
        "examples/runtime_intelligence/"
        "aiguard_runtime_operation_guard_analysis_optional_stale_drop.json"
    ),
    "schema_version": "inferedge-aiguard-diagnosis-v1",
    "role": "aiguard-optional-stale-drop-full-evidence-source",
    "context_role": "read_only_cross_repo_traceability",
    "reproduction_command": EXPECTED_AIGUARD_REPRODUCTION_COMMAND,
}
SUMMARY_MARKERS = (
    "source_traceability_alignment: EdgeEnv handoff and AIGuard optional-present fixture match",
    "edgeenv_optional_source_traceability: read_only_optional_source_traceability preserved",
    "aiguard_optional_present_source_artifact: "
    f"{EXPECTED_AIGUARD_SOURCE_ARTIFACT_MARKER}",
    "aiguard_optional_present_reproduction_command: "
    f"{EXPECTED_AIGUARD_REPRODUCTION_COMMAND_MARKER}",
    "ownership: edgeenv_does_not_generate_guard_analysis=true, lab_is_final_decision_owner=true",
)


def _record(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def _load_json(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"{label} not found: {path}: {exc}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is invalid JSON: {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{label} must be a JSON object: {path}")
        return {}
    return payload


def _source_artifact_from_handoff(
    handoff: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    _record(
        handoff.get("schema_version") == EXPECTED_HANDOFF_SCHEMA_VERSION,
        errors,
        f"EdgeEnv handoff schema_version must be {EXPECTED_HANDOFF_SCHEMA_VERSION}",
    )
    alignment = handoff.get("lab_bundle_alignment")
    _record(
        isinstance(alignment, dict),
        errors,
        "EdgeEnv handoff lab_bundle_alignment must be an object",
    )
    if not isinstance(alignment, dict):
        return {}
    traceability = alignment.get("optional_aiguard_source_traceability")
    _record(
        isinstance(traceability, dict),
        errors,
        "EdgeEnv handoff lab_bundle_alignment.optional_aiguard_source_traceability "
        "must be an object",
    )
    if not isinstance(traceability, dict):
        return {}

    _record(
        traceability.get("context_role")
        == EXPECTED_EDGEENV_TRACEABILITY_CONTEXT_ROLE,
        errors,
        "EdgeEnv optional source traceability context_role must be "
        f"{EXPECTED_EDGEENV_TRACEABILITY_CONTEXT_ROLE}",
    )
    _record(
        traceability.get("edgeenv_does_not_generate_guard_analysis") is True,
        errors,
        "EdgeEnv optional source traceability must keep "
        "edgeenv_does_not_generate_guard_analysis=true",
    )
    _record(
        traceability.get("lab_is_final_decision_owner") is True,
        errors,
        "EdgeEnv optional source traceability must keep "
        "lab_is_final_decision_owner=true",
    )
    source_artifact = traceability.get("optional_present_source_artifact")
    _record(
        isinstance(source_artifact, dict),
        errors,
        "EdgeEnv optional source traceability optional_present_source_artifact "
        "must be an object",
    )
    return source_artifact if isinstance(source_artifact, dict) else {}


def _source_artifact_from_aiguard_alignment(
    alignment: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    _record(
        alignment.get("schema_version")
        == EXPECTED_AIGUARD_ALIGNMENT_SCHEMA_VERSION,
        errors,
        "AIGuard alignment schema_version must be "
        f"{EXPECTED_AIGUARD_ALIGNMENT_SCHEMA_VERSION}",
    )
    _record(
        alignment.get("status") == "passed",
        errors,
        "AIGuard optional-present alignment status must be passed",
    )
    _record(
        alignment.get("decision_owner") == "lab",
        errors,
        "AIGuard optional-present alignment decision_owner must be lab",
    )
    _record(
        alignment.get("diagnosis_owner") == "aiguard",
        errors,
        "AIGuard optional-present alignment diagnosis_owner must be aiguard",
    )
    _record(
        alignment.get("aiguard_validates_optional_evidence_as_required") is False,
        errors,
        "AIGuard optional-present alignment must keep optional evidence "
        "read-only",
    )
    source_artifact = alignment.get("optional_present_source_artifact")
    _record(
        isinstance(source_artifact, dict),
        errors,
        "AIGuard optional-present alignment optional_present_source_artifact "
        "must be an object",
    )
    return source_artifact if isinstance(source_artifact, dict) else {}


def _validate_source_artifact(
    source_artifact: dict[str, Any],
    *,
    label: str,
    errors: list[str],
) -> None:
    _record(
        source_artifact == EXPECTED_AIGUARD_SOURCE_ARTIFACT,
        errors,
        f"{label} source artifact must match the Lab-known AIGuard optional "
        "stale-drop source artifact",
    )


def _write_summary(path: Path, errors: list[str]) -> None:
    lines = [
        "# Runtime Intelligence Source Traceability Gate",
        "",
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
        lines.append("## Validated Source Traceability")
        lines.append("")
        lines.extend(f"- {marker}" for marker in SUMMARY_MARKERS)
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(
    edgeenv_handoff: str,
    aiguard_alignment: str,
    summary_out: str = "",
) -> int:
    errors: list[str] = []
    handoff = _load_json(Path(edgeenv_handoff), errors, "EdgeEnv handoff manifest")
    alignment = _load_json(
        Path(aiguard_alignment),
        errors,
        "AIGuard optional-present alignment",
    )
    handoff_source_artifact = (
        _source_artifact_from_handoff(handoff, errors) if handoff else {}
    )
    aiguard_source_artifact = (
        _source_artifact_from_aiguard_alignment(alignment, errors)
        if alignment
        else {}
    )

    if handoff_source_artifact:
        _validate_source_artifact(
            handoff_source_artifact,
            label="EdgeEnv handoff",
            errors=errors,
        )
    if aiguard_source_artifact:
        _validate_source_artifact(
            aiguard_source_artifact,
            label="AIGuard alignment",
            errors=errors,
        )
    if handoff_source_artifact and aiguard_source_artifact:
        _record(
            handoff_source_artifact == aiguard_source_artifact,
            errors,
            "EdgeEnv handoff and AIGuard optional-present alignment must "
            "reference the same source artifact and reproduction command",
        )

    if summary_out:
        _write_summary(Path(summary_out), errors)
    return 2 if errors else 0


def cli() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Runtime Intelligence optional source traceability between "
            "EdgeEnv handoff metadata and AIGuard optional-present alignment."
        )
    )
    parser.add_argument("--edgeenv-handoff", required=True)
    parser.add_argument("--aiguard-alignment", required=True)
    parser.add_argument("--summary-out", default="")
    args = parser.parse_args()
    return main(
        edgeenv_handoff=args.edgeenv_handoff,
        aiguard_alignment=args.aiguard_alignment,
        summary_out=args.summary_out,
    )


if __name__ == "__main__":
    raise SystemExit(cli())
