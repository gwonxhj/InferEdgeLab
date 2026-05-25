import json
import subprocess
import sys
from pathlib import Path

from scripts.check_runtime_intelligence_bundle_manifest import main as manifest_gate


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "examples" / "runtime_intelligence_chain" / "bundle_manifest.json"
EDGEENV_HANDOFF = (
    REPO_ROOT
    / "examples"
    / "runtime_intelligence_chain"
    / "edgeenv_lab_handoff_manifest.json"
)


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
    assert "## Validated Contract Markers" in summary
    assert (
        "source_repositories: Runtime, EdgeEnv, Orchestrator, AIGuard, Lab"
        in summary
    )
    assert (
        "producer_contracts: EdgeEnv history, Orchestrator feed, AIGuard diagnosis"
        in summary
    )
    assert (
        "orchestrator_producer_markers: "
        "source_repository=InferEdgeOrchestrator,"
        "artifact_role=orchestrator-supplemental-operation-context,"
        "producer_contract=inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1"
        in summary
    )
    assert (
        "orchestrator_mapping_hint: "
        "aiguard_evidence_candidates=runtime_queue_overload,runtime_thermal_instability"
        in summary
    )
    assert (
        "aiguard_raw_context: telemetry_coverage_source=history_telemetry_coverage"
        in summary
    )
    assert (
        "aiguard_raw_context: missing_telemetry_orchestrator_context preserved"
        in summary
    )


