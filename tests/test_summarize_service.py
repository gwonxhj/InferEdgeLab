from __future__ import annotations

import json
from pathlib import Path

import pytest

from edgebench.services.summarize_service import build_summary_markdown


def write_report(
    tmp_path: Path,
    name: str,
    *,
    model_name: str,
    mean_ms: float,
    p99_ms: float,
    timestamp: str,
    engine: str = "onnxruntime",
    device: str = "cpu",
    batch: int = 1,
    height: int = 224,
    width: int = 224,
    flops_estimate: int = 126444160,
) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": {"path": f"models/{model_name}"},
                "static": {"flops_estimate": flops_estimate},
                "runtime": {
                    "engine": engine,
                    "device": device,
                    "latency_ms": {"mean": mean_ms, "p99": p99_ms},
                    "extra": {"batch": batch, "height": height, "width": width},
                },
                "timestamp": timestamp,
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_build_summary_markdown_latest_keeps_only_latest_per_group(tmp_path):
    write_report(
        tmp_path,
        "older.json",
        model_name="toy224.onnx",
        mean_ms=0.500,
        p99_ms=0.600,
        timestamp="2026-04-16T09:00:00Z",
    )
    write_report(
        tmp_path,
        "newer.json",
        model_name="toy224.onnx",
        mean_ms=0.450,
        p99_ms=0.488,
        timestamp="2026-04-16T10:00:00Z",
    )

    text = build_summary_markdown(pattern=str(tmp_path / "*.json"), mode="latest", sort="p99")

    assert "## Latest (recommended)" in text
    assert text.count("| toy224.onnx | onnxruntime | cpu |") == 1
    assert "0.488" in text
    assert "2026-04-16T10:00:00Z" in text


def test_build_summary_markdown_history_keeps_all_rows(tmp_path):
    write_report(
        tmp_path,
        "older.json",
        model_name="toy224.onnx",
        mean_ms=0.500,
        p99_ms=0.600,
        timestamp="2026-04-16T09:00:00Z",
    )
    write_report(
        tmp_path,
        "newer.json",
        model_name="toy224.onnx",
        mean_ms=0.450,
        p99_ms=0.488,
        timestamp="2026-04-16T10:00:00Z",
    )

    text = build_summary_markdown(pattern=str(tmp_path / "*.json"), mode="history", sort="time")

    assert "## History (raw)" in text
    assert text.count("| toy224.onnx | onnxruntime | cpu |") == 2


def test_build_summary_markdown_both_contains_both_sections(tmp_path):
    write_report(
        tmp_path,
        "older.json",
        model_name="toy224.onnx",
        mean_ms=0.500,
        p99_ms=0.600,
        timestamp="2026-04-16T09:00:00Z",
    )
    write_report(
        tmp_path,
        "newer.json",
        model_name="toy224.onnx",
        mean_ms=0.450,
        p99_ms=0.488,
        timestamp="2026-04-16T10:00:00Z",
    )

    text = build_summary_markdown(pattern=str(tmp_path / "*.json"), mode="both", sort="time")

    assert "## Latest (recommended)" in text
    assert "## History (raw)" in text
    assert text.count("| Model | Engine | Device | Batch | Input(HxW) | FLOPs | Mean (ms) | P99 (ms) | Timestamp (UTC) |") == 2


def test_build_summary_markdown_invalid_mode_raises_value_error(tmp_path):
    write_report(
        tmp_path,
        "one.json",
        model_name="toy224.onnx",
        mean_ms=0.450,
        p99_ms=0.488,
        timestamp="2026-04-16T10:00:00Z",
    )

    with pytest.raises(ValueError, match="--mode must be one of: latest, history, both"):
        build_summary_markdown(pattern=str(tmp_path / "*.json"), mode="invalid", sort="time")


def test_build_summary_markdown_recent_limits_to_latest_n_before_grouping(tmp_path):
    write_report(
        tmp_path,
        "first.json",
        model_name="toy224.onnx",
        mean_ms=0.700,
        p99_ms=0.800,
        timestamp="2026-04-16T08:00:00Z",
    )
    write_report(
        tmp_path,
        "second.json",
        model_name="toy224.onnx",
        mean_ms=0.500,
        p99_ms=0.600,
        timestamp="2026-04-16T09:00:00Z",
    )
    write_report(
        tmp_path,
        "third.json",
        model_name="toy320.onnx",
        mean_ms=0.450,
        p99_ms=0.488,
        timestamp="2026-04-16T10:00:00Z",
    )

    text = build_summary_markdown(pattern=str(tmp_path / "*.json"), mode="history", sort="time", recent=2)

    assert "2026-04-16T08:00:00Z" not in text
    assert "2026-04-16T09:00:00Z" in text
    assert "2026-04-16T10:00:00Z" in text
