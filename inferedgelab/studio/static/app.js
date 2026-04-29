const pipelineStages = [
  {
    key: "forge",
    name: "Forge",
    description: "provenance",
  },
  {
    key: "runtime",
    name: "Runtime",
    description: "execution",
  },
  {
    key: "lab",
    name: "Lab",
    description: "analysis + decision",
  },
  {
    key: "aiguard",
    name: "AIGuard",
    description: "optional evidence",
    optional: true,
  },
];

let currentJobs = [];
let selectedJob = null;
let selectedJobId = null;
let compareData = null;
let activeDecision = null;
let importedResult = null;

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

function setStatus(id, message, tone = "muted") {
  const target = document.querySelector(id);
  if (!target) {
    return;
  }
  target.textContent = message;
  target.className = `status-line ${tone}`;
}

function setState(id, state) {
  const target = document.querySelector(id);
  if (!target) {
    return;
  }
  target.textContent = state;
  target.className = `state-pill ${normalizeState(state)}`;
}

function setLoading(selector, label = "Loading...") {
  const target = document.querySelector(selector);
  if (!target) {
    return;
  }
  target.replaceChildren(createElement("p", "empty-state loading-dot", label));
}

function setEmpty(selector, label = "No data available") {
  const target = document.querySelector(selector);
  if (!target) {
    return;
  }
  target.replaceChildren(createElement("p", "empty-state", label));
}

async function fetchJson(url) {
  assertHttpStudio();
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }
  return response.json();
}

async function postJson(url, payload) {
  assertHttpStudio();
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }
  return response.json();
}

function assertHttpStudio() {
  if (window.location.protocol === "file:") {
    throw new Error("Open Studio from http://127.0.0.1:8000/studio so it can call the local API.");
  }
}

async function responseErrorMessage(response) {
  const fallback = `Request failed: ${response.status}`;
  try {
    const payload = await response.clone().json();
    if (payload?.detail) {
      return Array.isArray(payload.detail) ? payload.detail.map(String).join("; ") : String(payload.detail);
    }
    if (payload?.error) {
      return typeof payload.error === "string" ? payload.error : JSON.stringify(payload.error);
    }
  } catch (error) {
    const text = await response.text();
    return text || fallback;
  }
  return fallback;
}

async function loadJobs(preferredJobId = selectedJobId) {
  setLoading("#job-list");
  try {
    const payload = await fetchJson("/studio/api/jobs");
    currentJobs = Array.isArray(payload.jobs) ? payload.jobs : [];
    if (currentJobs.length > 0) {
      const preferredJob = currentJobs.find((job) => job.job_id === preferredJobId);
      const nextJob = preferredJob || currentJobs[0];
      selectedJobId = nextJob.job_id;
      renderJobList();
      await loadJobDetail(nextJob.job_id);
    } else {
      selectedJob = null;
      selectedJobId = null;
      renderJobList();
      renderJobDetail();
    }
  } catch (error) {
    currentJobs = [];
    selectedJob = null;
    selectedJobId = null;
    setEmpty("#job-list");
    renderJobDetail();
  }
  renderPipeline();
}

async function loadJobDetail(jobId) {
  if (!jobId) {
    selectedJob = null;
    selectedJobId = null;
    renderJobDetail();
    return;
  }

  selectedJobId = jobId;
  renderJobList();
  setLoading("#job-detail");
  try {
    selectedJob = await fetchJson(`/studio/api/job/${encodeURIComponent(jobId)}`);
    selectedJobId = selectedJob.job_id || jobId;
    renderJobDetail();
    renderJobList();
    updateDecision(extractDecision(selectedJob));
  } catch (error) {
    selectedJob = null;
    renderJobDetail(`Unable to load ${jobId}.`);
  }
  renderPipeline();
}

async function loadCompare() {
  setLoading("#compare-panel");
  try {
    compareData = await fetchJson("/studio/api/compare/latest");
    renderCompare();
    const decision = extractDecision(compareData);
    if (compareData.status === "empty") {
      activeDecision = null;
      renderDecision(decision);
    } else if (!activeDecision) {
      updateDecision(decision);
    }
  } catch (error) {
    compareData = null;
    renderCompare();
    if (!activeDecision) {
      updateDecision(null);
    }
  }
  renderPipeline();
}

