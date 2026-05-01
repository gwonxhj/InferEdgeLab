# Validation Problem Cases

InferEdge does not hide validation failures. These fixtures show how the Lab evidence layer records cases that need review or should be blocked.

## Cases

| Case | Decision Signal | What It Demonstrates |
|---|---|---|
| annotation missing | review | Accuracy is intentionally skipped when annotation evidence is unavailable. |
| invalid detection structure | blocked | Score/bbox structural checks can block malformed detection output. |
| contract shape mismatch | blocked | Runtime input shape must match the declared `model_contract.json`. |

## Files

- `examples/validation_demo/problem_cases/annotation_missing_report.json`
- `examples/validation_demo/problem_cases/invalid_detection_structure_report.json`
- `examples/validation_demo/problem_cases/contract_shape_mismatch_report.json`

## Interpretation

These are deliberately small report fixtures, not production SaaS records.
They make the portfolio story clearer: InferEdge is a contract/preset validation pipeline, so missing annotations, malformed outputs, and contract mismatches are explicit evidence states.

Local Studio includes these problem cases in the `Load Demo Evidence` flow so the browser demo can show both the happy path and the review/block paths.
