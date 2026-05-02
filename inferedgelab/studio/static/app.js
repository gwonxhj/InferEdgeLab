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
let demoEvaluationReport = null;
let demoProblemCases = [];
let activeGuardAnalysis = null;
const importedResultsByJobId = {};

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
  try {
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      throw new Error(await responseErrorMessage(response));
    }
    return await parseJsonResponse(response);
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error(`Invalid JSON response from ${url}.`);
    }
    throw error;
  }
}

async function postJson(url, payload) {
  assertHttpStudio();
  try {
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
    return await parseJsonResponse(response);
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error(`Invalid JSON response from ${url}.`);
    }
    throw error;
  }
}

function assertHttpStudio() {
  if (window.location.protocol === "file:") {
    throw new Error("Open Studio from http://127.0.0.1:8000/studio so it can call the local API.");
  }
}

function markFileMode() {
  if (window.location.protocol === "file:") {
    document.body.classList.add("file-mode");
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

async function parseJsonResponse(response) {
  try {
    return await response.json();
  } catch (error) {
    throw new SyntaxError("Response body is not valid JSON.");
  }
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
    setEmpty("#job-list", `Error: ${formatError(error)}`);
    renderJobDetail(`Unable to load jobs: ${formatError(error)}`);
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
    updateGuardEvidence(extractGuardAnalysis(selectedJob));
  } catch (error) {
    selectedJob = null;
    renderJobDetail(`Unable to load ${jobId}: ${formatError(error)}`);
  }
  renderPipeline();
}

async function loadCompare() {
  setLoading("#compare-panel");
  try {
    compareData = await fetchJson("/studio/api/compare/latest");
    renderCompare();
    const decision = extractDecision(compareData);
    updateGuardEvidence(extractGuardAnalysis(compareData));
    if (compareData.status === "empty") {
      activeDecision = null;
      renderDecision(decision);
    } else {
      updateDecision(decision);
    }
  } catch (error) {
    compareData = { status: "error", error: formatError(error) };
    renderCompare();
    updateGuardEvidence(null);
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
    const payload = await postJson("/studio/api/run", {
      model_path: modelPath,
      options: runOptions(),
    });
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
  const jsonPayload = document.querySelector("#import-json-payload").value.trim();
  if (!jsonPath && !jsonPayload) {
    setStatus("#import-status", "Error: enter a result path or JSON payload.", "error");
    return;
  }

  button.disabled = true;
  setState("#import-state", "running");
  setStatus("#import-status", "Loading: importing Runtime result...", "loading");
  renderPipeline();
  try {
    const payload = await postJson("/studio/api/import", buildImportPayload(jsonPath, jsonPayload));
    importedResult = payload.result;
    rememberImportedResultForSelectedJob(importedResult);
    setStatus(
      "#import-status",
      payload.compare_ready
        ? "Success: imported. Compare is ready."
        : "Success: imported. Add one more result for compare.",
      "success",
    );
    setState("#import-state", "completed");
    renderImportEvidence(payload);
    renderImportedResult();
    await loadCompare();
    renderPipeline();
  } catch (error) {
    setStatus("#import-status", `Error: ${formatError(error)}`, "error");
    setState("#import-state", "idle");
  } finally {
    button.disabled = false;
    renderPipeline();
  }
}

function buildImportPayload(path, jsonPayload) {
  const payload = {};
  if (jsonPayload) {
    try {
      payload.result = JSON.parse(jsonPayload);
    } catch (error) {
      throw new Error("JSON payload is not valid JSON.");
    }
  } else {
    payload.path = path;
  }
  const backendOverride = document.querySelector("#import-backend-preset")?.value || "";
  if (backendOverride) {
    payload.backend_override = backendOverride;
  }
  if (selectedJobId) {
    payload.job_id = selectedJobId;
  }
  return payload;
}

function runOptions() {
  return {
    backend: document.querySelector("#run-backend")?.value || "onnxruntime",
    device: document.querySelector("#run-device")?.value || "cpu",
  };
}

function rememberImportedResultForSelectedJob(result) {
  if (!selectedJobId || !result) {
    return;
  }
  importedResultsByJobId[selectedJobId] = result;
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

async function loadDemoEvidence() {
  const button = document.querySelector("#load-demo-evidence");
  button.disabled = true;
  setState("#demo-state", "running");
  setStatus("#demo-status", "Loading: importing bundled Runtime evidence...", "loading");
  renderPipeline();
  try {
    const payload = await fetchJson("/studio/api/demo-evidence");
    const results = Array.isArray(payload.results) ? payload.results : [];
    importedResult = results[results.length - 1] || null;
    demoEvaluationReport = payload.evaluation_report || null;
    demoProblemCases = Array.isArray(payload.problem_cases) ? payload.problem_cases : [];
    compareData = payload.compare || null;
    updateGuardEvidence(payload.guard_analysis || payload.compare?.guard_analysis || null);
    selectedJobId = payload.job_id || payload.job?.job_id || selectedJobId;
    selectedJob = payload.job || selectedJob;
    setState("#demo-state", "completed");
    setState("#import-state", "completed");
    setStatus("#demo-status", "Success: demo evidence loaded.", "success");
    setStatus("#import-status", "Success: demo ONNX Runtime + TensorRT evidence imported.", "success");
    renderImportEvidence({ result: importedResult });
    renderDemoEvaluation(demoEvaluationReport);
    renderDemoProblemCases(demoProblemCases);
    renderImportedResult();
    await loadJobs(selectedJobId);
    await loadCompare();
  } catch (error) {
    setState("#demo-state", "idle");
    setStatus("#demo-status", `Error: ${formatError(error)}`, "error");
  } finally {
    button.disabled = false;
    renderPipeline();
  }
}

function renderDemoProblemCases(problemCases = []) {
  const target = document.querySelector("#demo-problem-cases");
  if (!target) {
    return;
  }
  target.replaceChildren();

  if (!problemCases.length) {
    return;
  }

  problemCases.forEach((problem) => {
    const signal = problem.deployment_signal || {};
    const card = createElement("article", `problem-case ${decisionTone(signal.decision)}`);
    card.append(
      createElement("p", "caption", problem.problem_case || "problem case"),
      createElement("h4", "", String(signal.decision || "review").toUpperCase()),
      createElement("p", "body-text", signal.reason || "Validation evidence requires review."),
      createElement("p", "caption", problemCaseDetail(problem)),
    );
    target.append(card);
  });
}

function problemCaseDetail(problem = {}) {
  if (problem.problem_case_type === "runtime_latency" || problem.latency_checks) {
    const checks = problem.latency_checks || {};
    const mean = checks.mean_latency?.delta_pct;
    const p99 = checks.p99_latency?.delta_pct;
    const fps = checks.fps?.delta_pct;
    return `mean=${formatPercent(mean)} / p99=${formatPercent(p99)} / fps=${formatPercent(fps)} / run_config=${checks.run_config?.status || "-"}`;
  }
  const structural = problem.structural_validation || {};
  const contractShape = problem.contract_validation?.input_shape || {};
  const accuracy = problem.accuracy || {};
  return `accuracy=${accuracy.status || "-"} / structure=${structural.status || "-"} / contract=${contractShape.status || "-"}`;
}

function renderDemoEvaluation(report) {
  const target = document.querySelector("#demo-report-summary");
  if (!target) {
    return;
  }
  target.replaceChildren();

  if (!report) {
    return;
  }

  const metrics = report.accuracy?.metrics || {};
  const structural = report.structural_validation || {};
  const contract = report.contract_validation?.input_shape || {};
  target.append(
    evidenceItem("preset", report.preset || "yolov8_coco"),
    evidenceItem("samples", report.runtime_result?.sample_count ?? "-"),
    evidenceItem("mAP50", metrics.map50 === undefined ? "-" : formatNumber(metrics.map50)),
    evidenceItem("precision", metrics.precision === undefined ? "-" : formatNumber(metrics.precision)),
    evidenceItem("recall", metrics.recall === undefined ? "-" : formatNumber(metrics.recall)),
    evidenceItem("structure", structural.status || "-"),
    evidenceItem("contract", contract.status || "-"),
    evidenceItem("report", report.source || "-"),
  );
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
      card.append(createElement("p", "stage-note", "No guard run is required for local validation."));
    }
    target.append(card);
  });
}

