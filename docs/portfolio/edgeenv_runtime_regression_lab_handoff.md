# EdgeEnv Runtime Regression Lab Handoff

## Scope

This smoke fixes the handoff between InferEdgeEnv and InferEdgeLab:

```text
EdgeEnv runtime regression report
-> Lab compare --edgeenv-regression
-> Runtime Regression Evidence section
-> Runtime Telemetry Context subsection when EdgeEnv provides telemetry history context
-> optional AIGuard deterministic runtime regression diagnosis when --with-guard is enabled
-> Lab-owned deployment decision
```

EdgeEnv remains the local-first evidence registry, comparability checker, and runtime regression evidence source. Lab remains the validation/report/deployment decision owner.
AIGuard remains optional deterministic diagnosis evidence: it may explain runtime regression evidence, but it does not recompute EdgeEnv comparability and does not own the final deployment decision.

## Runtime Intelligence Evidence Chain

The current Runtime Intelligence handoff keeps the same ownership model while adding operation context from Orchestrator through EdgeEnv:

```text
Orchestrator edgeenv_runtime_telemetry_feed
-> EdgeEnv runtime telemetry history / regression context
-> AIGuard deterministic runtime anomaly evidence
-> Lab Runtime Intelligence Risk Summary
-> Lab-owned deployment risk report
```

Expected ownership:

- Orchestrator provides supplemental queue, deadline, fallback, thermal, and resource context. It does not make a deployment decision.
- EdgeEnv preserves that context as `orchestrator_operation_context` inside the runtime telemetry context and keeps comparability-first regression ownership.
- EdgeEnv handoff smoke requires preserved device-local `candidate_context.producer` lineage for Orchestrator context so producer/source/stage ownership survives replay.
- AIGuard may translate the nested operation context into deterministic evidence such as `runtime_queue_overload` or `runtime_thermal_instability`.
- Lab displays the combined evidence in the Runtime Intelligence Risk Summary and keeps the final deployment decision policy.

This makes the portfolio chain stronger without turning Lab into a production observability dashboard or making Orchestrator/AIGuard final decision owners.

## Fixture

Committed lightweight fixtures:

- `examples/edgeenv_regression/lab_baseline_result.json`
- `examples/edgeenv_regression/lab_candidate_result.json`
- `examples/edgeenv_regression/edgeenv_runtime_regression.json`

The EdgeEnv report fixture represents a same-condition runtime regression:

- `comparable: true`
- `mode: same-condition`
- `regression_detected: true`
- `regression_type: mixed`
- `severity: high`
- `mean_delta_pct: +18.0`
- `p99_delta_pct: +32.0`
- `fps_delta_pct: -22.0`
- `memory_peak_delta_pct: +40.0`
- `runtime_telemetry_context`: supplemental telemetry coverage and evidence-gap context from EdgeEnv history export
- `runtime_telemetry_context.history.telemetry_coverage`: EdgeEnv-owned replay summary for history-level coverage gaps and missing-field runs
- `runtime_telemetry_context.history.runs[].runtime_telemetry_history_seed`: Runtime seed preserved by EdgeEnv for local replay traceability
- `runtime_telemetry_context.<run>.orchestrator_operation_context`: supplemental operation context when EdgeEnv history was exported with an Orchestrator feed
- `runtime_telemetry_context.<run>.orchestrator_operation_context.edgeenv_mapping_hint`: producer hint that keeps Orchestrator candidate context supplemental while naming EdgeEnv as the telemetry coverage summary owner
- `runtime_telemetry_context.<run>.orchestrator_operation_context.candidate_context.producer`: device-local producer lineage preserved as traceability evidence, not as a Lab decision override
- `runtime_telemetry_context.<run>.orchestrator_operation_context.downstream_guard_alignment`: Orchestrator-declared marker that expects `edgeenv_orchestrator_producer_lineage` evidence downstream while keeping Lab as final decision owner

## Reproduction Command

```bash
poetry run inferedgelab compare \
  examples/edgeenv_regression/lab_baseline_result.json \
  examples/edgeenv_regression/lab_candidate_result.json \
  --edgeenv-regression examples/edgeenv_regression/edgeenv_runtime_regression.json \
  --markdown-out reports/edgeenv_regression_lab_handoff.md
```

Runtime Intelligence cross-repo evidence-chain smoke:

```bash
bash scripts/smoke_runtime_intelligence_chain.sh \
  --output-dir reports/runtime_intelligence_chain
```

The script runs the full local artifact chain:

