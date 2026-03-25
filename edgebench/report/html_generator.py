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


def _notes_to_html(notes: list[str]) -> str:
    if not notes:
        return ""
    items = "\n".join(f"<li>{escape(note)}</li>" for note in notes)
    return f"<ul>{items}</ul>"


def generate_compare_html(compare_result: Dict[str, Any], judgement: Dict[str, Any]) -> str:
    base_id = compare_result["base_id"]
    new_id = compare_result["new_id"]
    precision = compare_result["precision"]
    metrics = compare_result["metrics"]

    shape_rows = _table_rows_from_diff_map(
        {
            "batch": {
                "base": compare_result["shape"]["base"]["batch"],
                "new": compare_result["shape"]["new"]["batch"],
            },
            "height": {
                "base": compare_result["shape"]["base"]["height"],
                "new": compare_result["shape"]["new"]["height"],
            },
            "width": {
                "base": compare_result["shape"]["base"]["width"],
                "new": compare_result["shape"]["new"]["width"],
            },
        }
    )

    system_rows = _table_rows_from_diff_map(compare_result["system_diff"])
    run_rows = _table_rows_from_diff_map(compare_result["run_config_diff"])
    metric_rows = _table_rows_from_metric_map(metrics)
    notes_html = _notes_to_html(judgement["notes"])

    warning_html = ""
    if not judgement["precision_match"]:
        warning_html = """
        <div class="warning">
          <strong>Cross-precision comparison detected.</strong>
          <div>
            Interpret latency deltas as a precision trade-off signal, not a strict same-condition regression result.
          </div>
        </div>
        """

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
    .warning {{
      background: #fff7ed;
      border: 1px solid #fdba74;
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 24px;
      color: #9a3412;
    }}
    .summary {{
      font-size: 15px;
      line-height: 1.6;
      margin-top: 8px;
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
    ul {{
      margin: 8px 0 0 20px;
    }}
  </style>
</head>
<body>
  <h1>EdgeBench Compare Report</h1>

  <div class="meta">
    <p><strong>Base</strong>: <code>{escape(str(base_id["model"]))}</code> / <code>{escape(str(base_id["engine"]))}</code> / <code>{escape(str(base_id["device"]))}</code> / <code>{escape(str(base_id["timestamp"]))}</code></p>
    <p><strong>New</strong>: <code>{escape(str(new_id["model"]))}</code> / <code>{escape(str(new_id["engine"]))}</code> / <code>{escape(str(new_id["device"]))}</code> / <code>{escape(str(new_id["timestamp"]))}</code></p>
  </div>

  <div class="meta">
    <p><strong>Base precision</strong>: <code>{escape(str(precision["base"]))}</code></p>
    <p><strong>New precision</strong>: <code>{escape(str(precision["new"]))}</code></p>
    <p><strong>Precision match</strong>: <code>{escape(str(judgement["precision_match"]))}</code></p>
    <p><strong>Comparison mode</strong>: <code>{escape(str(judgement["comparison_mode"]))}</code></p>
    <p><strong>Precision pair</strong>: <code>{escape(str(judgement["precision_pair"]))}</code></p>
  </div>

  {warning_html}

  <div class="meta">
    <p><strong>Overall</strong>: <code>{escape(str(judgement["overall"]))}</code></p>
    {"<p><strong>Overall semantics</strong>: <code>trade-off status, not same-condition regression status</code></p>" if judgement["comparison_mode"] == "cross_precision" else ""}
    <p><strong>Shape match</strong>: <code>{escape(str(judgement["shape_match"]))}</code></p>
    <p><strong>System match</strong>: <code>{escape(str(judgement["system_match"]))}</code></p>
    <p><strong>Mean judgement</strong>: <code>{escape(str(judgement["mean_ms"]))}</code></p>
    <p><strong>P99 judgement</strong>: <code>{escape(str(judgement["p99_ms"]))}</code></p>
    <div class="summary"><strong>Summary</strong>: {escape(str(judgement["summary"]))}</div>
    {notes_html}
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