// 回測頁面邏輯

let _equityChart = null;
let _equitySeries = null;
let _bhSeries = null;

function initEquityChart() {
  const container = document.getElementById("equity-chart");
  _equityChart = LightweightCharts.createChart(container, {
    layout: { background: { color: "#0d1117" }, textColor: "#8b949e" },
    grid: { vertLines: { color: "#21262d" }, horzLines: { color: "#21262d" } },
    rightPriceScale: { borderColor: "#30363d" },
    timeScale: { borderColor: "#30363d", timeVisible: true },
  });

  _equitySeries = _equityChart.addLineSeries({ color: "#58a6ff", lineWidth: 2, title: "網格策略" });
  _bhSeries     = _equityChart.addLineSeries({ color: "#8b949e", lineWidth: 1, lineStyle: 2, title: "買入持有" });

  const ro = new ResizeObserver(entries => {
    for (const e of entries) _equityChart.resize(e.contentRect.width, e.contentRect.height);
  });
  ro.observe(container);
}

async function runBacktest() {
  const ticker  = document.getElementById("bt-ticker").value.trim();
  const upper   = parseFloat(document.getElementById("bt-upper").value);
  const lower   = parseFloat(document.getElementById("bt-lower").value);
  const nGrids  = parseInt(document.getElementById("bt-grids").value);
  const shares  = parseInt(document.getElementById("bt-shares").value);
  const startD  = document.getElementById("bt-start").value;
  const endD    = document.getElementById("bt-end").value;
  const capital = parseFloat(document.getElementById("bt-capital").value);
  const discount= parseFloat(document.getElementById("bt-discount").value);

  if (!ticker || isNaN(upper) || isNaN(lower) || isNaN(capital)) {
    return showToast("請填入完整參數", "error");
  }

  const btn = document.getElementById("btn-backtest");
  setLoading(btn, true);
  document.getElementById("bt-status").textContent = "回測中，請稍候…";

  try {
    const runRes = await API.backtest({
      ticker, upper, lower, n_grids: nGrids, shares_per_grid: shares,
      start_date: startD, end_date: endD,
      initial_capital: capital, fee_discount: discount,
    });

    const result = await API.backtestResult(runRes.job_id);
    renderBacktestResult(result, capital);
    document.getElementById("bt-status").textContent = "";
    showToast("回測完成！", "success");
  } catch (e) {
    document.getElementById("bt-status").textContent = "";
    showToast(e.message, "error");
  } finally {
    setLoading(btn, false);
  }
}

function renderBacktestResult(result, initial) {
  const perf = result.performance;

  // Stat cards
  document.getElementById("stat-return").textContent  = fmtPct(perf.total_return_pct);
  document.getElementById("stat-return").className    = "stat-value " + pctClass(perf.total_return_pct);
  document.getElementById("stat-ann").textContent     = fmtPct(perf.annualized_return_pct);
  document.getElementById("stat-ann").className       = "stat-value " + pctClass(perf.annualized_return_pct);
  document.getElementById("stat-dd").textContent      = `-${fmtNum(perf.max_drawdown_pct)}%`;
  document.getElementById("stat-dd").className        = "stat-value value-red";
  document.getElementById("stat-sharpe").textContent  = fmtNum(perf.sharpe_ratio, 3);
  document.getElementById("stat-winrate").textContent = fmtPct(perf.win_rate_pct);
  document.getElementById("stat-trades").textContent  = perf.total_trades;
  document.getElementById("stat-fees").textContent    = fmtMoney(perf.total_fees);
  document.getElementById("stat-final").textContent   = fmtMoney(perf.final_equity);
  document.getElementById("stat-bh").textContent      = fmtPct(result.buy_hold_return_pct);
  document.getElementById("stat-bh").className        = "stat-value " + pctClass(result.buy_hold_return_pct);

  // 網格停止原因
  const stopEl = document.getElementById("stat-stop");
  if (result.stop_reason === "upper_break") {
    stopEl.textContent = "突破上界 → 獲利了結";
    stopEl.style.color = "var(--green)";
  } else if (result.stop_reason === "lower_break") {
    stopEl.textContent = "跌破下界 → 強制停損";
    stopEl.style.color = "var(--red)";
  } else {
    stopEl.textContent = "回測期間未觸及上下界";
    stopEl.style.color = "var(--text-muted)";
  }

  // Equity curve
  const curve = result.equity_curve;
  if (curve && curve.length > 0) {
    const gridData = curve.map(p => ({ time: p.date, value: p.equity }));
    _equitySeries.setData(gridData);

    // 買入持有曲線（依初始資本等比例）
    const firstEq = curve[0].equity;
    // 用最後 n 天作為買入持有近似（以首日 equity 為基準）
    const bhData = curve.map((p, i) => ({
      time: p.date,
      value: initial * (1 + result.buy_hold_return_pct / 100 * (i / (curve.length - 1 || 1))),
    }));
    _bhSeries.setData(bhData);
    _equityChart.timeScale().fitContent();
  }

  // Trade records table
  renderTradeTable(result.trade_records || []);
}

function renderTradeTable(records) {
  const tbody = document.getElementById("trade-tbody");
  tbody.innerHTML = "";
  records.forEach(t => {
    const tr = document.createElement("tr");
    const isBuy = t.action === "buy";
    const actionLabel = {
      "buy": "買入", "sell": "賣出",
      "sell_upper": "止盈（上界）", "sell_lower": "停損（下界）",
    }[t.action] || t.action;
    const actionClass = isBuy ? "value-red" :
      t.action === "sell_lower" ? "value-red" : "value-green";
    tr.innerHTML = `
      <td>${t.date}</td>
      <td class="${actionClass}">${actionLabel}</td>
      <td>#${t.grid_index}</td>
      <td>${fmtNum(t.price)}</td>
      <td>${t.shares}</td>
      <td>${fmtMoney(t.amount)}</td>
      <td>${fmtNum(t.fee)}</td>
      <td class="${t.pnl > 0 ? 'value-green' : t.pnl < 0 ? 'value-red' : ''}">${isSell ? fmtNum(t.pnl) : "—"}</td>
    `;
    tbody.appendChild(tr);
  });
}

// 自動建議上下界（回測頁面）
async function btSuggest() {
  const ticker = document.getElementById("bt-ticker").value.trim();
  if (!ticker) return showToast("請輸入股票代碼", "error");
  try {
    const res = await API.suggest({ ticker, strategy: "atr" });
    const s = res.suggestions[0];
    document.getElementById("bt-upper").value = s.upper;
    document.getElementById("bt-lower").value = s.lower;
    showToast(`已填入 ATR 建議：${s.reasoning}`, "success");
  } catch (e) {
    showToast(e.message, "error");
  }
}
