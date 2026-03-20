from __future__ import annotations

from html import escape
from typing import Any, Dict, Optional


def _fmt_num(v: Optional[float]) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:+.2f}%"


def _table_rows_from_metric_map(metrics: Dict[str, Dict[str, Any]]) -> str:
    rows = []
    for metric_name, values in metrics.items():
        rows.append(
            f"""
            <tr>
              <td>{escape(metric_name)}</td>
              <td>{escape(_fmt_num(values.get("base")))}</td>
              <td>{escape(_fmt_num(values.get("new")))}</td>
              <td>{escape(_fmt_num(values.get("delta")))}</td>
              <td>{escape(_fmt_pct(values.get("delta_pct")))}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def _table_rows_from_diff_map(diff_map: Dict[str, Dict[str, Any]]) -> str:
    rows = []
    for field, values in diff_map.items():
        rows.append(
            f"""
            <tr>
              <td>{escape(field)}</td>
              <td>{escape(_fmt_num(values.get("base")))}</td>
              <td>{escape(_fmt_num(values.get("new")))}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def generate_compare_html(compare_result: Dict[str, Any]) -> str:
    base_id = compare_result["base_id"]
    new_id = compare_result["new_id"]
    metrics = compare_result["metrics"]

    shape_rows = _table_rows_from_diff_map(
        {
            "batch": compare_result["shape"]["base"] | {"new": compare_result["shape"]["new"]["batch"]},
            "height": {"base": compare_result["shape"]["base"]["height"], "new": compare_result["shape"]["new"]["height"]},
            "width": {"base": compare_result["shape"]["base"]["width"], "new": compare_result["shape"]["new"]["width"]},
        }
    )

    system_rows = _table_rows_from_diff_map(compare_result["system_diff"])
    run_rows = _table_rows_from_diff_map(compare_result["run_config_diff"])
    metric_rows = _table_rows_from_metric_map(metrics)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>EdgeBench Compare Report</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 32px;
      color: #111827;
      background: #f9fafb;
    }}
    h1, h2 {{
      color: #111827;
    }}
    .meta {{
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 24px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      margin-bottom: 24px;
      border: 1px solid #e5e7eb;
    }}
    th, td {{
      border: 1px solid #e5e7eb;
      padding: 10px 12px;
      text-align: left;
    }}
    th {{
      background: #f3f4f6;
    }}
    code {{
      background: #f3f4f6;
      padding: 2px 6px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <h1>EdgeBench Compare Report</h1>

  <div class="meta">
    <p><strong>Base</strong>: <code>{escape(str(base_id["model"]))}</code> / <code>{escape(str(base_id["engine"]))}</code> / <code>{escape(str(base_id["device"]))}</code> / <code>{escape(str(base_id["timestamp"]))}</code></p>
    <p><strong>New</strong>: <code>{escape(str(new_id["model"]))}</code> / <code>{escape(str(new_id["engine"]))}</code> / <code>{escape(str(new_id["device"]))}</code> / <code>{escape(str(new_id["timestamp"]))}</code></p>
  </div>

  <h2>Latency Comparison</h2>
  <table>
    <thead>
      <tr>
        <th>Metric</th>
        <th>Base</th>
        <th>New</th>
        <th>Delta</th>
        <th>Delta %</th>
      </tr>
    </thead>
    <tbody>
      {metric_rows}
    </tbody>
  </table>

  <h2>Input Shape</h2>
  <table>
    <thead>
      <tr>
        <th>Field</th>
        <th>Base</th>
        <th>New</th>
      </tr>
    </thead>
    <tbody>
      {shape_rows}
    </tbody>
  </table>

  <h2>System Info</h2>
  <table>
    <thead>
      <tr>
        <th>Field</th>
        <th>Base</th>
        <th>New</th>
      </tr>
    </thead>
    <tbody>
      {system_rows}
    </tbody>
  </table>

  <h2>Run Config</h2>
  <table>
    <thead>
      <tr>
        <th>Field</th>
        <th>Base</th>
        <th>New</th>
      </tr>
    </thead>
    <tbody>
      {run_rows}
    </tbody>
  </table>
</body>
</html>
"""