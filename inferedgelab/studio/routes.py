from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_ASSETS = {
    "app.js": "application/javascript",
    "style.css": "text/css",
}

router = APIRouter()


@router.get("/studio", include_in_schema=False)
def studio_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@router.get("/studio/static/{asset_name}", include_in_schema=False)
def studio_static(asset_name: str) -> FileResponse:
    media_type = STATIC_ASSETS.get(asset_name)
    if media_type is None:
        raise HTTPException(status_code=404, detail="studio asset not found")
    return FileResponse(STATIC_DIR / asset_name, media_type=media_type)


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


def register_studio(app: FastAPI, job_store: Any | None = None) -> None:
    app.state.studio_job_store = job_store
    app.include_router(router)


def _get_studio_job_store(request: Request) -> Any | None:
    return getattr(request.app.state, "studio_job_store", None)


def _get_api_endpoint(app: FastAPI, path: str) -> Any:
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise HTTPException(status_code=404, detail=f"API route not found: {path}")
