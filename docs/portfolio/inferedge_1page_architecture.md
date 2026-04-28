# InferEdge 1-Page Architecture Summary

## One-line Pitch

InferEdge is an end-to-end Edge AI inference validation pipeline that builds deployment artifacts, runs edge inference, compares results, diagnoses provenance issues, and produces deployment decisions.

## Problem

Edge AI deployment needs more than a latency number. A model candidate must be tied to the artifact that was built, the runtime result that was measured, the comparison policy that was applied, and the final deployment decision. Without artifact provenance, reproducible build records, compatible result schemas, and decision evidence, benchmark results are hard to trust or review.

## Pipeline

```text
ONNX model
-> InferEdgeForge
-> metadata / manifest / worker runtime summary
-> InferEdgeRuntime
-> Lab-compatible result JSON / worker_response
-> InferEdgeLab
-> compare / report / API / async job / deployment_decision
-> optional InferEdgeAIGuard
-> rule + evidence provenance diagnosis
-> deploy / review / blocked decision
```

## Repository Roles

- **InferEdgeForge:** build/provenance layer. Converts ONNX models into edge deployment artifacts and records metadata, manifests, hashes, presets, target/backend/precision/shape, and worker/runtime summaries.
- **InferEdgeRuntime:** C++ execution/result export layer. Validates or runs model/artifact inputs, measures runtime latency, exports Lab-compatible result JSON, and dry-run exports worker responses.
- **InferEdgeLab:** analysis/API/job/deployment decision owner. Compares Runtime results, generates reports, exposes API/job workflow contracts, preserves optional guard evidence, and owns the final `deployment_decision`.
- **InferEdgeAIGuard:** optional rule + evidence diagnosis layer. Detects provenance/artifact/config mismatches and returns deterministic `guard_analysis` evidence for Lab to consume.

## Implemented Evidence

- Lab API response contract
- `/api/compare` contract response
- `/api/analyze` in-memory job workflow
- Lab `worker_request` / `worker_response` boundary
- Runtime `worker_request` validation and `worker_response` dry-run export
- Forge worker/runtime summary
- AIGuard provenance mismatch diagnosis
- Lab decision/report guard evidence smoke
- all repo README pipeline summaries synced

## Current Non-Goals / Planned Production Work

- real worker daemon
- actual Forge/Runtime execution from a Lab worker
- database, Redis, or queue
- file upload
- frontend
- production authentication, billing, and deployment controls

## Interview Explanation

제가 만든 것은 단순 벤치마크 스크립트가 아니라, edge deployment artifact의 출처와 실행 결과를 연결해 배포 가능 여부까지 판단하는 검증 파이프라인입니다.

## Why It Matters

InferEdge shows a product-style AI inference engineering workflow: C++ runtime execution, Python orchestration, schema contracts, artifact provenance validation, SaaS API boundaries, rule-based diagnosis, and deployment decision ownership are connected as one pipeline instead of isolated scripts.
