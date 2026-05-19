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

Generate a Markdown report:

```bash
poetry run inferedgelab agent-runtime-report \
  --orchestration-summary examples/agent_runtime/agent_3_orchestration_summary.json \
  --guard-analysis examples/agent_runtime/aiguard_runtime_guard_analysis.json \
  --format markdown \
  --output reports/agent_runtime_reliability_report.md
```

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
  overload threshold.
- `worker_health_snapshot` for healthy/constrained/degraded worker state,
  executed/drop/deadline/fallback counts, and latency context.
- `runtime_event_summary` for event type counts.
- `runtime_event_timeline` sample rows for queue snapshots, policy decisions,
  drops, and execution outcomes.
- Optional Runtime result operation evidence through `--runtime-result`,
  including `runtime_health_snapshot`, `runtime_error_classification`, and
  `runtime_events`.
- Runtime timeout observation context, including `timeout_policy`,
  `timeout_budget_ms`, and `runtime_timeout_observed`. A timeout observation is
  treated as Lab `review_required` evidence because it means the configured
  latency threshold was breached; it does not claim production request
  cancellation.

These fields make the report path explicit:

```text
Runtime result operation evidence + Orchestrator operation evidence
-> AIGuard reliability explanation
-> Lab-owned deployment risk context
```

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

## Boundary

- Orchestrator records scheduling and policy evidence.
- Orchestrator operation-health fields are displayed as local runtime evidence.
- AIGuard explains runtime reliability risk.
- Lab remains the final deployment decision owner.
- This report is an additive agent-runtime path and does not change existing
  Runtime result, compare output, or classic deployment decision contracts.