async function runModel() {
  const button = document.querySelector("#run-button");
  const modelPath = document.querySelector("#run-model-path").value.trim();
  if (!modelPath) {
    setStatus("#run-status", "Error: enter a model path.", "error");
    return;
  }

  button.disabled = true;
  setState("#run-state", "running");
  setStatus("#run-status", "Loading: creating analyze job...", "loading");
  renderPipeline();
  try {
    const payload = await postJson("/studio/api/run", { model_path: modelPath });
    selectedJobId = payload.job_id;
    selectedJob = payload.job || null;
    setStatus("#run-status", `Success: created ${payload.job_id}`, "success");
    setState("#run-state", "completed");
    await loadJobs(payload.job_id);
  } catch (error) {
    setStatus("#run-status", `Error: ${formatError(error)}`, "error");
    setState("#run-state", "idle");
  } finally {
    button.disabled = false;
    renderPipeline();
  }
}

async function importResult() {
  const button = document.querySelector("#import-button");
  const jsonPath = document.querySelector("#import-json-path").value.trim();
  if (!jsonPath) {
    setStatus("#import-status", "Error: enter a result path.", "error");
    return;
  }

  button.disabled = true;
  setState("#import-state", "running");
  setStatus("#import-status", "Loading: importing Runtime result...", "loading");
  renderPipeline();
  try {
    const payload = await postJson("/studio/api/import", { path: jsonPath });
    importedResult = payload.result;
    setStatus(
      "#import-status",
      payload.compare_ready
        ? "Success: imported. Compare is ready."
        : "Success: imported. Add one more result for compare.",
      "success",
    );
    setState("#import-state", "completed");
    renderImportedResult();
    await loadCompare();
  } catch (error) {
    setStatus("#import-status", `Error: ${formatError(error)}`, "error");
    setState("#import-state", "idle");
  } finally {
    button.disabled = false;
    renderPipeline();
  }
}

async function loadJetsonCommand() {
  const textarea = document.querySelector("#jetson-command");
  setState("#jetson-state", "running");
  setStatus("#jetson-status", "Loading: preparing command...", "loading");
  try {
    const payload = await fetchJson("/studio/api/jetson-command");
    textarea.value = payload.command || "";
    setStatus("#jetson-status", "Success: command ready.", "success");
    setState("#jetson-state", "completed");
  } catch (error) {
    textarea.value = "";
    setStatus("#jetson-status", `Error: ${formatError(error)}`, "error");
    setState("#jetson-state", "idle");
  }
}

async function copyJetsonCommand() {
  const textarea = document.querySelector("#jetson-command");
  try {
    await navigator.clipboard.writeText(textarea.value);
    setStatus("#jetson-status", "Success: copied command.", "success");
  } catch (error) {
    textarea.select();
    setStatus("#jetson-status", "Select and copy manually.", "muted");
  }
}

function renderPipeline() {
  const target = document.querySelector("#pipeline-flow");
  target.replaceChildren();

  const states = pipelineStatus();
  pipelineStages.forEach((stage, index) => {
    const card = createElement("article", "pipeline-card");
    const top = createElement("div", "pipeline-card-top");
    top.append(
      createElement("span", "stage-index", String(index + 1).padStart(2, "0")),
      createElement("span", `state-pill ${states[stage.key]}`, states[stage.key]),
    );

    const title = createElement("h3", "", stage.name);
    const detail = createElement("p", "", stage.description);
    card.append(top, title, detail);
    if (stage.optional) {
      card.append(createElement("span", "soft-label", "optional"));
    }
    target.append(card);
  });
}

function renderRunPanel() {
  document.querySelector("#run-button").onclick = runModel;
  document.querySelector("#import-button").onclick = importResult;
  document.querySelector("#copy-jetson-command").onclick = copyJetsonCommand;
  setState("#run-state", "idle");
  setState("#import-state", "idle");
  setState("#jetson-state", "idle");
}

function renderJobList() {
  const target = document.querySelector("#job-list");
  const count = document.querySelector("#job-count");
  count.textContent = String(currentJobs.length);
  target.replaceChildren();

  if (!currentJobs.length) {
    setEmpty("#job-list", "No recent jobs. Run a model to create one.");
    return;
  }

  currentJobs.forEach((job) => {
    const row = createElement("button", "job-row");
    row.type = "button";
    if (selectedJobId === job.job_id) {
      row.classList.add("selected");
    }
    row.addEventListener("click", () => loadJobDetail(job.job_id));

    const main = createElement("span", "job-main");
    main.append(
      createElement("strong", "", job.job_id || "-"),
      createElement("span", "caption", job.updated_at || job.created_at || "-"),
    );
    row.append(main, createElement("span", `state-pill ${normalizeState(job.status)}`, job.status || "idle"));
    target.append(row);
  });
}

