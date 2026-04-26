from __future__ import annotations

import json

from inferedgelab.commands.compare import compare_runtime_dir_cmd


def _write_runtime_result(path, *, backend_key: str, mean_ms: float) -> None:
    path.write_text(
        json.dumps(
            {
                "runtime_role": "runtime-result",
                "compare_key": "toy224__b1__h224w224__fp32",
                "backend_key": backend_key,
                "mean_ms": mean_ms,
                "p99_ms": mean_ms + 1.0,
                "fps_value": 1000.0 / mean_ms,
                "success": True,
                "status": "ok",
            }
        ),
        encoding="utf-8",
    )


def test_compare_runtime_dir_cmd_prints_grouped_backend_comparison(tmp_path, capsys):
    _write_runtime_result(tmp_path / "onnx.json", backend_key="onnxruntime__cpu", mean_ms=1.4)
    _write_runtime_result(tmp_path / "trt.json", backend_key="tensorrt__jetson", mean_ms=5.2)

    compare_runtime_dir_cmd(str(tmp_path))

    out = capsys.readouterr().out
    assert "Compare Group: toy224__b1__h224w224__fp32" in out
    assert "onnxruntime__cpu: 1.4000 ms" in out
    assert "tensorrt__jetson: 5.2000 ms" in out
    assert "-> onnxruntime__cpu faster (3.7x)" in out


def test_compare_runtime_dir_cmd_writes_markdown_report(tmp_path):
    result_dir = tmp_path / "results"
    result_dir.mkdir()
    report_path = tmp_path / "reports" / "runtime_compare.md"
    _write_runtime_result(result_dir / "onnx.json", backend_key="onnxruntime__cpu", mean_ms=1.4)
    _write_runtime_result(result_dir / "trt.json", backend_key="tensorrt__jetson", mean_ms=5.2)

    compare_runtime_dir_cmd(str(result_dir), report=str(report_path))

    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    assert "# InferEdge Runtime Compare Report" in text
    assert "toy224__b1__h224w224__fp32" in text
    assert "onnxruntime__cpu" in text
    assert "tensorrt__jetson" in text
    assert "Speedup ratio: 3.7x" in text


def test_compare_runtime_dir_cmd_writes_empty_markdown_report(tmp_path):
    result_dir = tmp_path / "empty-results"
    result_dir.mkdir()
    report_path = tmp_path / "reports" / "runtime_compare.md"

    compare_runtime_dir_cmd(str(result_dir), report=str(report_path))

    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    assert "# InferEdge Runtime Compare Report" in text
    assert "No compare-ready runtime results found." in text
