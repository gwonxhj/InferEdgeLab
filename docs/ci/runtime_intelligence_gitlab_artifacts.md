# Runtime Intelligence GitLab Artifact Template

## Scope

`ci/gitlab/runtime-intelligence-artifacts.yml` is an optional GitLab CI template for Runtime Intelligence artifact automation.

It is not installed as the repository root `.gitlab-ci.yml` and it does not replace the existing GitHub benchmark workflow. The template exists so a GitLab mirror or downstream workspace can reproduce the same local-first evidence chain without making GitLab a core InferEdge product surface.

## Evidence Chain

The template follows the current Runtime Intelligence handoff:

```text
test
-> benchmark smoke
-> EdgeEnv runtime regression fixture report
-> deterministic anomaly summary smoke with precomputed AIGuard evidence
-> portfolio evidence report
-> deployment risk gate
```

The same file-based chain can be reproduced locally without GitLab:

```bash
bash scripts/smoke_runtime_intelligence_chain.sh \
  --output-dir reports/runtime_intelligence_chain
```

The optional template uses the same smoke script in the final
`deployment-risk` stage so the GitLab artifact gate and the local reproduction
path validate the same file bundle.

This maps to the ecosystem ownership model:

- Runtime evidence stays additive and Lab-compatible.
- EdgeEnv remains the comparability-first regression evidence source.
- AIGuard remains an optional deterministic diagnosis provider.
- Lab owns the report and deployment decision surface.
- CI stores artifacts and applies deterministic gates; it does not become a production runtime control plane.

## Template Stages

The template keeps the roadmap stage names explicit:

1. `test`
2. `benchmark`
3. `telemetry`
4. `anomaly-analysis`
5. `report`
6. `deployment-risk`

## Artifact Contract

Expected artifacts are intentionally file-based and local-first:

- benchmark result JSON under `reports/*.json`
- `BENCHMARKS.md`
- Runtime Intelligence bundle manifest under `examples/runtime_intelligence_chain/bundle_manifest.json`
- EdgeEnv producer-side handoff manifest under `examples/runtime_intelligence_chain/edgeenv_lab_handoff_manifest.json`
- EdgeEnv telemetry history artifact under `examples/runtime_intelligence_chain/runtime_telemetry_history.json`
- Runtime Intelligence bundle manifest gate summary
- EdgeEnv regression Markdown / HTML report under `reports/runtime_intelligence_ci/`
- deterministic Runtime Intelligence summary Markdown / HTML with precomputed AIGuard runtime operation evidence
- remote dispatch starter runtime event summary rows derived from precomputed AIGuard evidence
- AIGuard EdgeEnv handoff alignment JSON / Markdown summary
- Runtime Intelligence artifact gate summary
- portfolio demo check JSON / Markdown
- deployment risk summary JSON
- Runtime Intelligence CI artifact gate summary

The template uses committed lightweight fixtures under `examples/edgeenv_regression/` and `examples/runtime_intelligence_chain/` for the Runtime Intelligence smoke. It does not require real device access, long-lived workers, remote execution, or cloud telemetry storage.

## Gate Policy

The initial gate is conservative:

- full pytest must pass
- benchmark smoke must complete
- Runtime Intelligence bundle manifest must preserve file paths and ownership boundaries
- Runtime Intelligence report must contain the required risk summary rows
- Runtime Intelligence report must preserve telemetry coverage gap markers such as
  `runtime_telemetry_field_gap` from the AIGuard evidence artifact
- AIGuard coverage evidence must preserve
  `telemetry_coverage_source=history_telemetry_coverage` and EdgeEnv history
  missing-field runs, so the artifact chain proves producer-side coverage
  summary reuse instead of downstream recomputation
- the preserved Orchestrator `edgeenv_mapping_hint` must keep
  `coverage_summary_owner=edgeenv`,
  `coverage_summary_path=runtime_telemetry_context.history.telemetry_coverage`,
  `operation_context_role=supplemental`, and the AIGuard evidence candidate
  hints for `runtime_queue_overload` and `runtime_thermal_instability`
- the preserved Orchestrator operation context must keep the producer markers
  `source_repository=InferEdgeOrchestrator`,
  `artifact_role=orchestrator-supplemental-operation-context`, and
  `producer_contract=inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1`