def test_runtime_intelligence_bundle_manifest_gate_validates_edgeenv_handoff(
    tmp_path,
):
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    assert (
        manifest_gate(
            manifest=str(MANIFEST),
            edgeenv_handoff=str(EDGEENV_HANDOFF),
            summary_out=str(summary_path),
        )
        == 0
    )
    summary = summary_path.read_text(encoding="utf-8")
    assert "edgeenv_handoff: lab_bundle_alignment validated" in summary
    assert "edgeenv_handoff: runtime_telemetry_history validated" in summary
    assert "edgeenv_handoff: missing_telemetry_orchestrator_context validated" in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_edgeenv_handoff(
    tmp_path,
):
    handoff = json.loads(EDGEENV_HANDOFF.read_text(encoding="utf-8"))
    handoff["lab_bundle_alignment"]["artifact_roles"][
        "aiguard_guard_analysis"
    ] = "edgeenv-generated-guard-analysis"
    handoff["lab_bundle_alignment"]["edgeenv_produced_file_keys"].append(
        "aiguard_guard_analysis"
    )
    handoff_path = tmp_path / "edgeenv_lab_handoff_manifest.json"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(
        manifest=str(MANIFEST),
        edgeenv_handoff=str(handoff_path),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert (
        "edgeenv_produced_file_keys must not include aiguard_guard_analysis"
        in summary
    )
    assert (
        "lab_bundle_alignment.artifact_roles.aiguard_guard_analysis "
        "must be aiguard-deterministic-runtime-anomaly-evidence"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_missing_handoff_history(
    tmp_path,
):
    handoff = json.loads(EDGEENV_HANDOFF.read_text(encoding="utf-8"))
    handoff["files"]["runtime_telemetry_history"] = "missing_runtime_history.json"
    handoff_path = tmp_path / "edgeenv_lab_handoff_manifest.json"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(
        manifest=str(MANIFEST),
        edgeenv_handoff=str(handoff_path),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "files.runtime_telemetry_history does not exist" in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_missing_history_context(
    tmp_path,
):
    handoff = json.loads(EDGEENV_HANDOFF.read_text(encoding="utf-8"))
    runtime_history_path = (
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / handoff["files"]["runtime_telemetry_history"]
    )
    runtime_history = json.loads(runtime_history_path.read_text(encoding="utf-8"))
    missing_context = runtime_history["missing_telemetry"][0][
        "orchestrator_operation_context"
    ]
    missing_context["artifact_role"] = "edgeenv-owned-regression-context"
    missing_context["edgeenv_mapping_hint"]["coverage_summary_owner"] = "orchestrator"

    runtime_history_copy = tmp_path / "runtime_telemetry_history.json"
    runtime_history_copy.write_text(json.dumps(runtime_history), encoding="utf-8")
    handoff["files"]["runtime_telemetry_history"] = str(runtime_history_copy)
    handoff_path = tmp_path / "edgeenv_lab_handoff_manifest.json"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(
        manifest=str(MANIFEST),
        edgeenv_handoff=str(handoff_path),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert (
        "missing_telemetry[edgeenv-smoke-missing].orchestrator_operation_context"
        ".artifact_role must be orchestrator-supplemental-operation-context"
    ) in summary
    assert (
        "orchestrator_operation_context.edgeenv_mapping_hint."
        "coverage_summary_owner must be edgeenv"
    ) in summary


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


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_orchestrator_producer_marker(
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
        "artifact_role"
    ] = "lab-owned-deployment-risk-report"

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
        "orchestrator_operation_context.artifact_role must be "
        "orchestrator-supplemental-operation-context"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_mapping_hint(
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
    operation_context = edgeenv["runtime_telemetry_context"]["candidate"][
        "orchestrator_operation_context"
    ]
    mapping_hint = operation_context["edgeenv_mapping_hint"]
    mapping_hint["coverage_summary_owner"] = "orchestrator"
    mapping_hint.pop("candidate_context_required_fields")
    mapping_hint["aiguard_evidence_candidates"] = ["runtime_queue_overload"]
    operation_context["candidate_context"].pop("telemetry_source")

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
        "edgeenv_mapping_hint.coverage_summary_owner must be edgeenv"
        in summary
    )
    assert "candidate_context_required_fields must be a list" in summary
    assert (
        "aiguard_evidence_candidates is missing "
        "['runtime_thermal_instability']"
    ) in summary
    assert "candidate_context is missing ['telemetry_source']" in summary


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


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_history_seed(
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
    history = edgeenv["runtime_telemetry_context"]["history"]
    history["summary"]["history_seed_runs"] = 1
    candidate_seed = history["runs"][1]["runtime_telemetry_history_seed"]
    candidate_seed["registry_owner"] = "runtime"
    candidate_seed["decision_owner"] = "aiguard"

    edgeenv_copy = tmp_path / "edgeenv_regression.json"
    edgeenv_copy.write_text(json.dumps(edgeenv), encoding="utf-8")
    manifest["files"]["edgeenv_regression_report"] = str(edgeenv_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "history.summary.history_seed_runs must be 2" in summary
    assert "runtime_telemetry_history_seed.registry_owner must be edgeenv" in summary
    assert "runtime_telemetry_history_seed.decision_owner must be lab" in summary


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


def test_runtime_intelligence_bundle_manifest_gate_fails_for_old_guard_coverage_source(
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
    coverage_evidence = next(
        item
        for item in guard_analysis["evidence"]
        if item.get("type") == "runtime_telemetry_context_coverage"
    )
    edgeenv_context = coverage_evidence["raw_context"]["edgeenv_regression"]
    edgeenv_context["telemetry_coverage_source"] = "runtime_telemetry_context"
    edgeenv_context.pop("history_telemetry_coverage_missing_field_runs")

    guard_copy = tmp_path / "aiguard_guard_analysis.json"
    guard_copy.write_text(json.dumps(guard_analysis), encoding="utf-8")
    manifest["files"]["aiguard_guard_analysis"] = str(guard_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "telemetry_coverage_source must be history_telemetry_coverage" in summary
    assert "history missing field runs must be a list" in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_guard_mapping_hint(
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
    coverage_evidence = next(
        item
        for item in guard_analysis["evidence"]
        if item.get("type") == "runtime_telemetry_context_coverage"
    )
    edgeenv_context = coverage_evidence["raw_context"]["edgeenv_regression"]
    edgeenv_context["orchestrator_edgeenv_mapping_hint"][
        "coverage_summary_owner"
    ] = "aiguard"
    edgeenv_context["orchestrator_edgeenv_mapping_hint"][
        "aiguard_evidence_candidates"
    ] = ["runtime_queue_overload"]
    edgeenv_context.pop("orchestrator_mapping_hint_candidate_context_required_fields")
    edgeenv_context.pop("orchestrator_mapping_hint_aiguard_evidence_candidates")
    edgeenv_context["orchestrator_candidate_context_telemetry_source"] = "unknown"

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
        "orchestrator_edgeenv_mapping_hint.coverage_summary_owner "
        "must be edgeenv"
    ) in summary
    assert (
        "orchestrator_mapping_hint_candidate_context_required_fields "
        "must be a list"
    ) in summary
    assert (
        "orchestrator_edgeenv_mapping_hint.aiguard_evidence_candidates "
        "is missing ['runtime_thermal_instability']"
    ) in summary
    assert (
        "orchestrator_mapping_hint_aiguard_evidence_candidates "
        "must be a list"
    ) in summary
    assert (
        "orchestrator_candidate_context_telemetry_source must be "
        "inferedge_orchestrator_operation_summary"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_guard_producer_marker(
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
    coverage_evidence = next(
        item
        for item in guard_analysis["evidence"]
        if item.get("type") == "runtime_telemetry_context_coverage"
    )
    edgeenv_context = coverage_evidence["raw_context"]["edgeenv_regression"]
    edgeenv_context["orchestrator_producer_contract"] = "unknown"

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
        "AIGuard coverage evidence orchestrator_producer_contract must be "
        "inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_guard_missing_context(
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
    coverage_evidence = next(
        item
        for item in guard_analysis["evidence"]
        if item.get("type") == "runtime_telemetry_context_coverage"
    )
    edgeenv_context = coverage_evidence["raw_context"]["edgeenv_regression"]
    edgeenv_context["history_missing_orchestrator_artifact_role"] = (
        "edgeenv-regression-context"
    )
    edgeenv_context["history_missing_orchestrator_edgeenv_mapping_hint"][
        "coverage_summary_owner"
    ] = "aiguard"
    edgeenv_context[
        "history_missing_orchestrator_mapping_hint_aiguard_evidence_candidates"
    ] = ["runtime_queue_overload"]

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
        "history_missing_orchestrator_artifact_role must be "
        "orchestrator-supplemental-operation-context"
    ) in summary
    assert (
        "history_missing_orchestrator_edgeenv_mapping_hint."
        "coverage_summary_owner must be edgeenv"
    ) in summary
    assert (
        "history_missing_orchestrator_mapping_hint_aiguard_evidence_candidates "
        "is missing ['runtime_thermal_instability']"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_guard_history_seed(
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
    coverage_evidence = next(
        item
        for item in guard_analysis["evidence"]
        if item.get("type") == "runtime_telemetry_context_coverage"
    )
    edgeenv_context = coverage_evidence["raw_context"]["edgeenv_regression"]
    edgeenv_context["history_telemetry_seed_runs"] = 1.0
    edgeenv_context[
        "candidate_runtime_telemetry_history_seed_registry_owner"
    ] = "runtime"
    edgeenv_context[
        "candidate_runtime_telemetry_history_seed_decision_owner"
    ] = "aiguard"

    guard_copy = tmp_path / "aiguard_guard_analysis.json"
    guard_copy.write_text(json.dumps(guard_analysis), encoding="utf-8")
    manifest["files"]["aiguard_guard_analysis"] = str(guard_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "history_telemetry_seed_runs must be 2.0" in summary
    assert (
        "candidate_runtime_telemetry_history_seed_registry_owner must be edgeenv"
        in summary
    )
    assert (
        "candidate_runtime_telemetry_history_seed_decision_owner must be lab"
        in summary
    )