function renderImportEvidence(payload) {
  const target = document.querySelector("#import-evidence");
  if (!target) {
    return;
  }
  target.replaceChildren();

  const result = payload?.result || {};
  const missing = missingResultKeys(result);
  target.append(
    evidenceItem("model", runtimeModelName(result)),
    evidenceItem("backend", normalizedBackendKey(result) || runtimeBackendName(result)),
    evidenceItem("compare", result.compare_key || fallbackLabel("compare_key")),
    evidenceItem("mean", result.mean_ms === undefined ? "-" : `${formatNumber(result.mean_ms)} ms`),
  );
  if (missing.length > 0) {
    target.append(
      createElement("p", "evidence-warning", `Fallback metadata: missing ${missing.join(", ")}.`),
    );
  }
}

function evidenceItem(label, value) {
  const item = createElement("div", "evidence-item");
  item.append(createElement("span", "metric-name", label), createElement("strong", "", formatValue(value)));
  return item;
}

function renderRunPanel() {
  document.querySelector("#run-button").onclick = runModel;
  document.querySelector("#import-button").onclick = importResult;
  document.querySelector("#copy-jetson-command").onclick = copyJetsonCommand;
  document.querySelector("#load-demo-evidence").onclick = loadDemoEvidence;
  setState("#run-state", "idle");
  setState("#import-state", "idle");
  setState("#jetson-state", "idle");
  setState("#demo-state", "idle");
  renderDemoEvaluation(null);
  renderDemoProblemCases([]);
}

