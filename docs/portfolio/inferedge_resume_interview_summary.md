# InferEdge Resume and Interview Summary

## Final Resume Bullets

- Built InferEdge, an end-to-end Edge AI inference validation pipeline that connects Forge build provenance, C++ Runtime execution, Lab comparison/report/API/job workflows, optional AIGuard diagnosis evidence, and Lab-owned deployment decisions.
- Validated real execution paths on both macOS and edge hardware: `yolov8n.onnx` through Lab -> C++ Runtime -> ONNX Runtime CPU -> Lab job result ingestion, and Jetson Orin Nano TensorRT execution through Forge manifest + `model.engine` + C++ Runtime CLI.
- Documented Jetson TensorRT smoke evidence with mean latency about 14.00 ms, p99 about 15.50 ms, and about 71.44 FPS on a Forge-generated TensorRT engine artifact.
- Added Local Studio as a local-first browser workflow UI that can replay bundled ONNX Runtime CPU and TensorRT Jetson demo evidence, showing 45.4299 ms vs 9.9375 ms mean latency and a 4.57x TensorRT speedup without claiming production SaaS readiness.
- Polished Runtime provenance readiness so manifest-backed TensorRT artifacts preserve source identity: `model.engine` can keep `compare_model_name=yolov8n` and `compare_key=yolov8n__b1__h640w640__fp32`.

## Role-Specific Resume Versions

### AI Inference Engineer

Built an end-to-end Edge AI inference validation pipeline across Forge, Runtime, Lab, and AIGuard. The system validates not only latency, but also artifact provenance, runtime result compatibility, comparison readiness, and deployment decision evidence. I verified `yolov8n.onnx` through ONNX Runtime CPU on macOS and a Forge-generated TensorRT `model.engine` on Jetson Orin Nano, with Jetson smoke evidence around 14.00 ms mean latency, 15.50 ms p99, and 71.44 FPS. Runtime now preserves Forge manifest source identity for compare keys, reducing ambiguity when TensorRT artifacts are executed as engine files.

### Embedded / Edge Engineer

Built a multi-repository edge inference validation workflow that connects model build artifacts to real device execution evidence. InferEdgeRuntime provides a C++ execution/result export boundary, and I validated a Jetson Orin Nano TensorRT smoke using a Forge manifest plus generated `model.engine` artifact. The run completed successfully through the C++ Runtime CLI with TensorRT backend, Jetson device target, manifest applied, mean latency about 14.00 ms, p99 about 15.50 ms, and about 71.44 FPS. This is manual/dev smoke evidence, while production worker orchestration remains future work.

### Backend / AI Platform

Built the Lab-side orchestration and contract foundation for an edge AI validation platform. InferEdgeLab exposes compare/API/job/deployment-decision boundaries, maps analyze jobs to worker requests, ingests worker responses, preserves optional AIGuard evidence, and provides a local-first Studio UI for browser-based workflow inspection. Current scope is SaaS/API/job contract foundation plus dev-only Runtime execution smoke and local Studio demo evidence; production worker daemon, persistent queue/database, file upload, production frontend, auth, and billing remain future work.

## Interview: First 30 Seconds

InferEdge는 단순 benchmark tool이 아니라 edge AI 모델의 build provenance, 실제 Runtime execution, 비교/report, optional diagnosis evidence, deployment decision을 연결하는 end-to-end validation pipeline입니다. 저는 macOS에서 `yolov8n.onnx`를 Lab -> C++ Runtime -> ONNX Runtime CPU -> Lab job result로 검증했고, Jetson Orin Nano에서는 Forge manifest와 TensorRT `model.engine`를 C++ Runtime CLI로 실행해 mean 약 14.00 ms, p99 약 15.50 ms, FPS 약 71.44의 smoke evidence를 확보했습니다. 최근에는 Runtime이 manifest source model identity를 보존하도록 보완해, engine artifact도 `compare_key=yolov8n__b1__h640w640__fp32` 형태를 유지할 수 있게 했습니다.

