---
name: world-perception
description: "Triggered when you receive a message starting with 'WORLD_EVENT:'. Parse the JSON perception event and translate it into a vivid Chinese MUD-style narrative for the player. Do NOT use this skill for regular player messages."
---

# World Perception Skill

Translate incoming world events into player-facing narrative.

## Input Format

Messages from the world arrive as:
```
WORLD_EVENT:{"perception_type":"you_see","source_event_id":"...","world_time":{"day":1,"hour":10,"minute":30},"actor_id":"agent_ming","event_type":"move","payload":{...},"narrative":"小明走向廚房"}
```

## Steps

1. Strip the `WORLD_EVENT:` prefix and parse the JSON
2. Look at `perception_type`:
   - `you_see` / `you_hear` / `addressed_to_you` → player witnesses something
   - `environment_changed` with `event_type: tick` → time passing (only show if a notable world minute, e.g., every 10 world minutes, or during period changes)
   - `environment_changed` with `event_type: time_period_changed` → narrate the time of day shift
   - `environment_changed` with `event_type: day_changed` → new day announcement
   - `environment_changed` with `event_type: time_jumped` → fast forward summary
3. Use `narrative` from the event as a base, but enhance it poetically if appropriate
4. Format output as MUD scene description (see SOUL.md for format)

## Filtering Ticks

Do NOT send a Telegram message for every tick event. Only narrate ticks when:
- `time_period_changed` (morning, noon, etc.)
- `day_changed`
- `time_jumped`
- A significant world event happens alongside the tick

Silently ignore plain `tick` events.

## Scene Query

After a `move` event confirms the player arrived somewhere new, automatically call:
```bash
curl -s "http://127.0.0.1:3000/api/state/me?entity_id=ENTITY_ID" 
```
Then format the room description:

```
【房間名稱 · 時間段 第N天 HH:MM】
房間描述文字。

在場：人名（正在做某事）
物品：蘋果、書
出口：廚房、臥室、陽台

> 
```
