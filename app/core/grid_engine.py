"""
網格計算引擎 — 純函數，無副作用。
最小交易單位：1 股（支援零股）。
"""
import math
from typing import List
from app.models import GridConfig, GridLevel, GridResult


# --- Tick size（台股價格跳動單位）---

def round_to_tick(price: float) -> float:
    if price <= 10:
        tick = 0.01
    elif price <= 50:
        tick = 0.05
    elif price <= 100:
        tick = 0.1
    elif price <= 500:
        tick = 0.5
    elif price <= 1000:
        tick = 1.0
    else:
        tick = 5.0
    return round(round(price / tick) * tick, 10)


# --- 手續費計算 ---

def _buy_cost(price: float, shares: int, fee_rate: float, discount: float) -> float:
    """買入總成本 = 股價 × 股數 × (1 + 手續費率 × 折扣)"""
    fee = price * shares * fee_rate * discount
    fee = max(fee, 20)  # 最低手續費 20 元（多數券商）
    return price * shares + fee


def _sell_revenue(price: float, shares: int, fee_rate: float, discount: float, tax_rate: float) -> float:
    """賣出收入 = 股價 × 股數 × (1 - 手續費率 × 折扣 - 交易稅率)"""
    fee = price * shares * fee_rate * discount
    fee = max(fee, 20)
    tax = price * shares * tax_rate
    return price * shares - fee - tax


# --- 主要計算函數 ---

def calculate_grid_levels(config: GridConfig) -> List[GridLevel]:
    """
    等距切割 [lower, upper] 成 n_grids 段，產生 n_grids+1 條格線。
    每條格線代表一個買賣觸發點。
    """
    if config.n_grids < 2:
        raise ValueError("格子數至少需要 2")
    if config.upper <= config.lower:
        raise ValueError("上界必須大於下界")

    step = (config.upper - config.lower) / config.n_grids
    levels = []

    fee_rate = config.brokerage_fee_rate
    discount = config.brokerage_discount
    tax_rate = config.transaction_tax_rate

    for i in range(config.n_grids + 1):
        price = round_to_tick(config.lower + i * step)
        shares = config.shares_per_grid

        buy_c = _buy_cost(price, shares, fee_rate, discount)
        sell_r = _sell_revenue(price, shares, fee_rate, discount, tax_rate)

        # 每格獲利 = 以下一格賣出 - 以此格買入
        if i < config.n_grids:
            sell_price = round_to_tick(config.lower + (i + 1) * step)
            profit = _sell_revenue(sell_price, shares, fee_rate, discount, tax_rate) - buy_c
        else:
            profit = 0.0

        levels.append(GridLevel(
            index=i,
            price=price,
            shares=shares,
            buy_cost=round(buy_c, 2),
            sell_revenue=round(sell_r, 2),
            profit_per_round=round(profit, 2),
        ))

    return levels


def calculate_capital_required(levels: List[GridLevel]) -> dict:
    """
    估算最壞情況（從最高格一路跌到最低格，全部買入）所需總資金。
    實際使用時可能用不完，但這是安全邊際估算。
    """
    # 排除最高格（最高格只賣不買）
    buy_levels = levels[:-1]
    total = sum(lv.buy_cost for lv in buy_levels)
    return {
        "total": round(total, 2),
        "per_grid_avg": round(total / len(buy_levels), 2) if buy_levels else 0,
        "grid_count": len(buy_levels),
    }


def calculate_grid_result(config: GridConfig) -> GridResult:
    levels = calculate_grid_levels(config)
    capital = calculate_capital_required(levels)
    step = (config.upper - config.lower) / config.n_grids
    avg_price = (config.upper + config.lower) / 2
    avg_profit = sum(lv.profit_per_round for lv in levels[:-1]) / config.n_grids

    return GridResult(
        config=config,
        levels=levels,
        total_capital_required=capital["total"],
        estimated_profit_per_grid=round(avg_profit, 2),
        grid_spacing=round(step, 4),
        grid_spacing_pct=round(step / avg_price * 100, 4),
    )
