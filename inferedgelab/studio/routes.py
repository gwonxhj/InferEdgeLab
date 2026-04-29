from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import Body
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse

from inferedgelab.compare.comparator import compare_results
from inferedgelab.compare.judgement import judge_comparison
from inferedgelab.result.loader import load_result
from inferedgelab.result.schema import normalize_result_schema
from inferedgelab.services.deployment_decision import build_deployment_decision

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_ASSETS = {
    "app.js": "application/javascript",
    "style.css": "text/css",
}

router = APIRouter()


@router.get("/studio", include_in_schema=False)
def studio_index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/studio로", include_in_schema=False)
def studio_korean_particle_redirect() -> RedirectResponse:
    return RedirectResponse(url="/studio", status_code=307)


@router.get("/studio/static/{asset_name}", include_in_schema=False)
def studio_static(asset_name: str) -> FileResponse:
    media_type = STATIC_ASSETS.get(asset_name)
    if media_type is None:
        raise HTTPException(status_code=404, detail="studio asset not found")
    return FileResponse(
        STATIC_DIR / asset_name,
        media_type=media_type,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/studio/api/jobs", include_in_schema=False)
def studio_jobs(request: Request) -> dict[str, Any]:
    store = _get_studio_job_store(request)
    jobs = []
    if store is not None:
        jobs = sorted(
            getattr(store, "_jobs", {}).values(),
            key=lambda job: str(job.get("updated_at") or job.get("created_at") or ""),
            reverse=True,
        )
    return {
        "source": "/api/jobs",
        "count": len(jobs),
        "jobs": jobs,
    }


@router.get("/studio/api/job/{job_id}", include_in_schema=False)
def studio_job_detail(request: Request, job_id: str) -> dict[str, Any]:
    endpoint = _get_api_endpoint(request.app, "/api/jobs/{job_id}")
    return endpoint(job_id=job_id)


@router.get("/studio/api/compare/latest", include_in_schema=False)
def studio_compare_latest(request: Request) -> dict[str, Any]:
    imported_results = _get_imported_results(request)
    if len(imported_results) >= 2:
        return _build_imported_compare_response(imported_results[-2], imported_results[-1])

    endpoint = _get_api_endpoint(request.app, "/api/compare-latest")
    try:
        return endpoint()
    except HTTPException as exc:
        if exc.status_code != 400:
            raise
        return {
            "status": "empty",
            "source": "/api/compare-latest",
            "error": exc.detail,
            "data": None,
            "deployment_decision": {
                "decision": "unknown",
                "reason": "No compare-ready result data is available yet.",
                "notes": "Run the CLI workflow or create result artifacts, then reload Local Studio.",
            },
        }


@router.post("/studio/api/run", include_in_schema=False)
def studio_run(request: Request, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    model_path = payload.get("model_path")
    if not isinstance(model_path, str) or not model_path.strip():
        raise HTTPException(status_code=400, detail="model_path is required")

    endpoint = _get_api_endpoint(request.app, "/api/analyze")
    analyze_payload: dict[str, Any] = {
        "model_path": model_path.strip(),
        "notes": "Created from Local Studio Run",
    }
    options = payload.get("options")
    if isinstance(options, dict):
        analyze_payload["options"] = dict(options)
    job = endpoint(payload=analyze_payload)
    return {
        "status": "created",
        "source": "/api/analyze",
        "job_id": job["job_id"],
        "job": job,
    }


@router.post("/studio/api/import", include_in_schema=False)
def studio_import(request: Request, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    result = _load_import_payload(payload)
    result = _apply_backend_override(result, payload.get("backend_override"))
    imported_results = _get_imported_results(request)
    imported_results.append(result)
    return {
        "status": "imported",
        "source": "studio-memory",
        "count": len(imported_results),
        "result": result,
        "compare_ready": len(imported_results) >= 2,
    }


@router.get("/studio/api/jetson-command", include_in_schema=False)
def studio_jetson_command() -> dict[str, str]:
    command = "\n".join(
        [
            "./inferedge-runtime \\",
            "  --manifest ~/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16/manifest.json \\",
            "  --model ~/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16/model.engine \\",
            "  --engine tensorrt \\",
            "  --device jetson \\",
            "  --runs 5 \\",
            "  --warmup 1 \\",
            "  --output results/jetson/yolov8n_jetson_tensorrt_manifest_smoke.json",
        ]
    )
    return {"command": command}


@router.get("/studio{suffix:path}", include_in_schema=False)
def studio_path_fallback(suffix: str) -> RedirectResponse:
    if suffix.startswith("/api") or suffix.startswith("/static"):
        raise HTTPException(status_code=404, detail="studio route not found")
    if suffix:
        return RedirectResponse(url="/studio", status_code=307)
    return RedirectResponse(url="/studio", status_code=307)


def register_studio(app: FastAPI, job_store: Any | None = None) -> None:
    app.state.studio_job_store = job_store
    app.state.studio_imported_results = []
    app.include_router(router)


def _get_studio_job_store(request: Request) -> Any | None:
    return getattr(request.app.state, "studio_job_store", None)


def _get_imported_results(request: Request) -> list[dict[str, Any]]:
    imported_results = getattr(request.app.state, "studio_imported_results", None)
    if imported_results is None:
        imported_results = []
        request.app.state.studio_imported_results = imported_results
    return imported_results


def _get_api_endpoint(app: FastAPI, path: str) -> Any:
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise HTTPException(status_code=404, detail=f"API route not found: {path}")


def _load_import_payload(payload: dict[str, Any]) -> dict[str, Any]:
    path = payload.get("path") or payload.get("json_path")
    if isinstance(path, str) and path.strip():
        try:
            return _with_compare_keys(load_result(path.strip()))
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw_result = payload.get("result") or payload.get("payload") or payload.get("json")
    if raw_result is None:
        raw_result = payload
    if not isinstance(raw_result, dict):
        raise HTTPException(status_code=400, detail="import payload must be a JSON object")

    try:
        result = normalize_result_schema(dict(raw_result))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result.setdefault("legacy_result", False)
    return _with_compare_keys(result)


def _build_imported_compare_response(base: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    result = compare_results(base, new)
    judgement = judge_comparison(result)
    deployment_decision = build_deployment_decision(judgement)
    return {
        "status": "ok",
        "source": "studio-memory",
        "data": {
            "base": base,
            "new": new,
            "result": result,
            "judgement": judgement,
            "deployment_decision": deployment_decision,
        },
        "base": base,
        "new": new,
        "result": result,
        "judgement": judgement,
        "deployment_decision": deployment_decision,
    }


def _with_compare_keys(result: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(result)
    if not enriched.get("backend_key"):
        engine = _first_display_value(
            enriched.get("engine_backend"),
            enriched.get("engine"),
            enriched.get("backend"),
        )
        device = _first_display_value(enriched.get("device_name"), enriched.get("device"))
        if engine and device:
            enriched["backend_key"] = f"{engine}__{device}"
    if not enriched.get("compare_key"):
        model = _first_display_value(enriched.get("model_name"), enriched.get("model"))
        batch = enriched.get("batch")
        height = enriched.get("height")
        width = enriched.get("width")
        precision = enriched.get("precision")
        if model and batch and height and width and precision:
            enriched["compare_key"] = f"{model}__b{batch}__h{height}w{width}__{precision}"
    return enriched


def _apply_backend_override(result: dict[str, Any], override: Any) -> dict[str, Any]:
    if not isinstance(override, str) or not override.strip():
        return result

    override = override.strip()
    if override == "onnxruntime__cpu":
        engine = "onnxruntime"
        device = "cpu"
    elif override == "tensorrt__jetson":
        engine = "tensorrt"
        device = "jetson"
    else:
        raise HTTPException(status_code=400, detail="unsupported backend_override")

    enriched = dict(result)
    enriched["engine"] = engine
    enriched["engine_backend"] = engine
    enriched["device"] = device
    enriched["device_name"] = device
    enriched["backend_key"] = override
    return _with_compare_keys(enriched)


def _first_display_value(*values: Any) -> str:
    for value in values:
        display_value = _display_value(value)
        if display_value:
            return display_value
    return ""


def _display_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, dict):
        return _first_display_value(
            value.get("name"),
            value.get("backend"),
            value.get("path"),
            value.get("status"),
            value.get("id"),
        )
    return str(value)
