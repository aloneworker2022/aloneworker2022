# OpenClaw 虛擬世界模擬器

持續存在的文字虛擬世界，讓 OpenClaw agent 作為世界中的居民。

## 專案結構

```
world-server/    Node.js/TypeScript 世界伺服器，port 3755
agents/ming/     小明 agent 的 OpenClaw workspace 設定
agents/player/   玩家化身的 OpenClaw workspace 設定
```

## 快速啟動

### Phase 1: 啟動世界伺服器
```bash
cd world-server
npm install
npm run dev
```

驗收：
```bash
curl http://127.0.0.1:3755/health
curl http://127.0.0.1:3755/api/admin/snapshot
```

Admin Web UI（瀏覽器直接開）：
```
http://<RPi5-IP>:3755/
```

### Phase 2: 設定 OpenClaw Agents

**架構說明：** 所有 agent 共用同一個 OpenClaw 實例（同一個 port 18789）。
World Server 用 `agentId` 參數告訴 OpenClaw 這次要跑哪個角色。

#### 2a. 在 OpenClaw 設定多個 agent

在 `~/.openclaw/openclaw.json` 加入：
```json
{
  "agents": {
    "list": [
      { "id": "player", "name": "玩家化身", "workspace": "~/.openclaw/workspace-player" },
      { "id": "ming",   "name": "小明",     "workspace": "~/.openclaw/workspace-ming" }
    ]
  }
}
```

#### 2b. 複製 skill 設定到各 workspace

```bash
cp -r agents/player/* ~/.openclaw/workspace-player/
cp -r agents/ming/*   ~/.openclaw/workspace-ming/
```

#### 2c. 向世界伺服器註冊（兩個 agent 用同一個 webhook_url）

```bash
# 玩家化身
curl -X POST http://127.0.0.1:3755/api/entities/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "player_avatar",
    "name": "你的名字",
    "type": "player_avatar",
    "webhook_url": "http://127.0.0.1:18789/hooks/agent",
    "webhook_token": "YOUR_OPENCLAW_TOKEN",
    "openclaw_agent_id": "player",
    "start_room": "living_room"
  }'

# 小明
curl -X POST http://127.0.0.1:3755/api/entities/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "agent_ming",
    "name": "小明",
    "type": "agent",
    "webhook_url": "http://127.0.0.1:18789/hooks/agent",
    "webhook_token": "YOUR_OPENCLAW_TOKEN",
    "openclaw_agent_id": "ming",
    "start_room": "living_room"
  }'
```

World Server 推送事件時會自動帶 `agentId`，OpenClaw 就知道這次用哪個角色的 workspace 跑。

#### 2d. 儲存各自的 auth_token

```bash
echo '{"entity_id":"player_avatar","auth_token":"TOKEN_HERE"}' \
  > ~/.openclaw/workspace-player/world_config.json

echo '{"entity_id":"agent_ming","auth_token":"TOKEN_HERE"}' \
  > ~/.openclaw/workspace-ming/world_config.json
```

#### 2e. 設定 Telegram Bot（玩家化身用）

在 OpenClaw config 加入 telegram channel，對應 player workspace。

## API 速查

| 端點 | 說明 |
|------|------|
| `GET /api/admin/snapshot` | 整個世界當前狀態 |
| `POST /api/entities/register` | 註冊 agent |
| `POST /api/actions` | 送出行動 |
| `GET /api/state/me?entity_id=X` | 查詢自己狀態 |
| `GET /api/state/history?entity_id=X&since=Y` | 查詢事件歷史 |
| `POST /api/admin/fast_forward` | 時間快轉 `{"world_minutes": 60}` |
| `POST /api/admin/set_weather` | 設天氣 `{"weather":"rainy","temperature":18}` |
| `POST /api/admin/spawn_object` | 生成物件 |

## 世界時間

現實 1 分鐘 = 世界 10 分鐘。Tick 每 6 秒。

## 開發注意事項

- `world-server/data/` 是 runtime data（已 gitignore）
- 世界狀態保存在 `world-server/data/world-state.json`
- 事件日誌在 `world-server/data/world_log_day_N.jsonl`
- TypeScript 型別：`world-server/src/types.ts`
