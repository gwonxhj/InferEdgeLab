# InferEdgeLab SaaS Async Job Workflow Contract

## Purpose

This document defines the response contract for future InferEdgeLab SaaS async workflows such as `/api/analyze`. It fixes the job status model and response shape without introducing an external queue, database, Redis runtime, or worker implementation.

The goal is to let frontend and API clients handle long-running validation work consistently while InferEdgeLab keeps the existing compare, report, and deployment decision logic unchanged.

## Status Model

Supported job states:

- `queued`: the request has been accepted but work has not started.
- `running`: validation work is in progress.
- `completed`: work finished successfully and `result` contains the Lab API response contract bundle.
- `failed`: work failed and `error` explains the failure.
- `cancelled`: the request was cancelled before producing a result.

## Response Shape

Every job response must include:

| Field | Type | Purpose |
|---|---|---|
| `job_id` | string | Stable job identifier for polling and links. |
| `status` | string | One of `queued`, `running`, `completed`, `failed`, or `cancelled`. |
| `created_at` | string | Job creation timestamp. |
| `updated_at` | string | Last status update timestamp. |
| `input_summary` | object | Small, non-heavy summary of the request. |
| `result` | object or null | Completed Lab API response contract bundle. |
| `error` | object or null | Failure details for failed jobs. |
| `links` | object | Polling, result, cancel, or related endpoint links. |
| `next_actions` | list[string] | Client-facing next actions such as `poll_self` or `review_deployment_decision`. |

## State Rules

- `completed` jobs must include `result`.
- `completed.result` must include `deployment_decision`.
- `failed` jobs must set `result` to `null` and include `error`.
- `queued`, `running`, and `cancelled` jobs may set `result` to `null`.
- `result` may contain the existing `api_response_contract` bundle, including `summary`, `comparison`, `deployment_decision`, optional `guard_analysis`, `provenance`, `metadata`, `timestamps`, and `execution_info`.

## Example Flow

```text
POST /api/analyze
-> queued job response
-> GET /api/jobs/{job_id}
-> running job response
-> GET /api/jobs/{job_id}
-> completed job response with deployment_decision bundle
```

Failed jobs follow the same polling shape but return `status: failed`, `result: null`, and a structured `error` object.

For local development only, InferEdgeLab also exposes a mock completion path:

```text
POST /api/analyze
-> queued job response
POST /api/jobs/{job_id}/complete-dev
-> completed job response with caller-provided API response contract result
GET /api/jobs/{job_id}
-> same completed job response
```

`/api/jobs/{job_id}/complete-dev` is not a worker substitute. It validates that the supplied `result` follows the existing API response contract and stores it in the process-local job store so frontend/SaaS clients can smoke-test the full job lifecycle before Forge/Runtime worker integration exists.

The future Lab-to-worker boundary is documented in [worker_integration_contract.md](worker_integration_contract.md). It defines the minimum worker request, completed response, and failed response payloads while keeping queue and execution infrastructure out of scope.

## Current Implementation Scope

The current API implementation is an in-memory stub:

- `POST /api/analyze` accepts JSON with `model_path` or `artifact_path`, optional `metadata_path`, optional `manifest_path`, and optional `notes`.
- The endpoint creates a `queued` job response.
- Queued analyze jobs can be projected into the worker request contract for future Forge/Runtime workers.
- Terminal worker completed/failed responses can be projected back into valid Lab job responses.
- `GET /api/jobs/{job_id}` returns the stored in-memory job response.
- `POST /api/jobs/{job_id}/complete-dev` can complete a queued/running in-memory job with a mock API response contract result.
- The store is process-local and resets when the API process restarts.

This keeps the SaaS workflow contract executable without committing to queue, database, worker, upload, Forge build, or Runtime execution infrastructure.

## Lab-Side Workflow Smoke

The Lab-side smoke coverage verifies the current in-memory workflow boundary:

```text
POST /api/analyze
-> queued job
-> build worker_request from queued job
-> apply mock worker completed/failed response
-> validate completed/failed Lab job response
-> for completed jobs, store result through the dev-only completion path
-> GET /api/jobs/{job_id}
```

This smoke test uses mock worker payloads only. It does not run Forge, Runtime, external queues, databases, Redis, Celery, uploads, or background workers.

## Non-Goals

This contract does not introduce:

- external queue infrastructure
- database persistence
- Redis
- background worker runtime
- new Forge or Runtime execution behavior
- changes to `/api/compare`
- changes to Lab `deployment_decision` logic

## Fixtures And Tests

The contract is locked by:

- `tests/fixtures/api_job_queued.json`
- `tests/fixtures/api_job_completed.json`
- `tests/fixtures/api_job_failed.json`
- `tests/test_api_job_contract.py`
- `tests/fixtures/worker_request.json`
- `tests/fixtures/worker_completed_response.json`
- `tests/fixtures/worker_failed_response.json`
- `tests/test_worker_contract.py`
- `tests/test_api_worker_workflow.py`

These fixtures prepare InferEdgeLab for a later in-memory `/api/analyze` job stub while keeping infrastructure choices out of scope for this step.