- the same Orchestrator context must keep the downstream guard-alignment marker
  `downstream_guard_alignment.producer_lineage_evidence_type=edgeenv_orchestrator_producer_lineage`,
  with Lab marked as the final decision owner
- the preserved Orchestrator operation context in the EdgeEnv handoff history
  must also keep device-local `candidate_context.producer` lineage, including
  device-local producer sources, per-task source/stage mappings, positive
  event/task counts, and `operation_context_role=supplemental`
- AIGuard coverage evidence raw context must preserve the same mapping hint, so
  CI catches loss of EdgeEnv/Orchestrator ownership markers before Lab report
  generation
- AIGuard coverage evidence raw context must also preserve the same
  Orchestrator producer markers, so the diagnostic artifact remains traceable
  to the Orchestrator feed without making AIGuard the producer or decision owner
- AIGuard raw context must preserve the downstream guard-alignment marker and
  the producer-lineage evidence must confirm the marker on candidate and
  missing-telemetry Orchestrator contexts
- AIGuard EdgeEnv handoff alignment must show the same
  `producer_lineage_guard_alignment_run_ids` on the EdgeEnv handoff summary and
  the AIGuard `edgeenv_orchestrator_producer_lineage` raw context
- AIGuard coverage evidence raw context must preserve Orchestrator producer
  markers and mapping hints for EdgeEnv history `missing_telemetry` entries
  when such context exists, while keeping the entry an evidence gap rather than
  successful Runtime telemetry
- Orchestrator candidate context must include `run_id`, `telemetry_source`,
  `operation`, and `resource`, so CI can catch incomplete handoffs without
  making Orchestrator a regression owner
- precomputed AIGuard evidence must remain report context, not the final decision owner
- Orchestrator context must remain supplemental evidence, not a comparability gate
- bundle source repository mapping must keep Runtime, EdgeEnv, Orchestrator,
  AIGuard, and Lab roles separated
- producer schema markers for EdgeEnv history, Orchestrator feed, and AIGuard
  diagnosis evidence must stay aligned with the committed smoke artifacts
- portfolio demo check status must be `pass`
- deployment risk summary status must be `pass`
- the final deployment-risk job must re-check the collected manifest/report
  gate summaries and Runtime Intelligence Risk Summary markers before passing
- the bundle manifest gate summary must include validated contract markers for
  source repository separation, producer schemas, Lab/EdgeEnv ownership, the
  Orchestrator supplemental mapping hint, AIGuard evidence candidates, and
  AIGuard raw-context preservation, including Runtime history seed
  `run_config` traceability evidence
- the optional EdgeEnv handoff input must keep `lab_bundle_alignment` metadata
  aligned with the Lab bundle manifest, while leaving `aiguard_guard_analysis`
  as an external AIGuard artifact
- the same handoff must declare `external_aiguard_required_evidence_types`, and
  the bundle gate verifies those requirements against the bundled
  `guard_analysis.evidence` type set
- if the handoff declares `optional_aiguard_evidence_types`, the bundle gate
  validates the known stale-drop labels (`stale_frame_risk` and
  `edgeenv_orchestrator_stale_drop_summary`) as optional context that remains
  separate from the required AIGuard evidence set
- the EdgeEnv handoff `runtime_telemetry_history` file must exist and preserve
  the EdgeEnv history schema, telemetry coverage summary, and Runtime history
  seed ownership markers
- the same handoff history may include runs with missing Runtime telemetry; the
  gate treats them as evidence gaps, but requires any preserved Orchestrator
  context on those entries to keep source repository, artifact role, producer
  contract, owner boundary flags, EdgeEnv mapping hints, device-local producer
  lineage, per-task source/stage mappings, and positive event counts intact

