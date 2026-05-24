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
    assert bundle["guard_analysis"]["guard_verdict"] == "suspicious"
    assert bundle["guard_analysis"]["primary_reason"] == (
        "Runtime telemetry context has evidence gaps that require review."
    )
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
    assert "| Orchestrator operation feed context | 1 |" in bundle["markdown"]
    assert "| Runtime telemetry history seed | 2 |" in bundle["markdown"]
    assert "| Orchestrator context attached runs | candidate |" in bundle["markdown"]
    assert "runtime_queue_overload, runtime_thermal_instability" in bundle["markdown"]
    assert "| AIGuard Orchestrator context handoff | feeds=1.0, candidate |" in bundle[
        "markdown"
    ]
    assert "| AIGuard history seed handoff | seeds=2.0" in bundle["markdown"]
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
    assert "Runtime Intelligence Risk Summary" in markdown
    assert "Runtime telemetry coverage gaps" in markdown
    assert "Runtime telemetry history seed" in markdown
    assert "runtime_telemetry_field_gap" in markdown
    assert "coverage_missing_fields" in markdown
    assert "queue_depth" in markdown
    assert "AIGuard runtime operation anomalies" in markdown
    assert "Orchestrator context attached runs" in markdown
    assert "AIGuard history seed handoff" in markdown
    assert "Runtime Intelligence Risk Summary" in html
    assert "Runtime telemetry history seed" in html
    assert "runtime_queue_overload, runtime_thermal_instability" in html
