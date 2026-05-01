# InferEdge Portfolio Submission

## 1. Project Summary

InferEdge는 edge AI 모델을 변환, 실행, 비교, 진단하고 최종 배포 가능 여부를 판단하는 end-to-end inference validation pipeline이다.

InferEdge is not a benchmarking tool, but an end-to-end validation pipeline that connects artifact provenance, runtime behavior, and deployment decisions.

이 프로젝트는 단순 latency benchmark가 아니라 artifact provenance, runtime result compatibility, deployment decision까지 연결한다. 목표는 "빠른 숫자"를 보여주는 것이 아니라, 어떤 모델과 산출물이 어떤 환경에서 실행되었고 그 결과를 배포해도 되는지 검토 가능한 evidence로 남기는 것이다.

채용 포트폴리오용 5줄 요약:

- InferEdgeLab은 Runtime benchmark 결과를 분석해 comparison report, API response, async job result, deployment decision을 생성한다.
- InferEdge 전체 흐름은 Forge build provenance -> Runtime real execution -> Lab compare/report/API/job/deployment_decision -> optional AIGuard diagnosis evidence로 구성된다.
- Lab은 InferEdgeForge provenance metadata, InferEdge-Runtime C++ execution output, optional InferEdgeAIGuard diagnostic evidence를 하나의 검증 bundle로 연결한다.
- `yolov8n.onnx` manual smoke에서 Lab -> C++ Runtime CLI -> ONNX Runtime CPU execution -> Lab job result ingestion 경로가 dev-only minimal Runtime execution path로 검증되었다.
- 현재 상태는 portfolio-grade pipeline foundation이며, production worker daemon, persistent queue/database, file upload, production frontend beyond Local Studio, auth/billing은 future work로 명확히 분리한다.

Pipeline:

```text
ONNX model
-> InferEdgeForge build
-> metadata / manifest / worker runtime summary
-> InferEdgeRuntime validation / result export
-> InferEdgeLab compare / API / job workflow / deployment_decision
-> optional InferEdgeAIGuard provenance diagnosis
-> deploy / review / blocked decision
```

## 2. Problem Statement

Edge AI deployment에서는 모델 변환이나 latency 측정만으로는 충분하지 않다.

실제 배포 검증에는 다음 질문이 남는다:

- 이 artifact가 어떤 ONNX 모델과 build option에서 나왔는가?
- Runtime 결과가 Forge에서 만든 artifact와 같은 provenance를 가리키는가?
- 비교 결과가 batch, shape, precision, backend 조건을 고려하는가?
- accuracy와 latency trade-off를 함께 판단할 수 있는가?
- 최종적으로 deploy, review, blocked 중 어떤 판단을 내려야 하는가?

InferEdge는 이 질문들을 CLI, JSON schema, report, API contract, worker boundary, optional diagnosis layer로 연결한다.

## 3. System Architecture

InferEdge는 4개 repository를 하나의 pipeline으로 분리한다.

```text
Forge = build / provenance
Runtime = C++ execution / result export
Lab = compare / report / API / deployment decision
AIGuard = optional rule + evidence diagnosis
```

이 구조의 핵심은 responsibility boundary다. Forge는 artifact를 만들고 provenance를 남긴다. Runtime은 실제 실행과 profiling evidence를 만든다. Lab은 결과를 비교하고 report/API bundle과 deployment decision을 생성한다. AIGuard는 optional evidence로 provenance mismatch나 failure signal을 진단한다.

## 4. Repository Roles

## Repository Map

| Repository | One-line role |
|---|---|
| InferEdgeForge | Build provenance and handoff layer for converting ONNX models into edge deployment artifacts. |
| InferEdge-Runtime | C++ runtime execution and result export layer for ONNX Runtime/TensorRT edge inference validation. |
| InferEdgeLab | Analysis/API layer for end-to-end Edge AI inference validation, reports, jobs, and deployment decisions. |
| InferEdgeAIGuard | Optional deterministic diagnosis layer for provenance mismatch and suspicious inference result evidence. |

**InferEdgeForge**  
Build/provenance layer. ONNX 모델을 TensorRT/RKNN 등 edge deployment artifact로 변환하고, `metadata.json`, `manifest.json`, `worker_runtime_summary`로 source hash, artifact hash, backend, target, precision, shape, preset 정보를 보존한다.

**InferEdgeRuntime**  
C++ execution/result export layer. Forge artifact 또는 Lab worker_request를 받아 execution boundary를 담당하고, Lab-compatible result JSON과 worker_response dry-run export를 제공한다. 현재 ONNX Runtime C++ MVP와 contract validation을 중심으로 하며, Jetson Orin Nano에서는 Forge manifest와 TensorRT engine artifact를 C++ Runtime CLI로 실행한 manual smoke evidence도 확보했다. Production worker daemon 기반 자동 실행은 후속 단계로 분리했다.

