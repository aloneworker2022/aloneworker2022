from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GridLevel:
    index: int
    price: float          # 此格的觸發價格（格線）
    shares: int           # 每格買賣股數
    buy_cost: float       # 買入總成本（含手續費）
    sell_revenue: float   # 賣出總收入（扣手續費與稅）
    profit_per_round: float  # 一買一賣的淨獲利


@dataclass
class GridConfig:
    ticker: str
    upper: float
    lower: float
    n_grids: int
    shares_per_grid: int
    brokerage_fee_rate: float = 0.001425
    brokerage_discount: float = 1.0
    transaction_tax_rate: float = 0.003


@dataclass
class GridResult:
    config: GridConfig
    levels: List[GridLevel]
    total_capital_required: float
    estimated_profit_per_grid: float
    grid_spacing: float
    grid_spacing_pct: float


@dataclass
class OHLCVBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: float


@dataclass
class TradeRecord:
    date: str
    action: str          # 'buy' or 'sell'
    grid_index: int
    price: float
    shares: int
    amount: float        # 買入成本 or 賣出收入
    fee: float
    tax: float
    pnl: float           # 僅 sell 時有值，否則 0


@dataclass
class BacktestResult:
    ticker: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    annualized_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate_pct: float
    total_trades: int
    total_fees: float
    equity_curve: List[dict]   # [{date, equity, cash, position_value}]
    trade_records: List[TradeRecord]


@dataclass
class BoundarySuggestion:
    strategy: str
    upper: float
    lower: float
    current_price: float
    reasoning: str


@dataclass
class MonitorPosition:
    id: str
    ticker: str
    ticker_name: str
    config: GridConfig
    levels: List[GridLevel]
    active: bool = True
    created_at: str = ""
    last_checked: str = ""
    alerts: List[dict] = field(default_factory=list)
