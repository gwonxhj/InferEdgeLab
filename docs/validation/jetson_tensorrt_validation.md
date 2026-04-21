# Jetson TensorRT Validation Runbook

## 1. 목적

이 문서는 Jetson 환경에서 InferEdgeLab의 TensorRT 실행 경로를 재현 가능한 절차로 검증하기 위한 runbook이다.
단순 실행 성공만 확인하는 것이 아니라, TensorRT profiling 결과가 structured result로 저장되고 `compare-latest` 및 Markdown / HTML report 흐름에서 다시 재사용되는지까지 확인하는 것을 목표로 한다.

## 2. 검증 범위

- 환경
  - Jetson
  - TensorRT
  - ONNX source model + compiled engine artifact
- 모델
  - `resnet18`
  - `yolov8n`
- 확인 항목
  - preflight
  - profiling 성공
  - structured result 저장
  - `compare-latest` 재사용
  - Markdown / HTML report 저장

## 3. 사전 준비

검증에 사용한 모델/엔진 파일 예시는 아래와 같다.

- `models/resnet18.onnx`
- `models/resnet18.engine`
- `models/yolov8n.onnx`
- `models/yolov8n.engine`

`scripts/check_jetson_tensorrt_env.py` 는 Jetson에서 TensorRT 실행에 필요한 기본 준비 상태를 먼저 확인하기 위한 스크립트다.
실제 profiling 전에 Jetson / TensorRT / `cuda-python` 경로와 model/engine artifact 조합이 유효한지 점검하는 용도로 사용한다.

## 4. Preflight Check

실제 검증 명령:

```bash
python scripts/check_jetson_tensorrt_env.py \
  --model-path models/resnet18.onnx \
  --engine-path models/resnet18.engine
```

PASS 기준:

- 스크립트가 오류 없이 종료된다.
- Jetson marker(`/etc/nv_tegra_release`), `tensorrt` / `onnxruntime` / `numpy`, CUDA Python binding availability, `model_path`, `engine_path` 점검 항목이 성공으로 표시된다.
- 실패 시에는 Jetson 환경 자체 문제인지, TensorRT/Python module 준비 문제인지, CUDA Python binding 준비 문제인지, model/engine artifact 경로 문제인지 빠르게 분기할 수 있다.
- 이후 `python -m inferedgelab.cli profile --engine tensorrt ...` 실행 전제 조건이 충족된 것으로 판단한다.

## 5. ResNet18 Validation

### 5-1. Profiling 2회 실행

실제 검증은 `python -m inferedgelab.cli` 경로 기준으로 수행했다.
아래와 같은 동일 명령을 2회 실행해 latest pair를 만들었다.

```bash
python -m inferedgelab.cli profile models/resnet18.onnx \
  --engine tensorrt \
  --engine-path models/resnet18.engine \
  --precision fp16 \
  --warmup 10 \
  --runs 100 \
  --batch 1 \
  --height 224 \
  --width 224
```

```bash
python -m inferedgelab.cli profile models/resnet18.onnx \
  --engine tensorrt \
  --engine-path models/resnet18.engine \
  --precision fp16 \
  --warmup 10 \
  --runs 100 \
  --batch 1 \
  --height 224 \
  --width 224
```

### 5-2. Compare Latest

```bash
python -m inferedgelab.cli compare-latest \
  --model resnet18.onnx \
  --engine tensorrt \
  --device gpu \
  --precision fp16 \
  --selection-mode same_precision
```

### 5-3. 기대 확인 포인트

- structured result 2개 생성
- `engine` / `device` / `precision` metadata 저장
- `runtime_artifact_path` 저장
- `primary_input_name`, `resolved_input_shapes` 저장
- same-precision `compare-latest` 동작
- regression 판단 가능

### 5-4. 실제 관찰 예시

| 항목 | Base | New | 해석 |
|---|---:|---:|---|
| mean_ms | 2.8647 | 2.8265 | 소폭 감소 |
| p99_ms | 3.1388 | 3.0620 | 소폭 감소 |
| overall | - | neutral | threshold 기준 same-precision neutral |

