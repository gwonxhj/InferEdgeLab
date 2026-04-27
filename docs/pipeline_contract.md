# InferEdge Pipeline Contract

## Purpose

This document defines the contract that connects InferEdgeForge, InferEdgeRuntime, InferEdgeLab, and InferEdgeAIGuard into one end-to-end Edge AI inference validation pipeline.

InferEdgeLab is the final analysis, report, and deployment decision owner. Forge, Runtime, and AIGuard provide build, execution, profiling, and diagnosis evidence that Lab can consume without taking ownership of their implementation details.

## End-to-End Flow

```text
ONNX model
-> InferEdgeForge build
-> artifact + metadata.json + manifest.json 생성
-> InferEdgeRuntime execution/profiling
-> Lab-compatible result JSON 생성
-> InferEdgeLab compare/report/deployment_decision
-> optional InferEdgeAIGuard guard_analysis
-> final deployment decision
```

The intended product-level flow is:

1. A user starts with an ONNX model.
2. Forge builds a deployment artifact and records reproducible provenance.
3. Runtime executes the artifact or model and exports profiling evidence.
4. Lab compares results, generates reports, and produces a deployment decision.
5. AIGuard may optionally add rule-based failure diagnosis as `guard_analysis`.
6. Lab owns the final deployment decision.

## Repository Responsibilities

### InferEdgeForge

InferEdgeForge turns ONNX models into edge deployment artifacts such as TensorRT engines or RKNN artifacts.

Forge is responsible for:

- converting ONNX models into TensorRT engine, RKNN artifact, or other edge deployment artifacts
- generating `metadata.json`, `manifest.json`, and `run_summary.json`
- preserving source model hash, artifact hash, preset snapshot, target, backend, precision, and shape information
- allowing Runtime and Lab to read reproducible artifact provenance

Forge does not decide whether a candidate should be deployed. It creates the artifact and the provenance needed for later validation.

### InferEdgeRuntime

InferEdgeRuntime executes Forge artifacts on an edge device or host runtime and exports profiling evidence.

Runtime is responsible for:

- accepting Forge artifacts or compatible model inputs
- supporting the ONNX Runtime C++ MVP first
- expanding later to TensorRT C++ engine load, warmup, runs, and result export
- measuring mean, p50, p95, and p99 latency
- exporting runtime provenance as Lab-compatible result JSON

Runtime does not own comparison policy or deployment judgement. It produces trustworthy execution and measurement evidence.

### InferEdgeLab

InferEdgeLab analyzes Runtime result JSON and turns validation evidence into reusable reports and deployment decisions.

Lab is responsible for:

- analyzing Runtime result JSON
- running `compare`, `compare-latest`, and `history-report`
- generating Markdown, HTML, and API-oriented bundles
- creating `deployment_decision`
- consuming optional AIGuard `guard_analysis` when available
- continuing to work when AIGuard is not installed or not executed
- owning the final deployment decision

Lab is the policy and interpretation layer. It compares evidence, explains trade-offs, and decides whether the candidate is deployable, needs review, is blocked, or remains unknown.

### InferEdgeAIGuard

InferEdgeAIGuard performs rule + evidence based failure diagnosis over Lab, Runtime, and Forge evidence.

AIGuard is responsible for:

- analyzing Lab results, Runtime profiling results, and Forge metadata or manifest evidence
- keeping a detector-based structure instead of an abstract "AI decides everything" design
- diagnosing signals such as INT8 collapse, bbox collapse, confidence saturation, p99 spike, shape mismatch, and artifact mismatch
- providing optional `guard_analysis`

AIGuard does not replace Lab judgement. It adds reviewer-facing diagnosis evidence that Lab may reflect in the final deployment decision.

## Contract Artifacts

| Artifact | Owner repo | Consumer repo | Required purpose |
|---|---|---|---|
| Forge `metadata.json` | InferEdgeForge | InferEdgeRuntime, InferEdgeLab, InferEdgeAIGuard | Records build identity, source model hash, artifact hash, preset snapshot, target, backend, precision, and handoff context. |
| Forge `manifest.json` | InferEdgeForge | InferEdgeForge, InferEdgeRuntime, InferEdgeLab, InferEdgeAIGuard | Preserves reproducible build recipe and artifact provenance for rebuild, execution, and review. |
| Forge `run_summary.json` | InferEdgeForge | InferEdgeLab, InferEdgeAIGuard | Records downstream benchmark handoff or execution summary tied back to a build. |
| Runtime result JSON | InferEdgeRuntime | InferEdgeLab, InferEdgeAIGuard | Provides Lab-compatible profiling output with latency metrics, runtime provenance, and grouping keys. |
| Lab compare bundle | InferEdgeLab | InferEdgeLab API, reports, AIGuard, reviewers | Captures comparison metrics, judgement, report-ready evidence, and optional guard context. |
| Lab compare-latest bundle | InferEdgeLab | InferEdgeLab API, reports, AIGuard, reviewers | Captures latest-result comparison evidence using the same deployment decision surface as compare. |
| Lab `deployment_decision` | InferEdgeLab | API, reports, CI, deployment reviewers | Produces final Lab-owned deploy/review/block/unknown release signal. |
| AIGuard `guard_analysis` | InferEdgeAIGuard | InferEdgeLab | Provides optional rule + evidence based diagnosis with status, anomalies, suspected causes, recommendations, and confidence. |

## Deployment Decision Contract

InferEdgeLab 4.2 defines a Lab-owned deployment decision layer. The current decision values are:

- `deployable`: Lab judgement is favorable and required validation evidence is acceptable.
- `deployable_with_note`: deployment can proceed, but the release evidence should retain a note such as neutral judgement or reduced confidence.
- `review_required`: the candidate needs human review before deployment because Lab or Guard evidence indicates risk.
- `blocked`: deployment should not proceed because Guard or validation evidence reports an error-level issue.
- `unknown`: Lab cannot produce a confident deploy/review/block decision, often because optional evidence is unavailable or skipped.

Optional AIGuard `guard_analysis.status` can influence the Lab deployment decision:

- `ok`: if Lab judgement allows it, the result can become `deployable` or `deployable_with_note`.
- `warning`: the result can be raised to `review_required`.
- `error`: the result can be raised to `blocked`.
- `skipped`: AIGuard is not installed or not executed; the result can remain `unknown` or use a Lab-only decision depending on available evidence.

The final deployment decision is always owned by InferEdgeLab. AIGuard supplies optional diagnosis evidence; it does not overwrite Lab policy.

## SaaS Boundary

This contract matters for the SaaS expansion path because the UI and API should return stable evidence bundles even when the pipeline is split across workers or services.

The contract supports SaaS boundaries by ensuring:

- the API can return compare, report, and deployment decision bundles with stable fields
- Forge, Runtime, and AIGuard can later run as separate services or workers while preserving the same artifact handoff
- users can submit a model, artifact, or result and receive a deploy, review, or blocked decision without understanding every backend detail
- Lab remains the service boundary for final interpretation while other repos provide specialized evidence

## Non-Goals

This document does not:

- make Lab own Forge build implementation details
- make Lab own Runtime inference backend implementation details
- make AIGuard a required dependency
- change Lab `deployment_decision` logic
- change existing compare, compare-latest, history-report, profile, API, or accuracy behavior

## Next Alignment Steps

Recommended next work:

- add InferEdgeRuntime Lab-compatible result JSON fixture and tests
- align Forge metadata/manifest documentation with the Runtime input contract
- add AIGuard provenance-based artifact mismatch detector
- strengthen the Lab SaaS API response contract for compare/report/deployment decision bundles
