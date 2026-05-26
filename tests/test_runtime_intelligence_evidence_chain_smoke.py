from pathlib import Path

from inferedgelab.commands.compare import compare_cmd
from inferedgelab.services.compare_service import build_compare_bundle


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_RESULT = REPO_ROOT / "examples" / "edgeenv_regression" / "lab_baseline_result.json"
CANDIDATE_RESULT = REPO_ROOT / "examples" / "edgeenv_regression" / "lab_candidate_result.json"
EDGEENV_WITH_ORCHESTRATOR = (
    REPO_ROOT
    / "examples"
    / "runtime_intelligence_chain"
    / "edgeenv_regression_with_orchestrator_context.json"
)
AIGUARD_RUNTIME_OPERATION = (
    REPO_ROOT
    / "examples"
    / "runtime_intelligence_chain"
    / "aiguard_runtime_operation_guard_analysis.json"
)


def test_runtime_intelligence_chain_smoke_ingests_precomputed_guard_artifact():
    bundle = build_compare_bundle(
        base_path=str(BASE_RESULT),
        new_path=str(CANDIDATE_RESULT),
        edgeenv_regression_path=str(EDGEENV_WITH_ORCHESTRATOR),
        guard_analysis_path=str(AIGUARD_RUNTIME_OPERATION),
    )

    assert bundle["edgeenv_runtime_regression"]["runtime_telemetry_context"][
        "candidate"
    ]["orchestrator_context_present"] is True
    history = bundle["edgeenv_runtime_regression"]["runtime_telemetry_context"][
        "history"
    ]
    assert history["summary"]["history_seed_runs"] == 2
    assert history["summary"]["history_seed_run_config_runs"] == 2
    candidate_history_seed = next(
        item["runtime_telemetry_history_seed"]
        for item in history["runs"]
        if item["run_id"] == "edgeenv-smoke-candidate"
    )
    assert (
        candidate_history_seed["schema_version"]
        == "inferedge-runtime-telemetry-history-seed-v1"
    )
    assert candidate_history_seed["registry_owner"] == "edgeenv"
    assert candidate_history_seed["decision_owner"] == "lab"
    assert candidate_history_seed["production_monitoring"] is False
    assert candidate_history_seed["run_config"] == {
        "batch": 1,
        "height": 640,
        "width": 640,
        "warmup": 1,
        "runs": 10,
        "timeout_ms": None,
        "input_mode": "dummy",
        "input_preprocess": "none",
        "power_mode": "unknown",
        "jetson_clocks": "unknown",
    }
    operation_context = bundle["edgeenv_runtime_regression"][
        "runtime_telemetry_context"
    ]["candidate"]["orchestrator_operation_context"]
    mapping_hint = operation_context["edgeenv_mapping_hint"]
    assert mapping_hint["coverage_summary_owner"] == "edgeenv"
    assert (
        mapping_hint["coverage_summary_path"]
        == "runtime_telemetry_context.history.telemetry_coverage"
    )
    assert mapping_hint["operation_context_role"] == "supplemental"
    assert set(mapping_hint["candidate_context_required_fields"]) >= {
        "run_id",
        "telemetry_source",
        "operation",
        "resource",
    }
    assert set(mapping_hint["aiguard_evidence_candidates"]) >= {
        "runtime_queue_overload",
        "runtime_thermal_instability",
    }
    assert operation_context["candidate_context"]["telemetry_source"] == (
        "inferedge_orchestrator_operation_summary"
    )
    assert operation_context["downstream_guard_alignment"][
        "producer_lineage_evidence_type"
    ] == "edgeenv_orchestrator_producer_lineage"
    assert operation_context["downstream_guard_alignment"][
        "lab_is_final_decision_owner"
    ] is True
    assert bundle["guard_analysis"]["guard_verdict"] == "suspicious"
    assert bundle["guard_analysis"]["primary_reason"] == (
        "Runtime telemetry context has evidence gaps that require review."
    )
    evidence_types = {item["type"] for item in bundle["guard_analysis"]["evidence"]}
    assert "edgeenv_orchestrator_producer_lineage" in evidence_types
    assert "runtime_history_seed_run_config_traceability" in evidence_types
    coverage_evidence = next(
        item
        for item in bundle["guard_analysis"]["evidence"]
        if item["type"] == "runtime_telemetry_context_coverage"
    )
    assert coverage_evidence["status"] == "warning"
    assert coverage_evidence["observed_value"] == 1.0
    assert "runtime_telemetry_field_gap" in coverage_evidence["suspected_causes"]
    assert coverage_evidence["raw_context"]["edgeenv_regression"][
        "candidate_telemetry_coverage_missing_fields"
    ] == ["queue_depth"]
    assert coverage_evidence["raw_context"]["edgeenv_regression"][
        "telemetry_coverage_source"
    ] == "history_telemetry_coverage"
    assert coverage_evidence["raw_context"]["edgeenv_regression"][
        "history_telemetry_coverage_missing_field_runs"
    ] == [
        {
            "run_id": "edgeenv-smoke-candidate",
            "missing_fields": ["queue_depth"],
            "missing_field_count": 1,
            "missing_telemetry_is_failure": False,
        }
    ]
    guard_edgeenv_context = coverage_evidence["raw_context"]["edgeenv_regression"]
    assert guard_edgeenv_context["orchestrator_edgeenv_mapping_hint"][
        "coverage_summary_owner"
    ] == "edgeenv"
    assert guard_edgeenv_context["orchestrator_edgeenv_mapping_hint"][
        "coverage_summary_path"
    ] == "runtime_telemetry_context.history.telemetry_coverage"
    assert guard_edgeenv_context[
        "orchestrator_mapping_hint_operation_context_role"
    ] == "supplemental"
    assert set(
        guard_edgeenv_context["orchestrator_edgeenv_mapping_hint"][
            "aiguard_evidence_candidates"
        ]
    ) >= {"runtime_queue_overload", "runtime_thermal_instability"}
    assert set(
        guard_edgeenv_context[
            "orchestrator_mapping_hint_aiguard_evidence_candidates"
        ]
    ) >= {"runtime_queue_overload", "runtime_thermal_instability"}
    assert guard_edgeenv_context["orchestrator_candidate_context_telemetry_source"] == (
        "inferedge_orchestrator_operation_summary"
    )
    assert guard_edgeenv_context["orchestrator_downstream_guard_alignment"][
        "producer_lineage_evidence_type"
    ] == "edgeenv_orchestrator_producer_lineage"
    assert guard_edgeenv_context[
        "orchestrator_guard_alignment_producer_lineage_evidence_type"
    ] == "edgeenv_orchestrator_producer_lineage"
    assert guard_edgeenv_context[
        "orchestrator_guard_alignment_operation_evidence_candidates"
    ] == ["runtime_queue_overload", "runtime_thermal_instability"]
    assert (
        guard_edgeenv_context[
            "orchestrator_guard_alignment_lab_is_final_decision_owner"
        ]
        is True
    )
    assert guard_edgeenv_context["orchestrator_candidate_context_producer"][
        "operation_context_role"
    ] == "supplemental"
    assert guard_edgeenv_context[
        "orchestrator_candidate_device_local_producer_sources"
    ] == ["device_local_cli_override"]
    assert guard_edgeenv_context["orchestrator_candidate_producer_stage_by_task"] == {
        "vision_agent": "device_local_starter"
    }
    assert guard_edgeenv_context["orchestrator_candidate_device_local_event_count"] == 2.0
    assert guard_edgeenv_context[
        "history_missing_orchestrator_candidate_device_local_producer_sources"
    ] == ["device_local_cli_override"]
    assert guard_edgeenv_context["history_telemetry_seed_runs"] == 2.0
    assert (
        guard_edgeenv_context[
            "candidate_runtime_telemetry_history_seed_schema_version"
        ]
        == "inferedge-runtime-telemetry-history-seed-v1"
    )
    assert (
        guard_edgeenv_context["candidate_runtime_telemetry_history_seed_registry_owner"]
        == "edgeenv"
    )
    assert (
        guard_edgeenv_context["candidate_runtime_telemetry_history_seed_decision_owner"]
        == "lab"
    )
    assert guard_edgeenv_context["history_telemetry_seed_run_config_runs"] == 2.0
    assert (
        guard_edgeenv_context[
            "candidate_runtime_telemetry_history_seed_run_config_present"
        ]
        is True
    )
    assert guard_edgeenv_context[
        "candidate_runtime_telemetry_history_seed_run_config"
    ] == {
        "batch": 1,
        "height": 640,
        "width": 640,
        "warmup": 1,
        "runs": 10,
        "timeout_ms": None,
        "input_mode": "dummy",
        "input_preprocess": "none",
        "power_mode": "unknown",
        "jetson_clocks": "unknown",
    }
    guard_candidate_summary = bundle["guard_analysis"]["candidate_summary"][
        "edgeenv_regression"
    ]
    assert (
        guard_candidate_summary[
            "candidate_runtime_telemetry_history_seed_run_config_present"
        ]
        is True
    )
    assert (
        guard_edgeenv_context[
            "candidate_runtime_telemetry_history_seed_production_monitoring"
        ]
        is False
    )
    assert (
        guard_edgeenv_context[
            "candidate_runtime_telemetry_history_seed_missing_telemetry_is_failure"
        ]
        is False
    )
    assert guard_edgeenv_context["history_missing_telemetry_runs"] == 1.0
    assert guard_edgeenv_context["history_missing_orchestrator_context_run_ids"] == [
        "edgeenv-smoke-missing"
    ]
    producer_lineage_evidence = next(
        item
        for item in bundle["guard_analysis"]["evidence"]
        if item["type"] == "edgeenv_orchestrator_producer_lineage"
    )
    assert producer_lineage_evidence["status"] == "passed"
    assert producer_lineage_evidence["observed_value"] == 2
    assert producer_lineage_evidence["baseline_value"] == 2
    assert producer_lineage_evidence["raw_context"]["producer_lineage"][
        "candidate_device_local_sources"
    ] == ["device_local_cli_override"]
    assert producer_lineage_evidence["raw_context"]["producer_lineage"][
        "missing_device_local_sources"
    ] == ["device_local_cli_override"]
    assert producer_lineage_evidence["raw_context"]["producer_lineage"][
        "missing_context_run_ids"
    ] == ["edgeenv-smoke-missing"]
    assert producer_lineage_evidence["raw_context"]["producer_lineage"][
        "candidate_guard_alignment_valid"
    ] is True
    assert producer_lineage_evidence["raw_context"]["producer_lineage"][
        "candidate_guard_alignment_producer_lineage_evidence_type"
    ] == "edgeenv_orchestrator_producer_lineage"
    assert producer_lineage_evidence["raw_context"]["producer_lineage"][
        "missing_guard_alignment_valid"
    ] is True
    assert producer_lineage_evidence["raw_context"]["producer_lineage"][
        "missing_guard_alignment_producer_lineage_evidence_type"
    ] == "edgeenv_orchestrator_producer_lineage"
    assert (
        guard_edgeenv_context["history_missing_orchestrator_source_repository"]
        == "InferEdgeOrchestrator"
    )
    assert (
        guard_edgeenv_context["history_missing_orchestrator_artifact_role"]
        == "orchestrator-supplemental-operation-context"
    )
    run_config_traceability_evidence = next(
        item
        for item in bundle["guard_analysis"]["evidence"]
        if item["type"] == "runtime_history_seed_run_config_traceability"
    )
    assert run_config_traceability_evidence["status"] == "passed"
    assert run_config_traceability_evidence["observed_value"] == 2
    assert run_config_traceability_evidence["baseline_value"] == 2
    assert run_config_traceability_evidence["raw_context"]["history_seed_run_config"][
        "marker_labels"
    ] == [
        (
            "baseline/candidate=shape=1x640x640, input_mode=dummy, "
            "input_preprocess=none, power_mode=unknown, jetson_clocks=unknown, "
            "warmup=1, runs=10"
        )
    ]
    assert set(
        guard_edgeenv_context[
            "history_missing_orchestrator_mapping_hint_aiguard_evidence_candidates"
        ]
    ) >= {"runtime_queue_overload", "runtime_thermal_instability"}
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert bundle["deployment_decision"]["guard_status"] == "warning"
    assert "guard_warning_review" in bundle["deployment_decision"]["triggered_rules"]
    assert "edgeenv_runtime_regression_review" in bundle["deployment_decision"][
        "triggered_rules"
    ]
    assert (
        "| Runtime telemetry coverage gaps | baseline=none; candidate=queue_depth |"
        in bundle["markdown"]
    )
    assert "| Orchestrator operation feed context | 2 |" in bundle["markdown"]
    assert "| Runtime telemetry history seed | 2 |" in bundle["markdown"]
    assert "| Runtime history seed run_config | 2 |" in bundle["markdown"]
    assert "| Orchestrator context attached runs | candidate |" in bundle["markdown"]
    assert "runtime_queue_overload, runtime_thermal_instability" in bundle["markdown"]
    assert "| AIGuard Orchestrator context handoff | feeds=2.0, candidate |" in bundle[
        "markdown"
    ]
    assert (
        "| AIGuard producer lineage handoff | "
        "sources=device_local_cli_override, stages=vision_agent:device_local_starter, "
        "device_local_events=2.0, role=supplemental |"
    ) in bundle["markdown"]
    assert (
        "| AIGuard producer-lineage guard alignment | "
        "evidence=edgeenv_orchestrator_producer_lineage, "
        "candidates=runtime_queue_overload,runtime_thermal_instability, "
        "lab_final_owner=true |"
    ) in bundle["markdown"]
    assert "| AIGuard history seed handoff | seeds=2.0" in bundle["markdown"]
    assert (
        "| AIGuard history seed run_config markers | "
        "baseline/candidate=shape=1x640x640, input_mode=dummy, "
        "input_preprocess=none, power_mode=unknown, jetson_clocks=unknown, "
        "warmup=1, runs=10 |"
    ) in bundle["markdown"]
    assert (
        "| AIGuard run_config traceability evidence | "
        "status=passed, count=2/2, markers=baseline/candidate=shape=1x640x640, "
        "input_mode=dummy, input_preprocess=none, power_mode=unknown, "
        "jetson_clocks=unknown, warmup=1, runs=10 |"
    ) in bundle["markdown"]
    assert "Lab remains the final deployment decision owner" in bundle["markdown"]
    assert all(
        "raw_context" in item
        for item in bundle["guard_analysis"]["evidence"]
        if item["type"]
        in {"runtime_queue_overload", "runtime_thermal_instability"}
    )


