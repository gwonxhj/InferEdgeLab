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

## Boundary

- Orchestrator records scheduling and policy evidence.
- AIGuard explains runtime reliability risk.
- Lab remains the final deployment decision owner.
- This report is an additive agent-runtime path and does not change existing
  Runtime result, compare output, or classic deployment decision contracts.