function resetTransientInputs() {
  ["#run-model-path", "#import-json-path", "#import-json-payload"].forEach((selector) => {
    const target = document.querySelector(selector);
    if (target) {
      target.value = "";
    }
  });
  const importPreset = document.querySelector("#import-backend-preset");
  if (importPreset) {
    importPreset.value = "";
  }
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

  currentJobs.forEach((job, index) => {
    const row = createElement("button", "job-row");
    row.type = "button";
    if (selectedJobId === job.job_id) {
      row.classList.add("selected");
    }
    row.addEventListener("click", () => loadJobDetail(job.job_id));

    const main = createElement("span", "job-main");
    main.append(
      createElement("strong", "", jobDisplayName(job, index)),
      createElement("span", "caption", jobCaption(job)),
    );
    row.append(main, createElement("span", `state-pill ${normalizeState(job.status)}`, job.status || "idle"));
    target.append(row);
  });
}

function jobDisplayName(job, index) {
  if (job.display_name) {
    return job.display_name;
  }
  const input = job.input_summary || {};
  const modelPath = input.model_path || input.artifact_path;
  const modelName = modelPath ? modelPath.split("/").pop() : "";
  const prefix = modelName ? `Analyze ${modelName}` : `Analyze job ${index + 1}`;
  const options = input.options || {};
  const backend = firstDisplayValue(options.backend);
  const device = firstDisplayValue(options.device);
  const suffix = backend || device ? ` (${[backend, device].filter(Boolean).join("/")})` : "";
  return `${prefix}${suffix}`;
}

