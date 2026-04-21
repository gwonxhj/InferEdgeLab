from __future__ import annotations

import os
from datetime import datetime

import typer
from rich import print as rprint

from inferedgelab.core.evaluator import evaluate_classification_top1
from inferedgelab.result.schema import BenchmarkResult
from inferedgelab.result.saver import save_result
from inferedgelab.utils.system_info import collect_system_snapshot
from inferedgelab.engines.registry import (
    normalize_engine_name,
    supported_engines,
    supported_engines_display,
)


def _exit_with_runtime_error(message: str) -> None:
    rprint(f"[red]{message}[/red]")
    raise typer.Exit(code=1)

def _resolve_shape_dim(shape: list[object], index: int) -> int:
    if index >= len(shape):
        return 0

    value = shape[index]
    if value is None:
        return 0

    return int(value)


def evaluate_cmd(
    model_path: str = typer.Argument(..., help="평가할 ONNX 모델 경로"),
    dataset_manifest: str = typer.Option(..., "--dataset-manifest", help="JSONL manifest 경로"),
    task: str = typer.Option("classification", "--task", help="현재는 classification만 지원"),
    precision: str = typer.Option("fp32", "--precision", help="precision 메타데이터 (fp32, fp16, int8)"),
    input_key: str = typer.Option("input", "--input-key", help="manifest에서 입력 경로 키 이름"),
    label_key: str = typer.Option("label", "--label-key", help="manifest에서 정답 라벨 키 이름"),
    intra_threads: int = typer.Option(1, "--intra-threads", help="ONNX Runtime intra_op_num_threads"),
    inter_threads: int = typer.Option(1, "--inter-threads", help="ONNX Runtime inter_op_num_threads"),
    engine: str = typer.Option(
        "onnxruntime",
        "--engine",
        help="추론 엔진 선택 (현재 지원: onnxruntime, tensorrt)",
    ),
    out_dir: str = typer.Option("results", "--out-dir", help="structured result 저장 디렉토리"),
):
    rprint(f"[bold]Evaluating[/bold]: {model_path}")

    task = task.lower().strip()
    if task != "classification":
        raise typer.BadParameter("현재 evaluate 1차 버전은 --task classification 만 지원합니다.")

    precision = precision.lower().strip()
    allowed_precisions = {"fp32", "fp16", "int8"}
    if precision not in allowed_precisions:
        raise typer.BadParameter("--precision must be one of: fp32, fp16, int8")

    engine = normalize_engine_name(engine)
    allowed_engines = supported_engines()
    if engine not in allowed_engines:
        raise typer.BadParameter(
            f"--engine must be one of: {supported_engines_display()}"
        )

    try:
        eval_result = evaluate_classification_top1(
            model_path=model_path,
            manifest_path=dataset_manifest,
            input_key=input_key,
            label_key=label_key,
            intra_threads=intra_threads,
            inter_threads=inter_threads,
            engine_name=engine,
        )
    except RuntimeError as exc:
        _exit_with_runtime_error(str(exc))

    actual_input_shape = eval_result.actual_input_shape or []
    model_input_shape = actual_input_shape or (eval_result.model_input.get("shape") or [])

    structured = BenchmarkResult(
        model=os.path.basename(model_path),
        engine=eval_result.engine,
        device=eval_result.device,
        precision=precision,
        batch=_resolve_shape_dim(model_input_shape, 0),
        height=_resolve_shape_dim(model_input_shape, 2),
        width=_resolve_shape_dim(model_input_shape, 3),
        mean_ms=None,
        p99_ms=None,
        timestamp=datetime.utcnow().strftime("%Y%m%d-%H%M%S"),
        source_report_path=None,
        system=collect_system_snapshot(),
        run_config={
            "mode": "evaluate",
            "task": task,
            "engine": engine,
            "intra_threads": intra_threads,
            "inter_threads": inter_threads,
        },
        accuracy={
            "task": eval_result.task,
            "dataset": {
                "name": os.path.basename(dataset_manifest),
                "path": dataset_manifest,
            },
            "sample_count": eval_result.sample_count,
            "correct_count": eval_result.correct_count,
            "metrics": eval_result.metrics,
            "evaluation_config": {
                "input_key": input_key,
                "label_key": label_key,
                "input_format": "npy",
                "intra_threads": intra_threads,
                "inter_threads": inter_threads,
            },
            "notes": eval_result.notes,
        },
        extra={
            "evaluation": {
                "task": eval_result.task,
                "model_input": eval_result.model_input,
                "actual_input_shape": eval_result.actual_input_shape,
                "input_format": "npy",
            }
        },
    )

    result_path = save_result(structured, out_dir=out_dir)

    rprint(f"Task            : {eval_result.task}")
    rprint(f"Samples         : {eval_result.sample_count}")
    rprint(f"Correct         : {eval_result.correct_count}")
    rprint(f"Top-1 Accuracy  : {eval_result.metrics['top1_accuracy']:.4f}")
    rprint(f"[cyan]Saved structured result[/cyan]: {result_path}")
