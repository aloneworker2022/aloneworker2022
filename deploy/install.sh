#!/bin/bash
# 台股網格交易系統 — Raspberry Pi 5 一鍵安裝腳本

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== 台股網格交易系統 安裝程序 ==="
echo "專案目錄：$PROJECT_DIR"

# 1. 系統依賴
echo ""
echo "[1/5] 更新系統並安裝依賴..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv \
    libatlas-base-dev libopenblas-dev libhdf5-dev

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
pip install -r requirements.txt

# 4. 建立快取目錄
echo ""
echo "[4/5] 初始化目錄..."
mkdir -p "$PROJECT_DIR/data_cache"

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
