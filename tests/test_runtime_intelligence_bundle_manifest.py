import json
import subprocess
import sys
from pathlib import Path

from scripts.check_runtime_intelligence_bundle_manifest import main as manifest_gate


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "examples" / "runtime_intelligence_chain" / "bundle_manifest.json"


def test_runtime_intelligence_bundle_manifest_gate_passes():
    assert manifest_gate(manifest=str(MANIFEST)) == 0


def test_runtime_intelligence_bundle_manifest_gate_cli_passes(tmp_path):
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = subprocess.run(
        [
            sys.executable,
            str(
                REPO_ROOT
                / "scripts"
                / "check_runtime_intelligence_bundle_manifest.py"
            ),
            "--manifest",
            str(MANIFEST),
            "--summary-out",
            str(summary_path),
        ],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Runtime Intelligence bundle manifest gate passed." in result.stdout
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Status: passed" in summary
    assert "- Error count: 0" in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_owner(tmp_path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["ownership"]["deployment_decision_owner"] = "aiguard"
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Status: failed" in summary
    assert "ownership.deployment_decision_owner must be lab" in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_source_repo(
    tmp_path,
):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["source_repositories"]["orchestrator_operation_context"] = "InferEdgeLab"
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert (
        "source_repositories.orchestrator_operation_context must be "
        "InferEdgeOrchestrator"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_orchestrator_boundary(
    tmp_path,
):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    edgeenv_path = (
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / manifest["files"]["edgeenv_regression_report"]
    )
    edgeenv = json.loads(edgeenv_path.read_text(encoding="utf-8"))
    edgeenv["runtime_telemetry_context"]["candidate"]["orchestrator_operation_context"][
        "not_a_comparability_gate"
    ] = False

    edgeenv_copy = tmp_path / "edgeenv_regression.json"
    edgeenv_copy.write_text(json.dumps(edgeenv), encoding="utf-8")
    manifest["files"]["edgeenv_regression_report"] = str(edgeenv_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = manifest_gate(manifest=str(manifest_path))

    assert result == 2


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_orchestrator_schema(
    tmp_path,
):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    edgeenv_path = (
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / manifest["files"]["edgeenv_regression_report"]
    )
    edgeenv = json.loads(edgeenv_path.read_text(encoding="utf-8"))
    edgeenv["runtime_telemetry_context"]["candidate"]["orchestrator_operation_context"][
        "schema_version"
    ] = "unknown"

    edgeenv_copy = tmp_path / "edgeenv_regression.json"
    edgeenv_copy.write_text(json.dumps(edgeenv), encoding="utf-8")
    manifest["files"]["edgeenv_regression_report"] = str(edgeenv_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert (
        "orchestrator_operation_context.schema_version must be "
        "inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_incomplete_guard_evidence(
    tmp_path,
):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    guard_path = (
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / manifest["files"]["aiguard_guard_analysis"]
    )
    guard_analysis = json.loads(guard_path.read_text(encoding="utf-8"))
    guard_analysis["evidence"][0].pop("raw_context")

    guard_copy = tmp_path / "aiguard_guard_analysis.json"
    guard_copy.write_text(json.dumps(guard_analysis), encoding="utf-8")
    manifest["files"]["aiguard_guard_analysis"] = str(guard_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "AIGuard evidence[0] is missing fields: ['raw_context']" in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_missing_edgeenv_coverage(
    tmp_path,
):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    edgeenv_path = (
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / manifest["files"]["edgeenv_regression_report"]
    )
    edgeenv = json.loads(edgeenv_path.read_text(encoding="utf-8"))
    edgeenv["runtime_telemetry_context"]["candidate"].pop("telemetry_coverage")

    edgeenv_copy = tmp_path / "edgeenv_regression.json"
    edgeenv_copy.write_text(json.dumps(edgeenv), encoding="utf-8")
    manifest["files"]["edgeenv_regression_report"] = str(edgeenv_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "candidate must include telemetry_coverage" in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_missing_history_coverage(
    tmp_path,
):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    edgeenv_path = (
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / manifest["files"]["edgeenv_regression_report"]
    )
    edgeenv = json.loads(edgeenv_path.read_text(encoding="utf-8"))
    edgeenv["runtime_telemetry_context"]["history"].pop("telemetry_coverage")

    edgeenv_copy = tmp_path / "edgeenv_regression.json"
    edgeenv_copy.write_text(json.dumps(edgeenv), encoding="utf-8")
    manifest["files"]["edgeenv_regression_report"] = str(edgeenv_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "history must include telemetry_coverage" in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_missing_guard_coverage(
    tmp_path,
):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    guard_path = (
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / manifest["files"]["aiguard_guard_analysis"]
    )
    guard_analysis = json.loads(guard_path.read_text(encoding="utf-8"))
    guard_analysis["evidence"] = [
        item
        for item in guard_analysis["evidence"]
        if item.get("type") != "runtime_telemetry_context_coverage"
    ]

    guard_copy = tmp_path / "aiguard_guard_analysis.json"
    guard_copy.write_text(json.dumps(guard_analysis), encoding="utf-8")
    manifest["files"]["aiguard_guard_analysis"] = str(guard_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert (
        "AIGuard evidence is missing types: "
        "['runtime_telemetry_context_coverage']"
    ) in summary
