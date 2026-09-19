const PALETTE = ["#d4a017", "#6ea8fe", "#3dbe8c", "#c084fc", "#f0a36c"];
const WEIGHT_TOLERANCE = 0.0001;

const fetchForm = document.querySelector("#fetch-form");
const weightsForm = document.querySelector("#weights-form");
const statusEl = document.querySelector("#status");
const statsEl = document.querySelector("#stats");
const fetchButton = document.querySelector("#fetch-button");
const analyzeButton = document.querySelector("#analyze-button");
const showBenchmark = document.querySelector("#show-benchmark");
const holdingsBody = document.querySelector("#holdings-table");
const corrTable = document.querySelector("#corr-table");
const weightFields = document.querySelector("#weight-fields");
const weightSumEl = document.querySelector("#weight-sum");
const chartTitle = document.querySelector("#chart-title");

let chart;
let latestAnalysis = null;
let chartView = "value";
let defaultWeights = {};
let currency = "EUR";

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function tickerList(value) {
  return value
    .split(/[\s,]+/)
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
}

async function readJson(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg || item).join("; ")
          : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return body;
}

function formatNumber(value, digits = 2) {
  if (value == null || Number.isNaN(Number(value))) {
    return "—";
  }
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatMoney(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return "—";
  }
  const prefix = currency === "EUR" ? "€" : "$";
  return `${prefix}${formatNumber(value, 2)}`;
}

function formatPct(value, digits = 2) {
  if (value == null || Number.isNaN(Number(value))) {
    return "—";
  }
  return `${(value * 100).toFixed(digits)}%`;
}

function signedClass(value) {
  if (value == null) {
    return "";
  }
  return value >= 0 ? "up" : "down";
}

function lastValue(values) {
  return [...(values || [])].reverse().find((value) => value != null) ?? null;
}

function currentWeights() {
  const weights = {};
  for (const input of weightFields.querySelectorAll("input")) {
    weights[input.dataset.ticker] = Number(input.value) || 0;
  }
  return weights;
}

function weightTotal() {
  return Object.values(currentWeights()).reduce((sum, value) => sum + value, 0);
}

function updateWeightSum() {
  const total = weightTotal();
  const ok = Math.abs(total - 1) <= WEIGHT_TOLERANCE;
  weightSumEl.textContent = `Sum: ${formatPct(total, 1)}`;
  weightSumEl.classList.toggle("error", !ok);
  return ok;
}

function renderWeightFields(tickers, weights) {
  weightFields.replaceChildren();
  for (const ticker of tickers) {
    const label = document.createElement("label");
    const value = weights[ticker] ?? defaultWeights[ticker] ?? 0;
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.step = "0.01";
    input.dataset.ticker = ticker;
    input.value = value;
    input.addEventListener("input", updateWeightSum);
    label.append(ticker, input);
    weightFields.appendChild(label);
  }
  updateWeightSum();
}

function metricLine(id, value, kind = "pct") {
  const el = document.querySelector(id);
  if (kind === "money") {
    el.textContent = formatMoney(value);
    el.className = "";
    return;
  }
  el.textContent = kind === "num" ? formatNumber(value, 2) : formatPct(value);
  el.className = signedClass(value);
}

function renderStats(payload) {
  const metrics = payload.metrics.portfolio;
  statsEl.hidden = false;
  document.querySelector("#stat-range").textContent = `${payload.start} → ${payload.end}`;
  metricLine("#stat-value", payload.portfolio.current_value, "money");
  metricLine("#stat-return", metrics.total_return);
  metricLine("#stat-cagr", metrics.annualized_return ?? metrics.cagr);
  metricLine("#stat-daily", lastValue(payload.portfolio.daily_returns));
  metricLine("#stat-vol", metrics.volatility);
  metricLine("#stat-sharpe", metrics.sharpe, "num");
  metricLine("#stat-dd", metrics.max_drawdown);
}

function pctSeries(values) {
  return (values || []).map((value) => (value == null ? null : value * 100));
}

function lineDataset(label, data, color, dashed = false) {
  return {
    label,
    data,
    borderColor: color,
    borderDash: dashed ? [5, 4] : [],
    backgroundColor: "transparent",
    borderWidth: dashed ? 1.5 : 2,
    pointRadius: 0,
    tension: 0.15,
  };
}