function jobCaption(job) {
  const timestamp = job.updated_at || job.created_at || "-";
  const jobId = job.job_id || "-";
  return `${jobId} · ${timestamp}`;
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
  const importedForJob = importedResultsByJobId[selectedJob.job_id] || {};
  const displayResult = hasRuntimeMetrics(runtimeResult) ? runtimeResult : importedForJob;
  const compareMetrics = result.comparison?.result?.metrics || result.data?.result?.metrics || {};
  const input = selectedJob.input_summary || {};
  const inputOptions = input.options || {};
  const hasMetrics = hasRuntimeMetrics(displayResult);

  const identityMetrics = [
    ["model", runtimeModelName(displayResult) || input.model_path || input.artifact_path],
    ["backend", runtimeBackendName(displayResult) || inputOptions.backend],
    ["device", runtimeDeviceName(displayResult) || inputOptions.device],
  ];
  const resultMetrics = [
    ["mean", displayResult.mean_ms ?? compareMetrics.mean_ms?.new],
    ["p99", displayResult.p99_ms ?? compareMetrics.p99_ms?.new],
    ["fps", displayResult.fps || displayResult.fps_value],
    ["compare_key", displayResult.compare_key],
    ["backend_key", displayResult.backend_key || normalizedBackendKey(displayResult)],
  ];
  const metrics = hasMetrics ? identityMetrics.concat(resultMetrics) : identityMetrics;

  metrics.forEach(([label, value]) => {
    target.append(metricTile(label, formatValue(value)));
  });

  const status = String(selectedJob.status || "").toLowerCase();
  if (!selectedJob.result && status === "queued" && !hasRuntimeMetrics(displayResult)) {
    target.append(
      detailNote(
        "Queued job",
        "This is a request record only. Runtime metrics are not attached to this job yet; use Import or Load Demo Evidence to inspect actual validation evidence.",
      ),
    );
  } else if (!selectedJob.result && hasRuntimeMetrics(displayResult)) {
    target.append(
      detailNote(
        "Imported evidence linked in Studio",
        "This queued analyze job is showing the latest Runtime result imported while the job was selected. The backend contract remains local and in-memory.",
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
    ["model", runtimeModelName(importedResult)],
    ["backend", runtimeBackendName(importedResult)],
    ["device", runtimeDeviceName(importedResult)],
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

  if (compareData?.status === "error") {
    target.append(errorCompareCard(compareData.error));
    return;
  }

  if (!compareData || compareData.status === "empty") {
    target.append(emptyCompareCard());
    return;
  }

  const base = compareData.base || compareData.data?.base || {};
  const newer = compareData.new || compareData.data?.new || {};
  const result = compareData.result || compareData.data?.result || {};
  const judgement = compareData.judgement || compareData.data?.judgement || {};
  const meanMetric = result.metrics?.mean_ms || {};
  const speedup = result.speedup || result.backend_comparison?.speedup || calculateSpeedup(base, newer);
  const tensorRt = findResultByBackend([base, newer], "tensorrt");
  const onnx = findResultByBackend([base, newer], "onnx");
  const sameBackend = normalizedBackendKey(base) && normalizedBackendKey(base) === normalizedBackendKey(newer);

  target.append(
    compareMetricCard("TensorRT", tensorRt, normalizedBackendKey(tensorRt) || "tensorrt"),
    compareMetricCard("ONNX Runtime", onnx, normalizedBackendKey(onnx) || "onnxruntime"),
    compareSummaryCard(meanMetric, speedup, base, newer, sameBackend, judgement.overall),
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
      createElement("p", "body-text", "No Lab comparison decision is available yet."),
      createElement("p", "caption", "Load demo evidence or import two compatible Runtime results. AIGuard remains optional."),
    );
    return;
  }

  const decisionName = String(decision.decision || "unknown");
  target.className = `decision-card ${decisionTone(decisionName)}`;
  target.append(
    createElement("p", "caption", "Decision"),
    createElement("h3", "", decisionName.toUpperCase()),
    createElement("p", "body-text", decisionReason(decision)),
    createElement("p", "caption", decisionNotes(decision)),
  );
}

function updateDecision(decision) {
  activeDecision = decision;
  renderDecision(decision);
}

function renderGuardEvidence(guardAnalysis) {
  const target = document.querySelector("#guard-evidence-panel");
  if (!target) {
    return;
  }
  target.replaceChildren();

  if (!guardAnalysis) {
    target.className = "guard-panel idle";
    target.append(
      createElement("p", "caption", "AIGuard"),
      createElement("h3", "", "OPTIONAL"),
      createElement("p", "body-text", "No AIGuard diagnosis evidence is loaded for this local workflow yet."),
      createElement("p", "caption", "Load Demo Evidence or run compare with guard-backed diagnosis evidence."),
    );
    return;
  }

  const verdict = guardVerdict(guardAnalysis);
  target.className = `guard-panel ${decisionTone(verdict)}`;
  target.append(
    createElement("p", "caption", "AIGuard diagnosis evidence"),
    createElement("h3", "", verdict.toUpperCase()),
    createElement("p", "body-text", guardAnalysis.primary_reason || guardAnalysis.reason || "Guard evidence is available."),
    guardSummary(guardAnalysis, verdict),
  );

  const source = guardAnalysis.source || {};
  if (Object.keys(source).length > 0) {
    const sourcePanel = createElement("div", "guard-source");
    sourcePanel.append(createElement("strong", "", "Source"));
    Object.entries(source).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        sourcePanel.append(evidenceItem(key, value));
      }
    });
    target.append(sourcePanel);
  }

  const evidence = guardEvidenceItems(guardAnalysis);
  if (evidence.length > 0) {
    const table = createElement("div", "guard-evidence-table");
    table.append(guardEvidenceRow(["type", "metric", "observed", "threshold", "status"], true));
    evidence.forEach((item) => {
      table.append(
        guardEvidenceRow([
          item.type || "-",
          item.metric_name || "-",
          item.observed_value,
          item.threshold,
          item.status || item.severity || "-",
        ]),
      );
    });
    target.append(table);
    target.append(guardExplanations(evidence));
  }

  target.append(guardList("Suspected causes", guardAnalysis.suspected_causes));
  target.append(guardList("Recommendations", guardAnalysis.recommendations));
}

