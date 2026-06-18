# InferEdgeAIGuard EdgeEnv Handoff Alignment Report

## Summary

| Metric | Value |
| --- | --- |
| status | passed |
| recommendation | alignment_satisfied |
| decision_owner | lab |
| diagnosis_owner | aiguard |
| required_evidence_type_count | 10 |
| optional_evidence_type_count | 2 |
| guard_evidence_type_count | 13 |
| lab_expected_report_marker_count | 18 |
| lab_report_marker_owner | lab |
| report_marker_context_role | lab_report_contract_context |
| aiguard_validates_expected_report_markers | False |
| optional_evidence_context_role | read_only_optional_guard_context |
| aiguard_validates_optional_evidence_as_required | False |
| handoff_duration_traceability_present | False |

## Evidence Alignment

| Field | Values |
| --- | --- |
| required_evidence_types | runtime_telemetry_context_coverage, edgeenv_orchestrator_producer_lineage, edgeenv_orchestrator_operation_risk_rollup, edgeenv_orchestrator_task_event_rollup, edgeenv_orchestrator_operation_timeline_summary, edgeenv_orchestrator_scheduler_fairness_summary, runtime_history_seed_run_config_traceability, runtime_queue_overload, runtime_thermal_instability, remote_execution_recovered_by_fallback |
| optional_aiguard_evidence_types | stale_frame_risk, edgeenv_orchestrator_stale_drop_summary |
| guard_analysis_evidence_types | runtime_telemetry_context_coverage, edgeenv_orchestrator_producer_lineage, edgeenv_orchestrator_operation_risk_summary, edgeenv_orchestrator_operation_risk_rollup, edgeenv_orchestrator_task_event_rollup, edgeenv_orchestrator_operation_timeline_summary, edgeenv_orchestrator_scheduler_fairness_summary, runtime_history_seed_run_config_traceability, runtime_thermal_instability, runtime_queue_overload, remote_execution_recovered_by_fallback, stale_frame_risk, edgeenv_orchestrator_stale_drop_summary |
| missing_required_evidence_types | [] |
| optional_guard_evidence_types_present | edgeenv_orchestrator_stale_drop_summary, stale_frame_risk |
| missing_optional_evidence_types | [] |
| optional_present_source_artifact | InferEdgeAIGuard/examples/runtime_intelligence/aiguard_runtime_operation_guard_analysis_optional_stale_drop.json |
| optional_present_reproduction_command | python -m inferedge_aiguard.cli build-runtime-intelligence-optional-stale-drop --edgeenv-regression examples/runtime_intelligence/edgeenv_runtime_regression_with_optional_stale_drop_context.json --remote-dispatch examples/runtime_intelligence/remote_dispatch_fallback_recovered_result.json --orchestration-summary examples/runtime_intelligence/orchestrator_multi_workload_sustained_summary.json --save-json examples/runtime_intelligence/aiguard_runtime_operation_guard_analysis_optional_stale_drop.json |
| supplemental_guard_evidence_types | edgeenv_orchestrator_operation_risk_summary, edgeenv_orchestrator_stale_drop_summary, stale_frame_risk |
| lab_expected_report_markers | Runtime Intelligence Risk Summary, Runtime replay duration scope, Orchestrator operation feed context, EdgeEnv fixture matrix coverage, Reviewer operation quick scan, Orchestrator task event rollup, Lab EdgeEnv preservation context, AIGuard operation risk rollup evidence, AIGuard task event rollup evidence, AIGuard operation timeline evidence, AIGuard scheduler fairness evidence, AIGuard runtime operation anomalies, AIGuard remote dispatch event summary, AIGuard remote event summary consistency, Remote fallback starter evidence, lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback, AIGuard producer-lineage guard alignment, Lab remains the final deployment decision owner. |
| handoff_duration_sources | [] |
| handoff_duration_scope_labels | [] |
| errors | [] |

## Raw CLI Summary

```text
InferEdgeAIGuard EdgeEnv handoff alignment summary
- status: passed
- recommendation: alignment_satisfied
- decision_owner: lab
- diagnosis_owner: aiguard
- lab_expected_report_markers: [Runtime Intelligence Risk Summary, Runtime replay duration scope, Orchestrator operation feed context, EdgeEnv fixture matrix coverage, Reviewer operation quick scan, Orchestrator task event rollup, Lab EdgeEnv preservation context, AIGuard operation risk rollup evidence, AIGuard task event rollup evidence, AIGuard operation timeline evidence, AIGuard scheduler fairness evidence, AIGuard runtime operation anomalies, AIGuard remote dispatch event summary, AIGuard remote event summary consistency, Remote fallback starter evidence, lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback, AIGuard producer-lineage guard alignment, Lab remains the final deployment decision owner.]
- report_marker_context_role: lab_report_contract_context
- aiguard_validates_expected_report_markers: False
- optional_evidence_context_role: read_only_optional_guard_context
- aiguard_validates_optional_evidence_as_required: False
- handoff_duration_sources: []
- handoff_duration_scope_labels: []
- required_evidence_types: [runtime_telemetry_context_coverage, edgeenv_orchestrator_producer_lineage, edgeenv_orchestrator_operation_risk_rollup, edgeenv_orchestrator_task_event_rollup, edgeenv_orchestrator_operation_timeline_summary, edgeenv_orchestrator_scheduler_fairness_summary, runtime_history_seed_run_config_traceability, runtime_queue_overload, runtime_thermal_instability, remote_execution_recovered_by_fallback]
- optional_aiguard_evidence_types: [stale_frame_risk, edgeenv_orchestrator_stale_drop_summary]
- guard_analysis_evidence_types: [runtime_telemetry_context_coverage, edgeenv_orchestrator_producer_lineage, edgeenv_orchestrator_operation_risk_summary, edgeenv_orchestrator_operation_risk_rollup, edgeenv_orchestrator_task_event_rollup, edgeenv_orchestrator_operation_timeline_summary, edgeenv_orchestrator_scheduler_fairness_summary, runtime_history_seed_run_config_traceability, runtime_thermal_instability, runtime_queue_overload, remote_execution_recovered_by_fallback, stale_frame_risk, edgeenv_orchestrator_stale_drop_summary]
- missing_required_evidence_types: []
- optional_guard_evidence_types_present: [edgeenv_orchestrator_stale_drop_summary, stale_frame_risk]
- missing_optional_evidence_types: []
- optional_present_source_artifact: InferEdgeAIGuard/examples/runtime_intelligence/aiguard_runtime_operation_guard_analysis_optional_stale_drop.json
- optional_present_reproduction_command: python -m inferedge_aiguard.cli build-runtime-intelligence-optional-stale-drop --edgeenv-regression examples/runtime_intelligence/edgeenv_runtime_regression_with_optional_stale_drop_context.json --remote-dispatch examples/runtime_intelligence/remote_dispatch_fallback_recovered_result.json --orchestration-summary examples/runtime_intelligence/orchestrator_multi_workload_sustained_summary.json --save-json examples/runtime_intelligence/aiguard_runtime_operation_guard_analysis_optional_stale_drop.json
- supplemental_guard_evidence_types: [edgeenv_orchestrator_operation_risk_summary, edgeenv_orchestrator_stale_drop_summary, stale_frame_risk]
- handoff_producer_lineage_guard_alignment_run_ids: [edgeenv-smoke-candidate, edgeenv-smoke-missing]
- guard_analysis_producer_lineage_guard_alignment_run_ids: [edgeenv-smoke-candidate, edgeenv-smoke-missing]
```
