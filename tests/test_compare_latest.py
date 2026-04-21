from __future__ import annotations

import json
import importlib
from pathlib import Path
import sys
import types

import pytest


def import_compare_latest_module():
    for module_name in (
        "typer",
        "rich",
        "rich.table",
        "inferedgelab.commands.compare_latest",
    ):
        sys.modules.pop(module_name, None)

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

    rich_stub = types.ModuleType("rich")
    rich_stub.print = print
    sys.modules["rich"] = rich_stub

    rich_table_stub = types.ModuleType("rich.table")

    class Table:
        def __init__(self, *args, **kwargs):
            self.rows = []

        def add_column(self, *args, **kwargs):
            return None

        def add_row(self, *args, **kwargs):
            self.rows.append(args)

    rich_table_stub.Table = Table
    sys.modules["rich.table"] = rich_table_stub

    return importlib.import_module("inferedgelab.commands.compare_latest")


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


def test_compare_latest_selects_latest_same_precision_pair(tmp_path, capsys):
    compare_latest = import_compare_latest_module()

    older = write_result(tmp_path, "older.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "other.json", timestamp="2026-04-13T09:30:00Z", precision="fp16")
    newer = write_result(tmp_path, "newer.json", timestamp="2026-04-13T10:00:00Z", precision="fp32")

    compare_latest.compare_latest_cmd(pattern=str(tmp_path / "*.json"), selection_mode="same_precision")
    out = capsys.readouterr().out

    assert f"Base path: {older}" in out
    assert f"New path : {newer}" in out


def test_compare_latest_selects_latest_cross_precision_pair(tmp_path, capsys):
    compare_latest = import_compare_latest_module()

    older_fp32 = write_result(tmp_path, "older-fp32.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "older-fp16.json", timestamp="2026-04-13T09:10:00Z", precision="fp16")
    newer_fp16 = write_result(tmp_path, "newer-fp16.json", timestamp="2026-04-13T10:00:00Z", precision="fp16")

    compare_latest.compare_latest_cmd(pattern=str(tmp_path / "*.json"), selection_mode="cross_precision")
    out = capsys.readouterr().out

    assert f"Base path: {older_fp32}" in out
    assert f"New path : {newer_fp16}" in out


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


def test_compare_latest_with_less_than_two_results_and_non_strict_returns(tmp_path):
    compare_latest = import_compare_latest_module()

    write_result(tmp_path, "only.json", timestamp="2026-04-13T10:00:00Z", precision="fp32")

    assert compare_latest.compare_latest_cmd(pattern=str(tmp_path / "*.json"), strict=False) is None


def test_compare_latest_same_precision_warns_when_core_run_config_differs(tmp_path, capsys):
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

    compare_latest.compare_latest_cmd(pattern=str(tmp_path / "*.json"), selection_mode="same_precision")
    out = capsys.readouterr().out

    assert "run_config" in out
    assert "runs" in out
    assert f"Base path: {older}" in out
    assert f"New path : {newer}" in out


def test_compare_latest_writes_markdown_and_html_from_bundle(tmp_path):
    compare_latest = import_compare_latest_module()

    write_result(tmp_path, "older.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "newer.json", timestamp="2026-04-13T10:00:00Z", precision="fp32")
    markdown_out = tmp_path / "compare_latest.md"
    html_out = tmp_path / "compare_latest.html"

    compare_latest.compare_latest_cmd(
        pattern=str(tmp_path / "*.json"),
        selection_mode="same_precision",
        markdown_out=str(markdown_out),
        html_out=str(html_out),
    )

    assert markdown_out.is_file()
    assert html_out.is_file()
    assert Path(markdown_out).read_text(encoding="utf-8")
    assert Path(html_out).read_text(encoding="utf-8")
