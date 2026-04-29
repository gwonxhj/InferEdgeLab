from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import HTTPException
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


def register_studio(app: FastAPI) -> None:
    app.include_router(router)
