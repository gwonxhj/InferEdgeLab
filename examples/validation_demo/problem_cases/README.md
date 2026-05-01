# Validation Problem Demo Cases

These fixtures show how InferEdgeLab records uncomfortable validation evidence instead of hiding it.
They are intentionally small JSON reports and do not include raw images.

| Case | Signal | Reason |
|---|---|---|
| `annotation_missing_report.json` | review | Accuracy is skipped because annotation evidence is not provided. |
| `invalid_detection_structure_report.json` | blocked | Detection output contains invalid score/bbox structure. |
| `contract_shape_mismatch_report.json` | blocked | Runtime input shape does not match `model_contract.json`. |

These reports are portfolio fixtures, not production SaaS data.
