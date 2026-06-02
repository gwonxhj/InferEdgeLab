# InferEdge 1-Page Architecture Summary 한국어 Quick Guide

언어: [English](inferedge_1page_architecture.md) | 한국어

이 문서는 한국어 리뷰어가 아키텍처 경계를 빠르게 파악하기 위한 요약본이다. 대표/canonical 문서는 [InferEdge 1-Page Architecture Summary](inferedge_1page_architecture.md)이다.

## 한 줄 정의

InferEdge는 Edge AI 모델의 artifact provenance, real runtime execution, comparability-first evidence, report, optional diagnosis, Lab-owned deployment decision을 하나로 연결하는 local-first inference validation pipeline이다.

## 구조

```text
ONNX model
-> Forge
-> Runtime
-> EdgeEnv
-> Lab
-> optional AIGuard
-> optional Orchestrator operation context
```

## 책임 경계

| Component | 책임 | 소유하지 않는 것 |
|---|---|---|
| Forge | build artifact/provenance | runtime scheduling |
| Runtime | inference execution/result export | anomaly detector, deployment decision |
| EdgeEnv | registry/comparability/regression evidence | Lab decision, public leaderboard |
| Lab | report/API/job/deployment decision | production SaaS infrastructure |
| AIGuard | deterministic diagnosis evidence | final decision owner |
| Orchestrator | queue/deadline/fallback operation context | Kubernetes/cloud orchestration |

## Runtime Intelligence 흐름

Runtime Intelligence는 새 repo나 monitoring SaaS가 아니다. Orchestrator operation feed, EdgeEnv telemetry/regression context, AIGuard deterministic warning evidence를 Lab report에 보존해 deployment risk를 더 쉽게 검토하게 만드는 local-first evidence extension이다.

## Reviewer focus

- Lab-owned deployment decision이 최종 판단 owner로 유지되는가.
- EdgeEnv comparability-first 정책이 regression 계산 전에 보존되는가.
- AIGuard/Orchestrator evidence가 supplemental context로 표시되는가.
- production SaaS, cloud control plane, production remote execution으로 과장되지 않는가.
