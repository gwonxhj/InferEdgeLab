const studioDemoData = {
  pipeline: [
    {
      name: "Forge",
      detail: "Build provenance and manifest evidence",
    },
    {
      name: "Runtime",
      detail: "Local execution, profiling, and result export",
    },
    {
      name: "Lab",
      detail: "Compare, report, job workflow, deployment decision",
    },
    {
      name: "AIGuard",
      detail: "Optional deterministic diagnosis evidence",
      optional: true,
    },
  ],
};

let activeDecision = null;

function createElement(tagName, className, textContent) {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  if (textContent !== undefined && textContent !== null) {
    element.textContent = textContent;
  }
  return element;
}

function setLoading(selector, label = "Loading...") {
  const target = document.querySelector(selector);
  target.replaceChildren(createElement("p", "empty-state", label));
}

function setEmpty(selector, label = "No data available") {
  const target = document.querySelector(selector);
  target.replaceChildren(createElement("p", "empty-state", label));
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadJobs() {
  setLoading("#job-list");
  try {
    const payload = await fetchJson("/studio/api/jobs");
    const jobs = Array.isArray(payload.jobs) ? payload.jobs : [];
    renderJobList(jobs);
    if (jobs.length > 0) {
      await loadJobDetail(jobs[0].job_id);
    } else {
      setEmpty("#job-detail");
    }
  } catch (error) {
    setEmpty("#job-list");
    setEmpty("#job-detail");
  }
}

async function loadJobDetail(jobId) {
  if (!jobId) {
    setEmpty("#job-detail");
    return;
  }

  setLoading("#job-detail");
  try {
    const job = await fetchJson(`/studio/api/job/${encodeURIComponent(jobId)}`);
    renderJobDetail(job);
    updateDecision(extractDecision(job));
  } catch (error) {
    setEmpty("#job-detail");
  }
}

async function loadCompare() {
  setLoading("#compare-panel");
  try {
    const compareResult = await fetchJson("/studio/api/compare/latest");
    renderCompare(compareResult);
    const decision = extractDecision(compareResult);
    if (compareResult.status !== "empty" || !activeDecision) {
      updateDecision(decision);
    }
  } catch (error) {
    setEmpty("#compare-panel");
    if (!activeDecision) {
      updateDecision(null);
    }
  }
}

async function runModel() {
  const button = document.querySelector("#run-button");
  const status = document.querySelector("#run-status");
  const modelPath = document.querySelector("#run-model-path").value.trim();
  if (!modelPath) {
    status.textContent = "Enter a model path.";
    return;
  }

  button.disabled = true;
  status.textContent = "Creating job...";
  try {
    const payload = await postJson("/studio/api/run", { model_path: modelPath });
    status.textContent = `Created ${payload.job_id}`;
    await loadJobs();
  } catch (error) {
    status.textContent = "Run failed.";
  } finally {
    button.disabled = false;
  }
}

async function importResult() {
  const button = document.querySelector("#import-button");
  const status = document.querySelector("#import-status");
  const jsonPath = document.querySelector("#import-json-path").value.trim();
  if (!jsonPath) {
    status.textContent = "Enter a JSON path.";
    return;
  }

  button.disabled = true;
  status.textContent = "Importing result...";
  try {
    const payload = await postJson("/studio/api/import", { path: jsonPath });
    status.textContent = payload.compare_ready
      ? "Imported. Compare is ready."
      : "Imported. Add one more result for compare.";
    renderImportedResult(payload.result);
    await loadCompare();
  } catch (error) {
    status.textContent = "Import failed.";
  } finally {
    button.disabled = false;
  }
}

async function loadJetsonCommand() {
  const textarea = document.querySelector("#jetson-command");
  const status = document.querySelector("#jetson-status");
  status.textContent = "Loading command...";
  try {
    const payload = await fetchJson("/studio/api/jetson-command");
    textarea.value = payload.command || "";
    status.textContent = "Command ready.";
  } catch (error) {
    textarea.value = "";
    status.textContent = "Command unavailable.";
  }
}

async function copyJetsonCommand() {
  const textarea = document.querySelector("#jetson-command");
  const status = document.querySelector("#jetson-status");
  try {
    await navigator.clipboard.writeText(textarea.value);
    status.textContent = "Copied.";
  } catch (error) {
    textarea.select();
    status.textContent = "Select and copy manually.";
  }
}

function renderPipeline(data = studioDemoData.pipeline) {
  const target = document.querySelector("#pipeline-flow");
  target.replaceChildren();

  data.forEach((step, index) => {
    const card = createElement("div", "pipeline-step");
    const number = createElement("span", "step-number", String(index + 1));
    const title = createElement("h3", "", step.name);
    const detail = createElement("p", "", step.detail);

    card.append(number, title, detail);
    if (step.optional) {
      card.append(createElement("span", "badge", "optional"));
    }
    target.append(card);
  });
}

function renderJobList(jobs) {
  const target = document.querySelector("#job-list");
  target.replaceChildren();

  if (!jobs.length) {
    setEmpty("#job-list");
    return;
  }

  jobs.forEach((job) => {
    const button = createElement("button", "summary-row job-row");
    button.type = "button";
    button.addEventListener("click", () => loadJobDetail(job.job_id));
    button.append(
      createElement("strong", "", job.job_id || "-"),
      createElement("span", "", `${job.status || "-"} / ${job.updated_at || job.created_at || "-"}`),
    );
    target.append(button);
  });
}

function renderJobDetail(job) {
  const target = document.querySelector("#job-detail");
  target.replaceChildren();

  if (!job) {
    setEmpty("#job-detail");
    return;
  }

  const result = job.result || {};
  const runtimeResult = result.runtime_result || result.data?.new || result.new || result;
  const compareMetrics = result.comparison?.result?.metrics || result.data?.result?.metrics || {};
  const input = job.input_summary || {};
  const metrics = [
    ["model", runtimeResult.model || input.model_path || input.artifact_path],
    ["engine/backend", runtimeResult.engine || runtimeResult.backend || runtimeResult.backend_key],
    ["device", runtimeResult.device || runtimeResult.device_name],
    ["mean_ms", runtimeResult.mean_ms ?? compareMetrics.mean_ms?.new],
    ["p99_ms", runtimeResult.p99_ms ?? compareMetrics.p99_ms?.new],
    ["fps", runtimeResult.fps || runtimeResult.fps_value],
    ["compare_key", runtimeResult.compare_key],
    ["backend_key", runtimeResult.backend_key],
    ["runtime status", runtimeResult.status || result.status || job.status],
  ];

  metrics.forEach(([label, value]) => {
    target.append(metricTile(label, formatValue(value)));
  });
}

function renderImportedResult(result) {
  const target = document.querySelector("#job-detail");
  target.replaceChildren();

  const metrics = [
    ["model", result.model],
    ["engine/backend", result.engine || result.backend || result.backend_key],
    ["device", result.device || result.device_name],
    ["mean_ms", result.mean_ms],
    ["p99_ms", result.p99_ms],
    ["fps", result.fps || result.fps_value],
    ["compare_key", result.compare_key],
    ["backend_key", result.backend_key],
    ["runtime status", result.status || result.runtime_role],
  ];

  metrics.forEach(([label, value]) => {
    target.append(metricTile(label, formatValue(value)));
  });
}

function renderCompare(compareResult) {
  const target = document.querySelector("#compare-panel");
  target.replaceChildren();

  if (!compareResult || compareResult.status === "empty") {
    setEmpty("#compare-panel");
    return;
  }

  const base = compareResult.base || compareResult.data?.base || {};
  const newer = compareResult.new || compareResult.data?.new || {};
  const result = compareResult.result || compareResult.data?.result || {};
  const meanMetric = result.metrics?.mean_ms || {};
  const speedup = result.speedup || result.backend_comparison?.speedup || calculateSpeedup(base, newer);

  const rows = [
    ["TensorRT backend_key", findBackendKey([base, newer], "tensorrt")],
    ["ONNX Runtime backend_key", findBackendKey([base, newer], "onnx")],
    ["latency diff", formatLatencyDiff(meanMetric)],
    ["speedup", speedup ? `${formatNumber(speedup)}x` : "-"],
    ["base backend_key", base.backend_key],
    ["new backend_key", newer.backend_key],
  ];

  rows.forEach(([label, value]) => {
    const row = createElement("div", "summary-row");
    row.append(createElement("strong", "", label), createElement("span", "", formatValue(value)));
    target.append(row);
  });
}

function renderDecision(decision) {
  const target = document.querySelector("#deployment-decision");
  target.replaceChildren();

  if (!decision) {
    setEmpty("#deployment-decision");
    return;
  }

  const rows = [
    ["decision", decision.decision],
    ["reason", decision.reason],
    ["notes", decision.notes || decision.recommended_action],
  ];

  rows.forEach(([label, value]) => {
    const row = createElement("div", "summary-row");
    row.append(createElement("strong", "", label), createElement("span", "", formatValue(value)));
    target.append(row);
  });
}

function updateDecision(decision) {
  activeDecision = decision;
  renderDecision(decision);
}

function metricTile(label, value) {
  const tile = createElement("div", "metric-tile");
  tile.append(createElement("span", "metric-name", label), createElement("span", "metric-value", value));
  return tile;
}

function extractDecision(payload) {
  if (!payload) {
    return null;
  }
  return payload.deployment_decision || payload.result?.deployment_decision || payload.data?.deployment_decision || null;
}

function findBackendKey(results, keyword) {
  const match = results.find((item) => String(item.backend_key || "").toLowerCase().includes(keyword));
  return match?.backend_key;
}

function formatLatencyDiff(metric) {
  if (!metric || Object.keys(metric).length === 0) {
    return "-";
  }
  const delta = metric.delta_ms ?? metric.delta;
  const deltaPct = metric.delta_pct;
  if (delta === undefined && deltaPct === undefined) {
    return "-";
  }
  const parts = [];
  if (delta !== undefined && delta !== null) {
    parts.push(`${formatNumber(delta)} ms`);
  }
  if (deltaPct !== undefined && deltaPct !== null) {
    parts.push(`${formatNumber(deltaPct)}%`);
  }
  return parts.join(" / ");
}

function calculateSpeedup(base, newer) {
  const baseMean = Number(base.mean_ms);
  const newMean = Number(newer.mean_ms);
  if (!Number.isFinite(baseMean) || !Number.isFinite(newMean) || newMean === 0) {
    return null;
  }
  return baseMean / newMean;
}

function formatNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return String(value);
  }
  return number.toFixed(3).replace(/\.?0+$/, "");
}

function formatValue(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  if (typeof value === "number") {
    return formatNumber(value);
  }
  return String(value);
}

window.onload = async () => {
  renderPipeline();
  document.querySelector("#run-button").addEventListener("click", runModel);
  document.querySelector("#import-button").addEventListener("click", importResult);
  document.querySelector("#copy-jetson-command").addEventListener("click", copyJetsonCommand);
  updateDecision(null);
  await loadJobs();
  await loadCompare();
  await loadJetsonCommand();
};
