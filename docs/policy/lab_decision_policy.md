# InferEdgeLab Decision Policy

Policy version: `inferedge-lab-decision-policy-v1`

This document is the reviewer-facing reference for the Lab-owned
`deployment_decision` surface. It explains why a comparison is marked
`deployable`, `deployable_with_note`, `review_required`, `blocked`, or
`unknown` without changing the existing compare, Runtime result, or AIGuard
contracts.

## Scope

InferEdgeLab owns the final deployment decision. Forge and Runtime provide
provenance and execution evidence, and AIGuard provides optional deterministic
diagnosis evidence. AIGuard, EdgeEnv, Orchestrator, and CI artifacts can add
context, but they do not replace Lab policy ownership.

## Decision Trace Fields

Every Lab deployment decision includes:

- `policy_version`: the policy identifier used to produce the decision.
- `triggered_rules`: compact rule IDs explaining which evidence paths affected
  the decision.
- `policy_summary`: reviewer-facing rule effects and descriptions for each
  triggered rule.

These fields are additive policy trace metadata. They do not remove or rename
existing deployment decision fields.

## Rule Table

| Rule | Effect | Description |
|---|---|---|
| `guard_error_block` | `blocked` | AIGuard reported error-level diagnosis evidence. |
| `guard_warning_review` | `review_required` | AIGuard reported warning-level diagnosis evidence. |
| `guard_skipped_unknown` | `unknown` | AIGuard was skipped, so diagnosis evidence is incomplete. |
| `guard_unavailable_unknown` | `unknown` | AIGuard evidence is unavailable for this comparison. |
| `guard_ok_lab_favorable_deployable` | `deployable` | Lab comparison is favorable and AIGuard passed. |
| `guard_ok_lab_neutral_deployable_note` | `deployable_with_note` | Lab comparison is neutral and AIGuard passed. |
| `guard_ok_lab_unfavorable_review` | `review_required` | Lab comparison indicates regression or mismatch despite AIGuard passing. |
| `guard_ok_lab_unknown` | `unknown` | Lab comparison judgement is not recognized by the decision policy. |
| `guard_status_unrecognized_unknown` | `unknown` | AIGuard status is not recognized by the decision policy. |
| `shape_mismatch_review` | `review_required` | Input shape mismatch requires explicit deployment review. |
| `system_mismatch_unfavorable_review` | `review_required` | System mismatch combined with unfavorable Lab judgement requires review. |
| `system_mismatch_note` | `deployable_with_note` | System mismatch reduces confidence and must be noted in release evidence. |
| `tradeoff_risk_review` | `review_required` | Latency/accuracy trade-off risk requires deployment review. |
| `worker_uncompared_unknown` | `unknown` | Worker result has not been compared by Lab yet. |
| `edgeenv_runtime_regression_review` | `review_required` | EdgeEnv same-condition runtime regression evidence requires review. |

## Reviewer Interpretation

- `blocked` means deployment should not proceed until the blocking evidence is
  resolved.
- `review_required` means a human reviewer should inspect the cited Lab,
  AIGuard, EdgeEnv, or contract evidence before deployment.
- `deployable_with_note` means deployment can proceed only with the noted
  evidence retained in the release record.
- `unknown` means Lab does not have enough compatible evidence to make a
  confident deployment call.

## Boundaries

- This policy does not mutate `metadata.json`, `manifest.json`, Runtime
  `result.json`, compare output, or AIGuard `guard_analysis`.
- This policy does not make AIGuard, EdgeEnv, Orchestrator, or CI the final
  deployment decision owner.
- This policy is local-first validation evidence. It is not a production SaaS
  approval workflow, cloud control plane, or model zoo automation policy.
