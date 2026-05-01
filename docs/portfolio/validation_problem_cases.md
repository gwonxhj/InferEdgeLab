# Validation Problem Cases

InferEdge does not hide validation failures. These fixtures show how the Lab evidence layer records cases that need review or should be blocked.

## Cases

| Case | Decision Signal | What It Demonstrates |
|---|---|---|
| annotation missing | review | Accuracy is intentionally skipped when annotation evidence is unavailable. |
| invalid detection structure | blocked | Score/bbox structural checks can block malformed detection output. |
| contract shape mismatch | blocked | Runtime input shape must match the declared `model_contract.json`. |
| latency regression | review_required | Same backend/run_config latency regression can force deployment review even when the result is structurally valid. |

## Files

- `examples/validation_demo/problem_cases/annotation_missing_report.json`
- `examples/validation_demo/problem_cases/invalid_detection_structure_report.json`
- `examples/validation_demo/problem_cases/contract_shape_mismatch_report.json`
- `examples/studio_demo/normal_baseline_result.json`
- `examples/studio_demo/latency_regression_result.json`
- `examples/studio_demo/latency_regression_summary.json`

## Interpretation

These are deliberately small report fixtures, not production SaaS records.
They make the portfolio story clearer: InferEdge is a contract/preset validation pipeline, so missing annotations, malformed outputs, contract mismatches, and latency regressions are explicit evidence states.

Local Studio includes these problem cases in the `Load Demo Evidence` flow so the browser demo can show both the happy path and the review/block paths. The latency regression case intentionally compares the same TensorRT Jetson FP16 backend and run configuration so the review signal is about performance regression, not a backend mismatch.
