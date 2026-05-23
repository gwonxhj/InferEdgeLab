# Runtime Intelligence GitLab Artifact Template

## Scope

`ci/gitlab/runtime-intelligence-artifacts.yml` is an optional GitLab CI template for Runtime Intelligence artifact automation.

It is not installed as the repository root `.gitlab-ci.yml` and it does not replace the existing GitHub benchmark workflow. The template exists so a GitLab mirror or downstream workspace can reproduce the same local-first evidence chain without making GitLab a core InferEdge product surface.

## Evidence Chain

The template follows the current Runtime Intelligence handoff:

```text
test
-> benchmark smoke
-> EdgeEnv runtime regression fixture report
-> deterministic anomaly summary smoke with precomputed AIGuard evidence
-> portfolio evidence report
-> deployment risk gate
```

This maps to the ecosystem ownership model:

- Runtime evidence stays additive and Lab-compatible.
- EdgeEnv remains the comparability-first regression evidence source.
- AIGuard remains an optional deterministic diagnosis provider.
- Lab owns the report and deployment decision surface.
- CI stores artifacts and applies deterministic gates; it does not become a production runtime control plane.

## Template Stages

The template keeps the roadmap stage names explicit:

1. `test`
2. `benchmark`
3. `telemetry`
4. `anomaly-analysis`
5. `report`
6. `deployment-risk`

## Artifact Contract

Expected artifacts are intentionally file-based and local-first:

- benchmark result JSON under `reports/*.json`
- `BENCHMARKS.md`
- EdgeEnv regression Markdown / HTML report under `reports/runtime_intelligence_ci/`
- deterministic Runtime Intelligence summary Markdown / HTML with precomputed AIGuard runtime operation evidence
- Runtime Intelligence artifact gate summary
- portfolio demo check JSON / Markdown
- deployment risk summary JSON

The template uses committed lightweight fixtures under `examples/edgeenv_regression/` and `examples/runtime_intelligence_chain/` for the Runtime Intelligence smoke. It does not require real device access, long-lived workers, remote execution, or cloud telemetry storage.

## Gate Policy

The initial gate is conservative:

- full pytest must pass
- benchmark smoke must complete
- Runtime Intelligence report must contain the required risk summary rows
- precomputed AIGuard evidence must remain report context, not the final decision owner
- Orchestrator context must remain supplemental evidence, not a comparability gate
- portfolio demo check status must be `pass`

The artifact gate is implemented by `scripts/check_runtime_intelligence_artifact_bundle.py`. It checks the generated Markdown / HTML report for the required Runtime Intelligence rows, including Lab ownership, EdgeEnv comparability, Orchestrator operation feed context, AIGuard runtime operation anomalies, and triggered deployment review rules.

Future GitLab-specific gates may include latency regression thresholds, anomaly severity thresholds, thermal instability thresholds, and deployment risk thresholds, but only after the corresponding deterministic evidence is already represented in the artifact bundle.

## Boundary

This template is not:

- a production observability platform
- a cloud monitoring service
- a Kubernetes replacement
- a production runtime control plane
- a new InferEdge Intelligence repo
- an ML or forecasting pipeline

It is a reproducible artifact automation starter for the existing InferEdge Runtime Intelligence evidence chain.
