from __future__ import annotations

from fastapi import FastAPI, HTTPException

from edgebench.services.compare_service import build_compare_bundle
from edgebench.services.history_report_service import build_history_report_outputs
from edgebench.services.list_results_service import build_list_results_bundle
from edgebench.services.summarize_service import build_summary_bundle


def create_app() -> FastAPI:
    app = FastAPI(title="EdgeBench API")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "edgebench-api"}

    @app.get("/api/list-results")
    def list_results(
        pattern: str = "results/*.json",
        limit: int = 10,
        model: str = "",
        engine: str = "",
        device: str = "",
        precision: str = "",
        batch: int | None = None,
        height: int | None = None,
        width: int | None = None,
        legacy_only: bool = False,
    ) -> dict:
        try:
            return build_list_results_bundle(
                pattern=pattern,
                limit=limit,
                model=model,
                engine=engine,
                device=device,
                precision=precision,
                batch=batch,
                height=height,
                width=width,
                legacy_only=legacy_only,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/summarize")
    def summarize(
        pattern: str,
        format: str = "md",
        mode: str = "latest",
        sort: str = "p99",
        recent: int = 0,
        top: int = 0,
    ) -> dict:
        try:
            return build_summary_bundle(
                pattern=pattern,
                format=format,
                mode=mode,
                sort=sort,
                recent=recent,
                top=top,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/history-report")
    def history_report(
        pattern: str = "results/*.json",
        model: str = "",
        engine: str = "",
        device: str = "",
        precision: str = "",
        batch: int | None = None,
        height: int | None = None,
        width: int | None = None,
        include_markdown: bool = False,
    ) -> dict:
        try:
            return build_history_report_outputs(
                pattern=pattern,
                model=model,
                engine=engine,
                device=device,
                precision=precision,
                batch=batch,
                height=height,
                width=width,
                include_markdown=include_markdown,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/compare")
    def compare(
        base_path: str,
        new_path: str,
    ) -> dict:
        try:
            return build_compare_bundle(
                base_path=base_path,
                new_path=new_path,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
