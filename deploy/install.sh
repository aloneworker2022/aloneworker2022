#!/bin/bash
# 台股網格交易系統 — Raspberry Pi 5 一鍵安裝腳本

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== 台股網格交易系統 安裝程序 ==="
echo "專案目錄：$PROJECT_DIR"
echo "系統架構：$(uname -m)"

# 1. 系統依賴
echo ""
echo "[1/5] 更新系統並安裝依賴..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv

# 選擇性安裝 BLAS/LAPACK（套件名稱因發行版而異）
echo "      安裝數值計算加速庫（不影響功能，安裝失敗會自動跳過）..."
sudo apt-get install -y libopenblas-dev 2>/dev/null || \
sudo apt-get install -y libatlas-base-dev 2>/dev/null || \
sudo apt-get install -y liblapack-dev libblas-dev 2>/dev/null || \
echo "      → 未找到 BLAS 庫，略過（不影響安裝，numpy 仍可運作）"

# 2. 建立虛擬環境
echo ""
echo "[2/5] 建立 Python 虛擬環境..."
cd "$PROJECT_DIR"
python3 -m venv .venv
source .venv/bin/activate

# 3. 安裝 Python 套件
echo ""
echo "[3/5] 安裝 Python 套件（首次可能需要 5-10 分鐘）..."
pip install --upgrade pip -q

# 先嘗試安裝所有套件
if ! pip install -r requirements.txt -q 2>&1; then
    echo "      → 嘗試逐套件安裝..."
    pip install flask pandas numpy requests pytz -q
    # yfinance 及其依賴
    pip install beautifulsoup4 lxml frozendict peewee platformdirs -q
    pip install "curl_cffi>=0.7,<0.14" -q 2>/dev/null || pip install curl_cffi -q
    pip install yfinance -q 2>/dev/null || echo "      → yfinance 安裝失敗，請手動執行：pip install yfinance"
fi

# 4. 建立快取目錄
echo ""
echo "[4/5] 初始化目錄..."
mkdir -p "$PROJECT_DIR/data_cache"

# 驗證核心模組
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from app.core.grid_engine import calculate_grid_result
from app.models import GridConfig
cfg = GridConfig(ticker='2330', upper=1000, lower=800, n_grids=10, shares_per_grid=5)
r = calculate_grid_result(cfg)
print(f'      ✓ 網格引擎正常（{len(r.levels)} 條格線，所需資金 {r.total_capital_required:,.0f} 元）')
" || echo "      ⚠ 核心模組驗證失敗，請檢查安裝"

# 5. 安裝 systemd service
echo ""
echo "[5/5] 設定 systemd 服務..."
CURRENT_USER=$(whoami)
SERVICE_FILE="$PROJECT_DIR/deploy/tw_grid_trader.service"
INSTALL_PATH="/etc/systemd/system/tw_grid_trader.service"

# 動態替換路徑與使用者
sed "s|/home/pi/aloneworker2022|$PROJECT_DIR|g; s|User=pi|User=$CURRENT_USER|g" \
    "$SERVICE_FILE" > /tmp/tw_grid_trader.service

sudo cp /tmp/tw_grid_trader.service "$INSTALL_PATH"
sudo systemctl daemon-reload
sudo systemctl enable tw_grid_trader

echo ""
echo "=== 安裝完成！==="
echo ""
echo "啟動服務：  sudo systemctl start tw_grid_trader"
echo "查看狀態：  sudo systemctl status tw_grid_trader"
echo "查看日誌：  sudo journalctl -u tw_grid_trader -f"
echo "手動啟動：  cd $PROJECT_DIR && .venv/bin/python run.py"
echo ""
echo "瀏覽器開啟：http://$(hostname -I | awk '{print $1}'):5000"
