from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run_runtime_inference(worker_request: dict[str, Any]) -> dict[str, Any]:
    """Run the Runtime CLI once and return a worker_response payload.

    This is a development-only execution bridge. It does not introduce a
    daemon, queue, database, Forge build step, or TensorRT expansion.
    """

    job_id = _require_string(worker_request, "job_id")
    model_path = _first_string(worker_request, ("model_path", "artifact_path"))
    if not model_path:
        return _failed_response(
            job_id,
            "runtime_input_missing",
            "worker_request requires model_path or artifact_path",
        )

    options = worker_request.get("options") if isinstance(worker_request.get("options"), dict) else {}
    runtime_cli = str(options.get("runtime_cli_path") or "./build/inferedge-runtime")

    with tempfile.TemporaryDirectory(prefix="inferedgelab-runtime-") as tmp_dir:
        output_path = Path(tmp_dir) / "runtime_result.json"
        command = [
            runtime_cli,
            "--model",
            model_path,
            "--runs",
            str(options.get("runs") or 5),
            "--warmup",
            str(options.get("warmup") or 1),
            "--output",
            str(output_path),
        ]

        for option_name, cli_name in (
            ("backend", "--engine"),
            ("engine", "--engine"),
            ("target", "--device"),
            ("device", "--device"),
            ("batch", "--batch"),
            ("height", "--height"),
            ("width", "--width"),
        ):
            value = options.get(option_name)
            if value is not None:
                command.extend([cli_name, str(value)])

        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            return _failed_response(job_id, "runtime_cli_unavailable", str(exc))

        if completed.returncode != 0:
            return _failed_response(
                job_id,
                "runtime_cli_failed",
                completed.stderr.strip() or completed.stdout.strip() or "Runtime CLI failed",
            )

        try:
            runtime_result = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _failed_response(job_id, "runtime_result_unreadable", str(exc))

    runtime_result = _normalize_runtime_result(runtime_result, model_path=model_path, options=options)
    return {
        "job_id": job_id,
        "status": "completed",
        "forge_metadata": _build_forge_metadata(worker_request),
        "runtime_result": runtime_result,
        "completed_at": _utc_now_iso(),
    }


def _normalize_runtime_result(
    runtime_result: dict[str, Any],
    *,
    model_path: str,
    options: dict[str, Any],
) -> dict[str, Any]:
    latency = runtime_result.get("latency_ms") if isinstance(runtime_result.get("latency_ms"), dict) else {}
    run_config = runtime_result.get("run_config") if isinstance(runtime_result.get("run_config"), dict) else {}
    extra = runtime_result.get("extra") if isinstance(runtime_result.get("extra"), dict) else {}

    normalized = dict(runtime_result)
    normalized.setdefault("model_path", normalized.get("model") or model_path)
    normalized.setdefault("engine", normalized.get("engine_backend") or normalized.get("backend") or options.get("backend") or "onnxruntime")
    normalized.setdefault("device", normalized.get("device_name") or normalized.get("target") or options.get("target") or "cpu")
    normalized.setdefault("precision", options.get("precision") or normalized.get("precision") or "unknown")
    normalized.setdefault("batch", _first_present(normalized, run_config, options, "batch", default=1))
    normalized.setdefault("height", _first_present(normalized, run_config, options, "height", default=1))
    normalized.setdefault("width", _first_present(normalized, run_config, options, "width", default=1))
    normalized.setdefault("mean_ms", latency.get("mean", normalized.get("mean_ms", 0.0)))
    normalized.setdefault("p50_ms", latency.get("p50", normalized.get("median_ms", normalized.get("p50_ms", 0.0))))
    normalized.setdefault("p95_ms", latency.get("p95", normalized.get("p95_ms", 0.0)))
    normalized.setdefault("p99_ms", latency.get("p99", normalized.get("p99_ms", 0.0)))
    normalized.setdefault("timestamp", _utc_now_iso())
    normalized["extra"] = extra
    normalized["extra"].setdefault("runtime_artifact_path", model_path)
    normalized["extra"].setdefault("runtime_executor_mode", "subprocess_dev")
    return normalized


def _build_forge_metadata(worker_request: dict[str, Any]) -> dict[str, Any]:
    input_summary = worker_request.get("input_summary") if isinstance(worker_request.get("input_summary"), dict) else {}
    options = worker_request.get("options") if isinstance(worker_request.get("options"), dict) else {}
    return {
        "metadata_path": worker_request.get("metadata_path"),
        "manifest_path": worker_request.get("manifest_path"),
        "model_path": worker_request.get("model_path"),
        "artifact_path": worker_request.get("artifact_path"),
        "backend": options.get("backend") or options.get("engine"),
        "target": options.get("target") or options.get("device"),
        "precision": options.get("precision"),
        "provenance": input_summary.get("provenance") or options.get("provenance"),
    }


def _failed_response(job_id: str, code: str, message: str) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "status": "failed",
        "error": {
            "code": code,
            "message": message,
            "stage": "runtime",
        },
        "failed_at": _utc_now_iso(),
    }


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _first_string(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _first_present(
    primary: dict[str, Any],
    secondary: dict[str, Any],
    tertiary: dict[str, Any],
    key: str,
    *,
    default: Any,
) -> Any:
    for data in (primary, secondary, tertiary):
        value = data.get(key)
        if value is not None:
            return value
    return default


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
