# InferEdge Portfolio Submission 한국어 Quick Guide

언어: [English](inferedge_portfolio_submission.md) | 한국어

이 문서는 한국어 리뷰어가 빠르게 맥락을 잡기 위한 요약본이다. 대표/canonical 문서는 [InferEdge Portfolio Submission](inferedge_portfolio_submission.md)이다.

## 핵심 메시지

InferEdgeLab은 Runtime 결과를 단순히 보여주는 도구가 아니라, runtime evidence를 비교하고 report/API/job result/deployment decision으로 정리하는 Lab-owned deployment decision layer다.

InferEdge 전체 흐름은 다음처럼 읽으면 된다.

```text
Forge build provenance
-> Runtime real execution evidence
-> EdgeEnv registry / comparability / regression context
-> Lab report / deployment decision
-> optional AIGuard deterministic evidence
-> optional Orchestrator operation context
```

## 한눈에 보는 역할 분리

| Layer | Owner | Reviewer가 확인할 것 |
|---|---|---|
| Forge | build/provenance | artifact가 어떤 model/config에서 만들어졌는가 |
| Runtime | execution/result export | 실제 runtime evidence가 Lab-compatible JSON으로 남았는가 |
| EdgeEnv | registry/comparability | 비교 가능한 조건인지 먼저 판정했는가 |
| Lab | report/deployment decision | 최종 deploy/review/blocked 판단을 Lab이 소유하는가 |
| AIGuard | deterministic diagnosis | runtime/output warning을 근거 기반으로 설명하는가 |
| Orchestrator | operation context | queue/deadline/fallback context가 supplemental evidence로 보존되는가 |

## 강한 evidence

- Local Studio demo pair: ONNX Runtime CPU FP32 `45.4299 ms` mean / `49.2128 ms` p99 / `22.0119 FPS`.
- Jetson TensorRT FP16 25W fixture: `10.066401 ms` mean / `15.548438 ms` p99 / `99.340373 FPS`.
- 같은 demo pair 기준 TensorRT Jetson FP16은 ONNX Runtime CPU 대비 약 `4.51x` 빠르다.
- Jetson EdgeEnv preservation smoke는 `device_local_starter`, live `tegrastats`, `runtime_operation_summary`, EdgeEnv run evidence, AIGuard warning, Lab deployment risk report까지 이어지는 local-first artifact chain을 보여준다.

## 경계

이 문서는 production SaaS, production observability platform, cloud control plane, production remote execution, public leaderboard 완성을 주장하지 않는다. Runtime Intelligence는 local-first artifact/evidence chain이며, Lab-owned deployment decision을 더 설명 가능하게 만드는 확장이다.

## 읽는 순서

1. README의 Portfolio entry points table을 먼저 본다.
2. 영어 canonical 문서에서 상세 evidence와 최신 수치를 확인한다.
3. 이 한국어 quick guide로 면접/리뷰 설명의 한글 표현을 정리한다.