**InferEdgeLab**  
Analysis/API/job/deployment decision owner. Runtime result JSON을 비교하고 Markdown/HTML report, SaaS API response, async job workflow contract, deployment_decision을 생성한다. AIGuard는 optional이며 최종 decision owner는 Lab이다.

**InferEdgeAIGuard**  
Rule + evidence diagnosis layer. Forge summary, Runtime worker_response, Lab result를 기반으로 artifact/source hash mismatch, backend/target/precision/shape mismatch, insufficient provenance 등을 deterministic detector로 진단한다. AIGuard는 LLM 추측이 아니라 rule + evidence 기반 detector 구조다.

## 5. Key Implemented Features

- Lab API response contract
- `/api/compare` contract response
- `/api/analyze` in-memory job workflow
- Lab worker_request / worker_response boundary
- Lab -> Runtime dev-only minimal execution smoke with `yolov8n.onnx`
- Jetson TensorRT Runtime smoke using Forge manifest + TensorRT engine artifact
- Runtime worker_request dry-run validation
- Runtime worker_response dry-run export
- Forge metadata/manifest to worker/runtime summary contract
- Forge summary to Lab worker_request compatibility
- Runtime worker_response compatibility ingest in Lab
- AIGuard worker provenance mismatch diagnosis
- AIGuard guard_analysis preservation in Lab deployment decision/report smoke
- Local Studio browser workflow for Run, Import, Jetson command helper, demo evidence replay, Compare View, and Lab-owned Deployment Decision inspection
- 4개 repository README pipeline summary sync

## 6. Validation Evidence

Recent validation evidence:

- InferEdgeLab: `poetry run python3 -m pytest -q` -> 262 passed
- InferEdgeForge: `python -m pytest -q` -> 89 passed
- InferEdgeRuntime: `python3 tests/test_lab_worker_adapter_contract.py` -> 12 tests passed
- InferEdgeRuntime: `scripts/smoke_default.sh` -> success
- InferEdgeAIGuard: `python -m pytest -q` -> 110 passed
- GitHub Actions: Lab Benchmarks success, Runtime CI success
- Lab PR #171 기준 1-page architecture summary 문서화 완료
- Lab -> Runtime manual smoke using `yolov8n.onnx`: `/api/analyze` created job `job_9e2321179256`, Lab invoked the C++ Runtime CLI through the dev-only subprocess path, ONNX Runtime executed the model successfully, and the latency/provenance JSON was ingested back into the Lab job result. The smoke reported ONNX Runtime backend available, benchmark status success, mean latency about 47.97 ms, p50 about 46.95 ms, p95/p99 about 51.80 ms, and about 20.85 FPS.
- Jetson TensorRT Runtime smoke: on Jetson Orin Nano (`Linux 5.15.148-tegra`, `aarch64`), the C++ Runtime CLI in `~/InferEdge-Runtime` executed Forge manifest `/home/risenano01/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16/manifest.json` and TensorRT engine artifact `/home/risenano01/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16/model.engine`. The output `results/jetson/yolov8n_jetson_tensorrt_manifest_smoke.json` reported `success: true`, `engine_backend: tensorrt`, `device_name: jetson`, `manifest_applied: true`, input shape `[1, 3, 640, 640]`, output shape `[1, 84, 8400]`, mean latency about 14.00 ms, p99 about 15.50 ms, and about 71.44 FPS.
- Runtime compare-key identity polish: InferEdgeRuntime now preserves Forge manifest source model identity for compare naming. If `manifest.source_model.path` is `models/onnx/yolov8n.onnx` and the explicit TensorRT artifact path is `model.engine`, Runtime can keep `compare_model_name=yolov8n` and `compare_key=yolov8n__b1__h640w640__fp32`.
- Guided demo entrypoint: `scripts/demo_pipeline_full.sh` summarizes the full Forge -> Runtime -> Lab -> optional AIGuard flow and can print the Jetson TensorRT Runtime command without claiming production worker or SaaS readiness.
- Local Studio demo evidence: `/studio` can load bundled ONNX Runtime CPU and TensorRT Jetson Runtime result fixtures from `examples/studio_demo`, keep the demo pair selectable in Recent jobs while the local server process is alive, and show TensorRT Jetson vs ONNX Runtime CPU comparison in the browser. The fixture-backed evidence records ONNX Runtime CPU at mean 45.4299 ms / p99 49.2128 ms / 22.0119 FPS and TensorRT Jetson at mean 9.9375 ms / p99 15.5231 ms / 100.6293 FPS, a 4.57x TensorRT speedup for this demo pair.
- YOLOv8 COCO subset evaluation: a 10-image local person-detection subset with 89 ground-truth boxes is converted into a COCO-style annotation fixture and evaluated through the `yolov8_coco` preset. The generated report records mAP@50 0.1410, precision 0.2941, recall 0.1685, and structural validation passed. This is documented as subset workflow evidence, not a full COCO benchmark claim.
- Validation problem cases: the demo bundle includes annotation-missing, invalid detection structure, and contract shape mismatch reports. These show that InferEdge records review/block evidence explicitly instead of presenting every validation path as successful.

