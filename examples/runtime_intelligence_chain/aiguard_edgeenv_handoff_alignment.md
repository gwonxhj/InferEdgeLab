# InferEdgeAIGuard EdgeEnv Handoff Alignment

- status: passed
- recommendation: alignment_satisfied
- decision_owner: lab
- diagnosis_owner: aiguard
- lab_expected_report_markers: Runtime Intelligence Risk Summary, Runtime replay duration scope, Orchestrator operation feed context, Orchestrator task event rollup, Lab EdgeEnv preservation context, AIGuard task event rollup evidence, AIGuard runtime operation anomalies, AIGuard remote dispatch event summary, AIGuard remote event summary consistency, Remote fallback starter evidence, lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback, AIGuard producer-lineage guard alignment, Lab remains the final deployment decision owner.
- report_marker_context_role: lab_report_contract_context
- aiguard_validates_expected_report_markers: False
- required_evidence_types: runtime_telemetry_context_coverage, edgeenv_orchestrator_producer_lineage, edgeenv_orchestrator_task_event_rollup, runtime_history_seed_run_config_traceability, runtime_queue_overload, runtime_thermal_instability, remote_execution_recovered_by_fallback
- guard_analysis_evidence_types: runtime_telemetry_context_coverage, edgeenv_orchestrator_producer_lineage, edgeenv_orchestrator_operation_risk_summary, edgeenv_orchestrator_task_event_rollup, runtime_history_seed_run_config_traceability, runtime_thermal_instability, runtime_queue_overload, remote_execution_recovered_by_fallback
- missing_required_evidence_types: -
- supplemental_guard_evidence_types: edgeenv_orchestrator_operation_risk_summary
- handoff_producer_lineage_guard_alignment_run_ids: edgeenv-smoke-candidate, edgeenv-smoke-missing
- guard_analysis_producer_lineage_guard_alignment_run_ids: edgeenv-smoke-candidate, edgeenv-smoke-missing
- guard_alignment_summary_errors: -
- errors: -
