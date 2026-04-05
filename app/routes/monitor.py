"""
即時監控路由：追蹤使用者設定的網格持倉，
定期檢查股價是否觸及格線並產生提醒。
持倉設定儲存在記憶體（Pi 5 重啟後需重新設定）。
"""
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.models import GridConfig
from app.core.grid_engine import calculate_grid_levels
from app.data import yfinance_client
from app import config as cfg

bp = Blueprint("monitor", __name__, url_prefix="/api/monitor")

_positions: dict = {}  # id → dict


@bp.get("/positions")
def list_positions():
    return jsonify(list(_positions.values()))


@bp.post("/positions")
def add_position():
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
        levels = calculate_grid_levels(gc)
        pos_id = str(uuid.uuid4())[:8]
        _positions[pos_id] = {
            "id": pos_id,
            "ticker": gc.ticker,
            "upper": gc.upper,
            "lower": gc.lower,
            "n_grids": gc.n_grids,
            "shares_per_grid": gc.shares_per_grid,
            "levels": [{"index": lv.index, "price": lv.price} for lv in levels],
            "active": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "alerts": [],
        }
        return jsonify({"id": pos_id, "status": "added"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.delete("/positions/<pos_id>")
def delete_position(pos_id):
    if pos_id in _positions:
        del _positions[pos_id]
        return jsonify({"status": "deleted"})
    return jsonify({"error": "找不到此持倉"}), 404


@bp.get("/alerts")
def get_alerts():
    """
    即時查詢所有持倉目前的股價，與格線比較，回傳觸及或接近的提醒。
    """
    alerts = []
    for pos_id, pos in _positions.items():
        if not pos["active"]:
            continue
        try:
            price = yfinance_client.fetch_current_price(pos["ticker"])
            levels = pos["levels"]
            prices = [lv["price"] for lv in levels]

            # 找出最近的上下格線
            above = [p for p in prices if p > price]
            below = [p for p in prices if p <= price]
            nearest_above = min(above) if above else None
            nearest_below = max(below) if below else None

            # 接近度（距最近格線 ≤ 1%）
            def near(target):
                return abs(price - target) / target <= 0.01

            status = "in_range" if (nearest_above and nearest_below) else (
                "above_range" if not nearest_above else "below_range"
            )

            pos_alerts = []
            if nearest_above and near(nearest_above):
                pos_alerts.append({"type": "near_sell", "grid_price": nearest_above,
                                   "message": f"股價 {price} 接近賣出格線 {nearest_above}"})
            if nearest_below and near(nearest_below):
                pos_alerts.append({"type": "near_buy", "grid_price": nearest_below,
                                   "message": f"股價 {price} 接近買入格線 {nearest_below}"})

            alerts.append({
                "position_id": pos_id,
                "ticker": pos["ticker"],
                "current_price": price,
                "status": status,
                "nearest_above": nearest_above,
                "nearest_below": nearest_below,
                "alerts": pos_alerts,
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        except Exception as e:
            alerts.append({"position_id": pos_id, "ticker": pos["ticker"], "error": str(e)})

    return jsonify(alerts)
