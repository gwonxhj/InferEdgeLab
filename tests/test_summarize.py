from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


def import_summarize_module():
    if "typer" not in sys.modules:
        typer_stub = types.ModuleType("typer")

        class BadParameter(Exception):
            pass

        def argument(default=None, *args, **kwargs):
            return default

        def option(default=None, *args, **kwargs):
            return default

        typer_stub.BadParameter = BadParameter
        typer_stub.Argument = argument
        typer_stub.Option = option
        sys.modules["typer"] = typer_stub

    if "rich" not in sys.modules:
        rich_stub = types.ModuleType("rich")
        rich_stub.print = print
        sys.modules["rich"] = rich_stub

    module_path = Path(__file__).resolve().parents[1] / "edgebench" / "commands" / "summarize.py"
    spec = importlib.util.spec_from_file_location("test_summarize_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_report(
    tmp_path: Path,
    name: str,
    *,
    model_name: str,
    mean_ms: float,
    p99_ms: float,
    timestamp: str,
) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": {"path": f"models/{model_name}"},
                "static": {"flops_estimate": 126444160},
                "runtime": {
                    "engine": "onnxruntime",
                    "device": "cpu",
                    "latency_ms": {
                        "mean": mean_ms,
                        "p99": p99_ms,
                    },
                    "extra": {
                        "batch": 1,
                        "height": 224,
                        "width": 224,
                    },
                },
                "timestamp": timestamp,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(path)


def test_summarize_latest_output_is_preserved(tmp_path, capsys):
    summarize = import_summarize_module()
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

    summarize.summarize(pattern=str(tmp_path / "*.json"), mode="latest", sort="p99")
    out = capsys.readouterr().out

    assert "## Latest (recommended)" in out
    assert out.count("| toy224.onnx | onnxruntime | cpu |") == 1
    assert "0.488" in out


def test_summarize_history_output_is_preserved(tmp_path, capsys):
    summarize = import_summarize_module()
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

    summarize.summarize(pattern=str(tmp_path / "*.json"), mode="history", sort="time")
    out = capsys.readouterr().out

    assert "## History (raw)" in out
    assert out.count("| toy224.onnx | onnxruntime | cpu |") == 2
    assert "2026-04-16T09:00:00Z" in out
    assert "2026-04-16T10:00:00Z" in out


def test_summarize_both_contains_latest_and_history_sections_and_tables(tmp_path, capsys):
    summarize = import_summarize_module()
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

    summarize.summarize(pattern=str(tmp_path / "*.json"), mode="both", sort="time")
    out = capsys.readouterr().out

    assert "## Latest (recommended)" in out
    assert "## History (raw)" in out
    assert out.count("| Model | Engine | Device | Batch | Input(HxW) | FLOPs | Mean (ms) | P99 (ms) | Timestamp (UTC) |") == 2
    assert out.count("| toy224.onnx | onnxruntime | cpu |") == 3


def test_summarize_invalid_mode_raises_bad_parameter(tmp_path):
    summarize = import_summarize_module()
    write_report(
        tmp_path,
        "one.json",
        model_name="toy224.onnx",
        mean_ms=0.450,
        p99_ms=0.488,
        timestamp="2026-04-16T10:00:00Z",
    )

    with pytest.raises(sys.modules["typer"].BadParameter) as exc_info:
        summarize.summarize(pattern=str(tmp_path / "*.json"), mode="invalid", sort="time")

    assert "--mode must be one of: latest, history, both" in str(exc_info.value)
