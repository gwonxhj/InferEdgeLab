from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from inferedgelab import __version__
from inferedgelab.services.compare_service import build_compare_bundle
from inferedgelab.services.compare_service import build_compare_latest_bundle
from inferedgelab.services.history_report_service import build_history_report_outputs
from inferedgelab.services.list_results_service import build_list_results_bundle
from inferedgelab.services.summarize_service import build_summary_bundle


def create_app() -> FastAPI:
    app = FastAPI(title="InferEdgeLab API")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "inferedgelab-api", "version": __version__}

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
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
        try:
            return build_compare_bundle(
                base_path=base_path,
                new_path=new_path,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/compare-latest")
    def compare_latest(
        pattern: str = "results/*.json",
        model: str = "",
        engine: str = "",
        device: str = "",
        precision: str = "",
        selection_mode: str = "same_precision",
        latency_improve_threshold: float | None = None,
        latency_regress_threshold: float | None = None,
        accuracy_improve_threshold: float | None = None,
        accuracy_regress_threshold: float | None = None,
        tradeoff_caution_threshold: float | None = None,
        tradeoff_risky_threshold: float | None = None,
        tradeoff_severe_threshold: float | None = None,
        pyproject_path: str = "pyproject.toml",
    ) -> dict[str, Any]:
        try:
            return build_compare_latest_bundle(
                pattern=pattern,
                model=model,
                engine=engine,
                device=device,
                precision=precision,
                selection_mode=selection_mode,
                latency_improve_threshold=latency_improve_threshold,
                latency_regress_threshold=latency_regress_threshold,
                accuracy_improve_threshold=accuracy_improve_threshold,
                accuracy_regress_threshold=accuracy_regress_threshold,
                tradeoff_caution_threshold=tradeoff_caution_threshold,
                tradeoff_risky_threshold=tradeoff_risky_threshold,
                tradeoff_severe_threshold=tradeoff_severe_threshold,
                pyproject_path=pyproject_path,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
