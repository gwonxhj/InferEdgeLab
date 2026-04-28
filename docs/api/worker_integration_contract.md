# Forge Runtime Worker Integration Contract

## Purpose

This document defines the minimum boundary contract between InferEdgeLab and future Forge/Runtime workers for `/api/analyze` execution.

The contract keeps InferEdgeLab responsible for SaaS job state, analysis, report bundling, and deployment decision ownership while allowing Forge and Runtime to run outside the API process later. It does not introduce a queue, database, file upload path, Forge build execution, or Runtime inference execution in this step.

## Current SaaS API State

InferEdgeLab currently exposes:

- `POST /api/compare`: returns the stable SaaS API response contract.
- `POST /api/analyze`: creates an in-memory `queued` job.
- `GET /api/jobs/{job_id}`: returns the in-memory job response.
- `POST /api/jobs/{job_id}/complete-dev`: development-only mock completion path.

The current implementation is intentionally process-local. It prepares the API shape and lifecycle tests before worker infrastructure is added.

## Target Worker Flow

```text
POST /api/analyze
-> Lab creates queued job
-> worker receives job request
-> Forge builds artifact and emits metadata/manifest
-> Runtime executes artifact and emits Lab-compatible result JSON
-> Lab compares/analyzes result
-> optional AIGuard adds guard_analysis
-> Lab stores completed job result
-> client reads /api/jobs/{job_id}
```

## Lab Responsibilities

InferEdgeLab owns:

- accepting `/api/analyze` requests
- creating and exposing job state
- building the worker request payload
- validating worker response payloads
- comparing/analyzing Runtime result JSON
- wrapping final output in the SaaS API response contract
- generating and storing the Lab-owned `deployment_decision`
- keeping AIGuard optional

## Forge Worker Responsibilities

The Forge worker owns:

- receiving the Lab worker request or a worker-specific projection of it
- building the edge deployment artifact from the source model
- emitting `metadata.json` and `manifest.json`
- preserving source model hash, artifact hash, backend, target, precision, shape, preset, and build provenance
- returning a Forge metadata/manifest summary to Lab or to the Runtime worker boundary

## Runtime Worker Responsibilities

The Runtime worker owns:

- consuming the Forge artifact and handoff metadata
- running the artifact in the selected backend/target context
- measuring latency and runtime provenance
- emitting Lab-compatible result JSON
- preserving runtime artifact path/hash and source model provenance when available

## AIGuard Optional Responsibilities

InferEdgeAIGuard may optionally consume:

- Lab compare/result context
- Runtime profiling provenance
- Forge metadata/manifest provenance

It returns `guard_analysis` as rule/evidence-based diagnosis. It remains optional and does not own the final deployment decision.

## Worker Request Contract

Worker requests are created by Lab from the queued analyze job.

| Field | Required | Purpose |
|---|---:|---|
| `job_id` | yes | Stable Lab job identifier. |
| `input_summary` | yes | Original lightweight analyze input summary. |
| `requested_at` | yes | Timestamp when Lab hands work to a worker boundary. |
| `model_path` | conditional | Source model path. Required when `artifact_path` is absent. |
| `artifact_path` | conditional | Existing artifact path. Required when `model_path` is absent. |
| `metadata_path` | no | Optional Forge metadata path. |
| `manifest_path` | no | Optional Forge manifest path. |
| `options` | yes | Backend, target, precision, shape, guard, and worker execution options. |

The fixture `tests/fixtures/worker_request.json` locks the minimum request shape.

### Queued Job Mapping

InferEdgeLab maps a queued analyze job into `worker_request` with these rules:

| Job field | Worker request field |
|---|---|
| `job_id` | `job_id` |
| `input_summary` | `input_summary` |
| `updated_at` or `created_at` | `requested_at` |
| `input_summary.model_path` | `model_path` |
| `input_summary.artifact_path` | `artifact_path` |
| `input_summary.metadata_path` | `metadata_path` |
| `input_summary.manifest_path` | `manifest_path` |
| `input_summary.options` plus optional caller options | `options` |
| `input_summary.notes` | `options.notes` when present |

