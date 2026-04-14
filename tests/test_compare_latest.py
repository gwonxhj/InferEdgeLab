from __future__ import annotations

import json
import sys
import types

import pytest


def import_compare_latest_module():
    if "typer" not in sys.modules:
        typer_stub = types.ModuleType("typer")

        class Exit(Exception):
            def __init__(self, code: int = 0):
                super().__init__(code)
                self.exit_code = code

        def option(default=None, *args, **kwargs):
            return default

        typer_stub.Exit = Exit
        typer_stub.Option = option
        sys.modules["typer"] = typer_stub

    if "rich" not in sys.modules:
        rich_stub = types.ModuleType("rich")
        rich_stub.print = print
        sys.modules["rich"] = rich_stub

    if "edgebench.commands.compare" not in sys.modules:
        compare_stub = types.ModuleType("edgebench.commands.compare")

        def compare_cmd(**kwargs):
            return None

        compare_stub.compare_cmd = compare_cmd
        sys.modules["edgebench.commands.compare"] = compare_stub

    from edgebench.commands import compare_latest

    return compare_latest


def write_result(
    tmp_path,
    name: str,
    *,
    timestamp: str,
    precision: str,
    model: str = "resnet18",
    engine: str = "onnxruntime",
    device: str = "cpu",
    batch: int = 1,
    height: int = 224,
    width: int = 224,
    run_config: dict | None = None,
) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": model,
                "engine": engine,
                "device": device,
                "precision": precision,
                "batch": batch,
                "height": height,
                "width": width,
                "mean_ms": 10.0,
                "p99_ms": 12.0,
                "timestamp": timestamp,
                "run_config": run_config or {},
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_compare_latest_selects_latest_same_precision_pair(tmp_path, monkeypatch):
    compare_latest = import_compare_latest_module()

    older = write_result(tmp_path, "older.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "other.json", timestamp="2026-04-13T09:30:00Z", precision="fp16")
    newer = write_result(tmp_path, "newer.json", timestamp="2026-04-13T10:00:00Z", precision="fp32")

    captured = {}

    def fake_compare_cmd(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(compare_latest, "compare_cmd", fake_compare_cmd)

    compare_latest.compare_latest_cmd(pattern=str(tmp_path / "*.json"), selection_mode="same_precision")

    assert captured["base_path"] == older
    assert captured["new_path"] == newer


def test_compare_latest_selects_latest_cross_precision_pair(tmp_path, monkeypatch):
    compare_latest = import_compare_latest_module()

    older_fp32 = write_result(tmp_path, "older-fp32.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "older-fp16.json", timestamp="2026-04-13T09:10:00Z", precision="fp16")
    newer_fp16 = write_result(tmp_path, "newer-fp16.json", timestamp="2026-04-13T10:00:00Z", precision="fp16")

    captured = {}

    def fake_compare_cmd(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(compare_latest, "compare_cmd", fake_compare_cmd)

    compare_latest.compare_latest_cmd(pattern=str(tmp_path / "*.json"), selection_mode="cross_precision")

    assert captured["base_path"] == older_fp32
    assert captured["new_path"] == newer_fp16


def test_compare_latest_cross_precision_with_precision_filter_strict_raises(tmp_path):
    compare_latest = import_compare_latest_module()

    write_result(tmp_path, "base.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "new.json", timestamp="2026-04-13T10:00:00Z", precision="fp16")

    with pytest.raises(sys.modules["typer"].Exit) as exc_info:
        compare_latest.compare_latest_cmd(
            pattern=str(tmp_path / "*.json"),
            selection_mode="cross_precision",
            precision="fp16",
            strict=True,
        )

    assert exc_info.value.exit_code == 1


def test_compare_latest_with_less_than_two_results_and_non_strict_returns(tmp_path, monkeypatch):
    compare_latest = import_compare_latest_module()

    write_result(tmp_path, "only.json", timestamp="2026-04-13T10:00:00Z", precision="fp32")

    def fail_compare_cmd(**kwargs):
        raise AssertionError("compare_cmd should not be called")

    monkeypatch.setattr(compare_latest, "compare_cmd", fail_compare_cmd)

    assert compare_latest.compare_latest_cmd(pattern=str(tmp_path / "*.json"), strict=False) is None


def test_compare_latest_same_precision_warns_when_core_run_config_differs(tmp_path, monkeypatch, capsys):
    compare_latest = import_compare_latest_module()

    older = write_result(
        tmp_path,
        "older.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp16",
        run_config={"runs": 100, "warmup": 10, "intra_threads": 1, "inter_threads": 1, "mode": None, "task": None},
    )
    newer = write_result(
        tmp_path,
        "newer.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp16",
        run_config={"runs": 50, "warmup": 10, "intra_threads": 1, "inter_threads": 1, "mode": None, "task": None},
    )

    captured = {}

    def fake_compare_cmd(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(compare_latest, "compare_cmd", fake_compare_cmd)

    compare_latest.compare_latest_cmd(pattern=str(tmp_path / "*.json"), selection_mode="same_precision")
    out = capsys.readouterr().out

    assert "run_config" in out
    assert "runs" in out
    assert captured["base_path"] == older
    assert captured["new_path"] == newer