The bundle manifest gate is implemented by `scripts/check_runtime_intelligence_bundle_manifest.py`. It verifies that the bundle contains baseline/candidate Runtime results, EdgeEnv regression evidence, AIGuard guard evidence, and explicit owner/boundary metadata before Lab generates the report. In this template it also consumes `--edgeenv-handoff examples/runtime_intelligence_chain/edgeenv_lab_handoff_manifest.json` to verify EdgeEnv producer-side file/source/role/schema alignment.
The same gate now also checks `source_repositories`, `artifact_roles`,
`producer_contracts`, device-local producer lineage, and AIGuard's preserved
producer-lineage source/stage/count shape. It also requires the Orchestrator
downstream guard-alignment marker for `edgeenv_orchestrator_producer_lineage`
to remain present in EdgeEnv/AIGuard handoff context. It also requires AIGuard
`edgeenv_orchestrator_task_event_rollup`,
`edgeenv_orchestrator_operation_timeline_summary`,
`runtime_history_seed_run_config_traceability`, and
`remote_execution_recovered_by_fallback` evidence so the smoke remains a
cross-repo handoff fixture rather than a Lab-only report sample. When an
EdgeEnv handoff is provided, the gate also checks that
`external_aiguard_required_evidence_types` is satisfied by the external
AIGuard artifact.
The same manifest gate requires `expected_report_markers` to match the
Lab-owned Runtime Intelligence report contract before optional CI artifact
packaging runs. That marker set preserves `Runtime Intelligence Risk Summary`,
`Runtime replay duration scope`,
`Orchestrator operation feed context`, `EdgeEnv fixture matrix coverage`,
`Reviewer operation quick scan`,
`Orchestrator task event rollup`,
`Lab EdgeEnv preservation context`,
`AIGuard task event rollup evidence`,
`AIGuard operation risk rollup evidence`,
`AIGuard operation timeline evidence`,
`AIGuard runtime operation anomalies`,
`AIGuard remote dispatch event summary`,
`AIGuard remote event summary consistency`,
`Remote fallback starter evidence`,
`lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback`,
`AIGuard producer-lineage guard alignment`, and `Lab remains the final deployment decision owner.`.
The gate summary also emits
`expected_report_markers: EdgeEnv fixture matrix coverage row declared` and
`expected_report_markers: remote fallback Lab context row declared` so CI can
verify the row-value marker declaration from the bundle summary artifact.

The smoke also includes the precomputed AIGuard
`aiguard_edgeenv_handoff_alignment` artifact. That artifact verifies that the
EdgeEnv handoff summary and AIGuard deterministic evidence agree on
`edgeenv-smoke-candidate` and `edgeenv-smoke-missing` as the preserved
producer-lineage guard-alignment run IDs. This keeps the cross-repo marker
check file-based and does not make AIGuard a deployment decision owner.
The handoff gate also compares Orchestrator operation risk rollup and operation
timeline summary run IDs against the preserved EdgeEnv regression context, so
compact AIGuard operation evidence remains traceable to producer-side
Orchestrator context.

The artifact gate is implemented by `scripts/check_runtime_intelligence_artifact_bundle.py`. It checks the generated Markdown / HTML report for the required Runtime Intelligence rows, including the short `Review Path` section, the `Review path` note, the `Reviewer Focus` quick-scan table, Lab ownership, EdgeEnv comparability, `EdgeEnv fixture matrix coverage`, telemetry coverage-gap markers, Runtime replay duration scope with `source=entrypoint_requested_frames` traceability, Orchestrator operation feed context, the Lab-owned `Reviewer operation quick scan` row, compact queue/deadline/fallback operation markers with `max_total_queue_depth`, AIGuard max queue raw-context traceability, Orchestrator task event rollup, Lab EdgeEnv preservation context, Jetson/device-local preservation identity and detail labels, Orchestrator `operation_risk_summary` navigation context, AIGuard runtime operation anomalies, AIGuard `edgeenv_orchestrator_operation_risk_summary` evidence, AIGuard `edgeenv_orchestrator_operation_risk_rollup` evidence, AIGuard `edgeenv_orchestrator_task_event_rollup` evidence, AIGuard `edgeenv_orchestrator_operation_timeline_summary` evidence, remote dispatch starter event summary, `Remote fallback starter evidence`, `edgeenv_orchestrator_producer_lineage`, `runtime_history_seed_run_config_traceability`, `remote_execution_recovered_by_fallback`, and triggered deployment review rules.

