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


def _fmt_pp(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:+.2f}pp"


def _badge_class_for_overall(overall: str) -> str:
    if overall in {"improvement", "tradeoff_faster"}:
        return "badge-good"
    if overall in {"regression", "tradeoff_slower", "mismatch"}:
        return "badge-bad"
    return "badge-neutral"


def _badge_class_for_risk(risk: str) -> str:
    if risk in {"acceptable_tradeoff", "not_applicable"}:
        return "badge-good"
    if risk in {"caution_tradeoff", "unknown_risk", "no_clear_tradeoff"}:
        return "badge-warn"
    if risk in {"risky_tradeoff", "severe_tradeoff", "not_beneficial"}:
        return "badge-bad"
    return "badge-neutral"


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


def _table_rows_from_accuracy_map(metrics: Dict[str, Dict[str, Any]]) -> str:
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
              <td>{escape(_fmt_pp(values.get("delta_pp")))}</td>
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


def _threshold_rows(thresholds: Dict[str, Any]) -> str:
    ordered_keys = [
        "latency_improve_threshold",
        "latency_regress_threshold",
        "accuracy_improve_threshold",
        "accuracy_regress_threshold",
        "tradeoff_caution_threshold",
        "tradeoff_risky_threshold",
        "tradeoff_severe_threshold",
    ]
    rows = []
    for key in ordered_keys:
        value = thresholds.get(key)
        suffix = "%" if "latency" in key else "pp"
        display = "-" if value is None else f"{float(value):+.2f}{suffix}"
        rows.append(
            f"""
            <tr>
              <td>{escape(key)}</td>
              <td>{escape(display)}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def generate_compare_html(compare_result: Dict[str, Any], judgement: Dict[str, Any]) -> str:
    base_id = compare_result["base_id"]
    new_id = compare_result["new_id"]
    precision = compare_result["precision"]
    metrics = compare_result["metrics"]
    accuracy = compare_result["accuracy"]
    thresholds = judgement.get("thresholds", {})
    shape_context = compare_result["shape_context"]

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

    provenance_rows = _table_rows_from_diff_map(
        {
            "requested_batch": {
                "base": shape_context["base"].get("requested_batch"),
                "new": shape_context["new"].get("requested_batch"),
            },
            "requested_height": {
                "base": shape_context["base"].get("requested_height"),
                "new": shape_context["new"].get("requested_height"),
            },
            "requested_width": {
                "base": shape_context["base"].get("requested_width"),
                "new": shape_context["new"].get("requested_width"),
            },
            "effective_batch": {
                "base": shape_context["base"].get("effective_batch"),
                "new": shape_context["new"].get("effective_batch"),
            },
            "effective_height": {
                "base": shape_context["base"].get("effective_height"),
                "new": shape_context["new"].get("effective_height"),
            },
            "effective_width": {
                "base": shape_context["base"].get("effective_width"),
                "new": shape_context["new"].get("effective_width"),
            },
            "primary_input_name": {
                "base": shape_context["base"].get("primary_input_name"),
                "new": shape_context["new"].get("primary_input_name"),
            },
            "resolved_input_shapes": {
                "base": str(shape_context["base"].get("resolved_input_shapes")),
                "new": str(shape_context["new"].get("resolved_input_shapes")),
            },
        }
    )

    sample_rows = _table_rows_from_diff_map(
        {
            "sample_count": {
                "base": accuracy["sample_count"]["base"],
                "new": accuracy["sample_count"]["new"],
            }
        }
    )

    system_rows = _table_rows_from_diff_map(compare_result["system_diff"])
    run_rows = _table_rows_from_diff_map(compare_result["run_config_diff"])
    metric_rows = _table_rows_from_metric_map(metrics)
    accuracy_rows = _table_rows_from_accuracy_map(accuracy["metrics"])
    notes_html = _notes_to_html(judgement["notes"])
    threshold_rows = _threshold_rows(thresholds)

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

    overall_badge_class = _badge_class_for_overall(str(judgement["overall"]))
    risk_badge_class = _badge_class_for_risk(str(judgement["tradeoff_risk"]))

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
      margin-bottom: 12px;
    }}
    .meta {{
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 24px;
    }}
    .warning {{
      background: #fff7ed;
      border: 1px solid #fdba74;
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 24px;
      color: #9a3412;
    }}
    .summary {{
      font-size: 15px;
      line-height: 1.6;
      margin-top: 8px;
    }}
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .card {{
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }}
    .card-title {{
      font-size: 13px;
      color: #6b7280;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .card-value {{
      font-size: 20px;
      font-weight: 700;
      color: #111827;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
    }}
    .badge-good {{
      background: #dcfce7;
      color: #166534;
    }}
    .badge-warn {{
      background: #fef3c7;
      color: #92400e;
    }}
    .badge-bad {{
      background: #fee2e2;
      color: #991b1b;
    }}
    .badge-neutral {{
      background: #e5e7eb;
      color: #374151;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      margin-bottom: 24px;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      overflow: hidden;
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

  <div class="card-grid">
    <div class="card">
      <div class="card-title">Overall</div>
      <div class="card-value"><span class="badge {overall_badge_class}">{escape(str(judgement["overall"]))}</span></div>
    </div>
    <div class="card">
      <div class="card-title">Trade-off Risk</div>
      <div class="card-value"><span class="badge {risk_badge_class}">{escape(str(judgement["tradeoff_risk"]))}</span></div>
    </div>
    <div class="card">
      <div class="card-title">Mean Judgement</div>
      <div class="card-value">{escape(str(judgement["mean_ms"]))}</div>
    </div>
    <div class="card">
      <div class="card-title">Accuracy Judgement</div>
      <div class="card-value">{escape(str(judgement["accuracy"]))}</div>
    </div>
  </div>

  <div class="meta">
    <p><strong>Shape match</strong>: <code>{escape(str(judgement["shape_match"]))}</code></p>
    <p><strong>System match</strong>: <code>{escape(str(judgement["system_match"]))}</code></p>
    <p><strong>P99 judgement</strong>: <code>{escape(str(judgement["p99_ms"]))}</code></p>
    <p><strong>Accuracy present</strong>: <code>{escape(str(judgement["accuracy_present"]))}</code></p>
    <div class="summary"><strong>Summary</strong>: {escape(str(judgement["summary"]))}</div>
    {notes_html}
  </div>

  <h2>Threshold Policy</h2>
  <table>
    <thead>
      <tr>
        <th>Threshold</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      {threshold_rows}
    </tbody>
  </table>

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

  <h2>Accuracy Comparison</h2>
  <div class="meta">
    <p><strong>Task</strong>: <code>{escape(str(accuracy.get("task") or "unknown"))}</code></p>
  </div>
  <table>
    <thead>
      <tr>
        <th>Metric</th>
        <th>Base</th>
        <th>New</th>
        <th>Delta</th>
        <th>Delta %</th>
        <th>Delta pp</th>
      </tr>
    </thead>
    <tbody>
      {accuracy_rows}
    </tbody>
  </table>

  <table>
    <thead>
      <tr>
        <th>Field</th>
        <th>Base</th>
        <th>New</th>
      </tr>
    </thead>
    <tbody>
      {sample_rows}
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

  <h2>Input Shape Provenance</h2>
  <table>
    <thead>
      <tr>
        <th>Field</th>
        <th>Base</th>
        <th>New</th>
      </tr>
    </thead>
    <tbody>
      {provenance_rows}
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
