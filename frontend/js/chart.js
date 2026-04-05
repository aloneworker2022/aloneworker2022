// K線圖 + 網格線（使用 Lightweight Charts v4）

let _chart = null;
let _candleSeries = null;
let _gridLines = [];
let _priceLine = null;

function initChart(containerId) {
  const container = document.getElementById(containerId);
  _chart = LightweightCharts.createChart(container, {
    layout: {
      background: { color: "#0d1117" },
      textColor: "#8b949e",
    },
    grid: {
      vertLines: { color: "#21262d" },
      horzLines: { color: "#21262d" },
    },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderColor: "#30363d" },
    timeScale: { borderColor: "#30363d", timeVisible: true },
    handleScroll: true,
    handleScale: true,
  });

  _candleSeries = _chart.addCandlestickSeries({
    upColor: "#3fb950",
    downColor: "#f85149",
    borderUpColor: "#3fb950",
    borderDownColor: "#f85149",
    wickUpColor: "#3fb950",
    wickDownColor: "#f85149",
  });

  // 自適應容器大小
  const ro = new ResizeObserver(entries => {
    for (const entry of entries) {
      _chart.resize(entry.contentRect.width, entry.contentRect.height);
    }
  });
  ro.observe(container);
}

function loadCandles(data) {
  // data: [{time, open, high, low, close}]
  const sorted = [...data].sort((a, b) => a.time.localeCompare(b.time));
  _candleSeries.setData(sorted);
  _chart.timeScale().fitContent();
}

function drawGridLines(levels, upper, lower) {
  // 清除舊格線
  _gridLines.forEach(line => _candleSeries.removePriceLine(line));
  _gridLines = [];

  levels.forEach((lv, i) => {
    const isFirst = i === 0;
    const isLast  = i === levels.length - 1;
    const line = _candleSeries.createPriceLine({
      price: lv.price,
      color: isFirst ? "#f85149" : isLast ? "#3fb950" : "#58a6ff55",
      lineWidth: isFirst || isLast ? 1 : 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: isFirst ? `下界 #${lv.index}` : isLast ? `上界 #${lv.index}` : `#${lv.index}`,
    });
    _gridLines.push(line);
  });
}

function drawCurrentPrice(price) {
  if (_priceLine) {
    _candleSeries.removePriceLine(_priceLine);
  }
  _priceLine = _candleSeries.createPriceLine({
    price,
    color: "#d29922",
    lineWidth: 2,
    lineStyle: LightweightCharts.LineStyle.Solid,
    axisLabelVisible: true,
    title: "現價",
  });
}

function clearGridLines() {
  _gridLines.forEach(line => _candleSeries.removePriceLine(line));
  _gridLines = [];
  if (_priceLine) {
    _candleSeries.removePriceLine(_priceLine);
    _priceLine = null;
  }
}
