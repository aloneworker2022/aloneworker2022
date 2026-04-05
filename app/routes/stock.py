from flask import Blueprint, jsonify, request
from app.data import yfinance_client

bp = Blueprint("stock", __name__, url_prefix="/api/stock")

# 常見台股靜態清單（搜尋用）
_STOCK_LIST = [
    ("2330", "台積電"), ("2317", "鴻海"), ("2454", "聯發科"), ("2308", "台達電"),
    ("2382", "廣達"), ("2412", "中華電"), ("2881", "富邦金"), ("2882", "國泰金"),
    ("2886", "兆豐金"), ("2303", "聯電"), ("2357", "華碩"), ("2379", "瑞昱"),
    ("2395", "研華"), ("3711", "日月光投控"), ("2891", "中信金"), ("2884", "玉山金"),
    ("5880", "合庫金"), ("2892", "第一金"), ("2885", "元大金"), ("2887", "台新金"),
    ("0050", "元大台灣50"), ("0056", "元大高股息"), ("00878", "國泰永續高股息"),
    ("00919", "群益台灣精選高息"), ("00929", "復華台灣科技優息"),
    ("2002", "中鋼"), ("1301", "台塑"), ("1303", "南亞"), ("1326", "台化"),
    ("2207", "和泰車"), ("2912", "統一超"), ("2801", "彰銀"), ("5876", "上海商銀"),
]


@bp.get("/<ticker>/ohlcv")
def get_ohlcv(ticker):
    period = request.args.get("period", "1y")
    interval = request.args.get("interval", "1d")
    try:
        df = yfinance_client.fetch_ohlcv(ticker, period, interval)
        records = []
        for ts, row in df.iterrows():
            records.append({
                "time": str(ts)[:10],
                "open":  round(float(row.get("Open",  row.iloc[0])), 2),
                "high":  round(float(row.get("High",  row.iloc[1])), 2),
                "low":   round(float(row.get("Low",   row.iloc[2])), 2),
                "close": round(float(row.get("Close", row.iloc[3])), 2),
                "volume": int(row.get("Volume", row.iloc[4]) or 0),
            })
        return jsonify({"ticker": ticker, "period": period, "data": records})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.get("/<ticker>/current")
def get_current(ticker):
    try:
        price = yfinance_client.fetch_current_price(ticker)
        return jsonify({"ticker": ticker, "price": price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.get("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    q_upper = q.upper()
    results = [
        {"code": code, "name": name}
        for code, name in _STOCK_LIST
        if q_upper in code or q in name
    ]
    return jsonify(results[:10])
