# EdgeBench

> Edge AI Inference Profiling Framework  
> ONNX 모델의 구조 분석과 실제 추론 성능을 정량화하는 개발자용 벤치마크 도구

---

## 📌 프로젝트 개요

EdgeBench는 엣지 환경에서 AI 모델을 배포하기 전에  
모델의 구조적 특성과 실제 추론 성능을 분석하기 위한 CLI 기반 도구입니다.

정확도(Accuracy)만으로는 모델의 배포 가능성을 판단할 수 없습니다.

EdgeBench는 다음을 제공합니다:

- 모델 파라미터 수 계산
- 모델 파일 크기 확인
- FLOPs 추정
- CPU 기반 실제 추론 latency 측정
- JSON 형태의 정량 리포트 출력

---

## ⚡ 핵심 기능

EdgeBench는 단순한 벤치마크 도구가 아니라  
**모델 성능을 정량적으로 비교·추적하는 시스템**입니다.

- 📊 Static Analysis  
  - Parameters, FLOPs, Model size 분석

- ⚡ Runtime Profiling  
  - ONNX Runtime 기반 실제 latency 측정 (mean / p99)

- 🧱 Structured Result System  
  - 모든 결과를 JSON 스키마로 저장
  - 이후 비교 및 리포트 생성 가능

- 🔍 Result Comparison  
  - 두 실행 결과를 자동 비교 (delta / % 변화)
  - regression / improvement 판단

- 📄 Report Generation  
  - Markdown / HTML 리포트 자동 생성

- 🤖 CI Benchmark Pipeline  
  - PR마다 자동 벤치마크 실행
  - 성능 회귀(regression) 자동 감지

---

## 🎯 왜 필요한가?

Jetson, RK3588, CPU-only 환경과 같은 엣지 디바이스에서는  
모델의 정확도보다 다음 요소가 더 중요합니다:

- 실시간 처리 가능 여부
- 연산량
- 메모리 요구량
- 실제 추론 지연 시간

EdgeBench는 이러한 정보를 하나의 CLI 인터페이스에서 통합 제공합니다.

---

## 🧠 아키텍처

CLI 기반 구조:

- Analyzer: 정적 모델 분석
- Profiler: 동적 추론 성능 측정
- Engine Interface: 추론 엔진 추상화 계층

현재 지원:
- ONNX Runtime CPU

향후 확장 예정:
- TensorRT
- RKNN
- Jetson CUDA Backend
- C++ 추론 엔진

---

## 🧱 Structured Result System

EdgeBench는 모든 벤치마크 결과를 다음과 같은 구조로 저장합니다:

- model / engine / device
- input shape (batch, height, width)
- latency (mean, p99)
- system info (OS, CPU, Python)
- run config (threads, warmup, runs)

이 구조를 기반으로:

- 결과 비교 (compare)
- 리포트 생성 (markdown / html)
- CI 성능 추적

이 가능합니다.

---

## 📊 Comparison & Report

EdgeBench는 두 실행 결과를 자동으로 비교합니다:

- latency delta 계산
- percentage 변화
- regression / improvement 판별

또한 결과를 다음 형태로 출력할 수 있습니다:

- CLI 표 (rich)
- Markdown 리포트
- HTML 리포트

---

## 🛠 향후 확장 계획

- TensorRT backend
- RKNN (NPU) 지원
- Jetson GPU inference
- multi-device benchmark 비교
- visualization dashboard

---

## 🖥 CLI 사용 예시

### 1. 모델 성능 측정

```bash
edgebench profile model.onnx \
  --warmup 10 \
  --runs 300 \
  --batch 1 \
  --height 320 --width 320
```

---

### 2. 최근 결과 비교
`edgebench compare-latest`

---

### 3. 두 결과 직접 비교
`edgebench compare result_a.json result_b.json`

---

### 4. 결과 목록 확인
`edgebench list-results`

---

## 🗺 개발 로드맵

자세한 계획은 Roadmap.md 참고

---

## 🤖 CI Benchmark & Regression Guard

EdgeBench는 CI 환경에서 자동으로:

1. 모델 생성 및 profiling 수행
2. 결과를 artifact로 저장
3. baseline과 비교하여 성능 변화 분석

- regression 허용 범위 설정 가능
- PR 단계에서 성능 저하 자동 차단

이를 통해 모델 성능을 지속적으로 추적할 수 있습니다.

---

## 📈 Benchmarks

EdgeBench는 정적 지표(FLOPs, Parameters)와 동적 지표(Latency)를 하나의 리포트 스키마로 통합 제공합니다.

> 환경: GitHub Codespaces (Linux x86_64), ONNX Runtime CPU  
> 설정: warmup=10, intra_threads=1, inter_threads=1

---

### 🔄 Auto-Generated Benchmark Results
> 아래 표는 'make demo' 또는 CI 실행 시 자동 갱신됩니다.

<!-- EDGE_BENCH:START -->

| Model | Engine | Device | Batch | Input(HxW) | FLOPs | Mean (ms) | P99 (ms) | Timestamp (UTC) |
|---|---|---:|---:|---:|---:|---:|---:|---|
| toy224.onnx | onnxruntime | cpu | 1 | 224x224 | 126,444,160 | 0.450 | 0.488 | 2026-02-27T07:05:49Z |
| toy320.onnx | onnxruntime | cpu | 1 | 320x320 | 258,048,640 | 0.908 | 0.943 | 2026-02-27T07:05:50Z |
| toy640.onnx | onnxruntime | cpu | 1 | 640x640 | 1,032,192,640 | 4.250 | 5.423 | 2026-02-27T07:05:53Z |

<!-- EDGE_BENCH:END -->

> 전체 히스토리(raw)는 BENCHMARKS.md 참고

---

## 📜 License

MIT License

---


