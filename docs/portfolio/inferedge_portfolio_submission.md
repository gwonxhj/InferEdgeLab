# InferEdge Portfolio Submission

## 1. Project Summary

InferEdge는 edge AI 모델을 변환, 실행, 비교, 진단하고 최종 배포 가능 여부를 판단하는 end-to-end inference validation pipeline이다.

이 프로젝트는 단순 latency benchmark가 아니라 artifact provenance, runtime result compatibility, deployment decision까지 연결한다. 목표는 "빠른 숫자"를 보여주는 것이 아니라, 어떤 모델과 산출물이 어떤 환경에서 실행되었고 그 결과를 배포해도 되는지 검토 가능한 evidence로 남기는 것이다.

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

**InferEdgeForge**  
Build/provenance layer. ONNX 모델을 TensorRT/RKNN 등 edge deployment artifact로 변환하고, `metadata.json`, `manifest.json`, `worker_runtime_summary`로 source hash, artifact hash, backend, target, precision, shape, preset 정보를 보존한다.

**InferEdgeRuntime**  
C++ execution/result export layer. Forge artifact 또는 Lab worker_request를 받아 execution boundary를 담당하고, Lab-compatible result JSON과 worker_response dry-run export를 제공한다. 현재 중심은 ONNX Runtime C++ MVP와 contract validation이며, TensorRT 실행 확장은 후속 단계로 분리했다.

**InferEdgeLab**  
Analysis/API/job/deployment decision owner. Runtime result JSON을 비교하고 Markdown/HTML report, SaaS API response, async job workflow contract, deployment_decision을 생성한다. AIGuard는 optional이며 최종 decision owner는 Lab이다.

**InferEdgeAIGuard**  
Rule + evidence diagnosis layer. Forge summary, Runtime worker_response, Lab result를 기반으로 artifact/source hash mismatch, backend/target/precision/shape mismatch, insufficient provenance 등을 deterministic detector로 진단한다. AIGuard는 LLM 추측이 아니라 rule + evidence 기반 detector 구조다.

## 5. Key Implemented Features

- Lab API response contract
- `/api/compare` contract response
- `/api/analyze` in-memory job workflow
- Lab worker_request / worker_response boundary
- Runtime worker_request dry-run validation
- Runtime worker_response dry-run export
- Forge metadata/manifest to worker/runtime summary contract
- Forge summary to Lab worker_request compatibility
- Runtime worker_response compatibility ingest in Lab
- AIGuard worker provenance mismatch diagnosis
- AIGuard guard_analysis preservation in Lab deployment decision/report smoke
- 4개 repository README pipeline summary sync

## 6. Validation Evidence

Recent validation evidence:

- InferEdgeLab: `poetry run python3 -m pytest -q` -> 238 passed
- InferEdgeForge: `python -m pytest -q` -> 89 passed
- InferEdgeRuntime: `python3 tests/test_lab_worker_adapter_contract.py` -> 12 tests passed
- InferEdgeRuntime: `scripts/smoke_default.sh` -> success
- InferEdgeAIGuard: `python -m pytest -q` -> 110 passed
- GitHub Actions: Lab Benchmarks success, Runtime CI success
- Lab PR #171 기준 1-page architecture summary 문서화 완료

The current cross-repository loop is fixture/smoke covered:

```text
Forge summary
-> Lab worker_request
-> Runtime worker_response
-> AIGuard provenance diagnosis
-> Lab deployment_decision/report evidence
```

## 7. Technical Highlights

- **C++ Runtime boundary:** Runtime is implemented as a C++ execution/result export layer rather than a Python-only benchmark script.
- **Schema-first integration:** Lab, Runtime, Forge, and AIGuard are connected through explicit JSON contracts and fixtures.
- **Provenance validation:** Artifact/source hash and runtime provenance are treated as first-class deployment evidence.
- **SaaS-ready boundary:** Lab already has API response contracts, in-memory async job stubs, and worker request/response mapping without prematurely adding DB/queue infrastructure.
- **Deterministic diagnosis:** AIGuard uses rule + evidence detectors instead of vague LLM judgement.
- **Deployment decision ownership:** Lab keeps final deploy/review/blocked ownership while preserving optional guard evidence.

## 8. Current Limitations and Next Steps

Implemented contracts are stable enough for portfolio review, but several production features are intentionally not claimed as complete.

Current planned production work:

- real worker daemon
- actual Forge/Runtime execution from a Lab worker
- database, Redis, or queue
- file upload flow
- SaaS frontend
- production authentication, billing, and deployment controls

Next practical step:

- convert this Markdown draft into a PDF submission document
- keep the PDF concise enough for recruiter review
- add diagrams/screenshots only where they clarify the pipeline

PDF export:

```bash
bash scripts/export_portfolio_pdf.sh
```

The script reads this Markdown file and writes `artifacts/portfolio/inferedge_portfolio_submission.pdf`. The generated `artifacts/` directory is intentionally ignored by git.

## 9. Interview Talking Points

- "제가 만든 것은 단순 벤치마크 스크립트가 아니라, edge deployment artifact의 출처와 실행 결과를 연결해 배포 가능 여부까지 판단하는 검증 파이프라인입니다."
- "Forge, Runtime, Lab, AIGuard를 각각 build/provenance, C++ execution/result export, analysis/API/decision, rule/evidence diagnosis layer로 나눴습니다."
- "AIGuard는 LLM 추측이 아니라 artifact hash, source hash, precision, shape 같은 evidence를 비교하는 deterministic detector 구조입니다."
- "아직 production worker, DB/Redis/queue, frontend, auth/billing은 계획 단계로 명확히 구분했고, 먼저 contract와 smoke coverage를 안정화했습니다."
- "이 프로젝트는 AI inference engineer 포트폴리오 관점에서 C++ runtime, Python orchestration, schema contract, provenance validation, SaaS API boundary를 하나의 제품형 pipeline으로 연결한 사례입니다."
