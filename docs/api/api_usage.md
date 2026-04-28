# InferEdgeLab FastAPI Read-Only Adapter Usage Guide

## Purpose

InferEdgeLab API layer is a thin FastAPI adapter over the existing service layer.

- It exposes InferEdgeLab read-only workflows over HTTP
- It keeps business logic in reusable services, not in the API layer
- It provides a practical bridge toward future Web UI and SaaS expansion

This means the current API is intended to reuse the same validation flow already available from the CLI, not to replace it with a separate implementation.

---

## CLI, Service, API Adapter Relationship

InferEdgeLab currently follows this boundary:

- CLI: argument parsing, file saving, console rendering, command entrypoints
- Service layer: domain orchestration for compare, history-report, summarize, list-results
- API adapter: HTTP parameter binding and service response exposure

In short:

```text
CLI / HTTP API -> Service Layer -> Existing domain logic / loaders / renderers
```

The FastAPI layer is intentionally thin. It reuses the same service-layer logic used by the CLI, so compare/history/summarize/list-results behavior stays aligned across interfaces.

---

## Run the Server

Basic launch:

```bash
poetry run inferedgelab serve
```

Custom host and port:

```bash
poetry run inferedgelab serve --host 0.0.0.0 --port 8000
```

Development mode with auto-reload:

```bash
poetry run inferedgelab serve --host 127.0.0.1 --port 8000 --reload
```

By default, the API runs on `127.0.0.1:8000`.

---

## Endpoints

Current read-only endpoints:

- `GET /health`
- `GET /api/list-results`
- `GET /api/summarize`
- `GET /api/history-report`
- `GET /api/compare`

---

## Health Check

Request:

```bash
curl "http://127.0.0.1:8000/health"
```

Response:

```json
{"status":"ok","service":"inferedgelab-api","version":"0.1.0"}
```

---

## List Results

Purpose:

- Returns recent structured result items
- Reuses the `list-results` service bundle contract

Example:

```bash
curl "http://127.0.0.1:8000/api/list-results?limit=5"
```

Example with filters:

```bash
curl "http://127.0.0.1:8000/api/list-results?model=toy224.onnx&engine=onnxruntime&device=cpu&precision=fp32"
```

Response structure:

- `meta`
  - request metadata such as `pattern`, `limit`, `filters`, `count`
- `data`
  - `items`: structured result item list

---

## Summarize

Purpose:

- Builds summary bundle data and rendered Markdown
- Reuses the same summarize service used by CLI output generation

Example:

```bash
curl "http://127.0.0.1:8000/api/summarize?pattern=reports/*.json&mode=latest&sort=p99"
```

Example with recent/top:

```bash
curl "http://127.0.0.1:8000/api/summarize?pattern=reports/*.json&mode=both&sort=time&recent=5&top=3"
```

Response structure:

- `meta`
  - request metadata such as `pattern`, `format`, `mode`, `sort`, `recent`, `top`
- `data`
  - `rows`, `latest_rows`, `history_rows`
- `rendered`
  - `markdown`

---

## History Report

Purpose:

- Selects history results with filters
- Produces HTML and optional Markdown report content

Example:

```bash
curl "http://127.0.0.1:8000/api/history-report?model=toy224.onnx&include_markdown=true"
```

Example with shape filters:

```bash
curl "http://127.0.0.1:8000/api/history-report?engine=onnxruntime&device=cpu&batch=1&height=224&width=224"
```

Response structure:

- `history`
  - matched structured result history
- `filters`
  - applied history filters
- `html`
  - rendered HTML report text
- `markdown`
  - rendered Markdown report text or `null`

---

## Compare

Purpose:

- Compares two structured result files
- Returns the SaaS API response contract with compare result data, judgement, rendered Markdown/HTML, deployment decision, provenance, and optional AIGuard evidence

Path-based example:

```bash
curl "http://127.0.0.1:8000/api/compare?base_path=results/base.json&new_path=results/new.json"
```

JSON body example:

```bash
curl -X POST "http://127.0.0.1:8000/api/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "base_result": {"model": "resnet18", "engine": "onnxruntime", "device": "cpu", "precision": "fp32", "batch": 1, "height": 224, "width": 224, "mean_ms": 10.0, "p99_ms": 12.0, "timestamp": "2026-04-13T09:00:00Z"},
    "new_result": {"model": "resnet18", "engine": "onnxruntime", "device": "cpu", "precision": "fp32", "batch": 1, "height": 224, "width": 224, "mean_ms": 9.0, "p99_ms": 11.0, "timestamp": "2026-04-13T10:00:00Z"},
    "guard_analysis": {"status": "ok", "anomalies": [], "suspected_causes": [], "recommendations": [], "confidence": 0.5}
  }'
```

Response structure:

- `summary`
  - compact response type, comparison mode, overall judgement, deployment decision, and guard status
- `comparison`
  - compare metrics and context
- `deployment_decision`
  - Lab-owned deployment decision; always included
- `guard_analysis`
  - optional AIGuard evidence; omitted when not provided or not executed
- `provenance`, `metadata`, `timestamps`, `execution_info`
  - frontend/SaaS integration context

---

## InferEdgeLab API Response Contract

SaaS-facing compare responses should be wrapped into a stable external JSON shape. The wrapper preserves existing service-layer output and does not change compare, report, or deployment decision logic.

Required top-level fields:

- `summary`
  - compact response type, comparison mode, overall judgement, deployment decision, and guard status
- `comparison`
  - compare result, judgement, and rendered Markdown/HTML report content
- `deployment_decision`
  - Lab-owned deploy/review/block/unknown decision
- `guard_analysis`
  - optional AIGuard evidence; omitted when AIGuard is not installed or not executed
- `provenance`
  - runtime, shape, and run configuration provenance copied from the compare bundle
- `metadata`
  - request and bundle metadata such as paths and legacy warning state
- `timestamps`
  - base/new result timestamps when available
- `execution_info`
  - path, selection mode, and execution-context fields needed by frontend/SaaS clients

The fixture at `tests/fixtures/api_response_bundle.json` locks the external contract for `deployable`, `review_required`, `blocked`, and AIGuard-absent responses. AIGuard remains optional, and InferEdgeLab remains the final deployment decision owner.

---

## Notes

- The current API is read-only.
- The API layer reuses service-layer logic rather than duplicating benchmark logic inside HTTP handlers.
- This keeps CLI and API behavior aligned across compare, history-report, summarize, and list-results.
- The API is intentionally a bridge layer for future Web UI or SaaS-oriented expansion, not a separate product surface yet.
