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

## 역할 경계 한눈에 보기

| 영역 | Lab이 담당하는 일 | Lab이 담당하지 않는 일 |
|---|---|---|
| Validation decision | compare/evaluate/report/API/job workflow와 최종 `deployment_decision`을 생성한다. | Forge build, Runtime execution, EdgeEnv registry, AIGuard diagnosis policy, Orchestrator scheduling을 소유하지 않는다. |
| Forge / Runtime evidence | metadata, manifest, worker response, Runtime result, validation evidence를 ingest하고 정렬한다. | `metadata.json`, `manifest.json`, Runtime `result.json`, compare output contract를 임의 변경하지 않는다. |
| EdgeEnv regression evidence | comparability, regression, telemetry coverage, replay gap을 deployment risk context로 표시한다. | EdgeEnv registry/comparability ownership을 재계산하거나 comparability-first gate를 우회하지 않는다. |
| AIGuard / Orchestrator evidence | optional deterministic diagnosis와 supplemental operation context를 Lab-owned report에 보존한다. | AIGuard/Orchestrator를 final decision owner로 만들거나 production remote execution/control-plane readiness를 주장하지 않는다. |
| Local Studio / API | local-first evidence replay, in-memory job, reviewer workflow UI를 제공한다. | production SaaS, DB/queue/auth/billing/upload service, cloud dashboard가 되지 않는다. |

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

- Orchestrator operation feed를 supplemental context로 보존합니다.
- EdgeEnv telemetry history/regression evidence를 Lab report에 연결합니다.
- AIGuard deterministic runtime evidence가 있으면 같은 Lab-owned report에 보존합니다.
- Jetson EdgeEnv preservation smoke는 device-local ONNX Runtime probe evidence, live `tegrastats`, Runtime operation summary가 EdgeEnv run evidence를 거쳐 Lab deployment risk report까지 이어지는지 확인합니다.
- 기존 JSON contract를 바꾸지 않고 Lab-owned Runtime Intelligence Risk Summary를 생성합니다.

### Runtime Intelligence Risk Summary 빠른 읽기

| 먼저 볼 항목 | Quick signal | 의미 |
|---|---|---|
| Decision owner | `Lab remains the final deployment decision owner` | EdgeEnv, AIGuard, Orchestrator는 evidence provider이고 최종 판단은 Lab이 소유합니다. |
| EdgeEnv regression gate | EdgeEnv comparability / regression evidence | runtime regression은 EdgeEnv comparability context가 있을 때만 해석합니다. |
| Telemetry/replay quality | telemetry replay gap, `runtime_history_seed_run_config_traceability` | Runtime history seed와 `run_config` traceability가 보존됐는지 확인합니다. |
| Operation context | `Orchestrator queue/deadline/fallback markers` | queue pressure, `max_total_queue_depth`, deadline miss, fallback count를 한눈에 묶습니다. |
| AIGuard warnings | deterministic AIGuard runtime operation evidence | AIGuard warning은 Lab policy를 덮어쓰지 않는 review evidence입니다. |

Marker group:

| 그룹 | 핵심 row / label | 이유 |
|---|---|---|
| Producer lineage | `edgeenv_orchestrator_producer_lineage`, `runtime_history_seed_run_config_traceability` | EdgeEnv/Orchestrator lineage가 AIGuard와 Lab까지 보존됐는지 확인합니다. |
| Queue pressure | `Orchestrator queue/deadline/fallback markers`, `AIGuard max queue raw-context traceability` | `max_total_queue_depth`가 AIGuard deterministic raw context와 연결되는지 보여줍니다. |
| Replay / preservation | `Runtime replay duration scope`, `Lab EdgeEnv preservation context`, `Jetson/device-local EdgeEnv preservation run`, `Jetson/device-local EdgeEnv preservation details` | replay duration과 `identity=jetson_device_local_preservation`, `path=device_local_starter` label을 빠르게 찾게 합니다. |
| Task / operation risk | `Orchestrator task event rollup`, `AIGuard task event rollup evidence`, `AIGuard runtime operation anomalies` | scheduler delay, deadline miss, fallback decision, queue/drop reason을 review context로 보여줍니다. |
| Remote starter boundary | `AIGuard remote dispatch event summary`, `Remote fallback starter evidence`, `production_remote_execution=false` | remote dispatch를 production execution이 아니라 starter evidence로 제한합니다. |

세부 marker contract는 [docs/portfolio/edgeenv_runtime_regression_lab_handoff.md](docs/portfolio/edgeenv_runtime_regression_lab_handoff.md)에 정리되어 있습니다.

최신 Jetson EdgeEnv preservation smoke:

| Evidence | Value |
|---|---:|
| Operation path | `device_local_starter` |
| Frames | 32 |
| Max queue depth | 6 |
| Dropped / fallback count | 29 / 29 |
| Deadline missed count | 18 |
| Parsed `tegrastats` samples | 4 |
| Max temperature / RAM | 42.843 C / 999 MB |
| Vision mean / p95 latency | 166.941 ms / 423.192 ms |
| EdgeEnv run ID | `run-20260529-034704-fbf753f0` |
| EdgeEnv summary | `runtime_operation_summary` stored |
| AIGuard verdict | `blocked` / `high` |
| Lab decision | `blocked` |

이 기록은 Runtime Intelligence handoff를 위한 device-local starter smoke입니다. EdgeEnv는 local run evidence와 supplemental operation context를 보존하고, Lab은 final deployment decision owner로 남습니다. decoded YOLO accuracy validation, live camera operation, production remote execution, thermal endurance validation으로 해석하지 않습니다.

재현 smoke:

```bash
bash scripts/smoke_runtime_intelligence_chain.sh \
  --output-dir reports/runtime_intelligence_chain
```

이 smoke는 EdgeEnv가 선언한 external AIGuard evidence requirement가 bundled
`guard_analysis`로 충족되는지도 확인하는 artifact integrity check입니다.
EdgeEnv나 AIGuard가 Lab의 final deployment decision을 대체하지 않습니다.

## 현재 범위와 future work

현재 상태는 **local-first validation foundation**입니다. API/job/worker contract와 dev/manual smoke evidence는 갖췄지만, production SaaS가 완성된 것은 아닙니다.

Future work:

- production worker daemon
- persistent DB/queue
- file upload flow
- production frontend beyond Local Studio
- production auth/billing/deployment controls
