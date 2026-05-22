# EdgeEnv Runtime Regression Lab Handoff

## Scope

This smoke fixes the handoff between InferEdgeEnv and InferEdgeLab:

```text
EdgeEnv runtime regression report
-> Lab compare --edgeenv-regression
-> Runtime Regression Evidence section
-> Runtime Telemetry Context subsection when EdgeEnv provides telemetry history context
-> Lab-owned deployment decision
```

EdgeEnv remains the local-first evidence registry, comparability checker, and runtime regression evidence source. Lab remains the validation/report/deployment decision owner.

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

## Reproduction Command

```bash
poetry run inferedgelab compare \
  examples/edgeenv_regression/lab_baseline_result.json \
  examples/edgeenv_regression/lab_candidate_result.json \
  --edgeenv-regression examples/edgeenv_regression/edgeenv_runtime_regression.json \
  --markdown-out reports/edgeenv_regression_lab_handoff.md
```

Expected Lab behavior:

- CLI prints `Runtime Regression Evidence`.
- CLI prints `Runtime Telemetry Context` when the EdgeEnv regression report includes it.
- Markdown/HTML reports include a `Runtime Regression Evidence` section.
- Markdown/HTML reports include a `Runtime Telemetry Context` subsection with baseline/candidate telemetry coverage.
- Deployment decision is `review_required`.
- Triggered rules include `edgeenv_runtime_regression_review`.

## Boundary

This is not cloud monitoring, distributed tracing, production observability, a public leaderboard, or Kubernetes-style orchestration.

The purpose is narrower: Lab can consume EdgeEnv's comparability-first runtime regression evidence and supplemental runtime telemetry context as optional deployment review context without changing Runtime result or compare contracts.
