import uuid
from flask import Blueprint, jsonify, request
from app.models import GridConfig
from app.core.backtest_engine import run_backtest
from app.core.performance import compute_performance
from app.data import yfinance_client
from app import config as cfg

bp = Blueprint("backtest", __name__, url_prefix="/api/backtest")

# 簡單記憶體存儲（Pi 5 不需要 Redis）
_results: dict = {}


@bp.post("/run")
def run():
    data = request.json or {}
    try:
        gc = GridConfig(
            ticker=data["ticker"],
            upper=float(data["upper"]),
            lower=float(data["lower"]),
            n_grids=int(data.get("n_grids", cfg.DEFAULT_GRID_COUNT)),
            shares_per_grid=int(data.get("shares_per_grid", cfg.DEFAULT_SHARES_PER_GRID)),
            brokerage_fee_rate=float(data.get("fee_rate", cfg.BROKERAGE_FEE_RATE)),
            brokerage_discount=float(data.get("fee_discount", cfg.BROKERAGE_DISCOUNT)),
            transaction_tax_rate=float(data.get("tax_rate", cfg.TRANSACTION_TAX_RATE)),
        )
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        initial_capital = float(data.get("initial_capital", cfg.DEFAULT_INITIAL_CAPITAL))

        # 取得足夠的歷史資料（依日期範圍決定 period）
        df = yfinance_client.fetch_ohlcv(gc.ticker, period="5y")

        bt = run_backtest(df, gc, initial_capital, start_date, end_date)
        perf = compute_performance(bt)

        # 計算買入持有比較
        ec = bt["equity_curve"]
        if ec:
            first_price_approx = df.loc[df.index >= (start_date or df.index[0]), "Close"].iloc[0]
            last_price_approx  = df.loc[df.index <= (end_date   or df.index[-1]), "Close"].iloc[-1]
            bh_return = (float(last_price_approx) / float(first_price_approx) - 1) * 100
        else:
            bh_return = 0.0

        job_id = str(uuid.uuid4())[:8]
        _results[job_id] = {
            **bt,
            "performance": perf,
            "buy_hold_return_pct": round(bh_return, 2),
        }
        return jsonify({"job_id": job_id, "status": "done"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.get("/result/<job_id>")
def get_result(job_id):
    result = _results.get(job_id)
    if result is None:
        return jsonify({"error": "找不到結果，請重新執行回測"}), 404
    return jsonify(result)