실제 검증에서는 `reports/validation/resnet18_tensorrt_latest.md` 와 `reports/validation/resnet18_tensorrt_latest.html` 생성도 확인했다.
또한 structured result JSON 원문에서 아래 필드가 저장됨을 직접 확인했다.

- `run_config.engine_path = models/resnet18.engine`
- `extra.runtime_artifact_path = models/resnet18.engine`
- `extra.primary_input_name = input`
- `extra.resolved_input_shapes.input = [1, 3, 224, 224]`
- `extra.effective_batch / effective_height / effective_width = 1 / 224 / 224`

## 6. YOLOv8n Validation

### 6-1. Profiling 반복 실행

YOLOv8n도 동일 조건으로 profiling을 반복 실행해 latest pair를 만들었다.

```bash
python -m inferedgelab.cli profile models/yolov8n.onnx \
  --engine tensorrt \
  --engine-path models/yolov8n.engine \
  --precision fp16 \
  --warmup 10 \
  --runs 50 \
  --batch 1 \
  --height 640 \
  --width 640
```

```bash
python -m inferedgelab.cli profile models/yolov8n.onnx \
  --engine tensorrt \
  --engine-path models/yolov8n.engine \
  --precision fp16 \
  --warmup 10 \
  --runs 50 \
  --batch 1 \
  --height 640 \
  --width 640
```

### 6-2. Compare Latest

```bash
python -m inferedgelab.cli compare-latest \
  --model yolov8n.onnx \
  --engine tensorrt \
  --device gpu \
  --precision fp16 \
  --selection-mode same_precision
```

### 6-3. Markdown / HTML Report 저장

```bash
python -m inferedgelab.cli compare-latest \
  --model yolov8n.onnx \
  --engine tensorrt \
  --device gpu \
  --precision fp16 \
  --selection-mode same_precision \
  --markdown-out reports/validation/yolov8n_tensorrt_latest.md \
  --html-out reports/validation/yolov8n_tensorrt_latest.html
```

실제 검증에서는 `reports/validation/yolov8n_tensorrt_latest.md` 와 `reports/validation/yolov8n_tensorrt_latest.html` 생성도 확인했다.

### 6-4. 실제 관찰 예시

| 항목 | Base | New | 해석 |
|---|---:|---:|---|
| mean_ms | 14.4592 | 14.1108 | 소폭 감소 |
| p99_ms | 15.4154 | 15.2565 | 소폭 감소 |
| overall | - | neutral | same-precision neutral |

실제 검증에서는 `reports/validation/yolov8n_tensorrt_latest.md` 와 `reports/validation/yolov8n_tensorrt_latest.html` 생성도 확인했다.
또한 structured result JSON 원문에서 아래 필드가 저장됨을 직접 확인했다.

- `run_config.engine_path = models/yolov8n.engine`
- `extra.runtime_artifact_path = models/yolov8n.engine`
- `extra.primary_input_name = images`
- `extra.resolved_input_shapes.images = [1, 3, 640, 640]`
- `extra.effective_batch / effective_height / effective_width = 1 / 640 / 640`

## 7. 생성 산출물 정리

이번 Jetson TensorRT 실기 검증에서 확인한 산출물 종류는 아래와 같다.

### Auto-Synced Validation Evidence

<!-- EDGE_BENCH_JETSON_RUNBOOK_EVIDENCE:START -->

## Jetson TensorRT Validation Evidence - ResNet18

- Model: `resnet18.onnx`
- Engine: `tensorrt`
- Device: `gpu`
- Precision pair: `fp16_vs_fp16`
- Overall: **neutral**

| Metric | Base | New |
|---|---:|---:|
| mean_ms | 2.8647 | 2.8265 |
| p99_ms | 3.1388 | 3.0620 |

### Runtime Provenance
- Base runtime_artifact_path: `models/resnet18.engine`
- New runtime_artifact_path: `models/resnet18.engine`
- Base primary_input_name: `input`
- New primary_input_name: `input`
- Base resolved_input_shapes: `{'input': [1, 3, 224, 224]}`
- New resolved_input_shapes: `{'input': [1, 3, 224, 224]}`

### Reports
- Markdown: `reports/validation/resnet18_tensorrt_latest.md`
- HTML: `reports/validation/resnet18_tensorrt_latest.html`

