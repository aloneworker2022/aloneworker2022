---
name: player-intent
description: "Triggered when the player sends a message that does NOT start with 'WORLD_EVENT:'. Parse the player's natural language command and translate it into a world action. This is the primary MUD input handler."
---

# Player Intent Skill

Parse player commands and execute them in the world.

## Step 1: Pattern Matching (fast path, no LLM needed)

Try to match the player's message against these patterns first:

### Movement
- `去 {房間}` / `走去 {房間}` / `移動到 {房間}` / `前往 {房間}`
  → `move`, payload: `{"to_room": "<room_id>"}`

Room name → ID mapping:
| 玩家說 | room_id |
|--------|---------|
| 客廳 | living_room |
| 廚房 / 廚房 | kitchen |
| 臥室 / 房間 / 睡房 | bedroom |
| 陽台 | balcony |

### Speech
- `說 {內容}` / `大喊 {內容}` / `喊 {內容}`
  → `say`, payload: `{"content": "<content>"}`
- `對 {人名} 說 {內容}` / `悄悄對 {人名} 說 {內容}` / `低聲對 {人名} 說`
  → `whisper`, payload: `{"target": "<entity_id>", "content": "<content>"}`

### Objects
- `拿 {物品}` / `撿起 {物品}` / `拿起 {物品}`
  → `pick_up`, payload: `{"object_id": "<id>"}`
- `放下 {物品}` / `丟下 {物品}`
  → `drop`, payload: `{"object_id": "<id>"}`
- `給 {人名} {物品}` / `把 {物品} 給 {人名}`
  → `give`, payload: `{"target": "<entity_id>", "object_id": "<id>"}`
- `用 {物品}` / `使用 {物品}` / `吃 {物品}` / `讀 {物品}` / `看 {物品}`
  → `use`, payload: `{"object_id": "<id>"}`

### Look Around
- `看` / `環顧` / `環顧四周` / `我在哪` / `這裡有什麼` / `l` (MUD shorthand)
  → Call `GET http://127.0.0.1:3000/api/state/me?entity_id=ENTITY_ID` and format as room description

### Time
- `現在幾點` / `時間` / `幾點了`
  → Read world_time from state/me and reply: `現在是 早晨 第1天 07:30`

### Inventory
- `我有什麼` / `背包` / `物品欄` / `i` (MUD shorthand)
  → Read inventory from state/me and list items

## Step 2: LLM Fallback

If no pattern matches, use your reasoning to interpret the player's intent and map it to one of the action types above. If the intent is completely unclear, ask the player to clarify.

## Step 3: Execute

1. Call the world-action skill with the resolved action
2. On success: confirm briefly, then if it's a move, show the new room scene
3. On failure: translate the rejection reason into gentle in-world language

## Step 4: State Refresh After Action

After any successful action, optionally call state/me to refresh context if needed.

## Error Messages (in-world style)

| World reason | Player sees |
|-------------|-------------|
| Rooms are not connected | 你試著往那個方向走，但路被擋住了。 |
| Object is not in your room | 你找不到那個東西。 |
| Object is not in your inventory | 你手上沒有那個東西。 |
| Cooldown active | 你需要稍作休息才能繼續行動。 |
| Target is not in the same room | 那個人不在這裡。 |
