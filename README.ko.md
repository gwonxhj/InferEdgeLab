# InferEdgeLab

End-to-end Edge AI inference validation pipeline  
(C++ runtime · Jetson execution · validation · deployment decision)

언어: [English](README.md) | 한국어

InferEdgeLab은 InferEdge 전체 파이프라인에서 **analysis/API/job/deployment decision owner** 역할을 맡는 레포입니다.

InferEdge는 ONNX 모델을 edge deployment artifact로 만들고, C++ Runtime으로 실행한 뒤, Lab에서 비교/리포트/API/job 결과와 deployment decision을 생성하며, 필요하면 AIGuard의 deterministic diagnosis evidence를 optional로 보존하는 end-to-end Edge AI inference validation pipeline입니다.

```text
ONNX model
-> InferEdgeForge build/provenance
-> InferEdge-Runtime C++ execution/result export
-> InferEdgeLab analysis/API/job/deployment_decision
-> optional InferEdgeAIGuard deterministic diagnosis evidence
-> deploy / review / blocked decision

Experiment hygiene / comparability layer:
InferEdgeEnv -> v0.1.5 v1-complete local-first run evidence registry / comparability checker
```

## Summary

- End-to-end validation pipeline: Forge → Runtime → Lab → optional AIGuard
- Real device execution: Jetson TensorRT + ONNX Runtime CPU
- Structured comparison: latency, accuracy, validation evidence
- Deployment decision: deployable / review / blocked
- Comparability layer: InferEdgeEnv `v0.1.5`는 Lab decision과 분리된 local benchmark evidence와 comparability를 기록
- Local Studio: inference validation을 브라우저에서 확인하는 local-first workflow UI

## What Makes InferEdge Different?

InferEdge는 단순 benchmark tool이 아닙니다.

InferEdge는 다음을 연결하는 validation pipeline입니다.

- edge device에서 실제 inference 실행
- accuracy와 output validity 평가
- anomaly와 contract violation 감지
- deployment-ready decision 생성

## Local Studio (Recommended Demo Entry Point)

Local Studio는 CLI/API/job workflow를 브라우저에서 조작하고 관찰하는 local-first interface입니다.
cloud SaaS dashboard가 아니며, 사용자의 PC에서 실행되는 demo/review UI입니다.

Recommended demo flow:

1. `poetry run inferedgelab serve --host 127.0.0.1 --port 8000` 실행
2. `http://localhost:8000/studio` 접속
3. `Load Demo Evidence` 클릭
4. TensorRT vs ONNX Runtime 비교와 Lab-owned deployment decision context 확인

브라우저를 열지 않고도 같은 evidence 수치를 CLI에서 확인하거나 Markdown으로 export할 수 있습니다.

```bash
poetry run inferedgelab demo-evidence-summary
poetry run inferedgelab demo-evidence-summary --format json
poetry run inferedgelab agent-runtime-report \
  --orchestration-summary examples/agent_runtime/agent_3_orchestration_summary.json \
  --guard-analysis examples/agent_runtime/aiguard_runtime_guard_analysis.json
poetry run inferedgelab export-demo-evidence --output reports/studio_demo_evidence.md
```

Load Demo Evidence는 bundled ONNX Runtime CPU / TensorRT Jetson result fixture를 불러오고, Run / Import / Jetson Helper는 기존 CLI/API workflow를 local UI로 확장하는 보조 기능입니다.
Studio evidence와 jobs는 in-memory이며 local server process가 재시작되면 초기화됩니다.

`agent-runtime-report`는 Orchestrator scheduling evidence와 AIGuard runtime reliability `guard_analysis`를 Lab-owned agent deployment decision context로 묶는 additive report path입니다. 기존 Runtime result나 compare contract는 변경하지 않습니다.

## 이 레포의 역할

