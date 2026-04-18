from __future__ import annotations

import glob
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class Row:
    path: str
    model: str
    engine: str
    device: str
    h: int | None
    w: int | None
    batch: int | None
    flops: int | None
    mean_ms: float | None
    p99_ms: float | None
    ts_iso: str | None


def _load_one(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _to_int(x: Any) -> int | None:
    return int(x) if x is not None else None


def _to_float(x: Any) -> float | None:
    return float(x) if x is not None else None


def _parse_ts_iso(d: dict[str, Any]) -> str | None:
    ts = d.get("timestamp")
    if not ts:
        return None
    if isinstance(ts, str):
        return ts
    return None


def _ts_key(ts_iso: str | None) -> tuple[bool, datetime]:
    if not ts_iso:
        return (True, datetime.fromtimestamp(0, tz=timezone.utc))

    ts_string = ts_iso.replace("Z", "+00:00")
    try:
        return (False, datetime.fromisoformat(ts_string))
    except Exception:
        return (True, datetime.fromtimestamp(0, tz=timezone.utc))


def _to_row(path: str, d: dict[str, Any]) -> Row:
    model_path = (d.get("model") or {}).get("path") or ""
    model_name = model_path.split("/")[-1] if model_path else "unknown"

    runtime = d.get("runtime") or {}
    extra = runtime.get("extra") or {}
    static = d.get("static") or {}
    latency = runtime.get("latency_ms") or {}

    return Row(
        path=path,
        model=model_name,
        engine=str(runtime.get("engine") or "unknown"),
        device=str(runtime.get("device") or "unknown"),
        h=_to_int(extra.get("height")),
        w=_to_int(extra.get("width")),
        batch=_to_int(extra.get("batch")),
        flops=_to_int(static.get("flops_estimate")),
        mean_ms=_to_float(latency.get("mean")),
        p99_ms=_to_float(latency.get("p99")),
        ts_iso=_parse_ts_iso(d),
    )


def _fmt_int_commas(x: int | None) -> str:
    return "-" if x is None else f"{x:,}"


def _fmt_f3(x: float | None) -> str:
    return "-" if x is None else f"{x:.3f}"


def _hw(r: Row) -> str:
    return f"{r.h}x{r.w}" if (r.h and r.w) else "-"


def _md_table_latest(rows: list[Row]) -> str:
    lines: list[str] = []
    lines.append("| Model | Engine | Device | Batch | Input(HxW) | FLOPs | Mean (ms) | P99 (ms) | Timestamp (UTC) |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")

    for r in rows:
        lines.append(
            f"| {r.model} | {r.engine} | {r.device} | {r.batch or '-'} | {_hw(r)} | "
            f"{_fmt_int_commas(r.flops)} | {_fmt_f3(r.mean_ms)} | {_fmt_f3(r.p99_ms)} | {r.ts_iso or '-'} |"
        )
    return "\n".join(lines)


def _md_table_history(rows: list[Row]) -> str:
    lines: list[str] = []
    lines.append("| Model | Engine | Device | Batch | Input(HxW) | FLOPs | Mean (ms) | P99 (ms) | Timestamp (UTC) |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")

    for r in rows:
        lines.append(
            f"| {r.model} | {r.engine} | {r.device} | {r.batch or '-'} | {_hw(r)} | "
            f"{_fmt_int_commas(r.flops)} | {_fmt_f3(r.mean_ms)} | {_fmt_f3(r.p99_ms)} | {r.ts_iso or '-'} |"
        )
    return "\n".join(lines)


def _group_key(r: Row) -> tuple[str, str, str, int | None, int | None, int | None]:
    return (r.model, r.engine, r.device, r.batch, r.h, r.w)


def _sort_rows(rows: list[Row], sort: str) -> list[Row]:
    key = {
        "p99": lambda r: (r.p99_ms is None, r.p99_ms),
        "mean": lambda r: (r.mean_ms is None, r.mean_ms),
        "flops": lambda r: (r.flops is None, r.flops),
        "time": lambda r: _ts_key(r.ts_iso),
    }.get(sort)

    if key is None:
        raise ValueError("--sort must be one of: p99, mean, flops, time")

    return sorted(rows, key=key)


def _latest_per_group(rows: list[Row]) -> list[Row]:
    best: dict[tuple[str, str, str, int | None, int | None, int | None], Row] = {}
    for r in rows:
        group_key = _group_key(r)
        if group_key not in best or _ts_key(r.ts_iso) > _ts_key(best[group_key].ts_iso):
            best[group_key] = r
    return list(best.values())


def _row_to_dict(row: Row) -> dict[str, Any]:
    return asdict(row)


def build_summary_bundle(
    pattern: str,
    format: str = "md",
    mode: str = "latest",
    sort: str = "p99",
    recent: int = 0,
    top: int = 0,
) -> dict[str, Any]:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise ValueError(f"no files matched: {pattern}")

    rows = [_to_row(path, _load_one(path)) for path in paths]

    if recent > 0:
        rows = sorted(rows, key=lambda r: _ts_key(r.ts_iso))
        rows = rows[-recent:]

    if mode not in ("latest", "history", "both"):
        raise ValueError("--mode must be one of: latest, history, both")

    if format != "md":
        raise ValueError("--format currently supports only: md")

    history_rows = _sort_rows(rows, sort=sort)
    latest_rows = _sort_rows(_latest_per_group(rows), sort=sort)

    if top > 0:
        history_rows = history_rows[:top]
        latest_rows = latest_rows[:top]

    if mode == "latest":
        markdown = "## Latest (recommended)\n\n" + _md_table_latest(latest_rows) + "\n"
    elif mode == "history":
        markdown = "## History (raw)\n\n" + _md_table_history(history_rows) + "\n"
    else:
        markdown = (
            "## Latest (recommended)\n\n"
            + _md_table_latest(latest_rows)
            + "\n\n"
            + "## History (raw)\n\n"
            + _md_table_history(history_rows)
            + "\n"
        )

    return {
        "meta": {
            "pattern": pattern,
            "format": format,
            "mode": mode,
            "sort": sort,
            "recent": recent,
            "top": top,
        },
        "data": {
            "rows": [_row_to_dict(row) for row in rows],
            "latest_rows": [_row_to_dict(row) for row in latest_rows],
            "history_rows": [_row_to_dict(row) for row in history_rows],
        },
        "rendered": {
            "markdown": markdown,
        },
    }


def build_summary_markdown(
    pattern: str,
    format: str = "md",
    mode: str = "latest",
    sort: str = "p99",
    recent: int = 0,
    top: int = 0,
) -> str:
    bundle = build_summary_bundle(
        pattern=pattern,
        format=format,
        mode=mode,
        sort=sort,
        recent=recent,
        top=top,
    )
    return str(bundle["rendered"]["markdown"])
