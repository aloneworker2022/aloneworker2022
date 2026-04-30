import os
import time
import pandas as pd
import pytz
from datetime import datetime
from app import config


def _cache_path(ticker: str, period: str, interval: str) -> str:
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    filename = f"{ticker}_{period}_{interval}.csv".replace("/", "-")
    return os.path.join(config.CACHE_DIR, filename)


def _is_market_open() -> bool:
    tz = pytz.timezone(config.TW_TIMEZONE)
    now = datetime.now(tz)
    if now.weekday() >= 5:  # 週六日
        return False
    open_time = now.replace(hour=config.TW_MARKET_OPEN_H, minute=config.TW_MARKET_OPEN_M, second=0, microsecond=0)
    close_time = now.replace(hour=config.TW_MARKET_CLOSE_H, minute=config.TW_MARKET_CLOSE_M, second=0, microsecond=0)
    return open_time <= now <= close_time


def is_cache_valid(filepath: str) -> bool:
    if not os.path.exists(filepath):
        return False
    mtime = os.path.getmtime(filepath)
    age = time.time() - mtime
    ttl = config.CACHE_TTL_MARKET_OPEN if _is_market_open() else config.CACHE_TTL_MARKET_CLOSE
    return age < ttl


def get_cached(ticker: str, period: str, interval: str) -> pd.DataFrame | None:
    path = _cache_path(ticker, period, interval)
    if not is_cache_valid(path):
        return None
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df if not df.empty else None
    except Exception:
        return None


def save_cache(ticker: str, period: str, interval: str, df: pd.DataFrame) -> None:
    path = _cache_path(ticker, period, interval)
    df.to_csv(path)


def clear_cache(ticker: str = None) -> int:
    """清除快取，ticker=None 時清全部。回傳刪除數量。"""
    count = 0
    for f in os.listdir(config.CACHE_DIR):
        if f.endswith(".csv"):
            if ticker is None or f.startswith(ticker):
                os.remove(os.path.join(config.CACHE_DIR, f))
                count += 1
    return count