- Runtime benchmark/result JSON을 읽어 compare/report를 생성합니다.
- `/api/compare`, `/api/analyze`, in-memory job workflow, worker request/response contract를 제공합니다.
- `deployment_decision`의 최종 owner입니다.
- AIGuard `guard_analysis`는 optional evidence로 반영하지만, AIGuard가 최종 판단을 소유하지 않습니다.
- Forge provenance, Runtime result, AIGuard evidence를 하나의 검증 bundle로 정렬합니다.

## 현재 구현 evidence

- macOS ONNX Runtime CPU smoke: Lab -> C++ Runtime CLI -> ONNX Runtime CPU execution -> Lab job result ingestion 경로 검증.
- Jetson Orin Nano TensorRT smoke: Forge manifest + TensorRT engine artifact를 C++ Runtime CLI가 실행한 evidence 확보.
- Local Studio demo evidence:
  - TensorRT Jetson FP16 25W: mean `10.066401 ms`, p95 `15.476641 ms`, p99 `15.548438 ms`, FPS `99.340373`
  - ONNX Runtime CPU: mean `45.4299 ms`, p99 `49.2128 ms`, FPS `22.0119`
- Jetson Evidence Track:
  - TensorRT Jetson FP16 15W: mean `10.799106 ms`, p95 `15.438690 ms`, p99 `15.529218 ms`, FPS `92.600262`
  - power mode는 run configuration의 일부이므로 15W/25W 결과는 같은 조건 회귀가 아니라 system evidence로 해석합니다.
- Runtime source model identity polish: TensorRT `model.engine` 실행에서도 Forge manifest의 `source_model.path`를 우선해 `compare_key=yolov8n__b1__h640w640__fp32`를 유지할 수 있습니다.

## 설치와 빠른 실행

```bash
git clone https://github.com/gwonxhj/InferEdgeLab.git
cd InferEdgeLab
pip install poetry
poetry install
```

기본 테스트:

```bash
poetry run python3 -m pytest -q
```

포트폴리오용 guided demo:

```bash
bash scripts/demo_pipeline_full.sh
bash scripts/demo_pipeline_full.sh --help
bash scripts/demo_pipeline_full.sh --run-jetson-command-print
```

## 다른 InferEdge 레포와의 관계

- **InferEdgeForge:** ONNX 모델을 TensorRT/RKNN 등 edge deployment artifact로 만들고 metadata/manifest provenance를 남깁니다.
- **InferEdge-Runtime:** Forge artifact 또는 Lab worker request를 받아 C++ 실행/검증 결과 JSON을 생성합니다.
- **InferEdgeLab:** 결과를 비교/리포트/API/job/deployment decision으로 정리하는 owner입니다.
- **InferEdgeAIGuard:** provenance mismatch나 suspicious result를 rule/evidence 기반으로 진단하는 optional evidence layer입니다.
- **InferEdgeEnv:** `v0.1.5` v1-complete experiment hygiene / comparability layer로, Edge AI inference benchmark result를 local artifact와 SQLite registry로 고정하고 비교 가능성을 판정합니다.

포트폴리오 경계: InferEdgeLab은 validation / decision layer이고, InferEdgeEnv는 `v0.1.5` v1-complete experiment hygiene / comparability layer입니다. InferEdge는 모델이 배포 가능한지 검증하고, InferEdgeEnv는 benchmark evidence가 신뢰 가능하고 비교 가능한 형태로 기록됐는지 관리합니다. EdgeEnv runtime regression report에 `runtime_telemetry_context`가 포함되면 Lab은 이를 supplemental telemetry coverage / evidence-gap context로 표시하되, final deployment decision ownership은 Lab에 남깁니다.

## 현재 범위와 future work

현재 상태는 **SaaS-ready validation foundation**입니다. API/job/worker contract와 dev/manual smoke evidence는 갖췄지만, production SaaS가 완성된 것은 아닙니다.

Future work:

- production worker daemon
- persistent DB/queue
- file upload flow
- SaaS frontend
- production auth/billing/deployment controls
