# Agent Runtime Reliability Report

## Scope

This report is the first Lab-side bundle view for the reliable edge agent
runtime path.

It connects:

- Forge `agent_manifest.json` metadata
- Runtime `result.agent` metadata
- Orchestrator `inferedge-orchestration-summary-v1`
- AIGuard `inferedge-aiguard-diagnosis-v1`
- Lab-owned agent deployment decision context

This is a local-first report path. It is not a production cloud orchestration
dashboard and does not add DB/queue/auth/billing behavior.

Current demo scope: the committed evidence is a synthetic/dummy sustained
high-load 3-agent scenario. It proves the report and decision contract before
real lightweight workload contention or device-specific sustained validation is
added.

## Demo Bundle

Committed lightweight fixtures:

- `examples/agent_runtime/agent_3_orchestration_summary.json`
- `examples/agent_runtime/aiguard_runtime_guard_analysis.json`
- `examples/agent_runtime/remote_dispatch_plan_only.json`
- `examples/agent_runtime/remote_dispatch_fallback_recovered.json`
- `examples/agent_runtime/edgeenv_run_show_runtime_operation.json`

Generate a Markdown report:

```bash
poetry run inferedgelab agent-runtime-report \
  --orchestration-summary examples/agent_runtime/agent_3_orchestration_summary.json \
  --guard-analysis examples/agent_runtime/aiguard_runtime_guard_analysis.json \
  --remote-dispatch /tmp/inferedge_agent_runtime_e2e/06_remote_dispatch_result.json \
  --format markdown \
  --output reports/agent_runtime_reliability_report.md
```

Reproduce the committed remote dispatch starter paths:

```bash
bash scripts/smoke_agent_runtime_remote_paths.sh \
  --output-dir reports/agent_runtime_remote_paths
```

The smoke writes one report for plan-only worker selection and one report for
fallback-recovered starter execution. Both reports preserve
`remote_runtime_summary_boundary=remote dispatch starter evidence only`; they
do not start remote workers or claim production remote execution.

Reproduce the committed EdgeEnv run preservation report path:

```bash
bash scripts/smoke_agent_runtime_edgeenv_preservation.sh \
  --output-dir reports/agent_runtime_edgeenv_preservation
```

The smoke verifies that the Lab-owned Markdown/JSON report keeps the
`Runtime Intelligence EdgeEnv Preservation` section, EdgeEnv run ID, Runtime
operation summary schema, and `comparability_role=supplemental_evidence_not_gate`
visible from a lightweight `runs show` fixture. This is local registry
preservation evidence, not a production telemetry database or deployment
decision override.

Current starter coverage:

- file-based worker registry and task request ingestion
- selected/rejected worker evidence and decision reasons
- plan-only remote execution context for worker-selection review
- bounded fallback recovery context when starter execution is unavailable
- Lab report rows for remote runtime event count, consistency state, fallback
  recovery, and the explicit operation boundary marker

Future hardening, not current completion:

- production SSH/HTTP dispatch execution
- long-lived remote worker lifecycle management
- secure tunnel operation
- production retry/failover orchestration
- cloud control plane or Kubernetes-style scheduling

## Evidence Summary

| Evidence | Value |
|---|---:|
| executed_count | 10 |
| dropped_count | 14 |
| deadline_missed_count | 1 |
| fallback_count | 14 |
| drop_rate | 0.583333 |
| fallback_rate | 0.583333 |
| deadline_miss_rate | 0.1 |
| queue_backlog_policy_decision_count | 1 |
| max_total_queue_depth | 6 |
| top_policy_decision_reason | queue_backlog_threshold_exceeded |

AIGuard `guard_analysis` also includes `sustained_overload_risk`, which Lab
preserves as report evidence and reflects in the agent deployment decision
context.

The report also preserves the Orchestrator operation-health fields added for
runtime operation review:

- `queue_state_summary` for queue pressure, max backlog, final queue depth, and
  overload threshold. Newer Orchestrator summaries also surface
  `queue_pressure_reason`, `max_pressure_task`, policy/drop reason rollups, and
  `device_local_producer_sources` so Lab can explain why queue pressure became
  review evidence.
- `worker_health_snapshot` for healthy/constrained/degraded worker state,
  executed/drop/deadline/fallback counts, health reasons, per-worker
  drop/deadline/fallback rates, primary health reason, operation risk summary,
  producer context, and latency context.
- `runtime_event_summary` for event type counts, policy/drop reason counts,
  queue pressure reason counts, producer source coverage, device-local event
  counts, fallback decision counts, and scheduler-delay event counts.
