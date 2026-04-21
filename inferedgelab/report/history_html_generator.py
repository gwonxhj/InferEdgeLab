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


def _min_metric(history: List[Dict[str, Any]], field: str) -> float:
    values = [float(item.get(field) or 0.0) for item in history]
    return min(values) if values else 0.0


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


def _trend_svg(history: List[Dict[str, Any]], field: str, stroke: str) -> str:
    width = 900
    height = 260
    pad_left = 56
    pad_right = 20
    pad_top = 20
    pad_bottom = 40

    values = [float(item.get(field) or 0.0) for item in history]
    if not values:
        return "<p>No trend data</p>"

    min_v = _min_metric(history, field)
    max_v = _max_metric(history, field)

    if max_v <= min_v:
        max_v = min_v + 1.0

    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    def x_at(idx: int) -> float:
        if len(values) == 1:
            return pad_left + plot_w / 2.0
        return pad_left + (plot_w * idx / (len(values) - 1))

    def y_at(v: float) -> float:
        ratio = (v - min_v) / (max_v - min_v)
        return pad_top + plot_h - (ratio * plot_h)

    points = []
    for i, v in enumerate(values):
        points.append(f"{x_at(i):.2f},{y_at(v):.2f}")
    polyline = " ".join(points)

    circles = []
    labels = []
    for i, item in enumerate(history):
        v = float(item.get(field) or 0.0)
        x = x_at(i)
        y = y_at(v)
        ts = str(item.get("timestamp") or "-")

        circles.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{stroke}"><title>{escape(ts)}: {_fmt_num(v)}</title></circle>'
        )
        labels.append(
            f'<text x="{x:.2f}" y="{height - 14}" text-anchor="middle" class="axis-label">{escape(ts[-6:])}</text>'
        )

    y_ticks = []
    tick_labels = []
    for i in range(5):
        ratio = i / 4.0
        v = min_v + ((max_v - min_v) * (1.0 - ratio))
        y = pad_top + plot_h * ratio
        y_ticks.append(
            f'<line x1="{pad_left}" y1="{y:.2f}" x2="{width - pad_right}" y2="{y:.2f}" class="grid-line" />'
        )
        tick_labels.append(
            f'<text x="{pad_left - 8}" y="{y + 4:.2f}" text-anchor="end" class="axis-label">{escape(_fmt_num(v))}</text>'
        )

    return f"""
    <svg viewBox="0 0 {width} {height}" class="trend-svg" role="img" aria-label="{escape(field)} trend">
      <rect x="0" y="0" width="{width}" height="{height}" fill="white" rx="12"></rect>
      {''.join(y_ticks)}
      <line x1="{pad_left}" y1="{height - pad_bottom}" x2="{width - pad_right}" y2="{height - pad_bottom}" class="axis-line" />
      <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{height - pad_bottom}" class="axis-line" />
      {''.join(tick_labels)}
      <polyline fill="none" stroke="{stroke}" stroke-width="3" points="{polyline}" />
      {''.join(circles)}
      {''.join(labels)}
    </svg>
    """


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

    mean_svg = _trend_svg(history, "mean_ms", "#2563eb")
    p99_svg = _trend_svg(history, "p99_ms", "#dc2626")

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
    .chart-card {{
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
    .trend-svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .axis-line {{
      stroke: #9ca3af;
      stroke-width: 1;
    }}
    .grid-line {{
      stroke: #e5e7eb;
      stroke-width: 1;
    }}
    .axis-label {{
      fill: #6b7280;
      font-size: 11px;
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

  <div class="chart-card">
    <h2>Mean Latency Trend</h2>
    {mean_svg}
  </div>

  <div class="chart-card">
    <h2>P99 Latency Trend</h2>
    {p99_svg}
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