def test_compare_cmd_runtime_intelligence_chain_writes_markdown_and_html(
    tmp_path, capsys
):
    markdown_out = tmp_path / "runtime_intelligence_chain.md"
    html_out = tmp_path / "runtime_intelligence_chain.html"

    compare_cmd(
        base_path=str(BASE_RESULT),
        new_path=str(CANDIDATE_RESULT),
        markdown_out=str(markdown_out),
        html_out=str(html_out),
        with_guard=False,
        edgeenv_regression=str(EDGEENV_WITH_ORCHESTRATOR),
        guard_analysis=str(AIGUARD_RUNTIME_OPERATION),
    )

    out = capsys.readouterr().out
    markdown = markdown_out.read_text(encoding="utf-8")
    html = html_out.read_text(encoding="utf-8")

    assert "Guard Analysis" in out
    assert "runtime_queue_overload" in out
    assert "raw_context: preserved in artifact; omitted from console summary" in out
    assert "'raw_context':" not in out
    assert "Runtime Intelligence Risk Summary" in markdown
    assert "Runtime telemetry coverage gaps" in markdown
    assert "Runtime telemetry history seed" in markdown
    assert "Runtime history seed run_config" in markdown
    assert "runtime_telemetry_field_gap" in markdown
    assert "coverage_missing_fields" in markdown
    assert "queue_depth" in markdown
    assert "AIGuard runtime operation anomalies" in markdown
    assert "Orchestrator context attached runs" in markdown
    assert "AIGuard producer lineage handoff" in markdown
    assert "AIGuard producer-lineage guard alignment" in markdown
    assert "edgeenv_orchestrator_producer_lineage" in markdown
    assert "Device-local Orchestrator producer lineage is preserved" in markdown
    assert "device_local_cli_override" in markdown
    assert "AIGuard history seed handoff" in markdown
    assert "AIGuard history seed run_config markers" in markdown
    assert "AIGuard run_config traceability evidence" in markdown
    assert "runtime_history_seed_run_config_traceability" in markdown
    assert (
        "baseline/candidate=shape=1x640x640, input_mode=dummy, "
        "input_preprocess=none, power_mode=unknown, jetson_clocks=unknown, "
        "warmup=1, runs=10"
    ) in markdown
    assert "Runtime Intelligence Risk Summary" in html
    assert "AIGuard producer lineage handoff" in html
    assert "AIGuard producer-lineage guard alignment" in html
    assert "edgeenv_orchestrator_producer_lineage" in html
    assert "Device-local Orchestrator producer lineage is preserved" in html
    assert "device_local_cli_override" in html
    assert "Runtime telemetry history seed" in html
    assert "Runtime history seed run_config" in html
    assert "AIGuard history seed run_config markers" in html
    assert "AIGuard run_config traceability evidence" in html
    assert "runtime_history_seed_run_config_traceability" in html
    assert "runtime_queue_overload, runtime_thermal_instability" in html
