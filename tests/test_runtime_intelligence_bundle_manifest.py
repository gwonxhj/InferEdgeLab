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
        "orchestrator_downstream_guard_alignment: "
        "producer_lineage_evidence_type=edgeenv_orchestrator_producer_lineage"
        in summary
    )
    assert (
        "orchestrator_producer_lineage_shape: "
        "per-task source/stage/count mappings validated"
        in summary
    )
    assert "edgeenv_history_seed_run_config: run_config snapshots validated" in summary
    assert (
        "aiguard_evidence: runtime_history_seed_run_config_traceability validated"
        in summary
    )
    assert (
        "aiguard_evidence: remote_execution_recovered_by_fallback validated"
        in summary
    )
    assert (
        "aiguard_handoff_alignment: external required evidence types satisfied"
        in summary
    )
    assert "aiguard_raw_context: producer_lineage_shape preserved" in summary
    assert (
        "aiguard_raw_context: history_seed_run_config_traceability preserved"
        in summary
    )
    assert "aiguard_raw_context: remote_runtime_event_summary preserved" in summary
    assert (
        "aiguard_raw_context: remote_runtime_summary_boundary preserved"
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
    assert "aiguard_raw_context: downstream_guard_alignment preserved" in summary
    assert "aiguard_raw_context: producer_lineage_guard_alignment preserved" in summary
    assert (
        "expected_report_markers: Runtime Intelligence report markers declared"
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
    assert "edgeenv_handoff: history_seed_run_config validated" in summary
    assert "edgeenv_handoff: remote_dispatch_boundary preserved" in summary
    assert "edgeenv_handoff: device_local_producer_lineage validated" in summary
    assert "edgeenv_handoff: producer_lineage_guard_alignment validated" in summary
    assert "edgeenv_handoff: missing_telemetry_orchestrator_context validated" in summary
    assert (
        "edgeenv_handoff: external AIGuard evidence requirements declared"
        in summary
    )


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_seed_run_config(
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
    runtime_history["runs"][1]["runtime_telemetry_history_seed"]["run_config"][
        "runs"
    ] = "10"

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
        "runtime_telemetry_context.history.runs[edgeenv-smoke-candidate]"
        ".runtime_telemetry_history_seed.run_config.runs must be an integer"
        in summary
    )


def test_runtime_intelligence_bundle_manifest_gate_fails_without_remote_boundary(
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
    runtime_history["missing_telemetry"][0]["orchestrator_operation_context"].pop(
        "remote_runtime_event_summary"
    )

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
    assert "remote_runtime_event_summary must be an object" in summary


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


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_edgeenv_summary_guard_alignment(
    tmp_path,
):
    handoff = json.loads(EDGEENV_HANDOFF.read_text(encoding="utf-8"))
    handoff["files"]["edgeenv_regression_report"] = str(
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / "edgeenv_regression_with_orchestrator_context.json"
    )
    handoff["files"]["runtime_telemetry_history"] = str(
        REPO_ROOT
        / "examples"
        / "runtime_intelligence_chain"
        / "runtime_telemetry_history.json"
    )
    handoff["edgeenv_report_summary"][
        "producer_lineage_guard_alignment_run_ids"
    ] = ["edgeenv-smoke-candidate"]
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
        "edgeenv_report_summary.producer_lineage_guard_alignment_run_ids "
        "must match preserved downstream guard alignment run IDs"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_missing_external_guard_type(
    tmp_path,
):
    handoff = json.loads(EDGEENV_HANDOFF.read_text(encoding="utf-8"))
    required_types = handoff["lab_bundle_alignment"][
        "external_aiguard_required_evidence_types"
    ]
    required_types.remove("runtime_history_seed_run_config_traceability")
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
        "external_aiguard_required_evidence_types must match Lab-required "
        "AIGuard evidence types"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_missing_report_marker(
    tmp_path,
):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["expected_report_markers"].remove(
        "AIGuard remote dispatch event summary"
    )
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert (
        "expected_report_markers must match Lab-required Runtime "
        "Intelligence report markers"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_guard_handoff_mismatch(
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
        if item.get("type") != "runtime_history_seed_run_config_traceability"
    ]

    guard_copy = tmp_path / "aiguard_guard_analysis.json"
    guard_copy.write_text(json.dumps(guard_analysis), encoding="utf-8")
    manifest["files"]["aiguard_guard_analysis"] = str(guard_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(
        manifest=str(manifest_path),
        edgeenv_handoff=str(EDGEENV_HANDOFF),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert (
        "AIGuard handoff alignment missing required evidence types: "
        "['runtime_history_seed_run_config_traceability']"
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


def test_runtime_intelligence_bundle_manifest_gate_fails_for_missing_history_producer(
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
    candidate_context = runtime_history["runs"][1]["orchestrator_operation_context"][
        "candidate_context"
    ]
    candidate_context.pop("producer")

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
        "runs[edgeenv-smoke-candidate].orchestrator_operation_context."
        "candidate_context.producer must be an object"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_unmapped_device_source(
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
    producer = edgeenv["runtime_telemetry_context"]["candidate"][
        "orchestrator_operation_context"
    ]["candidate_context"]["producer"]
    producer["producer_sources_by_task"] = {"vision_agent": ["orchestration_summary"]}

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
        "device_local_producer_sources must also appear in "
        "producer_sources_by_task: ['device_local_cli_override']"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_handoff_stage_map(
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
    producer = runtime_history["runs"][1]["orchestrator_operation_context"][
        "candidate_context"
    ]["producer"]
    producer["producer_stage_by_task"] = {"vision_agent": ""}

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
        "producer_stage_by_task.vision_agent must be a non-empty string"
        in summary
    )


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


def test_runtime_intelligence_bundle_manifest_gate_fails_for_missing_guard_run_config_traceability(
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
        if item.get("type") != "runtime_history_seed_run_config_traceability"
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
        "['runtime_history_seed_run_config_traceability']"
    ) in summary


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_guard_run_config_traceability(
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
    traceability_evidence = next(
        item
        for item in guard_analysis["evidence"]
        if item.get("type") == "runtime_history_seed_run_config_traceability"
    )
    traceability_evidence["observed_value"] = 1
    context = traceability_evidence["raw_context"]["history_seed_run_config"]
    context["marker_labels"] = []
    context["registry_owner"] = "runtime"
    context["decision_owner"] = "aiguard"

    guard_copy = tmp_path / "aiguard_guard_analysis.json"
    guard_copy.write_text(json.dumps(guard_analysis), encoding="utf-8")
    manifest["files"]["aiguard_guard_analysis"] = str(guard_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "run_config traceability observed_value must be 2" in summary
    assert (
        "run_config traceability marker_labels must preserve "
        "baseline/candidate run_config markers"
    ) in summary
    assert "run_config traceability registry_owner must be edgeenv" in summary
    assert "run_config traceability decision_owner must be lab" in summary


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


def test_runtime_intelligence_bundle_manifest_gate_fails_for_bad_guard_lineage_evidence(
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
    lineage_evidence = next(
        item
        for item in guard_analysis["evidence"]
        if item.get("type") == "edgeenv_orchestrator_producer_lineage"
    )
    lineage_evidence["observed_value"] = 1
    lineage_evidence["raw_context"]["producer_lineage"][
        "missing_device_local_sources"
    ] = []
    lineage_evidence["raw_context"]["producer_lineage"][
        "candidate_lineage_shape_valid"
    ] = False

    guard_copy = tmp_path / "aiguard_guard_analysis.json"
    guard_copy.write_text(json.dumps(guard_analysis), encoding="utf-8")
    manifest["files"]["aiguard_guard_analysis"] = str(guard_copy)
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    summary_path = tmp_path / "bundle_manifest_gate_summary.md"

    result = manifest_gate(manifest=str(manifest_path), summary_out=str(summary_path))

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "producer lineage observed_value must be 2" in summary
    assert (
        "AIGuard producer lineage missing_device_local_sources must be "
        "['device_local_cli_override']"
    ) in summary
    assert "candidate_lineage_shape_valid must be true" in summary


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