function chartDatasets(payload) {
  if (chartView === "prices") {
    const datasets = Object.entries(payload.normalized).map(([ticker, values], index) =>
      lineDataset(ticker, values, PALETTE[index % PALETTE.length]),
    );
    if (showBenchmark.checked && payload.benchmark) {
      datasets.push(
        lineDataset(`${payload.benchmark_name} (benchmark)`, payload.benchmark.normalized, "#9aa7bd", true),
      );
    }
    return datasets;
  }

  if (chartView === "daily") {
    const datasets = Object.entries(payload.daily_returns).map(([ticker, values], index) =>
      lineDataset(ticker, pctSeries(values), PALETTE[index % PALETTE.length]),
    );
    datasets.unshift(lineDataset("Portfolio", pctSeries(payload.portfolio.daily_returns), "#e8edf7"));
    if (showBenchmark.checked && payload.benchmark?.daily_returns) {
      datasets.push(
        lineDataset(
          `${payload.benchmark_name} (benchmark)`,
          pctSeries(payload.benchmark.daily_returns),
          "#9aa7bd",
          true,
        ),
      );
    }
    return datasets;
  }

  if (chartView === "cumulative") {
    const datasets = Object.entries(payload.cumulative_returns).map(([ticker, values], index) =>
      lineDataset(ticker, pctSeries(values), PALETTE[index % PALETTE.length]),
    );
    datasets.unshift(lineDataset("Portfolio", pctSeries(payload.portfolio.cumulative_returns), "#e8edf7"));
    if (showBenchmark.checked && payload.benchmark?.cumulative_returns) {
      datasets.push(
        lineDataset(
          `${payload.benchmark_name} (benchmark)`,
          pctSeries(payload.benchmark.cumulative_returns),
          "#9aa7bd",
          true,
        ),
      );
    }
    return datasets;
  }

  if (chartView === "drawdown") {
    const datasets = [
      lineDataset("Portfolio", pctSeries(payload.portfolio.drawdown), PALETTE[0]),
    ];
    if (showBenchmark.checked && payload.benchmark) {
      datasets.push(
        lineDataset(`${payload.benchmark_name} (benchmark)`, pctSeries(payload.benchmark.drawdown), "#9aa7bd", true),
      );
    }
    return datasets;
  }

  const datasets = [lineDataset("Portfolio", payload.portfolio.equity, PALETTE[0])];
  if (showBenchmark.checked && payload.benchmark) {
    datasets.push(lineDataset(`${payload.benchmark_name} (benchmark)`, payload.benchmark.equity, "#9aa7bd", true));
  }
  return datasets;
}

function yTickCallback(value) {
  if (chartView === "value") {
    return formatMoney(value);
  }
  if (chartView === "prices") {
    return formatNumber(value, 2);
  }
  return `${value}%`;
}

function renderChart(payload) {
  const titles = {
    value: "Portfolio value (€)",
    cumulative: "Cumulative return",
    daily: "Daily return",
    prices: "Normalized price (start = 1)",
    drawdown: "Drawdown",
  };
  chartTitle.textContent = titles[chartView];
  const context = document.querySelector("#price-chart").getContext("2d");
  const config = {
    type: "line",
    data: {
      labels: payload.dates,
      datasets: chartDatasets(payload),
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#e8edf7" } },
      },
      scales: {
        x: {
          ticks: { color: "#9aa7bd", maxTicksLimit: 8 },
          grid: { color: "#2a3346" },
        },
        y: {
          ticks: {
            color: "#9aa7bd",
            callback: yTickCallback,
          },
          grid: { color: "#2a3346" },
        },
      },
    },
  };

  if (chart) {
    chart.data = config.data;
    chart.options = config.options;
    chart.update();
    return;
  }
  chart = new Chart(context, config);
}

