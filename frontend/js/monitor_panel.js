// 即時監控頁面邏輯

let _refreshInterval = null;

async function loadPositions() {
  try {
    const positions = await API.listPositions();
    renderPositions(positions);
  } catch (e) {
    showToast(e.message, "error");
  }
}

function renderPositions(positions) {
  const el = document.getElementById("positions-list");
  if (!positions.length) {
    el.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:20px">尚未設定任何監控持倉</p>`;
    return;
  }
  el.innerHTML = positions.map(p => `
    <div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:10px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <strong style="color:var(--blue)">${p.ticker}</strong>
        <button class="btn btn-danger btn-sm" onclick="removePosition('${p.id}')">移除</button>
      </div>
      <div class="info-row"><span class="label">區間</span><span class="value">${fmtNum(p.lower)} ～ ${fmtNum(p.upper)}</span></div>
      <div class="info-row"><span class="label">格子數</span><span class="value">${p.n_grids}</span></div>
      <div class="info-row"><span class="label">每格股數</span><span class="value">${p.shares_per_grid} 股</span></div>
      <div class="info-row"><span class="label">建立時間</span><span class="label">${p.created_at}</span></div>
    </div>
  `).join("");
}

async function removePosition(id) {
  try {
    await API.delPosition(id);
    showToast("已移除", "success");
    loadPositions();
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function addMonitorPosition() {
  const ticker = document.getElementById("mon-ticker").value.trim();
  const upper  = parseFloat(document.getElementById("mon-upper").value);
  const lower  = parseFloat(document.getElementById("mon-lower").value);
  const nGrids = parseInt(document.getElementById("mon-grids").value);
  const shares = parseInt(document.getElementById("mon-shares").value);

  if (!ticker || isNaN(upper) || isNaN(lower)) return showToast("請填入完整資訊", "error");

  try {
    await API.addPosition({ ticker, upper, lower, n_grids: nGrids, shares_per_grid: shares });
    showToast("已加入監控", "success");
    loadPositions();
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function refreshAlerts() {
  try {
    const alerts = await API.alerts();
    renderAlerts(alerts);
    document.getElementById("last-refresh").textContent =
      "最後更新：" + new Date().toLocaleTimeString("zh-TW");
  } catch (e) {
    showToast(e.message, "error");
  }
}

function renderAlerts(alerts) {
  const el = document.getElementById("alerts-list");
  if (!alerts.length) {
    el.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:20px">無持倉需監控</p>`;
    return;
  }
  el.innerHTML = alerts.map(a => {
    if (a.error) return `<div class="info-row"><span class="label">${a.ticker}</span><span class="value value-red">${a.error}</span></div>`;
    const statusColor = a.status === "in_range" ? "value-green" : "value-red";
    const statusText  = a.status === "in_range" ? "區間內" : a.status === "above_range" ? "超過上界" : "低於下界";
    const alertHtml   = (a.alerts || []).map(al =>
      `<div style="margin-top:4px;font-size:11px;color:var(--orange)">⚠ ${al.message}</div>`
    ).join("");

    return `
      <div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:8px">
        <div style="display:flex;justify-content:space-between">
          <strong style="color:var(--blue)">${a.ticker}</strong>
          <span class="${statusColor}">${statusText}</span>
        </div>
        <div class="info-row" style="margin-top:6px">
          <span class="label">現價</span>
          <span class="value value-orange">${fmtNum(a.current_price)}</span>
        </div>
        <div class="info-row">
          <span class="label">上方格線</span>
          <span class="value">${a.nearest_above ? fmtNum(a.nearest_above) : "—"}</span>
        </div>
        <div class="info-row">
          <span class="label">下方格線</span>
          <span class="value">${a.nearest_below ? fmtNum(a.nearest_below) : "—"}</span>
        </div>
        ${alertHtml}
        <div style="font-size:10px;color:var(--text-muted);margin-top:4px">${a.checked_at}</div>
      </div>
    `;
  }).join("");
}

function toggleAutoRefresh() {
  const btn = document.getElementById("btn-auto");
  if (_refreshInterval) {
    clearInterval(_refreshInterval);
    _refreshInterval = null;
    btn.textContent = "自動更新（60秒）";
    btn.className = "btn btn-secondary";
  } else {
    refreshAlerts();
    _refreshInterval = setInterval(refreshAlerts, 60000);
    btn.textContent = "停止自動更新";
    btn.className = "btn btn-danger";
  }
}

// 自動建議（監控頁面）
async function monSuggest() {
  const ticker = document.getElementById("mon-ticker").value.trim();
  if (!ticker) return showToast("請輸入股票代碼", "error");
  try {
    const res = await API.suggest({ ticker, strategy: "atr" });
    const s = res.suggestions[0];
    document.getElementById("mon-upper").value = s.upper;
    document.getElementById("mon-lower").value = s.lower;
    showToast(`ATR 建議：${s.reasoning}`, "success");
  } catch (e) {
    showToast(e.message, "error");
  }
}
