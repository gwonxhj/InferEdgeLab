## Same-Precision Gate: toy224.onnx

- Status: ✅ **passed**
- Selection mode: `same_precision`
- Overall: **neutral**
- Trade-off risk: **not_applicable**
- Base candidate: `toy224.onnx / onnxruntime / cpu / b1 / h0 / w0 / fp32 / 20260325-075644`
- New candidate: `toy224.onnx / onnxruntime / cpu / b1 / h0 / w0 / fp32 / 20260325-082431`

**Summary**: Some latency metrics are missing, so the comparison result is partially inconclusive. Accuracy delta: +0.00pp.

### Notes

- This is a same-precision comparison, so latency deltas are more suitable for regression tracking.
- Accuracy data is available and is compared using top1_accuracy with percentage-point deltas.
- Accuracy delta (new - base): +0.00pp.
- The new result shows no strong accuracy change.

