# InferEdge Pipeline Status 한국어 Quick Guide

언어: [English](inferedge_pipeline_status.md) | 한국어

이 문서는 한국어 리뷰어가 현재 구현 상태를 빠르게 확인하기 위한 요약본이다. 대표/canonical 문서는 [InferEdge Pipeline Status](inferedge_pipeline_status.md)이다.

## 현재 완료된 것

- Lab compare/report/API/job workflow와 Lab-owned deployment decision.
- Local Studio demo evidence replay.
- Runtime result JSON ingestion과 worker request/response contract.
- Jetson TensorRT FP16 25W/15W fixture evidence.
- EdgeEnv runtime telemetry/regression context ingestion.
- AIGuard deterministic runtime warning evidence preservation.
- Orchestrator queue/deadline/fallback context를 supplemental operation evidence로 표시.
- Runtime Intelligence operation risk rollup chain: Orchestrator operation risk/timeline context -> EdgeEnv handoff -> AIGuard deterministic evidence -> Lab Runtime Intelligence Risk Summary.

## 현재 evidence snapshot

| Evidence | 값 |
|---|---|
| ONNX Runtime CPU FP32 demo | `45.4299 ms` mean, `49.2128 ms` p99, `22.0119 FPS` |
| Jetson TensorRT FP16 25W demo | `10.066401 ms` mean, `15.548438 ms` p99, `99.340373 FPS` |
| Demo speedup | 약 `4.51x` |
| Jetson EdgeEnv preservation smoke | `device_local_starter`, `run-20260529-034704-fbf753f0`, `runtime_operation_summary` |
| Runtime Intelligence rollup chain | `operation_risk_rollup` -> EdgeEnv handoff -> AIGuard evidence -> Lab Risk Summary |

## 아직 구현하지 않았거나 명시적으로 제외한 것

- production worker daemon
- persistent DB/queue
- file upload
- production frontend beyond Local Studio
- auth/billing
- cloud control plane
- production remote execution
- production observability platform

## 안전한 표현

현재 상태는 production SaaS 완성이 아니라, portfolio-grade local-first validation workflow와 Runtime Intelligence evidence chain이 테스트/문서/fixture로 연결된 상태다.

Lab은 최종 decision owner다. EdgeEnv는 registry/comparability/regression evidence owner다. AIGuard는 deterministic evidence provider다. Orchestrator는 operation context provider다.

## Jetson 필요 여부

이 문서 확인과 README 링크 검증에는 Jetson 기기가 필요하지 않다. 새로운 live device-local smoke나 sustained replay evidence를 추가할 때는 Jetson 기기가 필요하다.