function renderJobDetail(emptyMessage = "Select a job or import a Runtime result.") {
  const target = document.querySelector("#job-detail");
  const selectedStatus = document.querySelector("#selected-job-status");
  target.replaceChildren();

  if (!selectedJob) {
    setState("#selected-job-status", "idle");
    setEmpty("#job-detail", emptyMessage);
    return;
  }

  selectedStatus.textContent = selectedJob.status || "idle";
  selectedStatus.className = `state-pill ${normalizeState(selectedJob.status)}`;

  const result = selectedJob.result || {};
  const runtimeResult = extractRuntimeResult(selectedJob);
  const compareMetrics = result.comparison?.result?.metrics || result.data?.result?.metrics || {};
  const input = selectedJob.input_summary || {};

  const metrics = [
    ["model", runtimeResult.model || input.model_path || input.artifact_path],
    ["backend", runtimeResult.engine || runtimeResult.backend || runtimeResult.backend_key],
    ["device", runtimeResult.device || runtimeResult.device_name],
    ["mean", runtimeResult.mean_ms ?? compareMetrics.mean_ms?.new],
    ["p99", runtimeResult.p99_ms ?? compareMetrics.p99_ms?.new],
    ["fps", runtimeResult.fps || runtimeResult.fps_value],
    ["compare_key", runtimeResult.compare_key],
    ["backend_key", runtimeResult.backend_key],
  ];

  metrics.forEach(([label, value]) => {
    target.append(metricTile(label, formatValue(value)));
  });

  const status = String(selectedJob.status || "").toLowerCase();
  if (!selectedJob.result && status === "queued") {
    target.append(
      detailNote(
        "Queued job",
        "The local API accepted this analyze job. Runtime metrics will appear after a worker/dev completion flow or after importing Runtime result JSON.",
      ),
    );
  } else if (selectedJob.error) {
    target.append(detailNote("Job error", selectedJob.error.message || selectedJob.error.detail || "Inspect job error details."));
  }
}

function renderImportedResult() {
  const target = document.querySelector("#job-detail");
  target.replaceChildren();
  setState("#selected-job-status", "completed");

  if (!importedResult) {
    setEmpty("#job-detail", "No imported result selected.");
    return;
  }

  const metrics = [
    ["model", importedResult.model],
    ["backend", importedResult.engine || importedResult.backend || importedResult.backend_key],
    ["device", importedResult.device || importedResult.device_name],
    ["mean", importedResult.mean_ms],
    ["p99", importedResult.p99_ms],
    ["fps", importedResult.fps || importedResult.fps_value],
    ["compare_key", importedResult.compare_key],
    ["backend_key", importedResult.backend_key],
  ];

  metrics.forEach(([label, value]) => {
    target.append(metricTile(label, formatValue(value)));
  });
}

function renderCompare() {
  const target = document.querySelector("#compare-panel");
  target.replaceChildren();

  if (!compareData || compareData.status === "empty") {
    target.append(emptyCompareCard());
    return;
  }

  const base = compareData.base || compareData.data?.base || {};
  const newer = compareData.new || compareData.data?.new || {};
  const result = compareData.result || compareData.data?.result || {};
  const meanMetric = result.metrics?.mean_ms || {};
  const speedup = result.speedup || result.backend_comparison?.speedup || calculateSpeedup(base, newer);
  const tensorRt = findResultByBackend([base, newer], "tensorrt");
  const onnx = findResultByBackend([base, newer], "onnx");

  target.append(
    compareMetricCard("TensorRT", tensorRt?.mean_ms, tensorRt?.backend_key || "tensorrt"),
    compareMetricCard("ONNX Runtime", onnx?.mean_ms, onnx?.backend_key || "onnxruntime"),
    compareSummaryCard(meanMetric, speedup, base, newer),
  );
}

