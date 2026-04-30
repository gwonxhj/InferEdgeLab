# InferEdge Pipeline Status

## Purpose

This document summarizes the current portfolio status of the InferEdge multi-repository project.

InferEdge is an end-to-end edge AI inference validation pipeline. It is designed to turn an ONNX model into deployment evidence by connecting artifact build provenance, runtime profiling, Lab comparison/reporting, optional rule-based diagnosis, and a final deployment decision.

For a compressed recruiter/interviewer entry point, see [InferEdge 1-Page Architecture Summary](inferedge_1page_architecture.md).

Interview summary:

> InferEdge is an end-to-end inference validation pipeline that converts, runs, compares, diagnoses, and decides whether an edge AI model candidate is ready to deploy.

## Product-Level Pipeline

```text
ONNX model
-> InferEdgeForge build
-> metadata / manifest / worker runtime summary
-> InferEdgeRuntime validation / result export
-> InferEdgeLab compare / API / job workflow / deployment_decision
-> optional InferEdgeAIGuard provenance diagnosis
-> deploy / review / blocked decision
```

The goal is not only to measure latency. The goal is to create reproducible evidence that can support deployment review.

## Repository Roles

### InferEdgeForge

Forge owns build artifact and provenance generation.

Current role:

- converts ONNX models into edge deployment artifacts such as TensorRT engine or RKNN artifact
- emits `metadata.json`, `manifest.json`, and build summaries
- preserves source model hash, artifact hash, backend, target, precision, shape, preset, and build id
- provides a worker/runtime summary that can feed Lab worker requests and Runtime invocation boundaries

### InferEdgeRuntime

Runtime owns execution, profiling, and result export.

Current role:

- provides the C++ runtime execution boundary
- validates Lab worker request payloads in dry-run mode
- exports Lab-compatible result JSON and dry-run worker completed/failed responses
- has manual smoke evidence for both macOS ONNX Runtime CPU execution and Jetson TensorRT engine execution
- keeps the Runtime-to-Lab worker response shape executable without introducing queue or daemon infrastructure

### InferEdgeLab

Lab owns comparison, reporting, API/job workflow contracts, and the final deployment decision.

Current role:

- consumes Runtime result JSON
- runs compare, compare-latest, report, and deployment decision flows
- exposes `/api/compare` with the SaaS API response contract
- exposes in-memory `/api/analyze` and `/api/jobs/{job_id}` workflow stubs
- exposes a local-first `/studio` workflow UI for Run, Import, Compare View, Jetson command helper, demo evidence replay, and deployment decision inspection
- maps analyze jobs to worker requests and worker responses back to job results
- preserves optional AIGuard evidence while keeping Lab as the final decision owner

### InferEdgeAIGuard

AIGuard owns deterministic failure and provenance diagnosis.

Current role:

- stays optional for Lab
- uses rule + evidence based detectors instead of abstract LLM guessing
- diagnoses artifact/source hash mismatch, precision/shape/backend/target mismatch, and missing provenance
- emits `guard_analysis` that Lab can preserve in report/API bundles and reflect in deployment decisions

## Implemented Connections

The current cross-repository loop is covered by documentation, fixtures, and smoke tests:

- Lab API response contract
- `/api/compare` contract response
- `/api/analyze` in-memory job stub
- Lab analyze job to `worker_request` mapping
- Lab `worker_response` to job result mapping
- Lab -> Runtime dev-only minimal execution path through `/api/jobs/{job_id}/run-runtime-dev`
- Runtime Lab `worker_request` dry-run validation
- Runtime worker completed/failed response dry-run export
- Runtime manual Jetson TensorRT smoke with Forge manifest + TensorRT engine artifact
- Runtime source-model identity preservation for manifest-backed TensorRT engine compare keys
- Forge worker/runtime summary contract
- Forge summary to Lab worker request compatibility
- Forge summary-origin Lab worker request validation in Runtime
- AIGuard worker provenance mismatch diagnosis
- Lab deployment decision/report evidence smoke for AIGuard worker provenance diagnosis
- Local Studio local-first workflow UI for viewing Forge -> Runtime -> Lab -> optional AIGuard state, creating in-memory analyze jobs, importing Runtime result JSON, replaying bundled demo evidence, comparing backends, and inspecting Lab-owned deployment decision context

This means the current product boundary is testable without running the production worker infrastructure.

InferEdge now has two runtime execution evidence paths:

