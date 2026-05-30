#!/bin/bash
# 在 Raspberry Pi 5 上執行此腳本，安裝 cthulhu-note 為 systemd 服務
# 用法：bash deploy/install-service.sh

set -e

SERVICE_FILE="$(dirname "$0")/cthulhu-note.service"
TARGET="/etc/systemd/system/cthulhu-note.service"

# 確認 cthulhu-note-web 在哪
BIN=$(which cthulhu-note-web 2>/dev/null || echo "")
if [ -z "$BIN" ]; then
  # 嘗試 venv
  BIN=$(ls /home/"$USER"/.venv/*/bin/cthulhu-note-web 2>/dev/null | head -1)
fi
if [ -z "$BIN" ]; then
  echo "找不到 cthulhu-note-web，請先 pip install -e ."
  exit 1
fi

echo "✓ 找到執行檔：$BIN"

# 動態填入目前的使用者和路徑
sed \
  -e "s|User=aw|User=$USER|g" \
  -e "s|WorkingDirectory=/home/aw|WorkingDirectory=$HOME|g" \
  -e "s|ExecStart=.*|ExecStart=$BIN|g" \
  "$SERVICE_FILE" > /tmp/cthulhu-note.service

echo "── 即將安裝的 service 檔案 ──"
cat /tmp/cthulhu-note.service
echo "────────────────────────────"

sudo cp /tmp/cthulhu-note.service "$TARGET"
sudo systemctl daemon-reload
sudo systemctl enable cthulhu-note
sudo systemctl restart cthulhu-note

echo ""
echo "✓ 已啟動！狀態："
sudo systemctl status cthulhu-note --no-pager -l
echo ""
echo "常用指令："
echo "  sudo systemctl status  cthulhu-note   # 查看狀態"
echo "  sudo systemctl restart cthulhu-note   # 重啟"
echo "  sudo systemctl stop    cthulhu-note   # 停止"
echo "  sudo journalctl -u cthulhu-note -f    # 即時 log"