The bundle manifest gate also checks the external AIGuard artifact before the
rendered report stage. In particular, `runtime_queue_overload` must preserve
`orchestrator_candidate_operation_max_total_queue_depth=7` in
`raw_context.edgeenv_regression`, so the Lab `max_total_queue_depth` report row
can be traced back to Orchestrator producer-side operation context. The report
now surfaces that check as `AIGuard max queue raw-context traceability`, keeping
the reviewer-facing row easy to identify in Markdown/HTML artifacts.
When that report gate passes, its summary now emits a
`Validated Duration Traceability` section with `duration_handoff_alignment`,
`duration_source: source=entrypoint_requested_frames`,
`duration_scope_label: scope_label=source=entrypoint_requested_frames`, and the
`short 96-frame-class replay (96 frames)` label. This is reviewer navigation
context for the Lab-owned report, not an AIGuard-owned marker decision.
The same report gate summary also emits `Validated Reviewer Focus` with
`reviewer_focus_operation_quick_scan: Reviewer Focus / Operation quick scan marker validated`,
so reviewers can confirm the promoted Lab quick-scan row from the compact gate
summary before opening the full Markdown/HTML report.
It also emits `Validated Review Path` with
`review_path_section: short Review Path section rendered`,
`review_path_fast_path: readable Review Path fast path rendered`,
`review_path: Reviewer Focus -> Detailed Evidence Rows guidance validated`,
and `review_path_artifact_gate_summary: artifact gate summary reference row validated`,
so the compact gate summary preserves the report reading order without making
CI the report owner or deployment decision owner.

The CI artifact gate is implemented by `scripts/check_runtime_intelligence_ci_artifacts.py`. It runs in the deployment-risk stage and verifies that the collected optional GitLab artifacts include the manifest gate summary, AIGuard handoff alignment artifact, report gate summary, Runtime Intelligence Risk Summary report, portfolio demo status, and the validated contract markers from the bundle manifest gate. This keeps the final CI gate file-based and deterministic without turning GitLab into a runtime control plane.
The final `runtime_intelligence_ci_artifact_gate_summary.md` also preserves the
report gate's `Validated Duration Traceability` section. It repeats
`duration_handoff_alignment`,
`duration_source: source=entrypoint_requested_frames`,
`duration_scope_label: scope_label=source=entrypoint_requested_frames`, and the
`short 96-frame-class replay (96 frames)` label so CI reviewers can confirm
duration handoff/source/scope alignment from the compact deployment-risk
summary before opening the full Lab report.
It also repeats the report gate's `Validated Reviewer Focus` section and the
`reviewer_focus_operation_quick_scan` marker, keeping the promoted
`Operation quick scan` row visible in CI artifacts without making CI a report
owner or runtime control plane.
The final CI summary also repeats `Validated Review Path`, the `review_path`
marker, the readable fast-path marker, and the artifact gate summary reference
marker, so reviewers can follow the same README -> Lab report -> gate-summary
reading order from the deployment-risk artifact.
The same CI artifact gate also checks the copied
`aiguard_edgeenv_handoff_alignment.json/.md` for Lab report marker context:
`lab_expected_report_markers` must match the Lab-owned Runtime Intelligence
report marker set, including the remote fallback row value marker
`lab=Remote fallback starter evidence; evidence=remote_execution_recovered_by_fallback`
and the `Reviewer operation quick scan` row marker,
`report_marker_context_role` must remain
`lab_report_contract_context`, and
`aiguard_validates_expected_report_markers` must remain `false`. This keeps
AIGuard as a deterministic external evidence provider while leaving report
marker enforcement to Lab's bundle/report gates.
The same alignment artifact also preserves
`optional_aiguard_evidence_types` as `read_only_optional_guard_context`. The CI
artifact gate checks `aiguard_validates_optional_evidence_as_required=false`,
records which optional stale-drop evidence labels are absent from the bundled
guard artifact, and keeps those absences out of the required evidence failure
path. A companion
`aiguard_edgeenv_handoff_alignment_optional_present.json/.md` fixture exercises
the same optional labels when they are present, proving the gate can record
`optional_guard_evidence_types_present` without promoting those labels to
required deployment-decision evidence.

Remote dispatch rows in this artifact chain are starter evidence only. The
gates require worker-selection, fallback recovery, event-count, consistency,
and `remote dispatch starter evidence only` boundary markers so the report can
prove the handoff without claiming production remote execution, secure tunnel
operation, long-lived workers, or cloud orchestration.

Future GitLab-specific gates may include latency regression thresholds, anomaly severity thresholds, thermal instability thresholds, and deployment risk thresholds, but only after the corresponding deterministic evidence is already represented in the artifact bundle.

## Boundary

This template is not:

- a production observability platform
- a cloud monitoring service
- a Kubernetes replacement
- a production runtime control plane
- a new InferEdge Intelligence repo
- an ML or forecasting pipeline

It is a reproducible artifact automation starter for the existing InferEdge Runtime Intelligence evidence chain.
