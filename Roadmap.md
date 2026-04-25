# InferEdgeLab Roadmap

## 📍 Project Status

InferEdgeLab is already usable as **a structured inference validation system with CLI, API, and CI integration**.

Today, the project already provides:

- [x] ONNX Runtime CPU support for structured profiling workflows
- [x] TensorRT Jetson validation flow with reusable compare and reporting outputs
- [x] RKNN curated validation import for real-device benchmark evidence
- [x] `compare`, `compare-latest`, and CI validation gate workflows that are already working end-to-end

---

## 🚀 Phase 1 – MVP (macOS / CPU) ✅ Completed

Goal:  
Establish a usable CLI workflow for ONNX model inspection and CPU-based inference benchmarking.

### Achieved Capabilities

- [x] Parse ONNX model structure for analysis
- [x] Quantify parameter counts
- [x] Inspect model file size
- [x] Estimate theoretical FLOPs
- [x] Measure CPU-based inference latency
- [x] Save reusable structured JSON benchmark results

---

## 🧠 Phase 2 – Engine Abstraction Layer 🟡 Partially Implemented

Goal:  
Generalize the runtime layer so multiple inference engines can share the same validation workflow.

### Achieved / Remaining Capabilities

- [x] Define a reusable engine base interface
- [x] Run the workflow on ONNX Runtime CPU backend
- [x] Validate a first working TensorRT Jetson path
- [ ] Complete RKNN runtime backend integration

---

## 📊 Phase 3 – Performance Analysis Expansion 🟡 Partially Implemented

Goal:  
Move from one-off execution timing to repeatable, statistics-based performance analysis.

### Achieved / Remaining Capabilities

- [x] Control warmup iterations for stable measurement
- [x] Benchmark across different batch sizes
- [x] Compute multi-run mean / p99 latency statistics
- [ ] Add memory usage measurement to the profiling workflow

---

## 🔥 Phase 4 – Advanced Edge Device Support 🟡 Partially Implemented

Goal:  
Make InferEdgeLab useful for real deployment decisions on actual edge hardware.

### Achieved / Remaining Capabilities

- [x] Support real Jetson GPU validation flow through TensorRT
- [x] Document Jetson TensorRT validation through a dedicated runbook
- [x] Reuse repeated profiling outputs through `compare-latest` and report generation
- [x] Preserve runtime provenance in structured results
- [x] Consume Jetson TensorRT latency results and add task-matched YOLOv8 detection accuracy through Lab enrichment and compare
- [x] Compare quantized models such as INT8 against higher-precision baselines
- [x] Interpret precision trade-offs through compare judgement
- [x] Import RKNN / Odroid curated hardware validation evidence
- [ ] Complete RKNN runtime backend integration
- [ ] Improve runtime robustness toward production-grade use

---

## 🧩 Phase 5 – Developer Experience and Product Surface ⬜ Future Extensions

Goal:  
Improve usability, discoverability, and expansion paths beyond the core CLI workflow.

### Achieved / Remaining Capabilities

- [x] Provide richer CLI presentation with Rich
- [x] Generate HTML benchmark and validation reports
- [x] Run automated benchmark / validation checks in CI
- [ ] Add a web dashboard mode

---

## ✅ Completed Scope Summary

- [x] Structured ONNX analysis, CPU profiling, and reusable JSON result generation
- [x] Engine abstraction with a working ONNX Runtime CPU backend
- [x] First validated TensorRT Jetson execution path
- [x] Jetson TensorRT repeated validation plus compare/report reuse documentation
- [x] Haeundae YOLOv8n TensorRT downstream accuracy enrichment and compare evidence
- [x] Warmup, batch, mean, and p99-based profiling workflow
- [x] Quantized compare and precision trade-off interpretation
- [x] Rich CLI output, HTML reports, and CI validation integration
- [x] RKNN curated hardware validation import
- [x] Service-layer and read-only API adapter structure for reuse beyond CLI-only flows

---

## 🧱 Partially Implemented Scope Summary

- [x] Jetson-oriented real-device validation path
- [x] Compare / compare-latest / report reuse on structured results
- [x] API-ready read-only adapter layer on top of reusable services
- [ ] Full RKNN runtime execution backend
- [ ] Memory profiling as part of validation output
- [ ] Production-grade runtime hardening

---

## 🔭 Future Direction

- [ ] Complete full RKNN runtime backend integration so curated and runtime validation share one end-to-end device workflow
- [ ] Evolve the current API adapter into a foundation for a web dashboard or SaaS-style validation surface
- [ ] Add memory profiling so deployment decisions are informed by both latency and resource pressure
- [ ] Explore multi-device distributed benchmarking for larger validation fleets and lab-scale experimentation
