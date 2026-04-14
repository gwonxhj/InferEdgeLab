# EdgeBench Roadmap

## 🚀 Phase 1 – MVP (macOS, CPU 기반) ✅ (Completed)

목표:  
CLI 환경에서 ONNX 모델의 구조 분석과 CPU 기반 추론 성능을 정량적으로 측정할 수 있는 최소 기능 구현

### 구현 항목

- [x] ONNX 모델 구조 파싱
- [x] 파라미터 수 계산
- [x] 모델 파일 크기 분석
- [x] FLOPs 추정 (이론적 연산량 계산)
- [x] CPU 기반 추론 latency 벤치마크
- [x] structured JSON result 저장

---

## 🧠 Phase 2 – 엔진 추상화 계층 설계 🟡 In Progress

목표:  
추론 엔진을 교체 가능하도록 구조를 일반화

### 구현 항목

- [x] Engine Base Interface 정의
- [x] ONNX Runtime CPU 백엔드 구현
- [x] TensorRT Jetson first working path
- [ ] RKNN runtime backend 구현

---

## 📊 Phase 3 – 성능 분석 확장 🟡 In Progress

목표:  
단일 실행 결과가 아닌 통계 기반 성능 분석 제공

### 구현 항목

- [x] Warmup 반복 횟수 제어
- [x] Batch size별 벤치마크 기능
- [x] 다중 실행 기반 mean / p99 통계 계산
- [ ] 메모리 사용량 측정

---

## 🔥 Phase 4 – 고급 엣지 디바이스 지원 🟡 In Progress (Jetson validation ongoing)

목표:  
실제 엣지 환경에서의 성능 비교 및 최적화 분석

### 구현 항목

- [x] Jetson GPU 실측 검증 경로 지원 (TensorRT Jetson first working path)
- [x] Jetson TensorRT validation runbook 문서화
- [x] repeated profiling / compare-latest / report 재사용 검증
- [x] 양자화 모델(INT8 등) 성능 비교
- [x] precision trade-off 분석 및 compare judgement
- [x] RKNN / Odroid curated hardware validation result import
- [ ] RKNN runtime backend 구현
- [ ] production-grade runtime robustness polish

---

## 🧩 Phase 5 – 개발자 경험(Developer Experience) 강화 ⬜ Planned

목표:  
도구의 사용성 향상 및 브랜딩 확장

### 구현 항목

- [x] Rich 기반 CLI UI 개선
- [x] HTML 성능 리포트 생성 기능
- [x] CI 기반 자동 벤치마크 / validation 시스템
- [ ] Web Dashboard 모드

---

## ✅ 현재 완료된 범위 요약

- [x] ONNX model parsing / params / file size / FLOPs / CPU profiling / structured JSON result
- [x] Engine base / ONNX Runtime CPU backend
- [x] TensorRT Jetson first working path
- [x] Jetson TensorRT repeated validation + compare/report reuse documentation
- [x] warmup / batch / mean / p99 기반 profiling
- [x] quantized compare / precision trade-off analysis
- [x] Rich CLI / HTML report / CI benchmark system
- [x] RKNN curated hardware validation result import

## ⏳ 아직 남은 항목 요약

- [ ] memory usage measurement
- [ ] RKNN runtime backend implementation
- [ ] Web Dashboard mode
- [ ] production-grade runtime robustness polish
