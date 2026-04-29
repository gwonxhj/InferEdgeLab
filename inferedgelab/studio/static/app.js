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
  evidence: [
    {
      label: "macOS ONNX Runtime CPU smoke",
      status: "validated evidence path",
    },
    {
      label: "Jetson Orin Nano TensorRT smoke",
      status: "validated evidence path",
    },
  ],
  metrics: [
    "mean_ms",
    "p99_ms",
    "fps",
    "compare_key",
    "backend_key",
  ],
  decision: {
    owner: "Lab",
    aiguardRole: "optional deterministic diagnosis evidence",
  },
};

function createElement(tagName, className, textContent) {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  if (textContent) {
    element.textContent = textContent;
  }
  return element;
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

function renderEvidenceSummary(data = studioDemoData.evidence) {
  const target = document.querySelector("#evidence-summary");
  target.replaceChildren();

  data.forEach((item) => {
    const row = createElement("div", "summary-row");
    row.append(
      createElement("strong", "", item.label),
      createElement("span", "", item.status),
    );
    target.append(row);
  });
}

function renderMetrics(data = studioDemoData.metrics) {
  const target = document.querySelector("#result-metrics");
  target.replaceChildren();

  data.forEach((metric) => {
    const tile = createElement("div", "metric-tile");
    tile.append(
      createElement("span", "metric-name", metric),
      createElement("span", "metric-value", "placeholder"),
    );
    target.append(tile);
  });
}

function renderDecision(data = studioDemoData.decision) {
  const target = document.querySelector("#deployment-decision");
  target.replaceChildren();

  const owner = createElement("div", "summary-row");
  owner.append(
    createElement("strong", "", "decision owner"),
    createElement("span", "", data.owner),
  );

  const role = createElement("div", "summary-row");
  role.append(
    createElement("strong", "", "AIGuard role"),
    createElement("span", "", data.aiguardRole),
  );

  target.append(owner, role);
}

function renderStudio(data = studioDemoData) {
  renderPipeline(data.pipeline);
  renderEvidenceSummary(data.evidence);
  renderMetrics(data.metrics);
  renderDecision(data.decision);
}

renderStudio();
