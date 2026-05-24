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
- Runtime Intelligence bundle manifest under `examples/runtime_intelligence_chain/bundle_manifest.json`
- Runtime Intelligence bundle manifest gate summary
- EdgeEnv regression Markdown / HTML report under `reports/runtime_intelligence_ci/`
- deterministic Runtime Intelligence summary Markdown / HTML with precomputed AIGuard runtime operation evidence
- Runtime Intelligence artifact gate summary
- portfolio demo check JSON / Markdown
- deployment risk summary JSON
- Runtime Intelligence CI artifact gate summary

The template uses committed lightweight fixtures under `examples/edgeenv_regression/` and `examples/runtime_intelligence_chain/` for the Runtime Intelligence smoke. It does not require real device access, long-lived workers, remote execution, or cloud telemetry storage.

## Gate Policy

The initial gate is conservative:

- full pytest must pass
- benchmark smoke must complete
- Runtime Intelligence bundle manifest must preserve file paths and ownership boundaries
- Runtime Intelligence report must contain the required risk summary rows
- Runtime Intelligence report must preserve telemetry coverage gap markers such as
  `runtime_telemetry_field_gap` from the AIGuard evidence artifact
- AIGuard coverage evidence must preserve
  `telemetry_coverage_source=history_telemetry_coverage` and EdgeEnv history
  missing-field runs, so the artifact chain proves producer-side coverage
  summary reuse instead of downstream recomputation
- the preserved Orchestrator `edgeenv_mapping_hint` must keep
  `coverage_summary_owner=edgeenv`,
  `coverage_summary_path=runtime_telemetry_context.history.telemetry_coverage`,
  `operation_context_role=supplemental`, and the AIGuard evidence candidate
  hints for `runtime_queue_overload` and `runtime_thermal_instability`
- AIGuard coverage evidence raw context must preserve the same mapping hint, so
  CI catches loss of EdgeEnv/Orchestrator ownership markers before Lab report
  generation
- Orchestrator candidate context must include `run_id`, `telemetry_source`,
  `operation`, and `resource`, so CI can catch incomplete handoffs without
  making Orchestrator a regression owner
- precomputed AIGuard evidence must remain report context, not the final decision owner
- Orchestrator context must remain supplemental evidence, not a comparability gate
- bundle source repository mapping must keep Runtime, EdgeEnv, Orchestrator,
  AIGuard, and Lab roles separated
- producer schema markers for EdgeEnv history, Orchestrator feed, and AIGuard
  diagnosis evidence must stay aligned with the committed smoke artifacts
- portfolio demo check status must be `pass`
- the final deployment-risk job must re-check the collected manifest/report
  gate summaries and Runtime Intelligence Risk Summary markers before passing
- the bundle manifest gate summary must include validated contract markers for
  source repository separation, producer schemas, Lab/EdgeEnv ownership, the
  Orchestrator supplemental mapping hint, AIGuard evidence candidates, and
  AIGuard raw-context preservation

The bundle manifest gate is implemented by `scripts/check_runtime_intelligence_bundle_manifest.py`. It verifies that the bundle contains baseline/candidate Runtime results, EdgeEnv regression evidence, AIGuard guard evidence, and explicit owner/boundary metadata before Lab generates the report.
The same gate now also checks `source_repositories`, `artifact_roles`, and `producer_contracts` so the smoke remains a cross-repo handoff fixture rather than a Lab-only report sample.

The artifact gate is implemented by `scripts/check_runtime_intelligence_artifact_bundle.py`. It checks the generated Markdown / HTML report for the required Runtime Intelligence rows, including Lab ownership, EdgeEnv comparability, telemetry coverage-gap markers, Orchestrator operation feed context, AIGuard runtime operation anomalies, and triggered deployment review rules.

The CI artifact gate is implemented by `scripts/check_runtime_intelligence_ci_artifacts.py`. It runs in the deployment-risk stage and verifies that the collected optional GitLab artifacts include the manifest gate summary, report gate summary, Runtime Intelligence Risk Summary report, portfolio demo status, and the validated contract markers from the bundle manifest gate. This keeps the final CI gate file-based and deterministic without turning GitLab into a runtime control plane.

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
