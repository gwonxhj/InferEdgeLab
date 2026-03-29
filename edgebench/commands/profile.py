from __future__ import annotations

import os
from datetime import datetime

import typer
from rich import print as rprint

from edgebench.utils.system_info import collect_system_snapshot

from edgebench.core.analyzer import analyze_onnx, collect_package_versions, collect_system_info
from edgebench.core.profiler import profile_model, normalize_engine_name
from edgebench.core.report import (
    EdgeBenchReport,
    ModelInfo,
    StaticAnalysis,
    SystemInfo,
    RuntimeProfile,
    utc_now_iso,
)
from edgebench.result.schema import BenchmarkResult
from edgebench.result.saver import save_result


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
        help="추론 엔진 선택 (현재 지원: onnxruntime)",
    ),
    precision: str = typer.Option("fp32", "--precision", help="precision 메타데이터 (fp32, fp16, int8)"),
    output: str = typer.Option("", "--output", "-o", help="JSON 리포트 저장 경로(미지정 시 자동 파일명)"),
    no_hash: bool = typer.Option(True, "--no-hash/--hash", help="profile 시 해시 계산(기본 off)"),
):
    rprint(f"[bold]Profiling[/bold]: {model_path}")

    precision = precision.lower().strip()
    allowed_precisions = {"fp32", "fp16", "int8"}
    if precision not in allowed_precisions:
        raise typer.BadParameter("--precision must be one of: fp32, fp16, int8")

    engine = normalize_engine_name(engine)
    allowed_engines = {"onnxruntime"}
    if engine not in allowed_engines:
        raise typer.BadParameter("--engine must be one of: onnxruntime")

    result = analyze_onnx(
        model_path,
        compute_hash=(not no_hash),
        height=height if height > 0 else None,
        width=width if width > 0 else None,
    )
    sysinfo = collect_system_info()
    pkgs = collect_package_versions()
    system_snapshot = collect_system_snapshot()

    prof = profile_model(
        model_path=model_path,
        engine=engine,
        warmup=warmup,
        runs=runs,
        batch=batch,
        height=height if height > 0 else None,
        width=width if width > 0 else None,
        intra_threads=intra_threads,
        inter_threads=inter_threads,
    )

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
            f"{model_name}__{prof.engine}_{prof.device}__b{batch}__h{height or 0}w{width or 0}__r{runs}__{ts}.json",
        )

    report.write_json(output)
    rprint(f"[green]Saved[/green]: {output}")

    structured = BenchmarkResult(
        model=os.path.basename(model_path),
        engine=prof.engine,
        device=prof.device,
        precision=precision,
        batch=batch,
        height=height if height > 0 else 0,
        width=width if width > 0 else 0,
        mean_ms=prof.latency_ms.get("mean"),
        p99_ms=prof.latency_ms.get("p99"),
        timestamp=ts,
        source_report_path=output,
        system=system_snapshot,
        run_config={
            "engine": engine,
            "warmup": warmup,
            "runs": runs,
            "intra_threads": intra_threads,
            "inter_threads": inter_threads,
        },
        extra={
            "input_names": prof.extra.get("input_names"),
        },
    )

    result_path = save_result(structured)
    rprint(f"[cyan]Saved structured result[/cyan]: {result_path}")