# Benchmarks

> 현재 이 문서는 Jetson TensorRT validation reference와 Odroid RKNN curated hardware validation 결과를 먼저 정리합니다.
> CI / auto-generated benchmark summary가 생성되면 동일 문서에 함께 누적됩니다.

이 문서는 다음 두 목적을 함께 가집니다.

1. CPU auto-generated benchmark 요약 보관
2. 실제 Edge HW validation evidence를 표 중심으로 정리하는 benchmark reference

Jetson TensorRT 실기 검증 evidence는 README와 portfolio 문서에서 서술형으로 설명하고,
이 파일은 그 결과를 빠르게 확인할 수 있는 표 중심 reference 역할에 집중합니다.

## Curated Hardware Validation

이 섹션은 실제 Odroid RKNN 실험에서 확보한 대표 결과를 EdgeBench result schema로 정리한 표입니다.
즉, 단순 보고서용 표가 아니라 이후 `compare`, `compare-latest`, report workflow에 재사용되는 validation evidence입니다.

## Jetson TensorRT Validation Reference

이 섹션은 Jetson 실기 검증에서 실제 생성된 structured result / compare-latest 결과를 기준으로 정리한 표입니다.
즉, 단순 설명용 숫자가 아니라 TensorRT execution → structured result 저장 → compare/report 재사용까지 확인된 validation evidence입니다.

| Model | Engine | Device | Precision | Batch | Input(HxW) | Warmup | Runs | Base Mean (ms) | New Mean (ms) | Base P99 (ms) | New P99 (ms) | Overall | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| resnet18.onnx | tensorrt | gpu | fp16 | 1 | 224x224 | 10 | 100 | 2.9544 | 2.8265 | 3.4980 | 2.8929 | improvement | same-precision compare, runtime provenance confirmed |
| yolov8n.onnx | tensorrt | gpu | fp16 | 1 | 640x640 | 10 | 50 | 14.2246 | 14.0697 | 14.7342 | 14.7342 | neutral | same-precision compare, runtime provenance confirmed |

> 참고:
> - 위 Jetson 표는 실제 `compare-latest` 결과와 structured result JSON 원문 확인을 기반으로 정리한 값입니다.
> - `runtime_artifact_path`는 각각 `models/resnet18.engine`, `models/yolov8n.engine`로 저장됨을 확인했습니다.

### Quick Takeaway

- Odroid M2 + YOLOv8n 기준 FP16 → INT8 전환 시 mean latency가 약 `22.764 ms → 15.403 ms`로 감소
- 같은 비교에서 `map50` 기준 accuracy 변화도 함께 추적 가능
- EdgeBench는 이런 실측 결과를 structured result로 흡수해 동일 compare/report 체계에서 재사용함
- Jetson TensorRT 실기 검증은 별도 structured result / compare / report evidence로 확보되었으며, 해당 서사는 README와 portfolio 문서에서 함께 정리됨

### Odroid RKNN Benchmarks

These entries are curated hardware validation results imported from documented Odroid RKNN experiments, separate from the CI-generated CPU benchmark tables above.


| Model | Engine | Device | Precision | Batch | Input(HxW) | Mean (ms) | P99 (ms) | mAP50 | F1 | Precision | Recall | Quantization | Preset | Source | Timestamp (UTC) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| YOLOv8n | rknn | odroid_m1 | fp16 | 1 | 640x640 | 34.812 | 39.457 | 0.621 | 0.588 | 0.641 | 0.543 | fp16 | default | odroid_report | 2026-04-13T00:00:00Z |
| YOLOv8n | rknn | odroid_m2 | fp16 | 1 | 640x640 | 22.764 | 25.118 | 0.621 | 0.588 | 0.641 | 0.543 | fp16 | default | odroid_report | 2026-04-13T00:05:00Z |
| YOLOv8n | rknn | odroid_m2 | int8 | 1 | 640x640 | 15.403 | 17.086 | 0.612 | 0.581 | 0.635 | 0.537 | hybrid_int8 | default | odroid_report | 2026-04-13T00:10:00Z |
| YOLOv8s | rknn | odroid_m2 | int8 | 1 | 640x640 | 24.917 | 27.844 | 0.671 | 0.624 | 0.689 | 0.585 | hybrid_int8 | default | odroid_report | 2026-04-13T00:15:00Z |

> 참고: 이 표는 RKNN runtime backend 직접 실행 결과가 아니라, 문서화된 Odroid 실측 결과를 curated import 방식으로 연결한 validation 데이터입니다.
