![CI](https://github.com/gwonxhj/edgebench/actions/workflows/benchmarks.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

# InferEdgeLab

> InferEdgeLab is an edge AI inference validation CLI that turns raw benchmark results into structured, reproducible, and accuracy-aware deployment decisions across different runtimes and hardware.  
> InferEdgeLab turns benchmark runs into reproducible, comparable **deployment-ready validation evidence**.  
> Validated on real hardware: RKNN (Odroid M2) and TensorRT (Jetson)  
> Cross-precision benchmarking on RKNN showed up to **~51% latency reduction with INT8**, with structured comparison and `acceptable_tradeoff` classification across YOLOv8n/s/m

InferEdgeLab is designed for workflows where **latency, accuracy, and risk must be evaluated together**.

InferEdgeLab is a CLI-first validation system that treats benchmarking as a **continuous validation workflow**, not a one-off script.

Instead of a single latency number, InferEdgeLab answers:

- Is the new result actually faster under the **same conditions**?
- Is INT8 a valid trade-off or a **risky degradation**?
- Can benchmark results be **reused** in CI and reports?

---

## What InferEdgeLab Solves

### 1. Inconsistent Benchmark Comparisons

Most benchmark comparisons silently differ in batch size, input shape, or precision — leading to false improvements and missed regressions.

InferEdgeLab stores `run_config` and input shape as structured metadata and enforces **same-condition comparison**, explicitly separating `same-precision` and `cross-precision` semantics.

### 2. No Interpretation for Precision Trade-offs

Switching FP32 → INT8 changes both latency and accuracy, but most tools only show raw numbers.

InferEdgeLab computes latency delta + accuracy delta together and classifies the result:

- `acceptable_tradeoff`
- `caution_tradeoff`
- `risky_tradeoff`
- `severe_tradeoff`

### 3. Benchmark Results Are Not Reusable

Typical benchmarking is one-time execution with no structured storage.

InferEdgeLab saves all results as **structured JSON**, enabling `compare`, `compare-latest`, and `history-report` — reused across CLI, FastAPI, and CI pipelines.

---

## Architecture Snapshot

```
CLI / API → Service Layer → Structured Result → Compare / Report
```

**CLI Layer:** profile, compare, compare-latest, summarize, list-results, history-report, enrich, serve  
**Service Layer:** reusable validation logic  
**API Adapter Layer:** FastAPI read-only endpoints  
**Engine Layer:** ONNX Runtime CPU · TensorRT (Jetson) · RKNN (Odroid)

---

## Key Results (Real Hardware Validation)

InferEdgeLab was validated on real edge hardware using YOLOv8 models.

### Jetson TensorRT (Haeundae YOLOv8n)

Jetson TensorRT validation now includes an accuracy-aware Haeundae YOLOv8n FP16 vs FP32 comparison using a task-matched detection dataset.
FP16 measured `8.8819ms` mean / `13.7437ms` p99 with `0.8037` mAP@50, while FP32 measured `10.2869ms` mean / `18.1921ms` p99 with `0.8041` mAP@50.
FP16 is the selected deployment precision for this validation context because FP32 provides negligible accuracy gain while substantially worsening latency.

### Odroid M2 (RKNN)

| Model | Precision | Mean Latency (ms) | P99 (ms) | Observation |
|---|---|---:|---:|---|
| YOLOv8n | FP16 | 72.4430 | 79.1559 | enriched runtime baseline |
| YOLOv8n | INT8 | 35.5771 | 45.3868 | -50.89% latency, acceptable_tradeoff |
| YOLOv8s | FP16 | 85.8169 | 109.4198 | enriched runtime baseline |
| YOLOv8s | INT8 | 49.9623 | 58.6213 | -41.78% latency, acceptable_tradeoff |
| YOLOv8m | FP16 | 171.9906 | 192.6720 | enriched runtime baseline |
| YOLOv8m | INT8 | 87.8136 | 111.5943 | -48.94% latency, acceptable_tradeoff |

### Interpretation

- INT8 quantization provided **~42–51% latency improvement** on RK3588 NPU across YOLOv8n/s/m
- Initial cross-precision runtime comparison is classified as `tradeoff_faster`
- Before accuracy attachment, the same runtime pair is classified as `unknown_risk`
- After attaching detection accuracy payloads through `enrich-pair`, the runtime pairs for `yolov8n`, `yolov8s`, and `yolov8m` are all reinterpreted as `acceptable_tradeoff`
- Primary metric (`map50`) improved across all three enriched pairs:
  - `yolov8n`: `0.7791 → 0.7977` (**+1.86pp**)
  - `yolov8s`: `0.7840 → 0.8090` (**+2.50pp**)
  - `yolov8m`: `0.7856 → 0.7975` (**+1.19pp**)
- Some secondary metrics such as `map50_95`, `f1_score`, and `precision` may still decline, which shows why deployment decisions should be based on an explicitly chosen primary metric rather than a single raw speed number

> This workflow demonstrates how a latency-only benchmark can be transformed into an accuracy-aware deployment decision without re-running the full profiling process.

---

## Proven in Practice

Validated on real edge hardware:

| Scope | Status |
|---|---|
| ONNX Runtime CPU profiling + structured result | ✅ |
| Jetson TensorRT repeated validation + report reuse | ✅ |
| Jetson TensorRT Haeundae YOLOv8n accuracy-aware FP16 vs FP32 validation | ✅ |
| Odroid RKNN curated validation + cross-precision comparison | ✅ |
| Odroid RKNN enriched validation with accuracy-aware trade-off interpretation (`yolov8n/s/m`) | ✅ |
| FastAPI read-only adapter (service reuse) | ✅ |
| CI benchmark + validation gate | ✅ |

---

## Start Here

- [Benchmark reference table](BENCHMARKS.md)
- [Jetson TensorRT validation runbook](docs/validation/jetson_tensorrt_validation.md)
- [FastAPI API usage guide](docs/api/api_usage.md)
- [Portfolio design & architecture](docs/portfolio/edgebench_portfolio.md)
- [Project roadmap](Roadmap.md)

---

## 🚀 Quickstart (3-minute demo)

### Clone and install

```bash
git clone https://github.com/gwonxhj/edgebench.git
cd edgebench

pip install poetry
poetry install
```

### Generate a toy model

```bash
poetry run python scripts/make_toy_model.py \
  --height 224 \
  --width 224 \
  --out models/toy224.onnx
```

### Profile

```bash
poetry run inferedgelab profile models/toy224.onnx \
  --warmup 10 \
  --runs 50 \
  --batch 1 \
  --height 224 \
  --width 224
```

### Compare

```bash
poetry run inferedgelab compare-latest \
  --model toy224.onnx \
  --engine onnxruntime \
  --device cpu
```

**Core workflow:**

```
profile → structured result → compare → report / CI
```

---

## API Server Usage

### Run server

```bash
poetry run inferedgelab serve --host 127.0.0.1 --port 8000
```

### Health check

```bash
curl "http://127.0.0.1:8000/health"
```

### Endpoints

- `/health`
- `/api/list-results`
- `/api/summarize`
- `/api/history-report`
- `/api/compare`
- `/api/compare-latest`

More details: [FastAPI API usage guide](docs/api/api_usage.md)

---

## CI / Benchmarks

InferEdgeLab integrates benchmarking into CI:

- structured result reuse
- compare-based regression detection
- `compare-latest` automation
- CI validation gate
- benchmark evidence tracking

### Auto-Generated Benchmark Summary

<!-- EDGE_BENCH:START -->

> No auto-generated report summaries are available yet.

<!-- EDGE_BENCH:END -->

See: [Benchmark reference table](BENCHMARKS.md) · [Project roadmap](Roadmap.md)

---

## License

MIT License