## Interview: What Actually Works?

현재 실제로 동작하는 범위는 세 단계로 설명할 수 있습니다. 첫째, Lab은 Runtime result를 compare/report/API/job/deployment_decision 형태로 정리할 수 있습니다. 둘째, dev-only 경로에서 Lab이 C++ Runtime CLI를 subprocess로 호출해 `yolov8n.onnx` ONNX Runtime CPU 실행 결과를 job result로 ingest하는 smoke가 성공했습니다. 셋째, Jetson Orin Nano에서 Forge manifest와 TensorRT `model.engine` artifact를 C++ Runtime CLI로 실행한 manual smoke가 성공했고, TensorRT backend, Jetson target, manifest applied, mean 약 14.00 ms, p99 약 15.50 ms, FPS 약 71.44 evidence를 확보했습니다. 다만 production worker daemon이나 queue 기반 자동 실행은 아직 구현 범위가 아닙니다.

## Interview: Is The SaaS Complete?

아직 production SaaS가 완성된 것은 아닙니다. 현재 구현된 것은 SaaS/API/job/worker contract foundation입니다. `/api/compare`, `/api/analyze`, `/api/jobs/{job_id}`, worker request/response mapping, dev-only Runtime execution smoke, deployment decision bundle, optional AIGuard evidence preservation까지는 구현되어 있습니다. 반면 production worker daemon, persistent DB/queue, upload flow, frontend, auth, billing은 future work로 명확히 분리했습니다. 그래서 정확한 표현은 "production SaaS"가 아니라 "SaaS-ready contract foundation plus dev/manual Runtime execution evidence"입니다.

## 1. Resume Project Entry: 5-Line Version

- Built InferEdge, an end-to-end Edge AI Inference Validation Pipeline that connects model artifact provenance, real runtime execution, result analysis, diagnosis evidence, and deployment decisions.
- Implemented InferEdgeLab as the analysis layer that turns Runtime benchmark outputs into comparison reports, API responses, async job results, and Lab-owned deployment decisions.
- Aligned Forge, Runtime, Lab, and AIGuard through JSON contracts: Forge for build/provenance, Runtime for C++ execution/result export, Lab for analysis/API/job/decision, and AIGuard for optional deterministic diagnosis evidence.
- Validated two runtime evidence paths: Lab -> C++ Runtime -> ONNX Runtime CPU -> Lab job result ingestion on macOS with `yolov8n.onnx`, and Jetson Orin Nano TensorRT execution using a Forge manifest plus TensorRT engine artifact.
- Current scope is a portfolio-grade SaaS API/job/worker contract foundation with dev-only Runtime execution smoke; production worker daemon, persistent queue/database, upload flow, frontend, auth, and billing remain future work.

## 2. Resume Project Entry: Detailed Version

InferEdge is an end-to-end Edge AI Inference Validation Pipeline built across four repositories. The system is designed to answer a deployment-oriented question: not just "how fast did this model run?", but "which artifact was built, how was it executed, what evidence was produced, and is it safe to deploy?"

InferEdgeForge owns build artifact provenance. It records metadata and manifests such as source model hash, artifact hash, backend, target, precision, shape, preset, and build id. InferEdgeRuntime owns the C++ execution and result export boundary. It validates Lab worker requests, exports Lab-compatible Runtime results, and supports dry-run worker response export. InferEdgeLab owns comparison, reporting, SaaS API/job contracts, and the final deployment decision. InferEdgeAIGuard is optional and provides deterministic rule/evidence diagnosis for provenance or artifact mismatch cases.

The Lab side includes `/api/compare`, `/api/analyze`, in-memory job stubs, worker request/response mapping, API response contracts, deployment decision bundles, and report evidence preservation. A recent manual smoke validated a real dev-only Runtime execution path using `yolov8n.onnx`: Lab created an analyze job, invoked the C++ Runtime CLI through subprocess, ONNX Runtime CPU executed the model, and the result JSON was ingested back into the Lab job result. The smoke completed successfully with mean latency about 47.97 ms, p95/p99 about 51.80 ms, and about 20.85 FPS.

