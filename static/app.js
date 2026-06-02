const runButton = document.querySelector("#run-button");
const screenButton = document.querySelector("#screen-button");
const statusPill = document.querySelector("#status-pill");
const resultTitle = document.querySelector("#result-title");
const screenSummary = document.querySelector("#screen-summary");
const metrics = document.querySelector("#metrics");
const equityRange = document.querySelector("#equity-range");
const rebalanceBody = document.querySelector("#rebalance-body");
const symbolBody = document.querySelector("#symbol-body");
const rebalanceCount = document.querySelector("#rebalance-count");
const symbolCount = document.querySelector("#symbol-count");
const screenDetailBody = document.querySelector("#screen-detail-body");
const screenDetailCount = document.querySelector("#screen-detail-count");
const selectedCodes = document.querySelector("#selected-codes");
const selectedCount = document.querySelector("#selected-count");
const screenMetrics = document.querySelector("#screen-metrics");
const universeCount = document.querySelector("#universe-count");

let frequency = "monthly";

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return `${(value * 100).toFixed(2)}%`;
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return Number(value).toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function activeStrategy() {
  return document.querySelector("#strategy").value;
}

function setStatus(text, className) {
  statusPill.textContent = text;
  statusPill.className = `status-pill ${className || ""}`;
}

function switchPage(pageId) {
  document.querySelectorAll(".page-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.page === pageId);
  });
  document.querySelectorAll(".page-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === pageId);
  });
  resultTitle.textContent = pageId === "screen-page" ? "今日选股" : "策略回测";
  screenSummary.textContent =
    pageId === "screen-page"
      ? "选择策略后，一键筛出指定日期符合条件的股票。"
      : "系统使用默认股票池作为历史可选宇宙，在每个调仓点重新按策略选股。";
}

document.querySelectorAll(".page-tab").forEach((tab) => {
  tab.addEventListener("click", () => switchPage(tab.dataset.page));
});

document.querySelectorAll(".segment").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".segment").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    frequency = button.dataset.frequency;
  });
});

function updateScreenMetrics(result) {
  const values = [
    ["扫描股票", result.stock_pool_count ?? result.candidate_count],
    ["读取成功", result.loaded_count],
    ["符合条件", result.selected_count],
    ["选股日期", result.screen_date],
  ];
  screenMetrics.innerHTML = values
    .map(([label, value]) => `<article><span>${label}</span><strong>${value}</strong></article>`)
    .join("");
}

function updateMetrics(summary) {
  const values = [
    ["总收益", percent(summary.total_return)],
    ["年化收益", percent(summary.annualized_return)],
    ["最大回撤", percent(summary.max_drawdown)],
    ["调仓次数", summary.rebalance_count],
  ];
  metrics.innerHTML = values
    .map(([label, value]) => `<article><span>${label}</span><strong>${value}</strong></article>`)
    .join("");
}

function drawLineChart(canvas, rows, key, options = {}) {
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  if (!rows.length) return;

  const padding = { top: 22, right: 24, bottom: 34, left: 58 };
  const values = rows.map((row) => Number(row[key]));
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (min === max) {
    min *= 0.98;
    max *= 1.02;
  }

  const x = (index) => padding.left + (index / Math.max(rows.length - 1, 1)) * (width - padding.left - padding.right);
  const y = (value) => padding.top + ((max - value) / (max - min)) * (height - padding.top - padding.bottom);

  ctx.strokeStyle = "#d9e0ea";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i < 4; i += 1) {
    const yy = padding.top + (i / 3) * (height - padding.top - padding.bottom);
    ctx.moveTo(padding.left, yy);
    ctx.lineTo(width - padding.right, yy);
  }
  ctx.stroke();

  ctx.fillStyle = "#677286";
  ctx.font = "12px system-ui";
  ctx.fillText(options.format ? options.format(max) : max.toFixed(2), 8, padding.top + 4);
  ctx.fillText(options.format ? options.format(min) : min.toFixed(2), 8, height - padding.bottom);
  ctx.fillText(rows[0].date, padding.left, height - 10);
  ctx.fillText(rows[rows.length - 1].date, width - padding.right - 82, height - 10);

  ctx.strokeStyle = options.color || "#0f766e";
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  rows.forEach((row, index) => {
    const xx = x(index);
    const yy = y(Number(row[key]));
    if (index === 0) ctx.moveTo(xx, yy);
    else ctx.lineTo(xx, yy);
  });
  ctx.stroke();
}