function renderDecision(decision) {
  const target = document.querySelector("#deployment-decision");
  target.replaceChildren();

  if (!decision) {
    target.className = "decision-card idle";
    target.append(
      createElement("p", "caption", "Decision"),
      createElement("h3", "", "UNKNOWN"),
      createElement("p", "body-text", "No deployment decision is available yet."),
    );
    return;
  }

  const decisionName = String(decision.decision || "unknown");
  target.className = `decision-card ${decisionTone(decisionName)}`;
  target.append(
    createElement("p", "caption", "Decision"),
    createElement("h3", "", decisionName.toUpperCase()),
    createElement("p", "body-text", decision.reason || "-"),
    createElement("p", "caption", decision.notes || decision.recommended_action || ""),
  );
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

function detailNote(title, message) {
  const note = createElement("div", "detail-note");
  note.append(createElement("strong", "", title), createElement("p", "body-text", message));
  return note;
}

function compareMetricCard(label, meanMs, backendKey) {
  const card = createElement("article", "compare-card");
  card.append(
    createElement("p", "caption", backendKey),
    createElement("h3", "", label),
    createElement("strong", "compare-value", meanMs === undefined || meanMs === null ? "-" : `${formatNumber(meanMs)} ms`),
  );
  return card;
}

function compareSummaryCard(metric, speedup, base, newer) {
  const card = createElement("article", "compare-card highlight");
  const diff = formatLatencyDiff(metric);
  const faster = speedup ? `${formatNumber(speedup)}x faster` : "speedup unavailable";
  card.append(
    createElement("p", "caption", "Latency comparison"),
    createElement("h3", "", faster),
    createElement("p", "body-text", `Latency diff: ${diff}`),
    createElement("p", "caption", `${base.backend_key || "-"} -> ${newer.backend_key || "-"}`),
  );
  return card;
}

function emptyCompareCard() {
  const card = createElement("article", "compare-card empty");
  card.append(
    createElement("p", "caption", "TensorRT vs ONNX Runtime"),
    createElement("h3", "", "No compare-ready result"),
    createElement("p", "body-text", "Import two compatible Runtime JSON files or run the CLI workflow, then reload Studio."),
  );
  return card;
}

function extractDecision(payload) {
  if (!payload) {
    return null;
  }
  return payload.deployment_decision || payload.result?.deployment_decision || payload.data?.deployment_decision || null;
}

function extractRuntimeResult(job) {
  const result = job?.result;
  if (!result) {
    return {};
  }
  return (
    result.runtime_result ||
    result.comparison?.result?.runtime_result ||
    result.comparison?.result?.new ||
    result.data?.new ||
    result.new ||
    result
  );
}

function pipelineStatus() {
  const anyRunning = currentJobs.some((job) => job.status === "queued" || job.status === "running");
  const anyCompleted = currentJobs.some((job) => job.status === "completed") || Boolean(importedResult);
  const hasCompareDecision = Boolean(activeDecision);
  return {
    forge: importedResult ? "completed" : "idle",
    runtime: anyRunning ? "running" : anyCompleted ? "completed" : "idle",
    lab: hasCompareDecision ? "completed" : anyRunning ? "running" : "idle",
    aiguard: hasCompareDecision && activeDecision?.guard_status ? "completed" : "idle",
  };
}

function normalizeState(state) {
  const value = String(state || "idle").toLowerCase();
  if (value === "queued") {
    return "running";
  }
  if (value === "completed" || value === "success" || value === "deployable") {
    return "completed";
  }
  if (value === "failed" || value === "blocked" || value === "error") {
    return "blocked";
  }
  if (value.includes("review")) {
    return "review";
  }
  if (value === "running") {
    return "running";
  }
  return "idle";
}

function decisionTone(decision) {
  const normalized = normalizeState(decision);
  if (normalized === "completed") {
    return "deployable";
  }
  return normalized;
}

function findResultByBackend(results, keyword) {
  return results.find((item) => String(item.backend_key || item.engine || "").toLowerCase().includes(keyword));
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

async function initLocalStudio() {
  try {
    renderRunPanel();
    renderPipeline();
    renderJobDetail();
    renderCompare();
    updateDecision(null);
    await loadJobs();
    await loadCompare();
    await loadJetsonCommand();
  } catch (error) {
    console.error("Local Studio initialization failed", error);
    if (window.location.protocol === "file:") {
      renderFileProtocolNotice();
    }
    renderSafeFallback();
  }
}

function renderFileProtocolNotice() {
  const message = "Open http://127.0.0.1:8000/studio instead of this file path to use Run, Import, Compare, and Jetson helpers.";
  setStatus("#run-status", message, "error");
  setStatus("#import-status", message, "error");
  setStatus("#jetson-status", message, "error");
}

function renderSafeFallback() {
  const requiredTargets = [
    ["#pipeline-flow", "Pipeline cards could not be initialized."],
    ["#job-list", "Job list is temporarily unavailable."],
    ["#job-detail", "Result detail is temporarily unavailable."],
    ["#compare-panel", "Compare view is temporarily unavailable."],
    ["#deployment-decision", "Deployment decision is temporarily unavailable."],
  ];

  requiredTargets.forEach(([selector, message]) => {
    const target = document.querySelector(selector);
    if (target && target.children.length === 0) {
      target.replaceChildren(createElement("p", "empty-state", message));
    }
  });
}

function formatError(error) {
  const message = error?.message || String(error || "request failed");
  return message.replace(/^Error:\s*/, "");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLocalStudio);
} else {
  initLocalStudio();
}
