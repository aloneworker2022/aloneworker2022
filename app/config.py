import os

# Server
HOST = "0.0.0.0"
PORT = 5000
DEBUG = False

# Cache
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_cache")
CACHE_TTL_MARKET_OPEN = 3600    # 盤中 1 小時
CACHE_TTL_MARKET_CLOSE = 86400  # 盤後 24 小時

# Taiwan market hours (Asia/Taipei)
TW_TIMEZONE = "Asia/Taipei"
TW_MARKET_OPEN_H = 9
TW_MARKET_OPEN_M = 0
TW_MARKET_CLOSE_H = 13
TW_MARKET_CLOSE_M = 30

# Trading fees
BROKERAGE_FEE_RATE = 0.001425   # 0.1425%
BROKERAGE_DISCOUNT = 1.0        # 折扣倍率（0.6 = 六折）
TRANSACTION_TAX_RATE = 0.003    # 賣出證交稅 0.3%

# Grid defaults
DEFAULT_GRID_COUNT = 10
DEFAULT_SHARES_PER_GRID = 1
MIN_GRID_COUNT = 2
MAX_GRID_COUNT = 100

# Boundary estimator
DEFAULT_ATR_PERIOD = 14
DEFAULT_ATR_MULTIPLIER = 2.0
DEFAULT_PCT_RANGE = 0.15        # ±15%
DEFAULT_PERCENTILE_PERIOD = 250 # 歷史分位數使用天數

# Backtest
DEFAULT_INITIAL_CAPITAL = 100000
