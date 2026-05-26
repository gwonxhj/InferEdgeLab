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

Runtime Intelligence smoke evidence chain:
InferEdgeOrchestrator operation feed
-> InferEdgeEnv telemetry history / comparability-first regression context
-> optional InferEdgeAIGuard deterministic runtime anomaly evidence
-> InferEdgeLab Runtime Intelligence Risk Summary / deployment risk report
```

## Summary

- End-to-end validation pipeline: Forge → Runtime → Lab → optional AIGuard
- Real device execution: Jetson TensorRT + ONNX Runtime CPU
- Structured comparison: latency, accuracy, validation evidence
- Deployment decision: deployable / review / blocked
- Comparability layer: InferEdgeEnv `v0.1.5`는 Lab decision과 분리된 local benchmark evidence와 comparability를 기록
- Runtime Intelligence smoke chain: Orchestrator operation context → EdgeEnv telemetry history/regression → AIGuard deterministic evidence → Lab-owned deployment risk report
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

### 브라우저 데모 실행

1. `poetry run inferedgelab serve --host 127.0.0.1 --port 8000` 실행
2. `http://localhost:8000/studio` 접속
3. `Load Demo Evidence` 클릭
4. TensorRT vs ONNX Runtime 비교와 Lab-owned deployment decision context 확인

### CLI 검증 명령

브라우저를 열지 않고도 같은 evidence 수치를 CLI에서 확인하거나 Markdown으로 export할 수 있습니다.

```bash
poetry run inferedgelab demo-evidence-summary
poetry run inferedgelab demo-evidence-summary --format json
poetry run inferedgelab portfolio-demo-check
poetry run inferedgelab core4-conformance-check
poetry run inferedgelab agent-runtime-report \
  --orchestration-summary examples/agent_runtime/agent_3_orchestration_summary.json \
  --guard-analysis examples/agent_runtime/aiguard_runtime_guard_analysis.json
poetry run inferedgelab export-demo-evidence --output reports/studio_demo_evidence.md
```

Guardrail:

- `portfolio-demo-check`는 committed Studio fixture, README/PPT 수치, portfolio docs, local Studio asset을 검증합니다.
- `core4-conformance-check`는 Forge manifest/metadata fixture, Runtime result JSON, Lab compare/deployment decision surface, AIGuard `guard_analysis` evidence를 기존 schema 변경 없이 검증합니다.

추가 report path:

- `agent-runtime-report`는 Orchestrator scheduling evidence와 AIGuard runtime reliability `guard_analysis`를 Lab-owned agent deployment decision context로 묶습니다.
- 현재 bundled agent evidence는 local review용 synthetic sustained high-load 3-agent scenario입니다.
- Runtime result JSON에 `runtime_health_snapshot`, `runtime_events`, `runtime_operation_summary`가 있으면 `--runtime-result <path>`로 같은 Lab report에 Runtime-side operation context를 추가할 수 있습니다.
- Orchestrator `inferedge-remote-dispatch-result-v1` JSON이 있으면 `--remote-dispatch <path>`로 file-based worker selection, retry/fallback plan, remote execution starter context를 추가할 수 있습니다.
- remote dispatch는 local-first review용 starter evidence이며 production remote execution을 주장하지 않습니다.

### Studio에서 볼 수 있는 것

Load Demo Evidence는 bundled ONNX Runtime CPU / TensorRT Jetson result fixture를 불러오고, Run / Import / Jetson Helper는 기존 CLI/API workflow를 local UI로 확장하는 보조 기능입니다.
AIGuard는 이 local Studio path에서 optional이며, Guard evidence가 없으면 Lab comparison은 가능하지만 diagnosis evidence는 제공되지 않았다고 decision context에 표시됩니다.

현재 Studio flow는 작은 `yolov8_coco` evaluation report summary도 함께 보여줍니다. 기준 값은 10 images, 89 ground-truth boxes, mAP@50 `0.1410`, precision `0.2941`, recall `0.1685`, structural validation `passed`입니다.

### 현재 범위

- Run은 기존 `/api/analyze` contract를 통해 in-memory analyze job을 생성합니다.
- Import는 Runtime result JSON path 또는 pasted JSON payload를 받아 compare-ready evidence set에 추가합니다.
- Load Demo Evidence는 stable browser demo를 위해 bundled ONNX Runtime CPU / TensorRT Jetson fixture를 불러옵니다.
- Compare View는 compatible evidence가 로드되면 mean latency, p99, FPS, latency diff, speedup을 보여줍니다.
- Jetson Helper는 Jetson device에서 Runtime을 실행하기 위한 local command shape를 보여줍니다.
- Deployment Decision은 Lab-owned이며, AIGuard는 optional deterministic diagnosis evidence입니다.

현재 non-goal은 변하지 않습니다. DB, queue, upload service, production auth, billing, production SaaS worker orchestration은 포함하지 않습니다.
Studio evidence와 jobs는 in-memory이며 local server process가 재시작되면 초기화됩니다.

## 이 레포의 역할

- Runtime benchmark/result JSON을 읽어 compare/report를 생성합니다.
- `/api/compare`, `/api/analyze`, in-memory job workflow, worker request/response contract를 제공합니다.
- `deployment_decision`의 최종 owner입니다.
- AIGuard `guard_analysis`는 optional evidence로 반영하지만, AIGuard가 최종 판단을 소유하지 않습니다.
- Forge provenance, Runtime result, AIGuard evidence를 하나의 검증 bundle로 정렬합니다.

