"""
回測引擎 — 逐日事件驅動模擬。

網格交易規則：
  - 區間內：觸碰格線 → 買入；上升到上一格 → 賣出
  - 突破上界：獲利了結，賣出所有持倉，停止交易
  - 跌破下界：強制停損，賣出所有持倉，停止交易

台股費用規則：
  - T+2 交割：買入後 2 個交易日才可賣出
  - 手續費：買賣各 0.1425%（可設折扣），最低 20 元
  - 交易稅：賣出 0.3%
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd

from app.models import GridConfig, GridLevel, TradeRecord
from app.core.grid_engine import calculate_grid_levels, _buy_cost, _sell_revenue


@dataclass
class _Position:
    """持倉中的一筆買入記錄"""
    buy_date_idx: int   # 買入當天的 row index（用於 T+2 判斷）
    buy_price: float
    shares: int
    grid_index: int
    buy_cost: float


def _force_sell_all(
    positions: Dict[int, List[_Position]],
    sell_price: float,
    date_str: str,
    fee_rate: float,
    discount: float,
    tax_rate: float,
    action: str,          # "sell_upper" 或 "sell_lower"
    cash: float,
    trade_records: List[TradeRecord],
) -> float:
    """強制清倉所有持倉（上界止盈 / 下界停損），回傳更新後的 cash。"""
    for gi, pos_list in positions.items():
        for pos in list(pos_list):
            sell_rev = _sell_revenue(sell_price, pos.shares, fee_rate, discount, tax_rate)
            pnl = sell_rev - pos.buy_cost
            fee = sell_price * pos.shares * fee_rate * discount
            fee = max(fee, 20)
            tax = sell_price * pos.shares * tax_rate
            cash += sell_rev
            trade_records.append(TradeRecord(
                date=date_str,
                action=action,
                grid_index=gi,
                price=sell_price,
                shares=pos.shares,
                amount=round(sell_rev, 2),
                fee=round(fee, 2),
                tax=round(tax, 2),
                pnl=round(pnl, 2),
            ))
        pos_list.clear()
    return cash


def run_backtest(
    df: pd.DataFrame,
    config: GridConfig,
    initial_capital: float = 100_000,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """
    執行回測，回傳結果字典。
    df 需包含欄位：Open, High, Low, Close（日線，index 為日期）
    """
    # --- 日期篩選 ---
    if start_date:
        df = df[df.index >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df.index <= pd.Timestamp(end_date)]
    if df.empty:
        raise ValueError("指定日期範圍內無資料")

    df = df.copy().reset_index()
    df.columns = [c if isinstance(c, str) else str(c) for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}
    open_col  = col_map.get("open",  "Open")
    high_col  = col_map.get("high",  "High")
    low_col   = col_map.get("low",   "Low")
    close_col = col_map.get("close", "Close")
    date_col  = df.columns[0]

    levels: List[GridLevel] = calculate_grid_levels(config)
    prices = [lv.price for lv in levels]
    n = len(levels)

    fee_rate = config.brokerage_fee_rate
    discount = config.brokerage_discount
    tax_rate = config.transaction_tax_rate

    cash = initial_capital
    positions: Dict[int, List[_Position]] = {i: [] for i in range(n)}
    trade_records: List[TradeRecord] = []
    equity_curve = []

    grid_active = True   # 突破上下界後停止交易
    stop_reason = None   # "upper_break" / "lower_break"

    for day_idx, row in df.iterrows():
        date_str  = str(row[date_col])[:10]
        day_high  = float(row[high_col])
        day_low   = float(row[low_col])
        day_close = float(row[close_col])

        if grid_active:
            # ══════════════════════════════════════════
            # 1. 突破上界 → 獲利了結，清倉，停止網格
            # ══════════════════════════════════════════
            if day_high >= config.upper:
                cash = _force_sell_all(
                    positions, config.upper, date_str,
                    fee_rate, discount, tax_rate,
                    "sell_upper", cash, trade_records,
                )
                grid_active = False
                stop_reason = "upper_break"

            # ══════════════════════════════════════════
            # 2. 跌破下界 → 強制停損，清倉，停止網格
            # ══════════════════════════════════════════
            elif day_low <= config.lower:
                cash = _force_sell_all(
                    positions, config.lower, date_str,
                    fee_rate, discount, tax_rate,
                    "sell_lower", cash, trade_records,
                )
                grid_active = False
                stop_reason = "lower_break"

            else:
                # ══════════════════════════════════════
                # 3. 正常網格交易（區間內）
                # ══════════════════════════════════════

                # --- 先處理賣出（T+2 後才可賣）---
                for gi in range(n - 1):
                    sell_trigger = prices[gi + 1]
                    if day_high >= sell_trigger:
                        eligible = [
                            p for p in positions[gi]
                            if (day_idx - p.buy_date_idx) >= 2
                        ]
                        for pos in eligible:
                            sell_rev = _sell_revenue(
                                sell_trigger, pos.shares, fee_rate, discount, tax_rate)
                            pnl = sell_rev - pos.buy_cost
                            fee = sell_trigger * pos.shares * fee_rate * discount
                            fee = max(fee, 20)
                            tax = sell_trigger * pos.shares * tax_rate
                            cash += sell_rev
                            trade_records.append(TradeRecord(
                                date=date_str,
                                action="sell",
                                grid_index=gi,
                                price=sell_trigger,
                                shares=pos.shares,
                                amount=round(sell_rev, 2),
                                fee=round(fee, 2),
                                tax=round(tax, 2),
                                pnl=round(pnl, 2),
                            ))
                            positions[gi].remove(pos)

                # --- 再處理買入 ---
                for gi in range(1, n):
                    buy_trigger = prices[gi - 1]
                    if day_low <= buy_trigger:
                        shares = config.shares_per_grid
                        cost = _buy_cost(buy_trigger, shares, fee_rate, discount)
                        if cash >= cost:
                            cash -= cost
                            fee = buy_trigger * shares * fee_rate * discount
                            fee = max(fee, 20)
                            positions[gi - 1].append(_Position(
                                buy_date_idx=day_idx,
                                buy_price=buy_trigger,
                                shares=shares,
                                grid_index=gi - 1,
                                buy_cost=cost,
                            ))
                            trade_records.append(TradeRecord(
                                date=date_str,
                                action="buy",
                                grid_index=gi - 1,
                                price=buy_trigger,
                                shares=shares,
                                amount=round(cost, 2),
                                fee=round(fee, 2),
                                tax=0.0,
                                pnl=0.0,
                            ))

        # ---- 計算當日權益（grid 停止後持倉應為 0）----
        position_value = sum(
            pos.shares * day_close
            for gi_list in positions.values()
            for pos in gi_list
        )
        equity = cash + position_value
        equity_curve.append({
            "date": date_str,
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "position_value": round(position_value, 2),
            "grid_active": grid_active,
        })

    final_close = float(df[close_col].iloc[-1])
    final_position_value = sum(
        pos.shares * final_close
        for gi_list in positions.values()
        for pos in gi_list
    )
    final_equity = cash + final_position_value

    return {
        "initial_capital": initial_capital,
        "final_equity": round(final_equity, 2),
        "final_cash": round(cash, 2),
        "final_position_value": round(final_position_value, 2),
        "stop_reason": stop_reason,          # None / "upper_break" / "lower_break"
        "equity_curve": equity_curve,
        "trade_records": [
            {
                "date": t.date,
                "action": t.action,
                "grid_index": t.grid_index,
                "price": t.price,
                "shares": t.shares,
                "amount": t.amount,
                "fee": t.fee,
                "tax": t.tax,
                "pnl": t.pnl,
            }
            for t in trade_records
        ],
        "start_date": str(df[date_col].iloc[0])[:10],
        "end_date": str(df[date_col].iloc[-1])[:10],
        "total_days": len(df),
    }
