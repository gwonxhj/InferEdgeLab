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
    assert operation_context["candidate_context"]["operation"][
        "max_total_queue_depth"
    ] == 7
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
    assert "edgeenv_orchestrator_operation_risk_summary" in evidence_types
    assert "edgeenv_orchestrator_task_event_rollup" in evidence_types
    assert "runtime_history_seed_run_config_traceability" in evidence_types
    assert "remote_execution_recovered_by_fallback" in evidence_types
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
    assert (
        guard_edgeenv_context[
            "orchestrator_candidate_operation_max_total_queue_depth"
        ]
        == 7.0
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
    operation_risk_evidence = next(
        item
        for item in bundle["guard_analysis"]["evidence"]
        if item["type"] == "edgeenv_orchestrator_operation_risk_summary"
    )
    assert operation_risk_evidence["status"] == "warning"
    assert operation_risk_evidence["observed_value"] == 4
    operation_risk_context = operation_risk_evidence["raw_context"][
        "operation_risk_summary"
    ]
    assert operation_risk_context["boundary_markers_valid"] is True
    assert operation_risk_context["queue_pressure_reason"] == (
        "queue_backlog_threshold_exceeded"
    )
    assert operation_risk_context["primary_health_reason"] == "worker_health_degraded"
    assert operation_risk_context["degraded_worker_ids"] == ["vision_agent"]
    task_event_rollup_evidence = next(
        item
        for item in bundle["guard_analysis"]["evidence"]
        if item["type"] == "edgeenv_orchestrator_task_event_rollup"
    )
    assert task_event_rollup_evidence["status"] == "warning"
    assert task_event_rollup_evidence["observed_value"] == 2
    assert task_event_rollup_evidence["raw_context"]["task_event_rollup"][
        "affected_tasks"
    ] == ["vision_agent", "voice_command_agent"]
    assert operation_risk_context["device_local_event_count"] == 15.0
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
    remote_fallback_evidence = next(
        item
        for item in bundle["guard_analysis"]["evidence"]
        if item["type"] == "remote_execution_recovered_by_fallback"
    )
    remote_dispatch_context = remote_fallback_evidence["raw_context"][
        "remote_dispatch"
    ]
    assert remote_dispatch_context["source_repository"] == "InferEdgeOrchestrator"
    assert remote_dispatch_context["production_remote_execution"] is False
    assert (
        remote_dispatch_context["operation_boundary"]
        == "remote dispatch starter evidence only"
    )
    assert remote_dispatch_context["remote_runtime_event_summary_present"] is True
    assert remote_dispatch_context["remote_runtime_event_summary_consistent"] is True
    assert (
        remote_dispatch_context["remote_runtime_event_summary_runtime_event_count"]
        == 3
    )
    assert (
        remote_dispatch_context["remote_runtime_event_summary_operation_boundary"]
        == "remote dispatch starter evidence only"
    )
    assert remote_dispatch_context["remote_runtime_event_summary"][
        "schema_version"
    ] == "inferedge-remote-runtime-event-summary-v1"
    assert remote_dispatch_context["remote_runtime_event_summary"][
        "runtime_event_count"
    ] == 3
    assert remote_dispatch_context["remote_runtime_event_summary"][
        "fallback_recovered"
    ] is True
    assert (
        remote_dispatch_context["remote_runtime_event_summary"][
            "operation_boundary"
        ]
        == "remote dispatch starter evidence only"
    )
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
    assert (
        "| AIGuard remote summary boundary | "
        "role=remote_dispatch_runtime_event_compact_summary, "
        "boundary=remote dispatch starter evidence only, "
        "production_remote_execution=False |"
    ) in bundle["markdown"]
    assert "| Orchestrator operation feed context | 2 |" in bundle["markdown"]
    assert "| Runtime telemetry history seed | 2 |" in bundle["markdown"]
    assert "| Runtime history seed run_config | 2 |" in bundle["markdown"]
    assert "| Orchestrator context attached runs | candidate |" in bundle["markdown"]
    assert (
        "| Orchestrator queue/deadline/fallback markers | candidate: "
        "queue_pressure_reason=queue_backlog_threshold_exceeded, "
        "max_total_queue_depth=7"
    ) in bundle["markdown"]
    assert (
        "| Jetson/device-local EdgeEnv preservation run | candidate: "
        "identity=jetson_device_local_preservation, path=device_local_starter, "
        "run=edgeenv-smoke-candidate |"
    ) in bundle["markdown"]
    assert (
        "| Jetson/device-local EdgeEnv preservation details | candidate: "
        "sources=device_local_cli_override, "
        "stages=vision_agent:device_local_starter, device_local_events=2, "
        "resource=tegrastats_timeline, queue=queue_backlog_threshold_exceeded |"
    ) in bundle["markdown"]
    assert "| Orchestrator task event rollup | candidate: " in bundle["markdown"]
    assert (
        "vision_agent(delay=1,miss=1,max_delay_cycles=3,max_wait_ms=15,"
        "policy=queue_backlog_threshold_exceeded:1)"
    ) in bundle["markdown"]
    assert (
        "voice_command_agent(fallback=1,policy=queue_backlog_threshold_exceeded:1,"
        "drop=load_shedding_backlog_threshold_exceeded:1)"
    ) in bundle["markdown"]
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
        "| AIGuard max queue raw-context traceability | candidate: "
        "report=max_total_queue_depth=7, "
        "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7, "
        "match=True |"
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
    assert (
        "| AIGuard remote dispatch event summary | "
        "events=3, final=succeeded, fallback_recovered=True |"
    ) in bundle["markdown"]
    assert "| AIGuard remote event summary consistency | consistent |" in bundle[
        "markdown"
    ]
    assert (
        "| AIGuard remote dispatch evidence | "
        "remote_execution_recovered_by_fallback |"
    ) in bundle["markdown"]
    assert (
        "| Remote fallback starter evidence | "
        "lab=Remote fallback starter evidence; "
        "evidence=remote_execution_recovered_by_fallback |"
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
    assert "### Reviewer Focus" in markdown
    assert "| Focus | Quick signal | First read |" in markdown
    assert "| Decision owner | Lab=review_required;" in markdown
    assert "| EdgeEnv regression gate | comparable=Yes; mode=same-condition;" in markdown
    assert "deltas=mean=+18.0%,p99=+32.0%,fps=-22.0%,+1 more" in markdown
    assert "| Telemetry/replay quality | gaps=0; history_missing_runs=1;" in markdown
    assert "| Operation context | queue_deadline_fallback=present;" in markdown
    assert "| AIGuard warnings | status=warning; verdict=suspicious;" in markdown
    assert "remote_dispatch=remote_execution_recovered_by_fallback" in markdown
    assert "### Detailed Evidence Rows" in markdown
    assert "Runtime telemetry coverage gaps" in markdown
    assert "Runtime telemetry history seed" in markdown
    assert "Runtime history seed run_config" in markdown
    assert "Runtime replay duration scope" in markdown
    assert "short 96-frame-class replay (96 frames)" in markdown
    assert "class=short_96_frame_class, frames=96" in markdown
    assert "source=entrypoint_requested_frames" in markdown
    assert "scope_label=source=entrypoint_requested_frames" in markdown
    assert "runtime_telemetry_field_gap" in markdown
    assert "coverage_missing_fields" in markdown
    assert "queue_depth" in markdown
    assert "AIGuard runtime operation anomalies" in markdown
    assert "AIGuard operation risk summary evidence" in markdown
    assert "edgeenv_orchestrator_operation_risk_summary" in markdown
    assert "AIGuard task event rollup evidence" in markdown
    assert "edgeenv_orchestrator_task_event_rollup" in markdown
    assert "tasks=vision_agent,voice_command_agent" in markdown
    assert "status=warning, markers=4" in markdown
    assert "health=worker_health_degraded" in markdown
    assert "Orchestrator context attached runs" in markdown
    assert "Orchestrator operation risk summary" in markdown
    assert "Jetson/device-local EdgeEnv preservation run" in markdown
    assert "Jetson/device-local EdgeEnv preservation details" in markdown
    assert "Lab EdgeEnv preservation context" in markdown
    assert "lab_report_preservation_context_present=True" in markdown
    assert "lab_preservation=present" in markdown
    assert (
        "identity=jetson_device_local_preservation, path=device_local_starter, "
        "run=edgeenv-smoke-candidate"
    ) in markdown
    assert (
        "| Reviewer operation quick scan | candidate: "
        "queue_pressure_reason=queue_backlog_threshold_exceeded, "
        "max_total_queue_depth=7, deadline_missed_count=2, fallback_count=1; "
        "preservation=identity=jetson_device_local_preservation, "
        "path=device_local_starter, run=edgeenv-smoke-candidate; "
        "task_rollup=present |"
    ) in markdown
    assert (
        "sources=device_local_cli_override, "
        "stages=vision_agent:device_local_starter, device_local_events=2, "
        "resource=tegrastats_timeline, queue=queue_backlog_threshold_exceeded"
    ) in markdown
    assert "queue=queue_backlog_threshold_exceeded" in markdown
    assert "AIGuard producer lineage handoff" in markdown
    assert "AIGuard max queue raw-context traceability" in markdown
    assert (
        "report=max_total_queue_depth=7, "
        "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7, "
        "match=True"
    ) in markdown
    assert "AIGuard producer-lineage guard alignment" in markdown
    assert "edgeenv_orchestrator_producer_lineage" in markdown
    assert "Device-local Orchestrator producer lineage is preserved" in markdown
    assert "device_local_cli_override" in markdown
    assert "AIGuard history seed handoff" in markdown
    assert "AIGuard history seed run_config markers" in markdown
    assert "AIGuard run_config traceability evidence" in markdown
    assert "runtime_history_seed_run_config_traceability" in markdown
    assert "AIGuard remote dispatch event summary" in markdown
    assert "events=3, final=succeeded, fallback_recovered=True" in markdown
    assert "AIGuard remote event summary consistency" in markdown
    assert "remote_execution_recovered_by_fallback" in markdown
    assert "Remote fallback starter evidence" in markdown
    assert "lab=Remote fallback starter evidence" in markdown
    assert (
        "baseline/candidate=shape=1x640x640, input_mode=dummy, "
        "input_preprocess=none, power_mode=unknown, jetson_clocks=unknown, "
        "warmup=1, runs=10"
    ) in markdown
    assert "Runtime Intelligence Risk Summary" in html
    assert "Reviewer Focus" in html
    assert "Quick signal" in html
    assert "Decision owner" in html
    assert "EdgeEnv regression gate" in html
    assert "Telemetry/replay quality" in html
    assert "Operation context" in html
    assert "AIGuard warnings" in html
    assert "Detailed Evidence Rows" in html
    assert "Orchestrator operation risk summary" in html
    assert "Orchestrator queue/deadline/fallback markers" in html
    assert "queue_pressure_reason=queue_backlog_threshold_exceeded" in html
    assert "Jetson/device-local EdgeEnv preservation run" in html
    assert "Jetson/device-local EdgeEnv preservation details" in html
    assert "Lab EdgeEnv preservation context" in html
    assert "Reviewer operation quick scan" in html
    assert "lab_report_preservation_context_present=True" in html
    assert "lab_preservation=present" in html
    assert "identity=jetson_device_local_preservation" in html
    assert "path=device_local_starter" in html
    assert "run=edgeenv-smoke-candidate" in html
    assert "Orchestrator task event rollup" in html
    assert (
        "vision_agent(delay=1,miss=1,max_delay_cycles=3,max_wait_ms=15,"
        "policy=queue_backlog_threshold_exceeded:1)"
    ) in html
    assert "queue=queue_backlog_threshold_exceeded" in html
    assert "AIGuard producer lineage handoff" in html
    assert "AIGuard max queue raw-context traceability" in html
    assert "orchestrator_candidate_operation_max_total_queue_depth=7" in html
    assert "AIGuard producer-lineage guard alignment" in html
    assert "edgeenv_orchestrator_producer_lineage" in html
    assert "Device-local Orchestrator producer lineage is preserved" in html
    assert "device_local_cli_override" in html
    assert "Runtime telemetry history seed" in html
    assert "Runtime history seed run_config" in html
    assert "Runtime replay duration scope" in html
    assert "short 96-frame-class replay (96 frames)" in html
    assert "source=entrypoint_requested_frames" in html
    assert "scope_label=source=entrypoint_requested_frames" in html
    assert "AIGuard history seed run_config markers" in html
    assert "AIGuard run_config traceability evidence" in html
    assert "runtime_history_seed_run_config_traceability" in html
    assert "runtime_queue_overload, runtime_thermal_instability" in html
    assert "AIGuard operation risk summary evidence" in html
    assert "edgeenv_orchestrator_operation_risk_summary" in html
    assert "AIGuard task event rollup evidence" in html
    assert "edgeenv_orchestrator_task_event_rollup" in html
    assert "tasks=vision_agent,voice_command_agent" in html
    assert "health=worker_health_degraded" in html
    assert "AIGuard remote dispatch event summary" in html
    assert "events=3, final=succeeded, fallback_recovered=True" in html
    assert "AIGuard remote event summary consistency" in html
    assert "remote_execution_recovered_by_fallback" in html
    assert "Remote fallback starter evidence" in html
    assert "lab=Remote fallback starter evidence" in html
