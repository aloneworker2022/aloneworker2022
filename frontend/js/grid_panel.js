// 網格設定面板邏輯

let _currentLevels = [];
let _currentPrice = null;
let _currentTicker = "";

async function loadStock() {
  const ticker = document.getElementById("ticker").value.trim();
  const period  = document.getElementById("period").value;
  if (!ticker) return showToast("請輸入股票代碼", "error");

  const btn = document.getElementById("btn-load");
  setLoading(btn, true);
  try {
    const [ohlcvData, priceData] = await Promise.all([
      API.ohlcv(ticker, period),
      API.price(ticker),
    ]);
    loadCandles(ohlcvData.data);
    _currentPrice = priceData.price;
    _currentTicker = ticker;

    document.getElementById("info-price").textContent = fmtNum(_currentPrice);
    showToast(`已載入 ${ticker} 股價 $${_currentPrice}`, "success");

    // 若已有網格設定，重新繪製
    if (_currentLevels.length > 0) drawGridLines(_currentLevels);
    drawCurrentPrice(_currentPrice);
  } catch (e) {
    showToast(e.message, "error");
  } finally {
    setLoading(btn, false);
  }
}

async function suggestBounds() {
  if (!_currentTicker) return showToast("請先載入股票", "error");
  const btn = document.getElementById("btn-suggest");
  setLoading(btn, true);
  try {
    const res = await API.suggest({ ticker: _currentTicker, strategy: "all" });
    const pills = document.getElementById("suggest-pills");
    pills.innerHTML = "";
    res.suggestions.forEach(s => {
      const el = document.createElement("div");
      el.className = "pill";
      el.title = s.reasoning;
      const label = s.strategy === "atr" ? "ATR" : s.strategy === "pct" ? "±%" : "分位";
      el.textContent = `${label}: ${fmtNum(s.lower)}～${fmtNum(s.upper)}`;
      el.onclick = () => {
        document.getElementById("upper").value = s.upper;
        document.getElementById("lower").value = s.lower;
        showToast(`已套用 ${label} 建議：${s.reasoning}`, "success");
      };
      pills.appendChild(el);
    });
  } catch (e) {
    showToast(e.message, "error");
  } finally {
    setLoading(btn, false);
  }
}

async function calculateGrid() {
  const ticker = document.getElementById("ticker").value.trim();
  const upper  = parseFloat(document.getElementById("upper").value);
  const lower  = parseFloat(document.getElementById("lower").value);
  const nGrids = parseInt(document.getElementById("n_grids").value);
  const shares = parseInt(document.getElementById("shares").value);

  if (!ticker || isNaN(upper) || isNaN(lower) || isNaN(nGrids) || isNaN(shares)) {
    return showToast("請填入完整參數", "error");
  }
  if (upper <= lower) return showToast("上界必須大於下界", "error");

  const btn = document.getElementById("btn-calc");
  setLoading(btn, true);
  try {
    const res = await API.calculate({ ticker, upper, lower, n_grids: nGrids, shares_per_grid: shares });
    _currentLevels = res.levels;

    drawGridLines(res.levels, res.upper, res.lower);
    if (_currentPrice) drawCurrentPrice(_currentPrice);

    renderGridTable(res);
    renderGridSummary(res);
    showToast(`計算完成，共 ${res.levels.length} 條格線`, "success");
  } catch (e) {
    showToast(e.message, "error");
  } finally {
    setLoading(btn, false);
  }
}

function renderGridTable(res) {
  const tbody = document.getElementById("grid-tbody");
  tbody.innerHTML = "";
  res.levels.forEach(lv => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>#${lv.index}</td>
      <td>${fmtNum(lv.price)}</td>
      <td>${lv.shares}</td>
      <td>${fmtMoney(lv.buy_cost)}</td>
      <td class="${lv.profit_per_round > 0 ? 'value-green' : ''}">${fmtNum(lv.profit_per_round)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderGridSummary(res) {
  document.getElementById("info-capital").textContent  = fmtMoney(res.total_capital_required);
  document.getElementById("info-profit").textContent   = fmtNum(res.estimated_profit_per_grid);
  document.getElementById("info-spacing").textContent  = `${fmtNum(res.grid_spacing)} (${fmtNum(res.grid_spacing_pct, 3)}%)`;
  document.getElementById("info-grids").textContent    = res.levels.length;
}

// 股票搜尋
let _searchTimeout = null;
function onTickerInput() {
  clearTimeout(_searchTimeout);
  const q = document.getElementById("ticker").value.trim();
  if (q.length < 1) {
    document.getElementById("search-results").innerHTML = "";
    return;
  }
  _searchTimeout = setTimeout(async () => {
    try {
      const results = await API.search(q);
      const el = document.getElementById("search-results");
      el.innerHTML = results.map(r =>
        `<div class="pill" onclick="selectStock('${r.code}','${r.name}')">${r.code} ${r.name}</div>`
      ).join("");
    } catch {}
  }, 300);
}

function selectStock(code, name) {
  document.getElementById("ticker").value = code;
  document.getElementById("search-results").innerHTML = "";
  document.getElementById("ticker-label").textContent = name || code;
}

// 新增到監控
async function addToMonitor() {
  const ticker = document.getElementById("ticker").value.trim();
  const upper  = parseFloat(document.getElementById("upper").value);
  const lower  = parseFloat(document.getElementById("lower").value);
  const nGrids = parseInt(document.getElementById("n_grids").value);
  const shares = parseInt(document.getElementById("shares").value);
  if (!ticker || isNaN(upper) || isNaN(lower)) return showToast("請先計算網格", "error");

  try {
    await API.addPosition({ ticker, upper, lower, n_grids: nGrids, shares_per_grid: shares });
    showToast("已加入監控清單", "success");
  } catch (e) {
    showToast(e.message, "error");
  }
}