function updateGuardEvidence(guardAnalysis) {
  activeGuardAnalysis = guardAnalysis || null;
  renderGuardEvidence(activeGuardAnalysis);
}

function guardSummary(guardAnalysis, verdict) {
  const summary = createElement("div", "guard-summary");
  summary.append(
    evidenceItem("guard_verdict", verdict),
    evidenceItem("severity", guardAnalysis.severity || "-"),
    evidenceItem("confidence", guardAnalysis.confidence ?? "-"),
    evidenceItem("schema", guardAnalysis.schema_version || "legacy"),
  );
  return summary;
}

function guardEvidenceRow(values, heading = false) {
  const row = createElement("div", heading ? "guard-row guard-row-heading" : "guard-row");
  values.forEach((value) => row.append(createElement("span", "", formatValue(value))));
  return row;
}

function guardExplanations(evidence) {
  const explanations = createElement("div", "guard-explanations");
  evidence.forEach((item) => {
    if (!item.explanation && !item.recommendation) {
      return;
    }
    const explanation = createElement("article", "detail-note");
    explanation.append(
      createElement("strong", "", item.metric_name || item.type || "evidence"),
      createElement("p", "body-text", item.explanation || "-"),
    );
    if (item.recommendation) {
      explanation.append(createElement("p", "caption", `Recommendation: ${item.recommendation}`));
    }
    explanations.append(explanation);
  });
  return explanations;
}