I also validated a Jetson Orin Nano TensorRT Runtime smoke. On Linux `5.15.148-tegra` / `aarch64`, the C++ Runtime CLI in `~/InferEdge-Runtime` executed a Forge-generated manifest and TensorRT engine artifact from `yolov8n__jetson__tensorrt__jetson_fp16`. The result reported `success: true`, `engine_backend: tensorrt`, `device_name: jetson`, `manifest_applied: true`, input shape `[1, 3, 640, 640]`, output shape `[1, 84, 8400]`, mean latency about 14.00 ms, p99 about 15.50 ms, and about 71.44 FPS. Runtime also preserves the Forge manifest source model identity for compare naming, so a `model.engine` artifact can keep `compare_model_name=yolov8n` and `compare_key=yolov8n__b1__h640w640__fp32`.

The project intentionally separates implemented portfolio-grade pipeline foundation from future production SaaS infrastructure. The current implementation demonstrates contracts, smoke coverage, and a dev-only execution path, while production worker daemons, persistent queues/databases, file upload, frontend, auth, and billing are explicitly planned future work.

## 3. 30-Second Interview Explanation

InferEdge is my end-to-end Edge AI inference validation pipeline. It does more than run a latency benchmark: Forge preserves build provenance, Runtime executes or validates model artifacts through a C++ boundary, Lab compares results and produces reports/API/job outputs plus deployment decisions, and AIGuard optionally adds deterministic diagnosis evidence. I validated both a macOS `yolov8n.onnx` Lab-to-ONNX Runtime CPU smoke and a Jetson Orin Nano TensorRT smoke where the C++ Runtime executed a Forge manifest plus TensorRT engine artifact. It is not a fully productionized SaaS yet; it is a portfolio-grade pipeline foundation with API/job/worker contracts and manual/dev smoke evidence.

## 4. 90-Second Interview Explanation

InferEdge started from a simple edge inference benchmarking problem, but I expanded it into an end-to-end validation pipeline. In edge AI, a raw latency number is not enough. You need to know which model produced which artifact, what backend and precision were used, whether the runtime result is compatible with the analysis layer, and whether the result should be deployed, reviewed, or blocked.

I split the system into four repositories with clear responsibilities. InferEdgeForge is the build/provenance layer. It records metadata, manifests, hashes, precision, target, shape, preset, and build id. InferEdgeRuntime is the C++ execution/result export layer. It validates worker request payloads and produces Lab-compatible runtime result or worker response JSON. InferEdgeLab is the analysis and decision owner. It provides compare/report flows, SaaS API response contracts, in-memory job workflow stubs, worker request/response mapping, and deployment decision output. InferEdgeAIGuard remains optional and performs rule/evidence based diagnosis, such as artifact or provenance mismatch detection.

The important recent validation is that this is no longer only contract-level documentation. I ran a manual dev-only smoke using `yolov8n.onnx`: `/api/analyze` created a Lab job, `/api/jobs/{job_id}/run-runtime-dev` invoked the C++ Runtime CLI through subprocess, ONNX Runtime CPU executed the model, and the Runtime JSON was ingested back into the Lab job result. The result completed successfully, with mean latency about 47.97 ms, p95/p99 about 51.80 ms, and about 20.85 FPS. The deployment decision is `unknown` at that direct execution stage because the result has not yet gone through Lab compare/report, which is expected behavior.

Separately, I validated Jetson TensorRT execution on Jetson Orin Nano. Runtime consumed a Forge manifest and the generated `model.engine`, applied the manifest, executed with `engine_backend: tensorrt` and `device_name: jetson`, and exported a successful result with mean latency about 14.00 ms, p99 about 15.50 ms, and about 71.44 FPS. The earlier compare naming limitation from explicit `model.engine` paths has been polished: Runtime now prefers Forge manifest `source_model.path`, so source identity such as `yolov8n` can survive into `compare_key`.

