from __future__ import annotations

from html import escape
from typing import Any, Dict, List, Optional


def _fmt_num(v: Optional[float]) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _max_metric(history: List[Dict[str, Any]], field: str) -> float:
    values = [float(item.get(field) or 0.0) for item in history]
    return max(values) if values else 1.0


def _bar_width(value: Optional[float], max_value: float) -> str:
    if value is None or max_value <= 0:
        return "0%"
    pct = (float(value) / max_value) * 100.0
    pct = max(0.0, min(pct, 100.0))
    return f"{pct:.2f}%"


def _history_rows(history: List[Dict[str, Any]]) -> str:
    max_mean = _max_metric(history, "mean_ms")
    max_p99 = _max_metric(history, "p99_ms")

    rows = []
    for item in history:
        mean_ms = item.get("mean_ms")
        p99_ms = item.get("p99_ms")

        rows.append(
            f"""
            <tr>
              <td>{escape(str(item.get("timestamp") or "-"))}</td>
              <td>{escape(str(item.get("model") or "-"))}</td>
              <td>{escape(str(item.get("engine") or "-"))}</td>
              <td>{escape(str(item.get("device") or "-"))}</td>
              <td>{escape(str(item.get("batch") or "-"))}</td>
              <td>{escape(str(item.get("height") or "-"))}x{escape(str(item.get("width") or "-"))}</td>
              <td>
                <div class="metric-cell">
                  <span>{escape(_fmt_num(mean_ms))}</span>
                  <div class="bar-wrap"><div class="bar mean-bar" style="width:{_bar_width(mean_ms, max_mean)}"></div></div>
                </div>
              </td>
              <td>
                <div class="metric-cell">
                  <span>{escape(_fmt_num(p99_ms))}</span>
                  <div class="bar-wrap"><div class="bar p99-bar" style="width:{_bar_width(p99_ms, max_p99)}"></div></div>
                </div>
              </td>
            </tr>
            """
        )
    return "\n".join(rows)


def generate_history_html(
    history: List[Dict[str, Any]],
    filters: Dict[str, Any],
) -> str:
    latest = history[-1] if history else {}
    oldest = history[0] if history else {}

    rows = _history_rows(history)

    filter_lines = []
    for k, v in filters.items():
        if v not in ("", None):
            filter_lines.append(f"<li><strong>{escape(str(k))}</strong>: {escape(str(v))}</li>")

    filter_html = "\n".join(filter_lines) if filter_lines else "<li>No filters</li>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>EdgeBench History Report</title>
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
      vertical-align: middle;
    }}
    th {{
      background: #f3f4f6;
    }}
    code {{
      background: #f3f4f6;
      padding: 2px 6px;
      border-radius: 6px;
    }}
    .metric-cell {{
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 220px;
    }}
    .bar-wrap {{
      flex: 1;
      height: 10px;
      background: #e5e7eb;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar {{
      height: 100%;
      border-radius: 999px;
    }}
    .mean-bar {{
      background: #2563eb;
    }}
    .p99-bar {{
      background: #dc2626;
    }}
  </style>
</head>
<body>
  <h1>EdgeBench History Report</h1>

  <div class="meta">
    <h2>Filters</h2>
    <ul>
      {filter_html}
    </ul>
  </div>

  <div class="meta">
    <h2>Summary</h2>
    <p><strong>Total records</strong>: <code>{len(history)}</code></p>
    <p><strong>Oldest timestamp</strong>: <code>{escape(str(oldest.get("timestamp") or "-"))}</code></p>
    <p><strong>Latest timestamp</strong>: <code>{escape(str(latest.get("timestamp") or "-"))}</code></p>
  </div>

  <h2>History Table</h2>
  <table>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Model</th>
        <th>Engine</th>
        <th>Device</th>
        <th>Batch</th>
        <th>Input</th>
        <th>Mean (ms)</th>
        <th>P99 (ms)</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
"""