function guardList(title, values) {
  const panel = createElement("div", "guard-list");
  panel.append(createElement("strong", "", title));
  const list = createElement("ul", "");
  const items = Array.isArray(values) ? values : values ? [values] : [];
  if (!items.length) {
    list.append(createElement("li", "", "-"));
  } else {
    items.forEach((value) => list.append(createElement("li", "", formatValue(value))));
  }
  panel.append(list);
  return panel;
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

function compareMetricCard(label, result, backendKey) {
  const card = createElement("article", "compare-card");
  const meanMs = result?.mean_ms;
  card.append(
    createElement("p", "caption", backendKey),
    createElement("h3", "", label),
    createElement("strong", "compare-value", meanMs === undefined || meanMs === null ? "-" : `${formatNumber(meanMs)} ms`),
    compareStatList(result),
  );
  return card;
}

function compareStatList(result = {}) {
  const list = createElement("div", "compare-stat-list");
  list.append(
    compareStat("p99", result?.p99_ms === undefined ? "-" : `${formatNumber(result.p99_ms)} ms`),
    compareStat("fps", result?.fps_value ?? result?.fps ?? "-"),
  );
  return list;
}

function compareStat(label, value) {
  const row = createElement("div", "compare-stat");
  row.append(createElement("span", "", label), createElement("strong", "", formatValue(value)));
  return row;
}

function compareSummaryCard(metric, speedup, base, newer, sameBackend = false, overall = "unknown") {
  const card = createElement("article", `compare-card highlight ${compareTone(overall)}`);
  const diff = formatLatencyDiff(metric);
  const speedLabel = compareSpeedLabel(speedup, sameBackend);
  const note = sameBackend
    ? "Import a TensorRT and an ONNX Runtime result to compare backend speedup."
    : compareSpeedNote(speedup, diff);
  card.append(
    createElement("p", "caption", `Latency comparison / ${overall || "unknown"}`),
    createElement("h3", "", speedLabel),
    createElement("p", "body-text", note),
    createElement("p", "caption", `${normalizedBackendKey(base) || "-"} -> ${normalizedBackendKey(newer) || "-"}`),
  );
  return card;
}

function compareSpeedLabel(speedup, sameBackend = false) {
  if (sameBackend) {
    return "Same backend";
  }
  const ratio = Number(speedup);
  if (!Number.isFinite(ratio) || ratio <= 0) {
    return "speedup unavailable";
  }
  if (ratio >= 1) {
    return `${formatNumber(ratio)}x faster`;
  }
  return `${formatNumber(1 / ratio)}x slower`;
}

function compareSpeedNote(speedup, diff) {
  const ratio = Number(speedup);
  if (Number.isFinite(ratio) && ratio > 0 && ratio < 1) {
    return `New result is slower. Latency diff: ${diff}`;
  }
  return `Latency diff: ${diff}`;
}

function errorCompareCard(message) {
  const card = createElement("article", "compare-card empty error-card");
  card.append(
    createElement("p", "caption", "Compare error"),
    createElement("h3", "", "Unable to load compare data"),
    createElement("p", "body-text", message || "No error detail was provided."),
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

function extractGuardAnalysis(payload) {
  if (!payload) {
    return null;
  }
  return (
    payload.guard_analysis ||
    payload.result?.guard_analysis ||
    payload.data?.guard_analysis ||
    payload.result?.comparison?.guard_analysis ||
    payload.result?.comparison?.data?.guard_analysis ||
    null
  );
}

function guardVerdict(guardAnalysis = {}) {
  if (guardAnalysis.guard_verdict) {
    return String(guardAnalysis.guard_verdict);
  }
  const status = String(guardAnalysis.status || "").toLowerCase();
  if (status === "ok") {
    return "pass";
  }
  if (status === "warning") {
    return "review_required";
  }
  if (status === "error") {
    return "blocked";
  }
  if (status === "skipped") {
    return "skipped";
  }
  return "unknown";
}

function guardEvidenceItems(guardAnalysis = {}) {
  if (Array.isArray(guardAnalysis.evidence)) {
    return guardAnalysis.evidence;
  }
  if (Array.isArray(guardAnalysis.anomalies)) {
    return guardAnalysis.anomalies;
  }
  return [];
}

function decisionReason(decision) {
  const decisionName = String(decision?.decision || "unknown").toLowerCase();
  if (decisionName === "unknown" && !decision?.guard_status) {
    return "Lab comparison is available, but AIGuard diagnosis evidence was not loaded for this local demo.";
  }
  return decision?.reason || "-";
}

function decisionNotes(decision) {
  const decisionName = String(decision?.decision || "unknown").toLowerCase();
  if (decisionName === "unknown" && !decision?.guard_status) {
    return "This is expected: AIGuard is optional and only needed when guard-backed diagnosis evidence is part of the review.";
  }
  return decision?.notes || decision?.recommended_action || "";
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

function hasRuntimeMetrics(result = {}) {
  return Boolean(
    result &&
      (result.mean_ms !== undefined ||
        result.p99_ms !== undefined ||
        result.fps !== undefined ||
        result.fps_value !== undefined ||
        result.compare_key ||
        normalizedBackendKey(result)),
  );
}

function pipelineStatus() {
  const anyRunning = currentJobs.some((job) => job.status === "queued" || job.status === "running");
  const anyCompleted = currentJobs.some((job) => job.status === "completed") || Boolean(importedResult);
  const hasCompareDecision = Boolean(activeDecision);
  const hasImportedEvidence = Boolean(importedResult);
  const hasGuardEvidence = Boolean(activeGuardAnalysis || activeDecision?.guard_status || activeDecision?.guard_verdict);
  return {
    forge: importedResult ? "completed" : "idle",
    runtime: hasImportedEvidence || anyCompleted ? "completed" : anyRunning ? "running" : "idle",
    lab: hasCompareDecision || hasImportedEvidence ? "completed" : anyRunning ? "running" : "idle",
    aiguard: hasGuardEvidence ? "completed" : "optional",
  };
}

function normalizeState(state) {
  const value = String(state || "idle").toLowerCase();
  if (value === "queued") {
    return "running";
  }
  if (value === "completed" || value === "success" || value === "deployable" || value === "pass") {
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
  if (value === "optional" || value === "skipped") {
    return "optional";
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
  return results.find((item) => normalizedBackendKey(item).toLowerCase().includes(keyword));
}

function runtimeModelName(result = {}) {
  return firstDisplayValue(result.model_name, result.model?.name, result.model, result.model_path);
}

function runtimeBackendName(result = {}) {
  return firstDisplayValue(
    result.engine_backend,
    result.engine?.backend,
    result.engine?.name,
    result.backend,
    result.engine,
    result.backend_key,
  );
}

function runtimeDeviceName(result = {}) {
  return firstDisplayValue(result.device_name, result.device?.name, result.device);
}

function normalizedBackendKey(result = {}) {
  return firstDisplayValue(result.backend_key, result.engine_backend, result.engine?.backend, result.engine?.name, result.engine);
}

function firstDisplayValue(...values) {
  for (const value of values) {
    const formatted = displayValue(value);
    if (formatted !== "-") {
      return formatted;
    }
  }
  return "";
}

function displayValue(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  if (typeof value === "number") {
    return formatNumber(value);
  }
  if (typeof value === "string" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map(displayValue).join(", ");
  }
  if (typeof value === "object") {
    return firstDisplayValue(value.name, value.backend, value.path, value.status, value.id);
  }
  return String(value);
}

function missingResultKeys(result = {}) {
  const missing = [];
  if (!result.compare_key) {
    missing.push("compare_key");
  }
  if (!normalizedBackendKey(result)) {
    missing.push("backend_key");
  }
  return missing;
}

function fallbackLabel(key) {
  return `${key} unavailable`;
}

function compareTone(overall) {
  const value = String(overall || "").toLowerCase();
  if (value.includes("improvement")) {
    return "improvement";
  }
  if (value.includes("regression")) {
    return "regression";
  }
  if (value.includes("neutral")) {
    return "neutral";
  }
  return "unknown";
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

function formatPercent(value) {
  if (value === undefined || value === null) {
    return "-";
  }
  return `${formatNumber(value)}%`;
}

function formatValue(value) {
  return displayValue(value);
}

async function initLocalStudio() {
  try {
    markFileMode();
    resetTransientInputs();
    renderRunPanel();
    renderPipeline();
    renderJobDetail();
    renderCompare();
    updateDecision(null);
    updateGuardEvidence(null);
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
