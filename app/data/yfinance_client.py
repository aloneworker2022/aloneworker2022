import time
import requests
import pandas as pd
import yfinance as yf
from app.data import csv_cache


def normalize_ticker(ticker: str) -> str:
    """2330 → 2330.TW，已有 .TW/.TWO 則不動"""
    ticker = ticker.strip().upper()
    if "." not in ticker:
        ticker = ticker + ".TW"
    return ticker


def _fetch_twse_price(code: str) -> float | None:
    """透過 TWSE 官方 API 取得即時報價（盤中優先）"""
    try:
        url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
        params = {"ex_ch": f"tse_{code}.tw", "json": "1", "delay": "0"}
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, params=params, headers=headers, timeout=5)
        data = r.json()
        msg_array = data.get("msgArray", [])
        if msg_array:
            z = msg_array[0].get("z", "-")
            if z != "-" and z:
                return float(z)
    except Exception:
        pass
    return None


def _fetch_yfinance_with_retry(ticker_tw: str, period: str, interval: str,
                                max_retries: int = 4) -> pd.DataFrame:
    """yfinance 下載，帶指數退避重試"""
    delays = [2, 4, 8, 16]
    last_exc = None
    for attempt in range(max_retries):
        try:
            df = yf.download(
                ticker_tw,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if df is not None and not df.empty:
                # yfinance 0.2.x 有時回傳 MultiIndex columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                df.index.name = "Date"
                return df
        except Exception as e:
            last_exc = e
        if attempt < max_retries - 1:
            time.sleep(delays[attempt])
    raise RuntimeError(f"yfinance 抓取失敗（{ticker_tw}）：{last_exc}")


def fetch_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """取得 OHLCV 日線資料，優先讀 CSV 快取"""
    ticker_tw = normalize_ticker(ticker)
    cached = csv_cache.get_cached(ticker_tw, period, interval)
    if cached is not None:
        return cached

    df = _fetch_yfinance_with_retry(ticker_tw, period, interval)
    csv_cache.save_cache(ticker_tw, period, interval, df)
    return df


def fetch_current_price(ticker: str) -> float:
    """取得目前股價：優先 TWSE 即時，fallback yfinance 最新收盤"""
    code = ticker.strip().upper().replace(".TW", "").replace(".TWO", "")

    price = _fetch_twse_price(code)
    if price is not None:
        return price

    # fallback: yfinance 5 天最新收盤
    try:
        ticker_tw = normalize_ticker(ticker)
        df = _fetch_yfinance_with_retry(ticker_tw, period="5d", interval="1d", max_retries=2)
        if not df.empty:
            return float(df["Close"].iloc[-1])
    except Exception:
        pass

    raise RuntimeError(f"無法取得 {ticker} 的股價")


def fetch_stock_name(ticker: str) -> str:
    """嘗試取得股票中文名稱，失敗回傳空字串"""
    try:
        ticker_tw = normalize_ticker(ticker)
        info = yf.Ticker(ticker_tw).fast_info
        return getattr(info, "long_name", "") or ""
    except Exception:
        return ""