```text
bundle manifest gate
-> EdgeEnv regression report
-> Runtime Intelligence report with precomputed AIGuard evidence
-> report artifact gate
-> CI artifact gate
```

The individual report command remains:

```bash
poetry run inferedgelab compare \
  examples/edgeenv_regression/lab_baseline_result.json \
  examples/edgeenv_regression/lab_candidate_result.json \
  --edgeenv-regression examples/runtime_intelligence_chain/edgeenv_regression_with_orchestrator_context.json \
  --guard-analysis examples/runtime_intelligence_chain/aiguard_runtime_operation_guard_analysis.json \
  --markdown-out reports/runtime_intelligence_chain.md \
  --html-out reports/runtime_intelligence_chain.html
```

This second smoke uses committed lightweight artifacts to represent the cross-repo handoff:

- `examples/runtime_intelligence_chain/bundle_manifest.json` declares the local-first artifact bundle, file paths, source repositories, artifact roles, producer contracts, owners, and boundary flags.
- `examples/runtime_intelligence_chain/edgeenv_lab_handoff_manifest.json` mirrors the EdgeEnv producer-side handoff manifest and its `lab_bundle_alignment` metadata, so Lab can verify EdgeEnv-produced file keys separately from external AIGuard evidence.
- The same handoff declares `external_aiguard_required_evidence_types`; Lab's bundle gate checks that those types are present in the external `guard_analysis.evidence` list without making AIGuard the final decision owner.
- `examples/runtime_intelligence_chain/runtime_telemetry_history.json` is the EdgeEnv producer-side telemetry history artifact referenced by the handoff manifest. It includes a missing-telemetry run as an evidence gap and preserves Orchestrator context on that entry without turning Orchestrator into a regression or deployment decision owner.
- Orchestrator context is preserved inside the EdgeEnv regression artifact as `orchestrator_operation_context`.
- AIGuard deterministic queue/thermal evidence is passed as a precomputed `guard_analysis` artifact that mirrors the AIGuard producer-side diagnosis v1 evidence shape.
- Lab owns the combined report and deployment decision.
- `scripts/check_runtime_intelligence_bundle_manifest.py` gates the bundle manifest before report generation, including source repository mapping, schema markers, and evidence-item shape for the EdgeEnv history, Orchestrator feed, and AIGuard diagnosis artifacts.
- The same gate can also consume `--edgeenv-handoff` to compare EdgeEnv producer-side `lab_bundle_alignment` metadata against Lab's bundle manifest contract.
- `scripts/check_runtime_intelligence_artifact_bundle.py` gates the generated report so required Runtime Intelligence rows and ownership text cannot disappear silently.

Expected Lab behavior:

