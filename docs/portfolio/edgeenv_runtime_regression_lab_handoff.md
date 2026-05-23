# EdgeEnv Runtime Regression Lab Handoff

## Scope

This smoke fixes the handoff between InferEdgeEnv and InferEdgeLab:

```text
EdgeEnv runtime regression report
-> Lab compare --edgeenv-regression
-> Runtime Regression Evidence section
-> Runtime Telemetry Context subsection when EdgeEnv provides telemetry history context
-> optional AIGuard deterministic runtime regression diagnosis when --with-guard is enabled
-> Lab-owned deployment decision
```

EdgeEnv remains the local-first evidence registry, comparability checker, and runtime regression evidence source. Lab remains the validation/report/deployment decision owner.
AIGuard remains optional deterministic diagnosis evidence: it may explain runtime regression evidence, but it does not recompute EdgeEnv comparability and does not own the final deployment decision.

## Runtime Intelligence Evidence Chain

The current Runtime Intelligence handoff keeps the same ownership model while adding operation context from Orchestrator through EdgeEnv:

```text
Orchestrator edgeenv_runtime_telemetry_feed
-> EdgeEnv runtime telemetry history / regression context
-> AIGuard deterministic runtime anomaly evidence
-> Lab Runtime Intelligence Risk Summary
-> Lab-owned deployment risk report
```

Expected ownership:

- Orchestrator provides supplemental queue, deadline, fallback, thermal, and resource context. It does not make a deployment decision.
- EdgeEnv preserves that context as `orchestrator_operation_context` inside the runtime telemetry context and keeps comparability-first regression ownership.
- AIGuard may translate the nested operation context into deterministic evidence such as `runtime_queue_overload` or `runtime_thermal_instability`.
- Lab displays the combined evidence in the Runtime Intelligence Risk Summary and keeps the final deployment decision policy.

This makes the portfolio chain stronger without turning Lab into a production observability dashboard or making Orchestrator/AIGuard final decision owners.

## Fixture

Committed lightweight fixtures:

- `examples/edgeenv_regression/lab_baseline_result.json`
- `examples/edgeenv_regression/lab_candidate_result.json`
- `examples/edgeenv_regression/edgeenv_runtime_regression.json`

The EdgeEnv report fixture represents a same-condition runtime regression:

- `comparable: true`
- `mode: same-condition`
- `regression_detected: true`
- `regression_type: mixed`
- `severity: high`
- `mean_delta_pct: +18.0`
- `p99_delta_pct: +32.0`
- `fps_delta_pct: -22.0`
- `memory_peak_delta_pct: +40.0`
- `runtime_telemetry_context`: supplemental telemetry coverage and evidence-gap context from EdgeEnv history export
- `runtime_telemetry_context.<run>.orchestrator_operation_context`: supplemental operation context when EdgeEnv history was exported with an Orchestrator feed

## Reproduction Command

```bash
poetry run inferedgelab compare \
  examples/edgeenv_regression/lab_baseline_result.json \
  examples/edgeenv_regression/lab_candidate_result.json \
  --edgeenv-regression examples/edgeenv_regression/edgeenv_runtime_regression.json \
  --markdown-out reports/edgeenv_regression_lab_handoff.md
```

Runtime Intelligence cross-repo evidence-chain smoke:

```bash
poetry run inferedgelab compare \
  examples/edgeenv_regression/lab_baseline_result.json \
  examples/edgeenv_regression/lab_candidate_result.json \
  --edgeenv-regression examples/runtime_intelligence_chain/edgeenv_regression_with_orchestrator_context.json \
  --guard-analysis examples/runtime_intelligence_chain/aiguard_runtime_operation_guard_analysis.json \
  --markdown-out reports/runtime_intelligence_chain.md \
  --html-out reports/runtime_intelligence_chain.html
```

This second smoke uses committed lightweight artifacts to represent the cross-repo handoff:

- `examples/runtime_intelligence_chain/bundle_manifest.json` declares the local-first artifact bundle, file paths, source repositories, artifact roles, producer contracts, owners, and boundary flags.
- Orchestrator context is preserved inside the EdgeEnv regression artifact as `orchestrator_operation_context`.
- AIGuard deterministic queue/thermal evidence is passed as a precomputed `guard_analysis` artifact that mirrors the AIGuard producer-side diagnosis v1 evidence shape.
- Lab owns the combined report and deployment decision.
- `scripts/check_runtime_intelligence_bundle_manifest.py` gates the bundle manifest before report generation, including source repository mapping, schema markers, and evidence-item shape for the EdgeEnv history, Orchestrator feed, and AIGuard diagnosis artifacts.
- `scripts/check_runtime_intelligence_artifact_bundle.py` gates the generated report so required Runtime Intelligence rows and ownership text cannot disappear silently.

Expected Lab behavior:

- CLI prints `Runtime Regression Evidence`.
- CLI prints `Runtime Telemetry Context` when the EdgeEnv regression report includes it.
- Markdown/HTML reports include a `Runtime Regression Evidence` section.
- Markdown/HTML reports include a `Runtime Telemetry Context` subsection with baseline/candidate telemetry coverage and history execution sequence context.
- When `--with-guard` is enabled and the installed AIGuard exposes EdgeEnv regression reasoning, Lab routes the EdgeEnv report to AIGuard and preserves diagnosis evidence such as `runtime_latency_regression`, `runtime_telemetry_context_coverage`, and `runtime_telemetry_replay_context`.
- Additional Lab test fixtures under `tests/fixtures/edgeenv_regression/` mirror EdgeEnv replay examples for candidate telemetry gaps and execution sequence inversion. These fixture smokes verify that replay warnings become Lab-owned report context without making Lab recompute EdgeEnv comparability.
- Markdown/HTML reports include a `Runtime Intelligence Risk Summary` that summarizes EdgeEnv comparability/regression, telemetry replay gaps, AIGuard deterministic evidence, and the Lab-owned deployment decision in one reviewer-facing table.
- When EdgeEnv includes preserved Orchestrator feed context, the `Runtime Intelligence Risk Summary` surfaces queue, thermal, throttling, memory, and fallback context as supplemental runtime evidence.
- When `--guard-analysis` is provided, Lab ingests the precomputed AIGuard artifact as evidence without requiring AIGuard to be installed in the Lab environment.
- Guard evidence details preserve explanatory fields such as `why_it_matters`, evidence-local `suspected_causes`, and `recommendation`.
- Deployment decision is `review_required`.
- Triggered rules include `edgeenv_runtime_regression_review`.
- Deployment decision reports include policy-summary descriptions for the triggered Lab rules.

## Boundary

This is not cloud monitoring, distributed tracing, production observability, a public leaderboard, or Kubernetes-style orchestration.

The purpose is narrower: Lab can consume EdgeEnv's comparability-first runtime regression evidence, supplemental runtime telemetry context, and optional AIGuard deterministic diagnosis evidence as deployment review context without changing Runtime result or compare contracts.
