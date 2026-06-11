# InferEdge Resume and Interview Summary 한국어 Quick Guide

언어: [English](inferedge_resume_interview_summary.md) | 한국어

이 문서는 한국어 이력서/면접 설명을 빠르게 잡기 위한 요약본이다. 대표/canonical 문서는 [InferEdge Resume and Interview Summary](inferedge_resume_interview_summary.md)이다.

## 45초 설명

InferEdge는 edge AI 모델을 build provenance, real runtime execution, 비교/report, optional deterministic diagnosis, Lab-owned deployment decision까지 연결하는 inference validation pipeline입니다. 저는 Lab에서 Runtime result를 compare/report/API/job workflow/deployment decision으로 묶고, EdgeEnv의 registry/comparability/regression evidence, Orchestrator `operation_risk_rollup`, AIGuard의 deterministic warning evidence를 Lab report에 보존하는 흐름을 구현했습니다. Jetson TensorRT FP16 25W fixture는 `10.066401 ms` mean, `15.548438 ms` p99, `99.340373 FPS`를 기록했고, Local Studio demo pair에서는 ONNX Runtime CPU 대비 약 `4.51x` speedup을 보여줍니다.

## 역할별 강조점

| 지원 역할 | 강조할 메시지 |
|---|---|
| AI Inference Engineer | TensorRT/ONNX Runtime evidence, latency/p99/FPS, provenance-aware compare key, deterministic anomaly context |
| Embedded / Edge Engineer | Jetson evidence, power-mode context, device-local preservation smoke, queue/deadline/fallback `operation_risk_rollup` |
| Backend / AI Platform | API/job/report contract, EdgeEnv handoff traceability, optional AIGuard evidence ingestion, Lab-owned decision |

## 역할별 피할 표현

| 지원 역할 | 피할 표현 |
|---|---|
| AI Inference Engineer | 자동 모델 품질 판정기나 ML root-cause 확정기처럼 말하지 않는다. |
| Embedded / Edge Engineer | live camera validation, thermal endurance certification, production remote execution 완료처럼 말하지 않는다. |
| Backend / AI Platform | production observability platform, cloud control plane, long-lived worker service, Lab final decision ownership을 넘기는 표현처럼 말하지 않는다. |

## 면접에서 강하게 말할 것

- 단순 benchmark가 아니라 artifact provenance -> runtime evidence -> deployment decision까지 이어지는 validation pipeline이다.
- EdgeEnv는 비교 가능성 판단과 regression evidence를 담당하고, Lab deployment decision을 대체하지 않는다.
- AIGuard는 LLM 추측이 아니라 deterministic evidence provider다.
- Orchestrator operation context와 `operation_risk_rollup`은 supplemental evidence이며 production scheduler 완성 주장이 아니다.

## 말하지 않을 것

- production SaaS 완성
- production observability platform
- cloud control plane
- production remote execution
- AIGuard가 최종 배포 판단을 자동으로 내린다는 표현

정확한 표현은 "portfolio-grade local-first validation and runtime intelligence evidence pipeline"이다.
