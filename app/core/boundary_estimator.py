"""
自動上下界估算：三種策略
  1. atr     — ATR-based（預設）
  2. pct     — 對稱百分比
  3. percentile — 歷史分位數（適合 ETF）
"""
import numpy as np
import pandas as pd
from app.models import BoundarySuggestion
from app.core.grid_engine import round_to_tick
from app import config as cfg


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def suggest_atr(df: pd.DataFrame, current_price: float,
                period: int = None, multiplier: float = None) -> BoundarySuggestion:
    period = period or cfg.DEFAULT_ATR_PERIOD
    multiplier = multiplier or cfg.DEFAULT_ATR_MULTIPLIER

    atr_val = _atr(df, period)
    upper = round_to_tick(current_price + multiplier * atr_val)
    lower = round_to_tick(current_price - multiplier * atr_val)

    return BoundarySuggestion(
        strategy="atr",
        upper=upper,
        lower=lower,
        current_price=current_price,
        reasoning=f"ATR({period})={atr_val:.2f}，倍數={multiplier}，區間 ±{multiplier * atr_val:.2f} 元",
    )


def suggest_pct(current_price: float, pct: float = None) -> BoundarySuggestion:
    pct = pct or cfg.DEFAULT_PCT_RANGE
    upper = round_to_tick(current_price * (1 + pct))
    lower = round_to_tick(current_price * (1 - pct))

    return BoundarySuggestion(
        strategy="pct",
        upper=upper,
        lower=lower,
        current_price=current_price,
        reasoning=f"對稱 ±{pct*100:.1f}%，區間 {lower:.2f}～{upper:.2f}",
    )


def suggest_percentile(df: pd.DataFrame, current_price: float,
                        low_pct: float = 5, high_pct: float = 95,
                        days: int = None) -> BoundarySuggestion:
    days = days or cfg.DEFAULT_PERCENTILE_PERIOD
    close = df["Close"].iloc[-days:] if len(df) >= days else df["Close"]

    lower = round_to_tick(float(np.percentile(close, low_pct)))
    upper = round_to_tick(float(np.percentile(close, high_pct)))

    return BoundarySuggestion(
        strategy="percentile",
        upper=upper,
        lower=lower,
        current_price=current_price,
        reasoning=f"過去 {len(close)} 天 {low_pct}th～{high_pct}th 百分位",
    )


def suggest_all(df: pd.DataFrame, current_price: float) -> list:
    return [
        suggest_atr(df, current_price),
        suggest_pct(current_price),
        suggest_percentile(df, current_price),
    ]
