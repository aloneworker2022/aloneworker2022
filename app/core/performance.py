"""
績效指標計算，輸入 run_backtest() 回傳的結果字典。
"""
import math
from typing import List


def compute_performance(bt: dict) -> dict:
    equity_curve = bt["equity_curve"]
    trade_records = bt["trade_records"]
    initial = bt["initial_capital"]
    final = bt["final_equity"]
    total_days = bt["total_days"]

    if not equity_curve:
        return {}

    # --- 總報酬率 ---
    total_return_pct = (final - initial) / initial * 100

    # --- 年化報酬率 ---
    years = total_days / 252
    if years > 0 and final > 0:
        ann_return_pct = ((final / initial) ** (1 / years) - 1) * 100
    else:
        ann_return_pct = 0.0

    # --- 最大回撤 ---
    equities = [e["equity"] for e in equity_curve]
    max_dd_pct = 0.0
    peak = equities[0]
    for eq in equities:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd_pct:
            max_dd_pct = dd

    # --- 日報酬序列 (用於 Sharpe) ---
    daily_returns = []
    for i in range(1, len(equities)):
        if equities[i - 1] > 0:
            daily_returns.append((equities[i] - equities[i - 1]) / equities[i - 1])

    # --- Sharpe Ratio（無風險利率 1.5% / 252）---
    rf_daily = 0.015 / 252
    if len(daily_returns) > 1:
        import statistics
        avg_r = statistics.mean(daily_returns) - rf_daily
        std_r = statistics.stdev(daily_returns)
        sharpe = (avg_r / std_r * math.sqrt(252)) if std_r > 0 else 0.0
    else:
        sharpe = 0.0

    # --- 勝率 ---
    sells = [t for t in trade_records if t["action"] == "sell"]
    win_trades = [t for t in sells if t["pnl"] > 0]
    win_rate_pct = (len(win_trades) / len(sells) * 100) if sells else 0.0

    # --- 總手續費 ---
    total_fees = sum(t["fee"] + t["tax"] for t in trade_records)

    # --- 買入持有比較 ---
    buy_hold_return_pct = 0.0
    if equity_curve:
        first_close = equity_curve[0]["equity"]  # 近似
        # 取第一筆買入成本或初始資本估算
        buy_hold_return_pct = total_return_pct  # placeholder，路由層可覆蓋

    return {
        "total_return_pct": round(total_return_pct, 2),
        "annualized_return_pct": round(ann_return_pct, 2),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "sharpe_ratio": round(sharpe, 3),
        "win_rate_pct": round(win_rate_pct, 2),
        "total_trades": len(trade_records),
        "buy_trades": len([t for t in trade_records if t["action"] == "buy"]),
        "sell_trades": len(sells),
        "total_fees": round(total_fees, 2),
        "final_equity": round(final, 2),
        "initial_capital": initial,
    }