function renderHoldings(payload) {
  holdingsBody.replaceChildren();
  for (const [ticker, holding] of Object.entries(payload.holdings || {})) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${ticker}</td>
      <td>${formatPct(holding.start_weight, 1)}</td>
      <td>${formatPct(holding.current_weight, 1)}</td>
      <td>${formatNumber(holding.shares, 4)}</td>
      <td>${formatMoney(holding.start_value)}</td>
      <td>${formatMoney(holding.current_value)}</td>
      <td class="${signedClass(holding.cumulative_return)}">${formatPct(holding.cumulative_return)}</td>
      <td class="${signedClass(holding.annualized_return)}">${formatPct(holding.annualized_return)}</td>
    `;
    holdingsBody.appendChild(row);
  }
}

function heatColor(value) {
  if (value == null) {
    return "transparent";
  }
  const t = (value + 1) / 2;
  const r = Math.round(224 + (61 - 224) * t);
  const g = Math.round(107 + (190 - 107) * t);
  const b = Math.round(107 + (140 - 107) * t);
  return `rgba(${r}, ${g}, ${b}, 0.35)`;
}

function renderCorrelation(payload) {
  const { columns, matrix } = payload.correlation;
  corrTable.replaceChildren();
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  headRow.appendChild(document.createElement("th"));
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = column;
    headRow.appendChild(th);
  }
  head.appendChild(headRow);
  const body = document.createElement("tbody");
  matrix.forEach((row, index) => {
    const tr = document.createElement("tr");
    const name = document.createElement("th");
    name.textContent = columns[index];
    tr.appendChild(name);
    for (const value of row) {
      const td = document.createElement("td");
      td.className = "corr-cell";
      td.textContent = value == null ? "—" : value.toFixed(2);
      td.style.background = heatColor(value);
      tr.appendChild(td);
    }
    body.appendChild(tr);
  });
  corrTable.appendChild(head);
  corrTable.appendChild(body);
}

function renderAnalysis(payload) {
  latestAnalysis = payload;
  currency = payload.currency || currency;
  const tickers = Object.keys(payload.prices);
  renderWeightFields(tickers, payload.weights);
  renderStats(payload);
  renderChart(payload);
  renderHoldings(payload);
  renderCorrelation(payload);
  const value = formatMoney(payload.portfolio.current_value);
  setStatus(`Buy-and-hold value ${value} across ${payload.rows} sessions (${payload.start} → ${payload.end}).`);
}

async function loadConfig() {
  const config = await readJson(await fetch("/api/config"));
  defaultWeights = config.weights || {};
  currency = config.currency || "EUR";
  document.querySelector("#tickers").value = config.tickers.join(" ");
  document.querySelector("#start").value = config.start;
  document.querySelector("#end").value = config.end;
  document.querySelector("#benchmark").value = config.benchmark;
  document.querySelector("#initial").value = config.initial_investment;
  document.querySelector("#rf").value = config.rf;
  renderWeightFields(config.tickers, defaultWeights);
}

async function loadAnalysis() {
  const response = await fetch("/api/analysis");
  if (response.status === 404) {
    setStatus("No prices stored yet. Fetch the example portfolio to begin.");
    return;
  }
  renderAnalysis(await readJson(response));
}

async function refreshPrices() {
  fetchButton.disabled = true;
  setStatus("Downloading and cleaning prices…");
  try {
    await readJson(
      await fetch("/api/prices/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tickers: tickerList(document.querySelector("#tickers").value),
          start: document.querySelector("#start").value,
          end: document.querySelector("#end").value,
          benchmark: document.querySelector("#benchmark").value.trim() || null,
        }),
      }),
    );
    await runAnalysis();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    fetchButton.disabled = false;
  }
}

async function runAnalysis() {
  if (!updateWeightSum()) {
    setStatus("Weights must sum to 1 before analysis.", true);
    return;
  }
  analyzeButton.disabled = true;
  setStatus("Calculating returns and portfolio value…");
  try {
    const payload = await readJson(
      await fetch("/api/analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          weights: currentWeights(),
          rf: Number(document.querySelector("#rf").value) || 0,
          initial_investment: Number(document.querySelector("#initial").value) || 10000,
        }),
      }),
    );
    renderAnalysis(payload);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    analyzeButton.disabled = false;
  }
}

fetchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  refreshPrices();
});

weightsForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runAnalysis();
});

showBenchmark.addEventListener("change", () => {
  if (latestAnalysis) {
    renderChart(latestAnalysis);
  }
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    chartView = tab.dataset.view;
    document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("is-active", item === tab));
    if (latestAnalysis) {
      renderChart(latestAnalysis);
    }
  });
});

loadConfig()
  .then(loadAnalysis)
  .catch((error) => setStatus(error.message, true));
