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
    "runtime_intelligence_bundle_manifest_gate_summary.md",
    "runtime_anomaly_gate_summary.md",
}
REQUIRED_JSON_ARTIFACTS = {
    "portfolio_demo_check.json",
    "deployment_risk_summary.json",
}
REQUIRED_BUNDLE_MANIFEST_SUMMARY_MARKERS = (
    "## Validated Contract Markers",
    "source_repositories: Runtime, EdgeEnv, Orchestrator, AIGuard, Lab",
    "producer_contracts: EdgeEnv history, Orchestrator feed, AIGuard diagnosis",
    "ownership: regression_owner=edgeenv, deployment_decision_owner=lab",
    "orchestrator_mapping_hint: coverage_summary_owner=edgeenv",
    "orchestrator_mapping_hint: operation_context_role=supplemental",
    "orchestrator_mapping_hint: aiguard_evidence_candidates=runtime_queue_overload,runtime_thermal_instability",
    "aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage",
    "aiguard_raw_context: orchestrator_mapping_hint preserved",
    "edgeenv_handoff: lab_bundle_alignment validated",
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
        "Runtime telemetry coverage gaps",
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
