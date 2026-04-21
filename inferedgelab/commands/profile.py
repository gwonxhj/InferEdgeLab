from __future__ import annotations

import os
from datetime import datetime

import typer
from rich import print as rprint

from inferedgelab.utils.system_info import collect_system_snapshot

from inferedgelab.core.analyzer import analyze_onnx, collect_package_versions, collect_system_info
from inferedgelab.core.profiler import profile_model
from inferedgelab.core.report import (
    EdgeBenchReport,
    ModelInfo,
    StaticAnalysis,
    SystemInfo,
    RuntimeProfile,
    utc_now_iso,
)
from inferedgelab.engines.registry import normalize_engine_name, supported_engines
from inferedgelab.result.schema import BenchmarkResult
from inferedgelab.result.saver import save_result



def _exit_with_runtime_error(message: str) -> None:
    rprint(f"[red]{message}[/red]")
    raise typer.Exit(code=1)

def profile_cmd(
    model_path: str = typer.Argument(..., help="프로파일링할 ONNX 모델 경로"),
    warmup: int = typer.Option(10, "--warmup", help="워밍업 반복 횟수"),
    runs: int = typer.Option(100, "--runs", help="측정 반복 횟수"),
    batch: int = typer.Option(1, "--batch", help="배치 크기(입력 0번째 차원 override)"),
    height: int = typer.Option(0, "--height", help="입력 height override (0이면 사용 안 함)"),
    width: int = typer.Option(0, "--width", help="입력 width override(0이면 사용 안 함)"),
    intra_threads: int = typer.Option(1, "--intra-threads", help="ONNX Runtime intra_op_num_threads"),
    inter_threads: int = typer.Option(1, "--inter-threads", help="ONNX Runtime inter_op_num_threads"),
    engine: str = typer.Option(
        "onnxruntime",
        "--engine",
        help="추론 엔진 선택 (현재 지원: onnxruntime, tensorrt, rknn)",
    ),
    precision: str = typer.Option("fp32", "--precision", help="precision 메타데이터 (fp32, fp16, int8)"),
    engine_path: str = typer.Option(
        "",
        "--engine-path",
        help="엔진 파일 경로 (예: TensorRT .engine 또는 RKNN .rknn). tensorrt/rknn 사용 시 필수",
    ),
    rknn_target: str = typer.Option(
        "",
        "--rknn-target",
        help="RKNN runtime target device name (e.g. rk3588)",
    ),
    device_name: str = typer.Option(
        "",
        "--device-name",
        help="Optional device metadata override stored with the result",
    ),
    output: str = typer.Option("", "--output", "-o", help="JSON 리포트 저장 경로(미지정 시 자동 파일명)"),
    no_hash: bool = typer.Option(True, "--no-hash/--hash", help="profile 시 해시 계산(기본 off)"),
):
    rprint(f"[bold]Profiling[/bold]: {model_path}")

    precision = precision.lower().strip()
    allowed_precisions = {"fp32", "fp16", "int8"}
    if precision not in allowed_precisions:
        raise typer.BadParameter("--precision must be one of: fp32, fp16, int8")

    engine = normalize_engine_name(engine)
    allowed_engines = supported_engines()
    if engine not in allowed_engines:
        raise typer.BadParameter(
            f"--engine must be one of: {', '.join(sorted(allowed_engines))}"
        )
    
    if engine in {"tensorrt", "rknn"} and not engine_path.strip():
        raise typer.BadParameter(f"--engine-path is required when --engine {engine} is used")

    result = analyze_onnx(
        model_path,
        compute_hash=(not no_hash),
        height=height if height > 0 else None,
        width=width if width > 0 else None,
    )
    sysinfo = collect_system_info()
    pkgs = collect_package_versions()
    system_snapshot = collect_system_snapshot()

    try:
        prof = profile_model(
            model_path=model_path,
            engine=engine,
            engine_path=engine_path.strip() or None,
            warmup=warmup,
            runs=runs,
            batch=batch,
            height=height if height > 0 else None,
            width=width if width > 0 else None,
            intra_threads=intra_threads,
            inter_threads=inter_threads,
            rknn_target=rknn_target.strip() or None,
            device_name=device_name.strip() or None,
        )
    except RuntimeError as exc:
        _exit_with_runtime_error(str(exc))

    effective_batch = prof.extra.get("effective_batch")
    if effective_batch is None:
        effective_batch = batch if batch is not None else 1

    effective_height = prof.extra.get("effective_height")
    if effective_height is None:
        effective_height = height if height > 0 else 0

    effective_width = prof.extra.get("effective_width")
    if effective_width is None:
        effective_width = width if width > 0 else 0

    report = EdgeBenchReport(
        schema_version="0.1",
        timestamp=utc_now_iso(),
        model=ModelInfo(
            path=model_path,
            file_size_bytes=result.file_size_bytes,
            sha256=(None if no_hash else result.sha256),
        ),
        static=StaticAnalysis(
            parameters=result.parameters,
            inputs=result.inputs,
            outputs=result.outputs,
            flops_estimate=result.flops_estimate,
            flops_breakdown=result.flops_breakdown,
            flops_hotspots=result.flops_hotspots,
            flops_assumptions=result.flops_assumptions,
        ),
        runtime=RuntimeProfile(
            engine=prof.engine,
            device=prof.device,
            warmup=prof.warmup,
            runs=prof.runs,
            latency_ms=prof.latency_ms,
            extra=prof.extra,
        ),
        system=SystemInfo(
            os=sysinfo["os"],
            python=sysinfo["python"],
            packages=pkgs,
        ),
        meta={"machine": sysinfo.get("machine"), "notes": "Phase 1 profile"},
    )

    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    if not output:
        os.makedirs("reports", exist_ok=True)
        model_name = os.path.splitext(os.path.basename(model_path))[0]
        output = os.path.join(
            "reports",
            f"{model_name}__{prof.engine}_{prof.device}__b{effective_batch}__h{effective_height}w{effective_width}__r{runs}__{ts}.json",
        )

    report.write_json(output)
    rprint(f"[green]Saved[/green]: {output}")

    structured = BenchmarkResult(
        model=os.path.basename(model_path),
        engine=prof.engine,
        device=prof.device,
        precision=precision,
        batch=effective_batch,
        height=effective_height,
        width=effective_width,
        mean_ms=prof.latency_ms.get("mean"),
        p99_ms=prof.latency_ms.get("p99"),
        timestamp=ts,
        source_report_path=output,
        system=system_snapshot,
        run_config={
            "engine": engine,
            "engine_path": engine_path.strip() or None,
            "rknn_target": rknn_target.strip() or None,
            "device_name": device_name.strip() or None,
            "warmup": warmup,
            "runs": runs,
            "intra_threads": intra_threads,
            "inter_threads": inter_threads,
            "requested_batch": batch,
            "requested_height": height if height > 0 else None,
            "requested_width": width if width > 0 else None,
        },
        extra={
            "input_names": prof.extra.get("input_names"),
            "runtime_artifact_path": engine_path.strip() or None,
            "rknn_target": rknn_target.strip() or None,
            "device_name": device_name.strip() or None,
            "primary_input_name": prof.extra.get("primary_input_name"),
            "resolved_input_shapes": prof.extra.get("resolved_input_shapes"),
            "effective_batch": effective_batch,
            "effective_height": effective_height,
            "effective_width": effective_width,
        },
    )

    result_path = save_result(structured)
    rprint(f"[cyan]Saved structured result[/cyan]: {result_path}")
