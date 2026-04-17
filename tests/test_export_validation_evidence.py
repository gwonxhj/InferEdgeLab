from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def import_export_validation_evidence_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "export_validation_evidence.py"
    spec = importlib.util.spec_from_file_location("test_export_validation_evidence_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_result(
    tmp_path: Path,
    name: str,
    *,
    timestamp: str,
    mean_ms: float,
    p99_ms: float,
    runtime_artifact_path: str,
) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": "resnet18.onnx",
                "engine": "tensorrt",
                "device": "gpu",
                "precision": "fp16",
                "batch": 1,
                "height": 224,
                "width": 224,
                "mean_ms": mean_ms,
                "p99_ms": p99_ms,
                "timestamp": timestamp,
                "source_report_path": "reports/resnet18.json",
                "system": {"os": "Linux"},
                "run_config": {
                    "engine": "tensorrt",
                    "engine_path": runtime_artifact_path,
                    "requested_batch": 1,
                    "requested_height": 224,
                    "requested_width": 224,
                },
                "accuracy": {},
                "extra": {
                    "runtime_artifact_path": runtime_artifact_path,
                    "primary_input_name": "input",
                    "resolved_input_shapes": {"input": [1, 3, 224, 224]},
                    "effective_batch": 1,
                    "effective_height": 224,
                    "effective_width": 224,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(path)


def test_export_validation_evidence_creates_markdown_with_compare_and_judgement_content(tmp_path):
    exporter = import_export_validation_evidence_module()
    base_result = write_result(
        tmp_path,
        "base.json",
        timestamp="20260417-100000",
        mean_ms=14.2246,
        p99_ms=14.7342,
        runtime_artifact_path="models/resnet18.engine",
    )
    new_result = write_result(
        tmp_path,
        "new.json",
        timestamp="20260417-101000",
        mean_ms=14.0697,
        p99_ms=14.7342,
        runtime_artifact_path="models/resnet18.engine",
    )
    markdown_out = tmp_path / "evidence" / "resnet18.md"

    saved_path = exporter.export_validation_evidence(
        base_result=base_result,
        new_result=new_result,
        label="Jetson TensorRT Validation Evidence",
        markdown_out=str(markdown_out),
    )

    text = Path(saved_path).read_text(encoding="utf-8")

    assert markdown_out.exists()
    assert "## Jetson TensorRT Validation Evidence" in text
    assert "Precision pair: `fp16_vs_fp16`" in text
    assert "Overall: **neutral**" in text
    assert "**Summary**:" in text
    assert "| mean_ms | 14.2246 | 14.0697 |" in text
    assert "| p99_ms | 14.7342 | 14.7342 |" in text
    assert "Base runtime_artifact_path: `models/resnet18.engine`" in text
    assert "New runtime_artifact_path: `models/resnet18.engine`" in text
    assert "Base primary_input_name: `input`" in text
    assert "New primary_input_name: `input`" in text
    assert "Base resolved_input_shapes: `{'input': [1, 3, 224, 224]}`" in text
    assert "New resolved_input_shapes: `{'input': [1, 3, 224, 224]}`" in text


def test_export_validation_evidence_includes_optional_report_paths(tmp_path):
    exporter = import_export_validation_evidence_module()
    base_result = write_result(
        tmp_path,
        "base.json",
        timestamp="20260417-100000",
        mean_ms=14.2246,
        p99_ms=14.7342,
        runtime_artifact_path="models/resnet18.engine",
    )
    new_result = write_result(
        tmp_path,
        "new.json",
        timestamp="20260417-101000",
        mean_ms=14.0697,
        p99_ms=14.7342,
        runtime_artifact_path="models/resnet18.engine",
    )
    markdown_out = tmp_path / "evidence.md"

    exporter.export_validation_evidence(
        base_result=base_result,
        new_result=new_result,
        label="Jetson TensorRT Validation Evidence",
        markdown_out=str(markdown_out),
        report_markdown_path="reports/validation/resnet18_tensorrt_latest.md",
        report_html_path="reports/validation/resnet18_tensorrt_latest.html",
    )

    text = markdown_out.read_text(encoding="utf-8")

    assert "### Reports" in text
    assert "- Markdown: `reports/validation/resnet18_tensorrt_latest.md`" in text
    assert "- HTML: `reports/validation/resnet18_tensorrt_latest.html`" in text