- `runtime_event_timeline` sample rows for queue snapshots, policy decisions,
  drops, execution outcomes, scheduler delay cycles, and queue wait evidence.
- Optional Runtime result operation evidence through `--runtime-result`,
  including `runtime_health_snapshot`, `runtime_error_classification`,
  `runtime_events`, and `runtime_operation_summary`.
- Runtime operation summary context, including `health_reason`, `risk_labels`,
  `evidence_gaps`, and conservative `recommended_action`. Lab preserves
  `decision_owner: lab` and `scheduler_owner: orchestrator` in the report so
  this remains deployment review evidence, not Runtime-owned deployment policy.
- Optional Orchestrator remote dispatch evidence through `--remote-dispatch`,
  including file-based worker selection, selected worker id, plan-only remote
  execution context, and retry/fallback plan fields.
- Runtime timeout observation context, including `timeout_policy`,
  `timeout_budget_ms`, and `runtime_timeout_observed`. A timeout observation is
  treated as Lab `review_required` evidence because it means the configured
  latency threshold was breached; it does not claim production request
  cancellation.
- Retryable Runtime error context, including `runtime_error_retryable` and
  `runtime_error_retry_hint`. For example, `runtime_execution_skipped` with
  `retry_hint: check_backend_availability` becomes Lab `review_required`
  evidence without turning Runtime or Lab into a production retry loop.
- AIGuard Runtime operation evidence, including
  `runtime_backend_unavailable`, `runtime_latency_budget_overrun`,
  `runtime_error_classification`, and
  `runtime_thermal_memory_evidence_missing` when Runtime health/error/event
  fields are analyzed by AIGuard.
- AIGuard Orchestrator operation evidence, including
  `worker_health_degradation` and `scheduler_delay_pattern` when Orchestrator
  worker health or runtime event telemetry is analyzed by AIGuard.
  Lab preserves health reasons, policy/drop reason counts, and scheduler delay
  counts as deployment context without making AIGuard the final decision owner.

These fields make the report path explicit:

```text
Runtime result operation evidence + Orchestrator operation evidence
-> optional remote worker-selection context
-> AIGuard reliability explanation
-> Lab-owned deployment risk context
```

Remote dispatch remains a starter contract. It records worker-selection and
fallback-plan evidence for review, but it does not claim production SSH/HTTP
execution, secure tunnel operation, or long-lived remote worker readiness.
Its portfolio value is the explicit operation boundary: Orchestrator produces
runtime operation evidence, AIGuard can explain deterministic warning context
when present, and Lab keeps the final deployment decision.

## Lab Decision Context

Expected decision:

```text
blocked
```

Primary reason:

```text
Agent runtime reliability evidence indicates blocked deployment risk.
```

Triggered rules:

- `guard_blocked_runtime_block`
- `drop_rate_block`
- `fallback_rate_block`
- `deadline_miss_review`
- `queue_backlog_review`
- `sustained_overload_review`
- `runtime_timeout_observed_review` when a Runtime result reports a latency
  timeout observation threshold breach.
- `runtime_operation_guard_block` when AIGuard reports failed high-severity
  Runtime operation evidence such as backend unavailable or latency budget
  overrun.
- `runtime_operation_guard_review` when AIGuard reports warning-level Runtime
  operation evidence such as missing Jetson thermal/memory context.

The report also surfaces Orchestrator operation guard evidence as context. For
example, `worker_health_degradation` shows degraded/constrained worker reasons
such as fallback policy use or dropped frames, while `scheduler_delay_pattern`
shows scheduler delay counts and related policy/drop reasons. These evidence
items contribute through AIGuard's overall guard verdict and remain separate
from Lab's final policy ownership.

## Boundary

- Orchestrator records scheduling and policy evidence.
- Orchestrator operation-health fields are displayed as local runtime evidence.
- Orchestrator remote dispatch result fields are displayed as worker-selection,
  retry/fallback, and remote execution starter evidence when provided.
- If explicit HTTP/SSH starter execution was requested by Orchestrator, Lab
  preserves the `remote_execution_result` status, transport, and error category
  as local deployment review context.
- AIGuard explains runtime reliability risk, including additive Runtime
  health/error/event warning evidence and Orchestrator worker/event telemetry
  warning evidence when provided.
- Lab remains the final deployment decision owner.
- This report is an additive agent-runtime path and does not change existing
  Runtime result, compare output, or classic deployment decision contracts.
