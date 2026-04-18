from __future__ import annotations

import json

import pytest

from edgebench.services.history_report_service import build_history_report_outputs


def write_result(
    tmp_path,
    name: str,
    *,
    timestamp: str,
    mean_ms: float,
    p99_ms: float,
    model: str = "resnet18",
    engine: str = "onnxruntime",
    device: str = "cpu",
    precision: str = "fp32",
    batch: int = 1,
    height: int = 224,
    width: int = 224,
) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "timestamp": timestamp,
                "mean_ms": mean_ms,
                "p99_ms": p99_ms,
                "model": model,
                "engine": engine,
                "device": device,
                "precision": precision,
                "batch": batch,
                "height": height,
                "width": width,
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_build_history_report_outputs_includes_markdown_and_sorted_history(tmp_path):
    write_result(tmp_path, "newer.json", timestamp="2026-04-14T10:00:00Z", mean_ms=11.0, p99_ms=13.0)
    write_result(tmp_path, "older.json", timestamp="2026-04-14T09:00:00Z", mean_ms=10.0, p99_ms=12.0)

    outputs = build_history_report_outputs(
        pattern=str(tmp_path / "*.json"),
        model="resnet18",
        include_markdown=True,
    )

    assert [item["timestamp"] for item in outputs["history"]] == [
        "2026-04-14T09:00:00Z",
        "2026-04-14T10:00:00Z",
    ]
    assert outputs["filters"] == {
        "model": "resnet18",
        "engine": "",
        "device": "",
        "precision": "",
        "batch": None,
        "height": None,
        "width": None,
        "pattern": str(tmp_path / "*.json"),
    }
    assert isinstance(outputs["html"], str) and outputs["html"]
    assert isinstance(outputs["markdown"], str) and outputs["markdown"]


def test_build_history_report_outputs_omits_markdown_when_disabled(tmp_path):
    write_result(tmp_path, "item.json", timestamp="2026-04-14T09:00:00Z", mean_ms=10.0, p99_ms=12.0)

    outputs = build_history_report_outputs(
        pattern=str(tmp_path / "*.json"),
        include_markdown=False,
    )

    assert len(outputs["history"]) == 1
    assert outputs["markdown"] is None
    assert isinstance(outputs["html"], str) and outputs["html"]


def test_build_history_report_outputs_raises_when_no_result_matches(tmp_path):
    write_result(
        tmp_path,
        "item.json",
        timestamp="2026-04-14T09:00:00Z",
        mean_ms=10.0,
        p99_ms=12.0,
        model="resnet18",
    )

    with pytest.raises(ValueError, match="조건에 맞는 structured result가 없습니다."):
        build_history_report_outputs(
            pattern=str(tmp_path / "*.json"),
            model="mobilenet",
        )