1. macOS ONNX Runtime CPU smoke through Lab's dev-only Runtime execution path using `yolov8n.onnx`. The smoke created Lab job `job_9e2321179256`, called the C++ Runtime CLI through Lab's subprocess path, executed ONNX Runtime on CPU with FP32, and ingested the resulting JSON back into the Lab job result. Runtime reported input shape `[1, 3, 640, 640]`, output shape `[1, 84, 8400]`, `warmup=1`, `runs=5`, benchmark status success, mean latency about 47.97 ms, p50 about 46.95 ms, p95/p99 about 51.80 ms, and about 20.85 FPS. The resulting `deployment_decision` was `unknown`, which is expected for direct Runtime execution before Lab compare/report.
2. Jetson Orin Nano TensorRT smoke using a Forge-generated manifest and TensorRT engine artifact executed by the C++ Runtime CLI. The manual Jetson smoke ran on Linux `5.15.148-tegra` / `aarch64` from `~/InferEdge-Runtime`, using Forge manifest `/home/risenano01/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16/manifest.json` and artifact `/home/risenano01/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16/model.engine`. The result JSON was `results/jetson/yolov8n_jetson_tensorrt_manifest_smoke.json` and reported `success: true`, `status: success`, `engine_backend: tensorrt`, `device_name: jetson`, `manifest_applied: true`, input shape `[1, 3, 640, 640]`, output shape `[1, 84, 8400]`, mean latency about 14.00 ms, p99 about 15.50 ms, and about 71.44 FPS.

Compare-key polish status: this limitation has been resolved in InferEdgeRuntime #37. When a Forge manifest is applied, Runtime now prefers `manifest.source_model.path` for compare naming, so a TensorRT artifact path such as `model.engine` can still produce `compare_model_name=yolov8n` and `compare_key=yolov8n__b1__h640w640__fp32`. This improves provenance and compare-readiness; it does not add production SaaS worker infrastructure.

Demo readiness: `scripts/demo_pipeline_full.sh` now provides a guided end-to-end portfolio entrypoint for Forge -> Runtime -> Lab -> optional AIGuard. The default mode prints a safe summary, `--run-jetson-command-print` prints the Jetson TensorRT command, and `--run-jetson-local` is reserved for running on the Jetson device. This is demo guidance for a SaaS-ready validation foundation, not production worker orchestration.

## Implemented vs Planned

### Implemented Now

- Structured benchmark/result comparison in Lab
- Markdown/HTML report generation
- Lab-owned `deployment_decision`
- Optional `guard_analysis` preservation
- SaaS API response contract
- `/api/compare` response wrapper
- In-memory async job contract and API stub
- Worker request and worker response boundary contracts
- Dev-only Lab -> Runtime execution smoke for a real `yolov8n.onnx` model
- Manual Jetson TensorRT Runtime smoke using Forge manifest and TensorRT engine artifact
- Runtime compare-key identity polish for manifest-backed engine artifacts
- Guided end-to-end demo entrypoint for portfolio and interview walkthroughs
- Local Studio at `/studio` for a local-first browser view of Run / Import / Demo Evidence / Compare / Decision / Jetson Helper workflows
- Cross-repo fixture compatibility across Forge, Runtime, Lab, and AIGuard
- Rule/evidence based provenance mismatch diagnosis

### Planned Later

- real worker daemon
- real Forge build execution from Lab jobs
- full automated Runtime inference execution from production Lab workers
- database persistence
- Redis, Celery, or another queue
- file upload handling
- production frontend beyond the local Studio workflow UI
- production authentication, billing, and deployment controls

These gaps are intentional. The current project fixes the contracts first, then leaves infrastructure choices for later.

## Portfolio Strengths

From a hiring perspective, InferEdge demonstrates:

- edge inference validation beyond raw latency measurement
- artifact provenance based reproducibility
- clean repository responsibility boundaries
- SaaS-ready worker boundary contracts before infrastructure is introduced
- rule + evidence based diagnosis instead of vague AI interpretation
- CLI, report, API, async job, and deployment decision surfaces connected as one product flow

## How To Explain It In An Interview

Short version:

> InferEdge validates edge AI model candidates end to end: Forge creates reproducible artifacts, Runtime measures execution, Lab compares and decides, and AIGuard optionally diagnoses provenance and failure evidence.

More concrete version:

> I built InferEdge as a multi-repository validation pipeline. It starts from an ONNX model, preserves build provenance through Forge, exports profiling evidence from Runtime, compares and reports in Lab, optionally diagnoses mismatch evidence through AIGuard, and produces a Lab-owned deploy/review/blocked decision.

## Related Documents

- [InferEdge 1-page architecture summary](inferedge_1page_architecture.md)
- [Pipeline contract](../pipeline_contract.md)
- [SaaS async job workflow](../api/saas_job_workflow.md)
- [Forge/Runtime worker integration contract](../api/worker_integration_contract.md)
- [Pipeline portfolio summary](inferedge_pipeline_portfolio.md)
- [YOLOv8n Runtime backend comparison](runtime_compare_yolov8n.md)
