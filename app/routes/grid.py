from flask import Blueprint, jsonify, request
from app.models import GridConfig
from app.core.grid_engine import calculate_grid_result
from app.core.boundary_estimator import suggest_all, suggest_atr, suggest_pct, suggest_percentile
from app.data import yfinance_client
from app import config as cfg

bp = Blueprint("grid", __name__, url_prefix="/api/grid")


def _parse_config(data: dict) -> GridConfig:
    return GridConfig(
        ticker=data["ticker"],
        upper=float(data["upper"]),
        lower=float(data["lower"]),
        n_grids=int(data.get("n_grids", cfg.DEFAULT_GRID_COUNT)),
        shares_per_grid=int(data.get("shares_per_grid", cfg.DEFAULT_SHARES_PER_GRID)),
        brokerage_fee_rate=float(data.get("fee_rate", cfg.BROKERAGE_FEE_RATE)),
        brokerage_discount=float(data.get("fee_discount", cfg.BROKERAGE_DISCOUNT)),
        transaction_tax_rate=float(data.get("tax_rate", cfg.TRANSACTION_TAX_RATE)),
    )


@bp.post("/calculate")
def calculate():
    data = request.json or {}
    try:
        gc = _parse_config(data)
        result = calculate_grid_result(gc)
        return jsonify({
            "ticker": gc.ticker,
            "upper": gc.upper,
            "lower": gc.lower,
            "n_grids": gc.n_grids,
            "shares_per_grid": gc.shares_per_grid,
            "grid_spacing": result.grid_spacing,
            "grid_spacing_pct": result.grid_spacing_pct,
            "total_capital_required": result.total_capital_required,
            "estimated_profit_per_grid": result.estimated_profit_per_grid,
            "levels": [
                {
                    "index": lv.index,
                    "price": lv.price,
                    "shares": lv.shares,
                    "buy_cost": lv.buy_cost,
                    "sell_revenue": lv.sell_revenue,
                    "profit_per_round": lv.profit_per_round,
                }
                for lv in result.levels
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.post("/suggest-boundaries")
def suggest_boundaries():
    data = request.json or {}
    ticker = data.get("ticker", "")
    strategy = data.get("strategy", "all")
    try:
        current_price = yfinance_client.fetch_current_price(ticker)
        df = yfinance_client.fetch_ohlcv(ticker, period="1y")

        if strategy == "atr":
            suggestions = [suggest_atr(df, current_price,
                                       period=data.get("atr_period"),
                                       multiplier=data.get("atr_multiplier"))]
        elif strategy == "pct":
            suggestions = [suggest_pct(current_price, pct=data.get("pct"))]
        elif strategy == "percentile":
            suggestions = [suggest_percentile(df, current_price)]
        else:
            suggestions = suggest_all(df, current_price)

        return jsonify({
            "ticker": ticker,
            "current_price": current_price,
            "suggestions": [
                {
                    "strategy": s.strategy,
                    "upper": s.upper,
                    "lower": s.lower,
                    "reasoning": s.reasoning,
                }
                for s in suggestions
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/capital-estimate")
def capital_estimate():
    data = request.json or {}
    try:
        gc = _parse_config(data)
        result = calculate_grid_result(gc)
        return jsonify({
            "total_capital_required": result.total_capital_required,
            "estimated_profit_per_grid": result.estimated_profit_per_grid,
            "grid_spacing": result.grid_spacing,
            "grid_spacing_pct": result.grid_spacing_pct,
            "n_grids": gc.n_grids,
            "shares_per_grid": gc.shares_per_grid,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400