function renderScreenDetails(details) {
  const rows = details || [];
  screenDetailCount.textContent = `${rows.length} 条`;
  screenDetailBody.innerHTML = rows.map((row) => {
    const klass = row.is_pass ? "positive" : "negative";
    const result = row.is_pass ? "通过" : (row.error || row.reason || "不通过");
    const priceZone = row.current_price && row.golden_382 ? `${money(row.current_price)} / ${money(row.golden_382)}` : "-";
    return `<tr>
      <td>${row.code}</td>
      <td class="${klass}">${result}</td>
      <td>${row.gain_pct ?? "-"}</td>
      <td>${row.n2_weeks ?? "-"}</td>
      <td>${row.max_drawdown_pct ?? "-"}</td>
      <td>${priceZone}</td>
      <td>${money(row.stop_loss)}</td>
    </tr>`;
  }).join("");
}

function renderBacktestTables(result) {
  rebalanceCount.textContent = `${result.rebalance_log.length} 条`;
  rebalanceBody.innerHTML = result.rebalance_log.slice().reverse().map((row) => {
    const periodReturn = row.period_return ?? null;
    const klass = periodReturn >= 0 ? "positive" : "negative";
    return `<tr><td>${row.date}</td><td>${row.selected.join(", ") || "空仓"}</td><td>${money(row.equity)}</td><td class="${klass}">${percent(periodReturn)}</td></tr>`;
  }).join("");

  symbolCount.textContent = `${result.symbol_stats.length} 只`;
  symbolBody.innerHTML = result.symbol_stats.map((row) => {
    const klass = row.return >= 0 ? "positive" : "negative";
    return `<tr><td>${row.code}</td><td>${row.bars}</td><td>${money(row.start_price)}</td><td>${money(row.end_price)}</td><td class="${klass}">${percent(row.return)}</td></tr>`;
  }).join("");
}

async function runTodayScreen() {
  setStatus("Screening", "running");
  screenButton.disabled = true;
  resultTitle.textContent = "正在筛选今日符合条件的票";
  const payload = {
    start_date: document.querySelector("#screen-start-date").value,
    end_date: document.querySelector("#screen-date").value,
    strategy: activeStrategy(),
  };

  try {
    const response = await fetch("/api/screen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Screening failed");
    selectedCodes.value = result.selected_codes.join(", ");
    selectedCount.textContent = `${result.selected_count} 只`;
    updateScreenMetrics(result);
    renderScreenDetails(result.details);
    const scannedCount = result.stock_pool_count ?? result.candidate_count;
    screenSummary.textContent = `扫描 ${scannedCount} 只，成功读取 ${result.loaded_count} 只，策略选出 ${result.selected_count} 只。`;
    resultTitle.textContent = result.selected_count ? "今日选股完成" : "今日没有符合条件的票";
    setStatus("Done", "done");
  } catch (error) {
    screenSummary.textContent = error.message;
    resultTitle.textContent = "选股失败";
    setStatus("Error", "error");
  } finally {
    screenButton.disabled = false;
  }
}

async function runBacktest(event) {
  event.preventDefault();
  setStatus("Running", "running");
  runButton.disabled = true;
  resultTitle.textContent = "正在回测策略 5 年表现";
  const payload = {
    start_date: document.querySelector("#backtest-start-date").value,
    end_date: document.querySelector("#backtest-end-date").value,
    strategy: activeStrategy(),
    frequency,
    initial_capital: Number(document.querySelector("#initial-capital").value),
    fee_bps: Number(document.querySelector("#fee-bps").value),
  };

  try {
    const response = await fetch("/api/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Backtest failed");

    updateMetrics(result.summary);
    drawLineChart(document.querySelector("#equity-chart"), result.equity_curve, "equity", { color: "#0f766e", format: money });
    drawLineChart(document.querySelector("#drawdown-chart"), result.drawdown_curve, "drawdown", { color: "#b91c1c", format: percent });
    renderBacktestTables(result);
    resultTitle.textContent = `${activeStrategy()} · ${frequency === "monthly" ? "月度" : "年度"}回测`;
    equityRange.textContent = `${result.summary.start_date} 至 ${result.summary.end_date}`;
    setStatus("Done", "done");
  } catch (error) {
    resultTitle.textContent = error.message;
    setStatus("Error", "error");
  } finally {
    runButton.disabled = false;
  }
}

async function loadUniverse() {
  try {
    const response = await fetch("/api/universe");
    const result = await response.json();
    if (response.ok) universeCount.textContent = `系统默认 ${result.count} 只`;
  } catch (_error) {
    universeCount.textContent = "系统默认股票池";
  }
}

screenButton.addEventListener("click", runTodayScreen);
document.querySelector("#backtest-form").addEventListener("submit", runBacktest);
loadUniverse();