I am careful not to claim this as a production SaaS platform yet. The production worker daemon, persistent queue/database, file upload flow, frontend, auth, and billing remain future work. What is implemented is the pipeline foundation: schemas, contracts, CLI/API/job boundaries, evidence preservation, and a minimal real Runtime execution path.

## 5. Answer: The Hardest Technical Problem

The hardest part was aligning four repositories into one coherent pipeline without turning it into a vague "AI system" or a collection of disconnected scripts. Each repository needed a precise responsibility boundary and a contract that the others could consume.

The key issue was provenance continuity. Forge knows how an artifact was built, Runtime knows how a model or artifact actually executed, Lab knows how to compare and decide, and AIGuard knows how to diagnose mismatch evidence. If those outputs do not share stable fields, the final deployment decision becomes hard to trust.

I handled this by making the integration schema-first. I added fixture tests and smoke tests for Forge metadata/manifest summaries, Lab worker requests, Runtime worker responses, AIGuard guard analysis, and Lab deployment decision/report ingestion. After that contract loop was stable, I added a dev-only Runtime execution path so Lab could invoke the C++ Runtime CLI and ingest a real result. That sequence kept the project grounded: contracts first, then minimal real execution, then future production infrastructure.

## 6. Answer: Why Is This Not Just a Benchmark Tool?

InferEdge is not just a benchmark tool because it treats latency as only one piece of deployment evidence.

A benchmark script usually answers: "How fast did this model run?" InferEdge asks a broader deployment question: "Which model and artifact produced this result, under what backend/precision/shape, how does it compare with previous results, is there any provenance mismatch, and should this candidate be deployed, reviewed, or blocked?"

That is why the project includes build provenance, Lab-compatible Runtime result JSON, compare/report flows, API response contracts, async job workflow contracts, optional AIGuard diagnosis evidence, and Lab-owned deployment decisions. The `yolov8n.onnx` smoke proves that the Lab-to-Runtime path can execute a real model through ONNX Runtime CPU and ingest the result, while the Jetson smoke proves that a Forge-generated TensorRT engine artifact can be executed by the C++ Runtime CLI on real edge hardware.

## 7. Answer: SaaS Status and Future Work

The current SaaS scope is a foundation, not a completed production SaaS product.

Implemented now:

- `/api/compare` returns a stable API response contract.
- `/api/analyze` creates in-memory analyze jobs.
- `/api/jobs/{job_id}` retrieves job state.
- Lab can map queued jobs to worker requests and worker responses back to job results.
- A dev-only endpoint can call the Runtime CLI and complete a job from a real Runtime result.
- API/job/worker response shapes are covered by fixtures and tests.

Future work:

- production worker daemon
- persistent queue or database
- file upload flow
- production Forge/Runtime worker orchestration
- SaaS frontend
- authentication, billing, deployment controls

So the accurate description is: InferEdgeLab has a SaaS/API/job contract foundation and dev-only Runtime execution smoke, but it is not yet a production SaaS platform.

## 8. Answer: Runtime, Lab, Forge, and AIGuard Roles

**InferEdgeForge** is the build/provenance layer. It turns ONNX models into edge deployment artifacts and records metadata such as source model hash, artifact hash, backend, target, precision, shape, preset, and build id.

**InferEdgeRuntime** is the C++ execution/result export layer. It validates or executes model/artifact inputs and emits Lab-compatible runtime result JSON or worker response payloads.

**InferEdgeLab** is the analysis, API/job workflow, report, and deployment decision owner. It consumes Runtime results, compares them, creates reports and API bundles, tracks job state, preserves optional diagnosis evidence, and owns the final deployment decision.

**InferEdgeAIGuard** is the optional deterministic diagnosis layer. It is not an LLM guessing system. It uses rule/evidence based detectors to identify artifact mismatch, source model mismatch, precision/shape/backend mismatch, and insufficient provenance evidence. Lab can consume its `guard_analysis`, but Lab remains the final decision owner.
