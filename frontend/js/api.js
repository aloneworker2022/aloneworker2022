// 統一 API 呼叫封裝

const BASE = "";  // 同域，無需前綴

async function apiFetch(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

const API = {
  // Stock
  ohlcv:   (ticker, period = "1y") => apiFetch(`/api/stock/${ticker}/ohlcv?period=${period}`),
  price:   (ticker)                 => apiFetch(`/api/stock/${ticker}/current`),
  search:  (q)                      => apiFetch(`/api/stock/search?q=${encodeURIComponent(q)}`),

  // Grid
  calculate: (body) => apiFetch("/api/grid/calculate",          { method: "POST", body: JSON.stringify(body) }),
  suggest:   (body) => apiFetch("/api/grid/suggest-boundaries", { method: "POST", body: JSON.stringify(body) }),
  capital:   (body) => apiFetch("/api/grid/capital-estimate",   { method: "POST", body: JSON.stringify(body) }),

  // Backtest
  backtest:       (body)   => apiFetch("/api/backtest/run",             { method: "POST", body: JSON.stringify(body) }),
  backtestResult: (job_id) => apiFetch(`/api/backtest/result/${job_id}`),

  // Monitor
  listPositions:  ()      => apiFetch("/api/monitor/positions"),
  addPosition:    (body)  => apiFetch("/api/monitor/positions",  { method: "POST", body: JSON.stringify(body) }),
  delPosition:    (id)    => apiFetch(`/api/monitor/positions/${id}`, { method: "DELETE" }),
  alerts:         ()      => apiFetch("/api/monitor/alerts"),
};
