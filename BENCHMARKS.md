# Benchmarks

> 현재 이 문서에는 curated hardware validation 결과가 먼저 정리되어 있습니다.
> CI / auto-generated benchmark summary가 생성되면 동일 문서에 함께 누적됩니다.

이 문서는 CPU auto-generated benchmark 요약과 curated hardware validation 데이터를 함께 관리하는 용도입니다.
Jetson TensorRT 실기 검증 evidence는 README와 portfolio 문서에서 서술형으로 정리하고,
이 파일은 표 중심의 benchmark reference 역할에 집중합니다.

## Curated Hardware Validation

이 섹션은 실제 Odroid RKNN 실험에서 확보한 대표 결과를 EdgeBench result schema로 정리한 표입니다.
즉, 단순 보고서용 표가 아니라 이후 `compare`, `compare-latest`, report workflow에 재사용되는 validation evidence입니다.

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
