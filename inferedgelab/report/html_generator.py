from __future__ import annotations

from html import escape
from typing import Any, Dict, Optional

from inferedgelab.report.runtime_intelligence import (
    build_runtime_intelligence_reviewer_focus_rows,
    build_runtime_intelligence_risk_rows,
)
from inferedgelab.services.guard_analysis import guard_primary_reason, guard_status, guard_verdict


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


def _ordered_accuracy_metrics(accuracy: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    metrics = accuracy.get("metrics") or {}
    primary_metric = str(accuracy.get("metric_name") or "")

    ordered: Dict[str, Dict[str, Any]] = {}
    if primary_metric and primary_metric in metrics:
        ordered[primary_metric] = metrics[primary_metric]

    for metric_name, values in metrics.items():
        if metric_name == primary_metric:
            continue
        ordered[metric_name] = values

    return ordered


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


def _guard_values_to_html(values: Any) -> str:
    if not values:
        return "<li>-</li>"
    if not isinstance(values, list):
        values = [values]
    return "\n".join(f"<li>{escape(str(value))}</li>" for value in values)


def _guard_source_to_html(source: Any) -> str:
    if not isinstance(source, dict) or not source:
        return ""
    items = "\n".join(
        f"<li><strong>{escape(str(key))}</strong>: <code>{escape(str(value))}</code></li>"
        for key, value in source.items()
    )
    return f"<p><strong>source</strong></p><ul>{items}</ul>"


def _guard_evidence_to_html(evidence: Any) -> str:
    if not isinstance(evidence, list) or not evidence:
        return ""
    rows: list[str] = []
    details: list[str] = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        rows.append(
            f"""
            <tr>
              <td>{escape(str(item.get("type", "-")))}</td>
              <td>{escape(str(item.get("metric_name", "-")))}</td>
              <td>{escape(str(item.get("observed_value", "-")))}</td>
              <td>{escape(str(item.get("baseline_value", "-")))}</td>
              <td>{escape(str(item.get("threshold", "-")))}</td>
              <td>{escape(str(item.get("status", "-")))}</td>
              <td>{escape(str(item.get("severity", "-")))}</td>
            </tr>
            """
        )
        explanation = item.get("explanation")
        why_it_matters = item.get("why_it_matters")
        suspected_causes = item.get("suspected_causes") or []
        recommendation = item.get("recommendation")
        if explanation:
            supplemental = ""
            if why_it_matters:
                supplemental += (
                    f"<br><em>why_it_matters</em>: {escape(str(why_it_matters))}"
                )
            if suspected_causes:
                supplemental += (
                    "<br><em>suspected_causes</em>: "
                    + escape(", ".join(str(cause) for cause in suspected_causes))
                )
            details.append(
                "<li>"
                f"<strong>{escape(str(item.get('metric_name', 'evidence')))}</strong>: "
                f"{escape(str(explanation))}"
                + supplemental
                + (
                    f"<br><em>recommendation</em>: {escape(str(recommendation))}"
                    if recommendation
                    else ""
                )
                + "</li>"
            )
    if not rows:
        return ""
    return f"""
    <h3>Guard Evidence</h3>
    <table>
      <thead>
        <tr>
          <th>type</th>
          <th>metric</th>
          <th>observed</th>
          <th>baseline</th>
          <th>threshold</th>
          <th>status</th>
          <th>severity</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <ul>{''.join(details)}</ul>
    """


def _guard_analysis_to_html(guard_analysis: Dict[str, Any] | None) -> str:
    if guard_analysis is None:
        return ""

    normalized_status = guard_status(guard_analysis)
    normalized_verdict = guard_verdict(guard_analysis)
    verdict_html = (
        f'<p><strong>guard_verdict</strong>: <code>{escape(str(normalized_verdict))}</code></p>'
        if normalized_verdict is not None
        else ""
    )
    severity_html = (
        f'<p><strong>severity</strong>: <code>{escape(str(guard_analysis.get("severity")))}</code></p>'
        if guard_analysis.get("severity") is not None
        else ""
    )
    primary_reason = guard_primary_reason(guard_analysis)
    primary_reason_html = (
        f"<p><strong>primary_reason</strong>: {escape(str(primary_reason))}</p>"
        if primary_reason
        else ""
    )

    if normalized_status == "skipped":
        return f"""
  <h2>Guard Analysis</h2>
  <div class="meta">
    <p><strong>status</strong>: <code>{escape(str(normalized_status))}</code></p>
    <p><strong>reason</strong>: {escape(str(guard_analysis.get("reason")))}</p>
  </div>
        """

    return f"""
  <h2>Guard Analysis</h2>
  <div class="meta">
    <p><strong>status</strong>: <code>{escape(str(normalized_status))}</code></p>
    {verdict_html}
    {severity_html}
    <p><strong>confidence</strong>: <code>{escape(str(guard_analysis.get("confidence")))}</code></p>
    {primary_reason_html}
    {_guard_source_to_html(guard_analysis.get("source"))}
    <p><strong>anomalies</strong></p>
    <ul>{_guard_values_to_html(guard_analysis.get("anomalies"))}</ul>
    <p><strong>suspected_causes</strong></p>
    <ul>{_guard_values_to_html(guard_analysis.get("suspected_causes"))}</ul>
    <p><strong>recommendations</strong></p>
    <ul>{_guard_values_to_html(guard_analysis.get("recommendations"))}</ul>
    {_guard_evidence_to_html(guard_analysis.get("evidence"))}
  </div>
    """


def _deployment_decision_to_html(deployment_decision: Dict[str, Any] | None) -> str:
    if deployment_decision is None:
        return ""

    triggered_rules = deployment_decision.get("triggered_rules") or []
    triggered_rules_html = ""
    if triggered_rules:
        triggered_rules_html = (
            "<p><strong>triggered_rules</strong>: "
            + ", ".join(f"<code>{escape(str(rule))}</code>" for rule in triggered_rules)
            + "</p>"
        )
    policy_summary_rows = []
    for item in deployment_decision.get("policy_summary") or []:
        if not isinstance(item, dict):
            continue
        policy_summary_rows.append(
            f"""
            <tr>
              <td><code>{escape(str(item.get("rule", "-")))}</code></td>
              <td><code>{escape(str(item.get("effect", "-")))}</code></td>
              <td>{escape(str(item.get("description", "-")))}</td>
            </tr>
            """
        )
    policy_summary_html = ""
    if policy_summary_rows:
        policy_summary_html = f"""
        <h3>Decision Policy Summary</h3>
        <table>
          <thead>
            <tr>
              <th>rule</th>
              <th>effect</th>
              <th>description</th>
            </tr>
          </thead>
          <tbody>{''.join(policy_summary_rows)}</tbody>
        </table>
        """

    return f"""
  <h2>Deployment Decision</h2>
  <div class="meta">
    <p><strong>policy_version</strong>: <code>{escape(str(deployment_decision.get("policy_version")))}</code></p>
    <p><strong>decision</strong>: <code>{escape(str(deployment_decision.get("decision")))}</code></p>
    <p><strong>reason</strong>: {escape(str(deployment_decision.get("reason")))}</p>
    <p><strong>lab_overall</strong>: <code>{escape(str(deployment_decision.get("lab_overall")))}</code></p>
    <p><strong>guard_status</strong>: <code>{escape(str(deployment_decision.get("guard_status")))}</code></p>
    <p><strong>recommended_action</strong>: {escape(str(deployment_decision.get("recommended_action")))}</p>
    {triggered_rules_html}
    {policy_summary_html}
  </div>
    """


def _edgeenv_regression_to_html(edgeenv_regression: Dict[str, Any] | None) -> str:
    if edgeenv_regression is None:
        return ""
    evidence = edgeenv_regression.get("evidence") or {}
    comparability = edgeenv_regression.get("comparability") or {}
    runtime_telemetry_context = edgeenv_regression.get("runtime_telemetry_context")
    triggered = evidence.get("triggered_thresholds") or []
    evidence_rows = []
    for field in (
        "mean_delta_pct",
        "p95_delta_pct",
        "p99_delta_pct",
        "fps_delta_pct",
        "memory_peak_delta_pct",
    ):
        evidence_rows.append(
            f"""
            <tr>
              <td>{escape(field)}</td>
              <td>{escape(_fmt_pct(evidence.get(field)))}</td>
            </tr>
            """
        )
    threshold_rows = []
    for item in triggered:
        if not isinstance(item, dict):
            continue
        threshold_rows.append(
            f"""
            <tr>
              <td>{escape(str(item.get("name", "-")))}</td>
              <td>{escape(str(item.get("metric", "-")))}</td>
              <td>{escape(_fmt_num(item.get("observed")))}</td>
              <td>{escape(_fmt_num(item.get("threshold")))}</td>
              <td>{escape(str(item.get("severity", "-")))}</td>
            </tr>
            """
        )
    threshold_html = ""
    if threshold_rows:
        threshold_html = f"""
        <h3>Triggered Thresholds</h3>
        <table>
          <thead>
            <tr>
              <th>name</th>
              <th>metric</th>
              <th>observed</th>
              <th>threshold</th>
              <th>severity</th>
            </tr>
          </thead>
          <tbody>{''.join(threshold_rows)}</tbody>
        </table>
        """
    reasons = comparability.get("reasons") or []
    reasons_html = _guard_values_to_html(reasons)
    runtime_telemetry_html = (
        _runtime_telemetry_context_to_html(runtime_telemetry_context)
        if isinstance(runtime_telemetry_context, dict)
        else ""
    )
    return f"""
  <h2>Runtime Regression Evidence</h2>
  <div class="meta">
    <p><strong>source</strong>: EdgeEnv Runtime Regression Monitor</p>
    <p><strong>comparable</strong>: <code>{escape(str(edgeenv_regression.get("comparable")))}</code></p>
    <p><strong>mode</strong>: <code>{escape(str(edgeenv_regression.get("mode")))}</code></p>
    <p><strong>regression_detected</strong>: <code>{escape(str(edgeenv_regression.get("regression_detected")))}</code></p>
    <p><strong>regression_type</strong>: <code>{escape(str(edgeenv_regression.get("regression_type")))}</code></p>
    <p><strong>severity</strong>: <code>{escape(str(edgeenv_regression.get("severity")))}</code></p>
    <p><strong>recommendation</strong>: {escape(str(edgeenv_regression.get("recommendation")))}</p>
    <p><strong>comparability_judgement</strong>: <code>{escape(str(comparability.get("comparable")))}</code></p>
    <p><strong>comparability_reasons</strong></p>
    <ul>{reasons_html}</ul>
    <table>
      <thead>
        <tr>
          <th>Evidence</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>{''.join(evidence_rows)}</tbody>
    </table>
    {threshold_html}
    {runtime_telemetry_html}
    <p><em>EdgeEnv regression evidence is local-first report context, not cloud monitoring, ranking, or production observability.</em></p>
  </div>
    """


def _runtime_telemetry_context_to_html(context: Dict[str, Any]) -> str:
    history = context.get("history") or {}
    history_summary = history.get("summary") or {}
    history_items = []
    for key in ("registered_runs", "telemetry_runs", "missing_telemetry_runs"):
        if key in history_summary:
            history_items.append(
                f"<li><strong>{escape(key)}</strong>: <code>{escape(str(history_summary.get(key)))}</code></li>"
            )
    history_coverage = history.get("telemetry_coverage") or {}
    history_coverage_items = []
    if isinstance(history_coverage, dict):
        for key in ("runs_with_coverage", "missing_field_run_count"):
            if key in history_coverage:
                history_coverage_items.append(
                    f"<li><strong>{escape(key)}</strong>: <code>{escape(str(history_coverage.get(key)))}</code></li>"
                )
        history_coverage_items.append(
            "<li><strong>missing_field_runs</strong>: "
            f"<code>{escape(_fmt_history_missing_field_runs(history_coverage))}</code></li>"
        )
    history_coverage_html = ""
    if history_coverage_items:
        history_coverage_html = (
            "<p><strong>history_telemetry_coverage</strong></p>"
            f"<ul>{''.join(history_coverage_items)}</ul>"
        )
    history_html = ""
    if history:
        history_html = f"""
        <p><strong>history_schema_version</strong>: <code>{escape(str(history.get("schema_version")))}</code></p>
        <ul>{''.join(history_items)}</ul>
        {history_coverage_html}
        """

    rows = []
    for label in ("baseline", "candidate"):
        run_context = context.get(label) or {}
        coverage = _runtime_telemetry_coverage(run_context)
        rows.append(
            f"""
            <tr>
              <td>{escape(label)} <code>{escape(str(run_context.get("run_id", "-")))}</code></td>
              <td>{escape(str(run_context.get("result_telemetry_present")))}</td>
              <td>{escape(str(run_context.get("history_entry_present")))}</td>
              <td>{escape(_fmt_num(run_context.get("execution_sequence_id")))}</td>
              <td>{escape(_fmt_num(run_context.get("history_execution_sequence_id")))}</td>
              <td>{escape(str(run_context.get("telemetry_source", "-")))}</td>
              <td>{escape(_fmt_coverage_ratio(coverage))}</td>
              <td>{escape(_fmt_coverage_missing_fields(coverage))}</td>
              <td>{escape(_fmt_missing_is_failure(coverage))}</td>
            </tr>
            """
        )

    evidence_gaps = context.get("evidence_gaps") or []
    if evidence_gaps:
        gap_items = []
        for gap in evidence_gaps:
            if not isinstance(gap, dict):
                continue
            gap_items.append(
                f"<li><code>{escape(str(gap.get('run_id', '-')))}</code>: {escape(str(gap.get('reason', '-')))}</li>"
            )
        gaps_html = f"<ul>{''.join(gap_items)}</ul>"
    else:
        gaps_html = "<p>none</p>"

    notes = context.get("notes") or []
    notes_html = _guard_values_to_html(notes)

    return f"""
    <h3>Runtime Telemetry Context</h3>
    <p><strong>role</strong>: <code>{escape(str(context.get("role")))}</code></p>
    <p><strong>source</strong>: <code>{escape(str(context.get("source")))}</code></p>
    {history_html}
    <table>
      <thead>
        <tr>
          <th>Run</th>
          <th>telemetry_present</th>
          <th>history_entry</th>
          <th>execution_sequence_id</th>
          <th>history_execution_sequence_id</th>
          <th>telemetry_source</th>
          <th>coverage_ratio</th>
          <th>coverage_missing_fields</th>
          <th>missing_is_failure</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <p><strong>Runtime telemetry evidence gaps</strong></p>
    {gaps_html}
    <p><strong>Telemetry context notes</strong></p>
    <ul>{notes_html}</ul>
    """


def _runtime_telemetry_coverage(context: Dict[str, Any]) -> Dict[str, Any] | None:
    coverage = context.get("telemetry_coverage")
    if isinstance(coverage, dict):
        return coverage
    coverage = context.get("history_telemetry_coverage")
    if isinstance(coverage, dict):
        return coverage
    return None


def _fmt_history_missing_field_runs(coverage: Dict[str, Any]) -> str:
    missing_field_runs = coverage.get("missing_field_runs")
    if not isinstance(missing_field_runs, list) or not missing_field_runs:
        return "none"
    labels: list[str] = []
    for item in missing_field_runs:
        if not isinstance(item, dict):
            continue
        missing_fields = item.get("missing_fields")
        if not isinstance(missing_fields, list):
            missing_fields = []
        fields = ",".join(str(field) for field in missing_fields) or "none"
        labels.append(f"{item.get('run_id', '-')}={fields}")
    return "; ".join(labels) if labels else "none"


def _fmt_coverage_ratio(coverage: Dict[str, Any] | None) -> str:
    if coverage is None:
        return "-"
    return _fmt_num(coverage.get("coverage_ratio"))


def _fmt_coverage_missing_fields(coverage: Dict[str, Any] | None) -> str:
    if coverage is None:
        return "-"
    missing_fields = coverage.get("missing_fields")
    if not isinstance(missing_fields, list) or not missing_fields:
        return "none"
    return ", ".join(str(item) for item in missing_fields)


def _fmt_missing_is_failure(coverage: Dict[str, Any] | None) -> str:
    if coverage is None:
        return "-"
    value = coverage.get("missing_telemetry_is_failure")
    if value is None:
        return "-"
    return str(value)


def _runtime_intelligence_risk_summary_to_html(
    *,
    guard_analysis: Dict[str, Any] | None,
    deployment_decision: Dict[str, Any] | None,
    edgeenv_regression: Dict[str, Any] | None,
) -> str:
    rows = build_runtime_intelligence_risk_rows(
        guard_analysis=guard_analysis,
        deployment_decision=deployment_decision,
        edgeenv_regression=edgeenv_regression,
    )
    if not rows:
        return ""

    focus_rows = build_runtime_intelligence_reviewer_focus_rows(
        guard_analysis=guard_analysis,
        deployment_decision=deployment_decision,
        edgeenv_regression=edgeenv_regression,
    )
    focus_html = []
    for focus, value, first_read in focus_rows:
        focus_html.append(
            f"""
            <tr>
              <td>{escape(focus)}</td>
              <td>{escape(value)}</td>
              <td>{escape(first_read)}</td>
            </tr>
            """
        )

    row_html = []
    for signal, value, interpretation in rows:
        row_html.append(
            f"""
            <tr>
              <td>{escape(signal)}</td>
              <td>{escape(value)}</td>
              <td>{escape(interpretation)}</td>
            </tr>
            """
        )

    review_path_html = (
        '<div class="review-path">'
        "<h3>Review Path</h3>"
        "<p><strong>Review path:</strong> start with <code>Reviewer Focus</code>, "
        "then open <code>Detailed Evidence Rows</code> only for comparable "
        "regression, telemetry/replay gaps, operation quick scan, preserved "
        "run/path, or deterministic warning evidence. Lab remains the final "
        "deployment decision owner.</p>"
        "<p><strong>Fast path:</strong> <code>Reviewer Focus</code> -> "
        "<code>Detailed Evidence Rows</code> only when a quick signal needs "
        "supporting evidence.</p>"
        '<div class="review-path-steps">'
        '<div class="review-step"><span class="review-step-index">1</span>'
        "<strong>Reviewer Focus</strong>: quick scan comparability, telemetry "
        "quality, operation pressure, and AIGuard warning status.</div>"
        '<div class="review-step"><span class="review-step-index">2</span>'
        "<strong>Detailed Evidence Rows</strong>: open only the rows needed "
        "to verify the specific regression, "
        "replay gap, preserved run/path, or deterministic warning evidence.</div>"
        "</div>"
        "</div>"
    )

    return f"""
  <h2>Runtime Intelligence Risk Summary</h2>
  <div class="meta">
    {review_path_html}
    <h3>Reviewer Focus</h3>
    <table>
      <thead>
        <tr>
          <th>Focus</th>
          <th>Quick signal</th>
          <th>First read</th>
        </tr>
      </thead>
      <tbody>{''.join(focus_html)}</tbody>
    </table>
    <h3>Detailed Evidence Rows</h3>
    <table>
      <thead>
        <tr>
          <th>Signal</th>
          <th>Value</th>
          <th>Lab interpretation</th>
        </tr>
      </thead>
      <tbody>{''.join(row_html)}</tbody>
    </table>
  </div>
    """


def generate_compare_html(
    compare_result: Dict[str, Any],
    judgement: Dict[str, Any],
    guard_analysis: Dict[str, Any] | None = None,
    deployment_decision: Dict[str, Any] | None = None,
    edgeenv_regression: Dict[str, Any] | None = None,
) -> str:
    base_id = compare_result["base_id"]
    new_id = compare_result["new_id"]
    precision = compare_result["precision"]
    metrics = compare_result["metrics"]
    accuracy = compare_result["accuracy"]
    primary_accuracy_metric = str(accuracy.get("metric_name") or "unknown")
    thresholds = judgement.get("thresholds", {})
    shape_context = compare_result["shape_context"]
    runtime_provenance = compare_result["runtime_provenance"]

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

    runtime_provenance_rows = _table_rows_from_diff_map(
        {
            "runtime_artifact_path": {
                "base": runtime_provenance["base"].get("runtime_artifact_path"),
                "new": runtime_provenance["new"].get("runtime_artifact_path"),
            },
            "primary_input_name": {
                "base": runtime_provenance["base"].get("primary_input_name"),
                "new": runtime_provenance["new"].get("primary_input_name"),
            },
            "requested_shape_summary": {
                "base": runtime_provenance["base"].get("requested_shape_summary"),
                "new": runtime_provenance["new"].get("requested_shape_summary"),
            },
            "effective_shape_summary": {
                "base": runtime_provenance["base"].get("effective_shape_summary"),
                "new": runtime_provenance["new"].get("effective_shape_summary"),
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
    accuracy_rows = _table_rows_from_accuracy_map(_ordered_accuracy_metrics(accuracy))
    notes_html = _notes_to_html(judgement["notes"])
    threshold_rows = _threshold_rows(thresholds)
    guard_analysis_html = _guard_analysis_to_html(guard_analysis)
    edgeenv_regression_html = _edgeenv_regression_to_html(edgeenv_regression)
    runtime_intelligence_risk_summary_html = _runtime_intelligence_risk_summary_to_html(
        guard_analysis=guard_analysis,
        deployment_decision=deployment_decision,
        edgeenv_regression=edgeenv_regression,
    )
    deployment_decision_html = _deployment_decision_to_html(deployment_decision)

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
    .review-path {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-left: 4px solid #2563eb;
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 18px;
    }}
    .review-path h3 {{
      margin-top: 0;
    }}
    .review-path p {{
      margin: 8px 0;
      line-height: 1.55;
    }}
    .review-path-steps {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 10px;
      margin-top: 12px;
    }}
    .review-step {{
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 12px;
      color: #4b5563;
      line-height: 1.45;
    }}
    .review-step strong {{
      font-weight: 700;
    }}
    .review-step-index {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      margin-right: 8px;
      border-radius: 999px;
      background: #dbeafe;
      color: #1e40af;
      font-size: 13px;
      font-weight: 700;
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

  <h2>Runtime Provenance Summary</h2>
  <table>
    <thead>
      <tr>
        <th>Field</th>
        <th>Base</th>
        <th>New</th>
      </tr>
    </thead>
    <tbody>
      {runtime_provenance_rows}
    </tbody>
  </table>

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
    <p><strong>Primary metric</strong>: <code>{escape(primary_accuracy_metric)}</code></p>
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
  {guard_analysis_html}
  {edgeenv_regression_html}
  {runtime_intelligence_risk_summary_html}
  {deployment_decision_html}
</body>
</html>
"""
