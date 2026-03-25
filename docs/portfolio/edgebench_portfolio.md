## 📌 프로젝트 개요

EdgeBench는 ONNX 기반 모델의 추론 성능을 분석하고,  
그 결과를 구조화하여 비교·추적·리포트화할 수 있는 CLI 기반 벤치마크 시스템입니다.

단순한 1회성 벤치마크가 아니라,  
지속적인 성능 추적과 회귀(regression) 감지, 그리고 precision-aware 비교 해석이 가능하도록 설계되었습니다.

- Static analysis (Parameters, FLOPs)
- Runtime profiling (mean / p99 latency)
- Structured result 저장
- same-precision / cross-precision 비교
- 최신 comparable pair 자동 선택
- HTML / Markdown 리포트 생성
- CI 기반 성능 검증

---

## 🎯 문제 정의

Edge 환경에서는 모델의 accuracy보다 latency와 리소스 사용량이 더 중요한 지표입니다.

하지만 기존 방식은 다음과 같은 문제가 있었습니다:

- 벤치마크 결과가 일회성으로 끝남
- 이전 결과와 비교가 어려움
- 성능 변화 추적이 불가능
- CI 환경에서 자동 검증이 어려움

즉, "지속적으로 성능을 관리할 수 있는 구조"가 부족했습니다.

---

## ⚠️ 기존 방식의 한계

일반적인 벤치마크 방식은 다음과 같습니다:

- 모델 실행 → latency 측정 → 결과 출력

이 방식은 다음 문제를 가집니다:

- 결과 저장 구조가 없음
- 비교 기준이 없음
- 성능 개선 여부 판단 불가
- regression 발생 시 감지 불가능

결과적으로, 모델 성능 관리가 수작업에 의존하게 됩니다.

---

## 🧠 해결 방법

이 문제를 해결하기 위해 다음과 같은 시스템을 설계했습니다:

1. 모든 benchmark 결과를 structured JSON 형태로 저장
2. model / engine / device / shape / precision 정보를 기준으로 comparable result를 식별
3. same-precision 비교와 cross-precision 비교를 분리하여 해석
4. latency 변화량(delta, %) 계산
5. 최신 comparable pair 자동 선택 (`compare-latest`)
6. history 기반 성능 추세 추적
7. HTML / Markdown 리포트 자동 생성
8. CI에서 regression 자동 감지

이를 통해 단순 벤치마크가 아닌
**지속적인 성능 관리와 precision trade-off 해석이 가능한 benchmarking system** 을 구축했습니다.

---

## 🧩 시스템 아키텍처

### 전체 처리 흐름

```mermaid
flowchart LR
    A[ONNX Model] --> B[Analyzer]
    A --> C[Profiler]

    B --> D[Static Analysis Result<br/>params / FLOPs / model size]
    C --> E[Runtime Profile Result<br/>mean / p99 latency]

    D --> F[Structured Result JSON]
    E --> F

    F --> G[Result Loader]
    G --> H[Comparator]
    G --> I[History Tracker]

    H --> J[Compare Report<br/>CLI / Markdown / HTML]
    I --> K[History Report<br/>Trend Chart / Markdown / HTML]

    F --> L[CI Regression Guard]
```

### CLI 중심 모듈 구조

```mermaid
flowchart TB
    CLI[Typer CLI] --> AnalyzeCmd[analyze]
    CLI --> ProfileCmd[profile]
    CLI --> CompareCmd[compare]
    CLI --> CompareLatestCmd[compare-latest]
    CLI --> ListResultsCmd[list-results]
    CLI --> HistoryReportCmd[history-report]

    AnalyzeCmd --> Analyzer
    ProfileCmd --> Profiler
    ProfileCmd --> ResultSaver[Structured Result Saver]

    CompareCmd --> Loader
    CompareLatestCmd --> Loader
    ListResultsCmd --> Loader
    HistoryReportCmd --> Loader

    Loader --> Comparator
    Loader --> HistoryTracker

    Comparator --> CompareMD[Markdown Generator]
    Comparator --> CompareHTML[HTML Generator]

    HistoryTracker --> HistoryMD[History Markdown Generator]
    HistoryTracker --> HistoryHTML[History HTML Generator]
```

- Analyzer: 모델 구조 분석 (FLOPs, params)
- Profiler: 실제 추론 latency 측정
- Result Loader: structured 결과 로딩 및 정렬
- Comparator: 두 결과 비교 및 delta 계산
- History Tracker: 과거 결과 기반 추세 분석
- Report Generator:
  - HTML (시각화)
  - Markdown (문서화)
- CLI Interface (Typer)

전체 흐름:

Profile -> JSON 저장 -> Compare -> History -> Report -> CI 검증

---

## 🔧 핵심 기술 포인트

- ONNX Runtime 기반 추론 성능 측정
- structured result schema 설계 (`model / engine / device / precision / shape / latency / system / run config`)
- CLI 인터페이스 설계 (Typer)
- HTML report generation (trend visualization / compare report)
- Markdown report generation (CI 활용 / compare report)
- 결과 비교 알고리즘 (delta / % 계산)
- 동일 조건 자동 매칭 (model / engine / device / precision / shape)
- latest comparable pair 자동 선택 로직
- same-precision regression semantics / cross-precision trade-off semantics 분리
- Github Actions 기반 regression guard

---

## 📈 결과 및 성과

기존:

- 단일 실행 기반 벤치마크
- 이전 결과와의 비교가 수작업에 의존
- precision 차이에 따른 비교 해석 기준이 없음

개선 후:

- 성능을 지속적으로 추적 가능한 시스템 구축
- latency 변화 자동 분석
- regression 자동 감지 가능
- same-precision regression tracking 지원
- cross-precision trade-off comparison 지원
- 최신 comparable pair 자동 선택 기능 구현
- CI 기반 성능 검증 파이프라인 구축

결과적으로:

> 모델 성능을 단순 측정하는 수준을 넘어,
> **비교·추적·해석까지 가능한 benchmarking workflow** 를 구현했습니다.

---

## 💡 배운 점

- 단순 기능 구현보다 "데이터 흐름 설계"가 중요하다는 것을 경험
- inference 성능은 단일 지표가 아니라 추세와 비교 맥락으로 봐야 한다는 점 이해
- same-condition regression과 precision trade-off comparison은 해석 용어부터 달라야 한다는 점 학습
- CLI UX와 개발자 경험(DevEx)의 중요성 체감
- CI와 결합했을 때 시스템의 가치가 크게 증가한다는 점 확인