- CLI prints `Runtime Regression Evidence`.
- CLI prints `Runtime Telemetry Context` when the EdgeEnv regression report includes it.
- Markdown/HTML reports include a `Runtime Regression Evidence` section.
- Markdown/HTML reports include a `Runtime Telemetry Context` subsection with baseline/candidate telemetry coverage and history execution sequence context.
- When EdgeEnv preserves `runtime_telemetry.coverage`, Lab surfaces coverage ratio, missing fields, and `missing_telemetry_is_failure` as evidence quality metadata. These fields do not override EdgeEnv comparability or Lab deployment policy.
- When `--with-guard` is enabled and the installed AIGuard exposes EdgeEnv regression reasoning, Lab routes the EdgeEnv report to AIGuard and preserves diagnosis evidence such as `runtime_latency_regression`, `runtime_telemetry_context_coverage`, and `runtime_telemetry_replay_context`.
- The Runtime Intelligence bundle gate requires AIGuard coverage evidence to declare `telemetry_coverage_source=history_telemetry_coverage`, proving that the precomputed guard artifact consumed EdgeEnv's producer-side replay summary.
- The Runtime Intelligence bundle gate requires Runtime `runtime_telemetry_history_seed` markers to remain visible through EdgeEnv history and AIGuard raw context, including `registry_owner=edgeenv` and `decision_owner=lab`.
- When EdgeEnv preserves Runtime `history_seed.run_config` snapshots, Lab surfaces the run_config seed count as replay/comparability traceability in the Runtime Intelligence Risk Summary. This does not override EdgeEnv comparability or Lab deployment policy.
- The same gate now requires AIGuard `runtime_history_seed_run_config_traceability` evidence so Runtime history seed `run_config` markers cannot disappear from the cross-repo Lab handoff silently.
- The Runtime Intelligence bundle gate requires the preserved Orchestrator `edgeenv_mapping_hint` to keep `coverage_summary_owner=edgeenv`, `coverage_summary_path=runtime_telemetry_context.history.telemetry_coverage`, and `operation_context_role=supplemental`.
- The same gate requires Orchestrator's AIGuard evidence candidate hint to preserve `runtime_queue_overload` and `runtime_thermal_instability`, keeping runtime operation anomaly evidence deterministic and supplemental.
- The same gate requires Orchestrator candidate context to carry `run_id`, `telemetry_source`, `operation`, and `resource`, so Lab can verify handoff completeness without treating Orchestrator context as a regression judgement.
- The same gate requires EdgeEnv-preserved Orchestrator producer markers to carry `source_repository=InferEdgeOrchestrator`, `artifact_role=orchestrator-supplemental-operation-context`, and `producer_contract=inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1`.
- When an EdgeEnv handoff manifest is provided, the bundle gate requires EdgeEnv-produced file keys, external AIGuard file keys, source repository mapping, artifact roles, producer contracts, and boundary flags to match Lab's Runtime Intelligence bundle contract.
- The same handoff gate verifies that the referenced `runtime_telemetry_history` artifact exists and preserves EdgeEnv history schema, telemetry coverage, and Runtime history seed ownership markers.
- The same handoff gate verifies that missing telemetry entries remain evidence gaps while preserving Orchestrator producer markers, owner boundary flags, and EdgeEnv mapping hints when Orchestrator context is attached.
- The same handoff gate validates `edgeenv_report_summary.producer_lineage_guard_alignment_run_ids` against the preserved EdgeEnv regression context so the Orchestrator-declared `edgeenv_orchestrator_producer_lineage` marker cannot disappear between EdgeEnv producer output and Lab bundle ingestion.
- The bundle gate also requires AIGuard coverage evidence raw context to preserve the same Orchestrator mapping hint and producer markers, proving that AIGuard kept EdgeEnv/Orchestrator ownership markers as diagnosis context rather than recomputing coverage or owning deployment policy.
- The same gate requires AIGuard `edgeenv_orchestrator_producer_lineage` evidence to preserve candidate and missing-telemetry device-local producer lineage as traceability evidence.
- The gate also requires the Orchestrator-declared downstream guard-alignment marker to survive the EdgeEnv/AIGuard handoff, so the Lab report can show which producer-lineage evidence type was expected without recomputing AIGuard reasoning.
- The same gate requires AIGuard replay raw context to preserve Orchestrator producer markers and mapping hints for EdgeEnv history `missing_telemetry` entries when present, keeping missing telemetry as replay evidence gap context.
- Additional Lab test fixtures under `tests/fixtures/edgeenv_regression/` mirror EdgeEnv replay examples for candidate telemetry gaps and execution sequence inversion. These fixture smokes verify that replay warnings become Lab-owned report context without making Lab recompute EdgeEnv comparability.
- Markdown/HTML reports include a `Runtime Intelligence Risk Summary` that summarizes EdgeEnv comparability/regression, telemetry replay gaps, Runtime history seed/run_config traceability, AIGuard deterministic evidence, and the Lab-owned deployment decision in one reviewer-facing table.
- When EdgeEnv includes preserved Orchestrator feed context, the `Runtime Intelligence Risk Summary` surfaces queue, thermal, throttling, memory, and fallback context as supplemental runtime evidence.
- When `--guard-analysis` is provided, Lab ingests the precomputed AIGuard artifact as evidence without requiring AIGuard to be installed in the Lab environment.
- The committed Runtime Intelligence guard fixture preserves AIGuard's coverage-gap diagnosis, `edgeenv_orchestrator_producer_lineage`, `runtime_history_seed_run_config_traceability`, and EdgeEnv history missing-field runs as deterministic review context rather than a Lab policy override.
- Guard evidence details preserve explanatory fields such as `why_it_matters`, evidence-local `suspected_causes`, and `recommendation`.
- Deployment decision is `review_required`.
- Triggered rules include `edgeenv_runtime_regression_review`.
- Deployment decision reports include policy-summary descriptions for the triggered Lab rules.

## Boundary

This is not cloud monitoring, distributed tracing, production observability, a public leaderboard, or Kubernetes-style orchestration.

The purpose is narrower: Lab can consume EdgeEnv's comparability-first runtime regression evidence, supplemental runtime telemetry context, and optional AIGuard deterministic diagnosis evidence as deployment review context without changing Runtime result or compare contracts.
