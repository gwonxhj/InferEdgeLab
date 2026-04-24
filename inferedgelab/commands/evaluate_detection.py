from __future__ import annotations

import os
from datetime import datetime

import typer
from rich import print as rprint

from inferedgelab.core.detection_evaluator import (
    build_accuracy_payload,
    evaluate_detection_engine,
    save_accuracy_payload,
)
from inferedgelab.engines.registry import (
    normalize_engine_name,
    supported_engines,
    supported_engines_display,
)
from inferedgelab.result.saver import save_result
from inferedgelab.result.schema import BenchmarkResult
from inferedgelab.utils.system_info import collect_system_snapshot


def _exit_with_runtime_error(message: str) -> None:
    rprint(f"[red]{message}[/red]")
    raise typer.Exit(code=1)


def evaluate_detection_cmd(
    model_path: str = typer.Argument(..., help="평가할 ONNX 모델 경로"),
    engine: str = typer.Option("tensorrt", "--engine", help="추론 엔진 선택"),
    engine_path: str = typer.Option("", "--engine-path", help="Runtime artifact 경로"),
    image_dir: str = typer.Option(..., "--image-dir", help="평가 이미지 디렉토리"),
    label_dir: str = typer.Option(..., "--label-dir", help="YOLO txt 라벨 디렉토리"),
    num_classes: int = typer.Option(1, "--num-classes", help="클래스 수"),
    precision: str = typer.Option("fp16", "--precision", help="precision 메타데이터 (fp32, fp16, int8)"),
    conf_threshold: float = typer.Option(0.2, "--conf-threshold", help="confidence threshold"),
    nms_threshold: float = typer.Option(0.45, "--nms-threshold", help="NMS IoU threshold"),
    iou_threshold: float = typer.Option(0.5, "--iou-threshold", help="evaluation IoU threshold"),
    rgb: bool = typer.Option(True, "--rgb/--bgr", help="Use RGB input conversion after OpenCV read"),
    out_json: str = typer.Option("", "--out-json", help="Accuracy payload 저장 경로"),
    out_dir: str = typer.Option("results", "--out-dir", help="structured result 저장 디렉토리"),
    save_structured_result: bool = typer.Option(
        True,
        "--save-structured-result/--no-save-structured-result",
        help="Whether to save BenchmarkResult output",
    ),
):
    rprint(f"[bold]Evaluating detection[/bold]: {model_path}")

    precision = precision.lower().strip()
    allowed_precisions = {"fp32", "fp16", "int8"}
    if precision not in allowed_precisions:
        raise typer.BadParameter("--precision must be one of: fp32, fp16, int8")

    engine = normalize_engine_name(engine)
    allowed_engines = supported_engines()
    if engine not in allowed_engines:
        raise typer.BadParameter(f"--engine must be one of: {supported_engines_display()}")

    if engine in {"tensorrt", "rknn"} and not engine_path.strip():
        raise typer.BadParameter(f"--engine-path is required when --engine {engine} is used")

    if num_classes <= 0:
        raise typer.BadParameter("--num-classes must be >= 1")

    try:
        eval_result = evaluate_detection_engine(
            model_path=model_path,
            engine_name=engine,
            engine_path=engine_path.strip() or None,
            image_dir=image_dir,
            label_dir=label_dir,
            num_classes=num_classes,
            conf_threshold=conf_threshold,
            nms_threshold=nms_threshold,
            iou_threshold=iou_threshold,
            use_rgb=rgb,
            input_size=640,
        )
    except RuntimeError as exc:
        _exit_with_runtime_error(str(exc))

    accuracy_payload = build_accuracy_payload(eval_result)

    saved_json_path = ""
    if out_json.strip():
        save_accuracy_payload(accuracy_payload, out_json)
        saved_json_path = out_json

    result_path = ""
    if save_structured_result:
        structured = BenchmarkResult(
            model=os.path.basename(model_path),
            engine=eval_result.engine,
            device=eval_result.device,
            precision=precision,
            batch=1,
            height=640,
            width=640,
            mean_ms=None,
            p99_ms=None,
            timestamp=datetime.utcnow().strftime("%Y%m%d-%H%M%S"),
            source_report_path=None,
            system=collect_system_snapshot(),
            run_config={
                "mode": "evaluate-detection",
                "task": "detection",
                "engine": engine,
                "engine_path": engine_path.strip() or None,
                "num_classes": num_classes,
            },
            accuracy=accuracy_payload,
            extra={
                "evaluation": {
                    "task": eval_result.task,
                    "model_input": eval_result.model_input,
                    "actual_input_shape": eval_result.actual_input_shape,
                    "dataset": eval_result.dataset,
                    "evaluation_config": eval_result.evaluation_config,
                    "engine_path": engine_path.strip() or None,
                    "runtime_artifact_path": eval_result.extra.get("runtime_artifact_path"),
                }
            },
        )
        result_path = save_result(structured, out_dir=out_dir)

    rprint(f"Engine          : {eval_result.engine}")
    rprint(f"Images          : {image_dir}")
    rprint(f"Labels          : {label_dir}")
    rprint(f"Samples         : {eval_result.sample_count}")
    rprint(f"Precision       : {eval_result.metrics['precision']:.4f}")
    rprint(f"Recall          : {eval_result.metrics['recall']:.4f}")
    rprint(f"F1 Score        : {eval_result.metrics['f1_score']:.4f}")
    rprint(f"mAP@50          : {eval_result.metrics['map50']:.4f}")
    rprint(f"mAP@50-95       : {eval_result.metrics['map50_95']:.4f}")

    if saved_json_path:
        rprint(f"[cyan]Saved accuracy[/cyan]  : {saved_json_path}")
    if result_path:
        rprint(f"[cyan]Saved structured result[/cyan]: {result_path}")
