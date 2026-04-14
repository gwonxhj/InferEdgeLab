# Jetson TensorRT Validation Examples

이 디렉토리는 Jetson 디바이스에서 실행한 실제 검증 결과(artifact)를 저장하기 위한 공간입니다.

## 📦 예정된 결과 파일

- resnet18_tensorrt_latest.md
- resnet18_tensorrt_latest.html
- yolov8n_tensorrt_latest.md
- yolov8n_tensorrt_latest.html

## ⚙️ 생성 방법

아래 스크립트를 통해 생성됩니다:

scripts/run_jetson_tensorrt_validation.py

## 📊 포함 내용

- structured benchmark comparison (구조화된 벤치마크 비교 결과)
- latency metrics (지연 시간 지표)
- accuracy comparison (정확도 비교, 존재할 경우)
- trade-off analysis (성능-정확도 트레이드오프 분석)

> 이 결과들은 실제 Edge 디바이스(Jetson) 환경에서의 추론 성능을 검증하기 위한 목적을 가집니다.