## 현재 구현 evidence

YOLOv8n은 현재 Local Studio evidence fixture와 Jetson Evidence Track result JSON으로 검증됩니다.
InferEdgeRuntime은 compare-ready JSON result를 생성하고, InferEdgeLab은 `compare_key`, `backend_key`, precision, run context 기준으로 결과를 묶고 비교합니다.

| Evidence | Backend | Precision | Power Mode | Mean ms | P95 ms | P99 ms | FPS |
|---|---|---|---|---:|---:|---:|---:|
| Local Studio baseline | ONNX Runtime CPU | FP32 | n/a | 45.4299 | n/a | 49.2128 | 22.0119 |
| Local Studio candidate | TensorRT Jetson | FP16 | 25W | 10.066401 | 15.476641 | 15.548438 | 99.340373 |
| Jetson power-mode evidence | TensorRT Jetson | FP16 | 15W | 10.799106 | 15.438690 | 15.529218 | 92.600262 |

현재 Local Studio demo 기준 TensorRT Jetson FP16 25W는 ONNX Runtime CPU FP32 baseline보다 약 4.51배 빠릅니다.
Jetson 15W/25W 비교는 power mode가 run configuration의 일부이므로 같은 조건 회귀가 아니라 system evidence로 해석합니다.
이 수치는 `trtexec` GPU-only latency가 아니라 InferEdgeRuntime end-to-end Runtime latency입니다.

추가 검증 경로:

- macOS ONNX Runtime CPU smoke: Lab -> C++ Runtime CLI -> ONNX Runtime CPU execution -> Lab job result ingestion 경로 검증
- Jetson Orin Nano TensorRT smoke: Forge manifest + TensorRT engine artifact를 C++ Runtime CLI가 실행한 evidence 확보
- Runtime source model identity polish: TensorRT `model.engine` 실행에서도 Forge manifest의 `source_model.path`를 우선해 `compare_key=yolov8n__b1__h640w640__fp32` 유지 가능

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

## 현재 역할 경계

InferEdgeLab은 validation / decision layer이고, InferEdgeEnv는 experiment hygiene / comparability layer입니다.

실제 책임은 다음처럼 나뉩니다.

- InferEdge는 모델 후보가 배포 가능한지 검증합니다.
- InferEdgeEnv는 benchmark evidence가 신뢰 가능하고 비교 가능한 형태인지 기록합니다.
- AIGuard는 사용 가능한 경우 deterministic diagnosis evidence를 추가합니다.
- Orchestrator는 supplemental operation context를 제공하며 최종 verdict를 소유하지 않습니다.
- Lab은 final deployment decision owner로 남습니다.

Runtime Intelligence는 local-first evidence automation으로 구현됩니다.

```text
Orchestrator supplemental operation context
-> EdgeEnv telemetry history / regression evidence
-> optional AIGuard deterministic diagnosis evidence
-> Lab Runtime Intelligence Risk Summary
```

이 흐름은 production observability platform이나 runtime control plane이 아닙니다.

## 현재 구현 상태

Core Lab workflow:

- API response contract
- `/api/compare`, `/api/analyze` in-memory jobs
- worker request/response mappings
- compare/report/deployment decision smoke coverage

Cross-repo evidence:

- Runtime dry-run validation/export
- Forge worker/runtime summary
- AIGuard provenance mismatch diagnosis
- dev-only Lab → Runtime ONNX Runtime smoke using `yolov8n.onnx`
- Forge manifest와 TensorRT engine artifact를 사용하는 manual Jetson TensorRT Runtime smoke
- compare-ready TensorRT engine result에서 Runtime source-model identity preservation

Runtime Intelligence smoke:

- Orchestrator operation feed를 supplemental context로 보존
- EdgeEnv telemetry history/regression evidence를 Lab report에 연결
- Runtime history seed `run_config` snapshot을 replay/comparability traceability로 표시
- 사용 가능한 경우 AIGuard deterministic runtime evidence 보존
- AIGuard `runtime_history_seed_run_config_traceability` evidence를 gate에서 필수 traceability evidence로 검증
- AIGuard raw context의 device-local producer lineage를 traceability evidence로 표시
- 기존 JSON contract를 바꾸지 않고 Lab-owned Runtime Intelligence Risk Summary 생성

EdgeEnv runtime regression report에 `runtime_telemetry_context`가 포함되면 Lab은 이를 supplemental telemetry coverage / evidence-gap context로 표시하되, final deployment decision ownership은 Lab에 남깁니다.

Runtime Intelligence report에서 읽어야 할 핵심 row:

- EdgeEnv comparability / regression evidence
- telemetry replay gap
- Runtime history seed `run_config` traceability
- Orchestrator device-local producer lineage
- AIGuard deterministic anomaly evidence
- Lab-owned deployment decision

재현 smoke:

```bash
bash scripts/smoke_runtime_intelligence_chain.sh \
  --output-dir reports/runtime_intelligence_chain
```

이 smoke는 artifact integrity check이며, EdgeEnv나 AIGuard가 Lab의 final deployment decision을 대체하지 않습니다.

## 현재 범위와 future work

현재 상태는 **local-first validation foundation**입니다. API/job/worker contract와 dev/manual smoke evidence는 갖췄지만, production SaaS가 완성된 것은 아닙니다.

Future work:

- production worker daemon
- persistent DB/queue
- file upload flow
- production frontend beyond Local Studio
- production auth/billing/deployment controls