Only `queued` jobs with `input_summary.workflow: analyze` may be converted. Completed, failed, cancelled, running, or non-analyze jobs must not be handed to workers through this helper.

## Worker Response Contract

Worker responses are terminal worker-boundary payloads. Lab may convert them into job responses after analysis/report/deployment decision wrapping.

### Completed Response

Required fields:

- `job_id`
- `status: completed`
- `forge_metadata` or a Forge manifest/metadata summary
- `runtime_result`
- optional `guard_analysis`
- `completed_at`

`runtime_result` must be Lab-compatible enough for compare/report/deployment decision flows. At minimum it must include model/backend/device/precision/shape, latency fields, and timestamp.

### Failed Response

Required fields:

- `job_id`
- `status: failed`
- `error`
- `failed_at`

Failed responses must not include a completed `runtime_result`.

The fixtures `tests/fixtures/worker_completed_response.json` and `tests/fixtures/worker_failed_response.json` lock the minimum response shapes.

### Runtime-Exported Response Compatibility

InferEdgeRuntime can dry-run export completed/failed worker responses for this boundary. Lab keeps compatibility fixtures for that shape:

- `tests/fixtures/runtime_worker_completed_response.json`
- `tests/fixtures/runtime_worker_failed_response.json`

The completed fixture follows Runtime's dry-run result naming, including `runtime_result.model_path`, `runtime_result.engine_backend`, and `runtime_result.device_name`. Lab treats these as compatible aliases for the generic `model`, `engine`, and `device` fields during worker response validation and job result mapping.

This smoke coverage verifies that Runtime-exported worker responses can be validated and applied to Lab jobs without running the Runtime binary, Forge, queues, databases, Redis, Celery, or external worker processes.

### Worker Response Mapping

InferEdgeLab maps terminal worker responses back into Lab job responses with these rules:

| Worker response | Lab job update |
|---|---|
| `job_id` | Must match the existing Lab job `job_id`. |
| `status: completed` | Sets Lab job `status` to `completed`. |
| `completed_at` | Becomes Lab job `updated_at`. |
| `runtime_result` | Is wrapped into the Lab job `result` payload. |
| `forge_metadata` | Is preserved in result provenance. |
| optional `guard_analysis` | Is preserved in completed job `result.guard_analysis`. |
| `status: failed` | Sets Lab job `status` to `failed`. |
| `failed_at` | Becomes Lab job `updated_at`. |
| `error` | Becomes Lab job `error`; Lab job `result` remains `null`. |

Only active jobs may accept worker responses. Completed, failed, or cancelled jobs must reject reapplication. Completed Lab job responses must still satisfy the SaaS job contract and include `result.deployment_decision`.

## Job State Transition

The intended transition model is:

```text
queued -> running -> completed
queued -> running -> failed
queued -> cancelled
running -> cancelled
```

Completed jobs must eventually store a SaaS API response contract bundle in `result`, including Lab-owned `deployment_decision`.

Failed jobs must keep `result` as `null` and include structured `error` details.

## Failure Handling

Worker failures should preserve stage and evidence where possible:

- Forge build failure: return `status: failed` with `error.stage: forge`.
- Runtime execution failure: return `status: failed` with `error.stage: runtime`.
- Result schema failure: return `status: failed` with `error.stage: lab_validation`.
- Optional AIGuard failure: do not fail the entire job by default; omit `guard_analysis` or mark it as skipped unless policy requires review.

Lab should validate worker payloads before storing completed or failed job state.

## Non-Goals

This contract does not add:

- actual Forge build execution
- actual Runtime inference execution
- file upload handling
- database persistence
- Redis, Celery, or external queue infrastructure
- changes to `/api/compare`
- changes to `/api/analyze` current in-memory behavior
- changes to `/api/jobs/{job_id}` current behavior
- changes to `deployment_decision` logic

## Next Implementation Steps

- Add an end-to-end workflow smoke test for job creation, worker request mapping, worker response mapping, and completed job polling.
- Later, introduce a worker adapter boundary without committing Lab to a specific queue implementation.
- Finally, connect real Forge/Runtime execution behind that adapter when artifacts and environments are ready.
