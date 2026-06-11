# InferEdge Local Studio Demo Walkthrough

Language: English | [한국어](local_studio_demo_walkthrough.ko.md)

Use this walkthrough when reviewing InferEdge through the local browser UI. It keeps the demo focused on committed evidence, role-specific talking points, and Lab-owned decision boundaries.

## Demo Boundary

Local Studio is a local-first workflow UI. It replays committed evidence and inspects API/job/report contracts on the user's machine.

It is not a production SaaS dashboard, cloud control plane, production worker service, or production remote execution proof.

## Run The Demo

```bash
poetry run inferedgelab serve --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000/studio`, then click `Load Demo Evidence`.

The stable browser path loads:

- ONNX Runtime CPU FP32 baseline fixture from `examples/studio_demo`
- TensorRT Jetson FP16 25W candidate fixture from `examples/studio_demo`
- Jetson 15W/25W power-mode context
- validation problem cases for review/block paths
- optional AIGuard portfolio evidence when available

## Review Order

1. Start with the TensorRT Jetson vs ONNX Runtime comparison.
2. Confirm the demo pair uses committed fixtures and does not require a live Jetson device.
3. Open the Lab-owned deployment decision context.
4. Use the problem cases to show that missing annotations, invalid structures, contract mismatch, and latency regression become explicit review/block evidence.
5. For Runtime Intelligence, pivot to the report path rather than treating Studio as a live observability dashboard.

## Evidence To Quote

| Evidence | Value |
|---|---:|
| ONNX Runtime CPU FP32 mean | `45.4299 ms` |
| ONNX Runtime CPU FP32 p99 | `49.2128 ms` |
| ONNX Runtime CPU FP32 FPS | `22.0119` |
| TensorRT Jetson FP16 25W mean | `10.066401 ms` |
| TensorRT Jetson FP16 25W p99 | `15.548438 ms` |
| TensorRT Jetson FP16 25W FPS | `99.340373` |
| Studio demo speedup | about `4.51x` |

Interpret the pair as deployment review evidence across backend/device/precision context, not same-condition regression.

## Runtime Intelligence Hand-Off

When the walkthrough moves from browser evidence to Runtime Intelligence, use the Lab-owned report chain:

```text
InferEdgeOrchestrator operation feed / operation_risk_rollup
-> InferEdgeEnv telemetry history / comparability-first regression context
-> optional InferEdgeAIGuard deterministic runtime evidence
-> InferEdgeLab Runtime Intelligence Risk Summary / deployment risk report
```

Point reviewers to:

- [EdgeEnv runtime regression Lab handoff](edgeenv_runtime_regression_lab_handoff.md)
- [Resume/interview summary](inferedge_resume_interview_summary.md)
- [Pipeline status](inferedge_pipeline_status.md)

The key sentence is: Orchestrator, EdgeEnv, and AIGuard provide evidence; Lab remains the final deployment decision owner.

## Role-Specific Route

| Role | Show first | Say clearly |
|---|---|---|
| AI Inference Engineer | Runtime comparison, latency/p99/FPS, compare identity | This is provenance-aware inference validation, not only a benchmark. |
| Embedded / Edge Engineer | Jetson FP16 25W/15W evidence and device-local preservation context | The demo can be replayed without live hardware; new live evidence still requires the device. |
| Backend / AI Platform | API/job/report contract, worker boundary, Lab decision context | This is contract and evidence orchestration, not DB/queue/auth/billing production SaaS. |

## Avoid Saying

- "production SaaS is complete"
- "Local Studio is a cloud dashboard"
- "Runtime Intelligence is production observability"
- "remote dispatch proves production remote execution"
- "AIGuard or Orchestrator owns the final deployment decision"
- "the Studio pair is same-condition regression"

## CLI Checks

Use these checks when the browser is not needed:

```bash
poetry run inferedgelab demo-evidence-summary
poetry run inferedgelab portfolio-demo-check
poetry run inferedgelab export-demo-evidence --output reports/studio_demo_evidence.md
```

`portfolio-demo-check` is the quick guard for committed Studio fixtures, README metrics, portfolio docs, and local Studio assets.