The direct Runtime execution result includes `deployment_decision`. Its `unknown` value is expected before Lab compare/report because the worker response has not yet been compared by Lab.

Jetson note: the earlier TensorRT smoke exposed a compare naming polish item where explicit `model.engine` paths could degrade the comparison model name to `model`. Runtime #37 resolved this by preferring Forge manifest source model identity when a manifest is applied. This is a provenance/compare-readiness improvement, not a production SaaS feature.

The current cross-repository loop is fixture/smoke covered:

```text
Forge summary
-> Lab worker_request
-> Runtime worker_response
-> AIGuard provenance diagnosis
-> Lab deployment_decision/report evidence
```

## 7. Technical Highlights

- **End-to-end pipeline:** Forge, Runtime, Lab, and AIGuard are connected as one validation flow from artifact build to deploy/review/blocked decision.
- **Real inference execution smoke:** Lab can create an analyze job, call the C++ Runtime CLI through a dev-only subprocess path, execute `yolov8n.onnx` with ONNX Runtime, ingest the result JSON, and complete the job.
- **Jetson TensorRT artifact execution evidence:** On Jetson Orin Nano, the C++ Runtime CLI executed a Forge-generated TensorRT engine artifact with its manifest and exported successful TensorRT latency evidence.
- **C++ Runtime execution layer:** Runtime is implemented as a C++ execution/result export boundary rather than a Python-only benchmark script.
- **Schema-first contract-based integration:** Lab, Runtime, Forge, and AIGuard communicate through explicit JSON contracts and compatibility fixtures.
- **Provenance-aware validation:** Artifact/source hash, manifest source model identity, and runtime provenance are treated as first-class deployment evidence.
- **SaaS-ready API + async job workflow:** Lab has API response contracts, in-memory async job stubs, and worker request/response mapping without prematurely adding DB/queue infrastructure.
- **Deterministic rule-based diagnosis:** AIGuard uses rule + evidence detectors instead of vague LLM judgement.
- **Deployment decision ownership:** Lab keeps final deploy/review/blocked ownership while preserving optional guard evidence.
- **Local-first Studio demo:** The browser UI can replay real validation evidence locally without adding DB, queue, upload, auth, billing, or production SaaS infrastructure.

## 8. Current Limitations and Next Steps

Implemented contracts are stable enough for portfolio review, but several production features are intentionally not claimed as complete.

Current planned production work:

- real worker daemon
- full automated Forge/Runtime execution from a production Lab worker
- database, Redis, or queue
- file upload flow
- production frontend beyond Local Studio
- production authentication, billing, and deployment controls

Next practical step:

- customize this portfolio for each target company
- refine evaluation datasets and real-world benchmarks
- extend the pipeline to production-ready worker execution

## 9. Interview Talking Points

- Final resume/interview wording is available in [InferEdge Resume and Interview Summary](inferedge_resume_interview_summary.md), including role-specific versions for AI Inference Engineer, Embedded/Edge Engineer, and Backend/AI Platform roles.
- "제가 만든 것은 단순 벤치마크 스크립트가 아니라, edge deployment artifact의 출처와 실행 결과를 연결해 배포 가능 여부까지 판단하는 검증 파이프라인입니다."
- "Forge, Runtime, Lab, AIGuard를 각각 build/provenance, C++ execution/result export, analysis/API/decision, rule/evidence diagnosis layer로 나눴습니다."
- "macOS ONNX Runtime CPU smoke와 Jetson Orin Nano TensorRT smoke를 모두 확보했고, Jetson에서는 Forge manifest + TensorRT `model.engine` + C++ Runtime CLI 실행으로 mean 약 14.00 ms, p99 약 15.50 ms, FPS 약 71.44 evidence를 확보했습니다."
- "Runtime source identity polish 이후에는 manifest-backed TensorRT engine artifact도 `compare_model_name=yolov8n`, `compare_key=yolov8n__b1__h640w640__fp32`를 유지할 수 있습니다."
- "AIGuard는 LLM 추측이 아니라 artifact hash, source hash, precision, shape 같은 evidence를 비교하는 deterministic detector 구조입니다."
- "아직 production worker, DB/Redis/queue, production frontend, auth/billing은 계획 단계로 명확히 구분했고, 먼저 contract와 smoke coverage를 안정화했습니다."
- "이 프로젝트는 AI inference engineer 포트폴리오 관점에서 C++ runtime, Python orchestration, schema contract, provenance validation, SaaS API boundary를 하나의 제품형 pipeline으로 연결한 사례입니다."