**Summary**: Same-precision comparison indicates no significant overall change. Accuracy trade-offs are not available in these results.

## Jetson TensorRT Validation Evidence - YOLOv8n

- Model: `yolov8n.onnx`
- Engine: `tensorrt`
- Device: `gpu`
- Precision pair: `fp16_vs_fp16`
- Overall: **neutral**

| Metric | Base | New |
|---|---:|---:|
| mean_ms | 14.4592 | 14.1108 |
| p99_ms | 15.4154 | 15.2565 |

### Runtime Provenance
- Base runtime_artifact_path: `models/yolov8n.engine`
- New runtime_artifact_path: `models/yolov8n.engine`
- Base primary_input_name: `images`
- New primary_input_name: `images`
- Base resolved_input_shapes: `{'images': [1, 3, 640, 640]}`
- New resolved_input_shapes: `{'images': [1, 3, 640, 640]}`

### Reports
- Markdown: `reports/validation/yolov8n_tensorrt_latest.md`
- HTML: `reports/validation/yolov8n_tensorrt_latest.html`

**Summary**: Same-precision comparison indicates no significant overall change. Accuracy trade-offs are not available in these results.

<!-- EDGE_BENCH_JETSON_RUNBOOK_EVIDENCE:END -->

### ResNet18

- structured runtime result
  - `results/resnet18.onnx__tensorrt__gpu__fp16__b1__h224w224__20260417-064935.json`
  - `results/resnet18.onnx__tensorrt__gpu__fp16__b1__h224w224__20260417-064937.json`
- compare report
  - `reports/validation/resnet18_tensorrt_latest.md`
  - `reports/validation/resnet18_tensorrt_latest.html`

### YOLOv8n

- structured runtime result
  - `results/yolov8n.onnx__tensorrt__gpu__fp16__b1__h640w640__20260417-065012.json`
  - `results/yolov8n.onnx__tensorrt__gpu__fp16__b1__h640w640__20260417-065014.json`
- compare report
  - `reports/validation/yolov8n_tensorrt_latest.md`
  - `reports/validation/yolov8n_tensorrt_latest.html`

정리하면 Jetson validation evidence는
1. repeated profiling으로 생성한 structured result,
2. latest comparable pair에서 생성한 Markdown / HTML compare report

의 두 층으로 구성됩니다.

또한 이 산출물들은 validation을 수행한 Jetson 로컬 환경에 생성되며,
README와 BENCHMARKS는 그 결과를 요약한 reference 역할을 담당합니다.

## 8. 검증 완료 기준

- [x] preflight PASS
- [x] TensorRT profile 성공
- [x] structured result 생성
- [x] `compare-latest` 성공
- [x] Markdown / HTML report 생성
- [x] runtime provenance 필드 확인

runtime provenance 확인 시에는 최소한 아래 필드를 함께 본다.

- `runtime_artifact_path`
- `primary_input_name`
- `resolved_input_shapes`

이번 실기 검증에서는 위 항목이 모두 충족되었고,
structured result JSON 원문에서도 runtime provenance 필드 저장을 직접 확인했다.

## 9. 해석 시 주의사항

- same-precision compare는 regression tracking 용도로 해석한다.
- `run_config` 가 다르면 결과 비교 해석에 주의해야 한다.
- accuracy 없이 수행한 TensorRT profile 결과는 latency 중심으로 해석한다.
- production-grade robustness 검증은 아직 후속 단계다.
- TensorRT `.engine` artifact는 디바이스/환경 의존성이 있으므로 가능하면 target Jetson에서 생성한 plan 파일을 사용하는 것이 바람직하다.
- 실제 실기 검증에서는 TensorRT가 `Using an engine plan file across different models of devices is not recommended` 경고를 출력했다.
- 실기 검증 중 ONNX Runtime의 `device_discovery.cc` warning이 출력될 수 있으나, 이번 검증에서는 profiling / compare / report 흐름을 깨는 치명적 오류는 아니었다.

## 10. 관련 문서

- [README.md](../../README.md)
- [BENCHMARKS.md](../../BENCHMARKS.md)
- [docs/portfolio/edgebench_portfolio.md](../portfolio/edgebench_portfolio.md)
