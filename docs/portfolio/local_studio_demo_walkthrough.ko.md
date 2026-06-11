# InferEdge Local Studio Demo Walkthrough 한국어 Quick Guide

언어: [English](local_studio_demo_walkthrough.md) | 한국어

이 문서는 Local Studio를 보여줄 때 어떤 순서로 설명하고, 역할별로 어떤 메시지를 강조할지 빠르게 확인하기 위한 요약본이다. 대표/canonical 문서는 [InferEdge Local Studio Demo Walkthrough](local_studio_demo_walkthrough.md)이다.

## 데모 경계

Local Studio는 사용자의 PC에서 committed evidence를 재생하고 API/job/report contract를 확인하는 local-first workflow UI다.

production SaaS dashboard, cloud control plane, production worker service, production remote execution proof가 아니다.

## 실행 순서

```bash
poetry run inferedgelab serve --host 127.0.0.1 --port 8000
```

`http://localhost:8000/studio`를 열고 `Load Demo Evidence`를 클릭한다.

이 경로는 live Jetson 없이도 다음 evidence를 보여준다.

- ONNX Runtime CPU FP32 baseline fixture
- TensorRT Jetson FP16 25W candidate fixture
- Jetson 15W/25W power-mode context
- review/block problem case
- available optional AIGuard portfolio evidence

## 보여줄 순서

1. TensorRT Jetson vs ONNX Runtime 비교부터 보여준다.
2. 이 demo pair가 committed fixture이며 live Jetson 없이 재생 가능하다고 말한다.
3. Lab-owned deployment decision context를 확인한다.
4. 문제 케이스로 annotation missing, invalid structure, contract mismatch, latency regression이 review/block evidence로 남는다는 점을 보여준다.
5. Runtime Intelligence는 Studio live dashboard가 아니라 Lab-owned report chain으로 설명한다.

## 인용할 수치

| Evidence | 값 |
|---|---:|
| ONNX Runtime CPU FP32 mean | `45.4299 ms` |
| ONNX Runtime CPU FP32 p99 | `49.2128 ms` |
| ONNX Runtime CPU FP32 FPS | `22.0119` |
| TensorRT Jetson FP16 25W mean | `10.066401 ms` |
| TensorRT Jetson FP16 25W p99 | `15.548438 ms` |
| TensorRT Jetson FP16 25W FPS | `99.340373` |
| Studio demo speedup | 약 `4.51x` |

이 pair는 backend/device/precision context가 다른 deployment review evidence이며, same-condition regression으로 말하지 않는다.

## Runtime Intelligence 연결

Studio evidence에서 Runtime Intelligence로 넘어갈 때는 아래 Lab-owned report chain을 사용한다.

```text
InferEdgeOrchestrator operation feed / operation_risk_rollup
-> InferEdgeEnv telemetry history / comparability-first regression context
-> optional InferEdgeAIGuard deterministic runtime evidence
-> InferEdgeLab Runtime Intelligence Risk Summary / deployment risk report
```

함께 볼 문서:

- [EdgeEnv runtime regression Lab handoff](edgeenv_runtime_regression_lab_handoff.md)
- [Resume/interview summary](inferedge_resume_interview_summary.md)
- [Pipeline status](inferedge_pipeline_status.md)

핵심 문장: Orchestrator, EdgeEnv, AIGuard는 evidence provider이고, final deployment decision owner는 Lab이다.

## 역할별 경로

| 역할 | 먼저 보여줄 것 | 명확히 말할 것 |
|---|---|---|
| AI Inference Engineer | Runtime comparison, latency/p99/FPS, compare identity | 단순 benchmark가 아니라 provenance-aware inference validation이다. |
| Embedded / Edge Engineer | Jetson FP16 25W/15W evidence, device-local preservation context | demo는 live hardware 없이 재생 가능하지만, 새 live evidence에는 device가 필요하다. |
| Backend / AI Platform | API/job/report contract, worker boundary, Lab decision context | contract/evidence orchestration이지 DB/queue/auth/billing production SaaS가 아니다. |

## 피할 표현

- production SaaS 완성
- Local Studio는 cloud dashboard
- Runtime Intelligence는 production observability
- remote dispatch가 production remote execution을 증명
- AIGuard나 Orchestrator가 final deployment decision owner
- Studio pair가 same-condition regression

## CLI 확인

브라우저를 열지 않을 때는 아래 명령으로 같은 evidence를 확인한다.

```bash
poetry run inferedgelab demo-evidence-summary
poetry run inferedgelab portfolio-demo-check
poetry run inferedgelab export-demo-evidence --output reports/studio_demo_evidence.md
```

`portfolio-demo-check`는 committed Studio fixture, README metric, portfolio docs, local Studio asset을 빠르게 검증하는 guard다.
