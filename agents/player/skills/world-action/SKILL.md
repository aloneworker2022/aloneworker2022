---
name: world-action
description: "Use this skill to send an action to the world server on behalf of the player avatar. Called internally by player-intent and world-perception skills. Sends HTTP POST to /api/actions and returns the result."
---

# World Action Skill

Send an action to the world server.

## Config
Read entity_id and auth_token from `~/.openclaw/workspace/world_config.json`.

## Steps

1. Read world_config.json to get entity_id and auth_token
2. Execute the action via curl:

```bash
curl -s -X POST http://127.0.0.1:3000/api/actions \
  -H "Content-Type: application/json" \
  -d "{\"entity_id\":\"ENTITY_ID\",\"auth_token\":\"AUTH_TOKEN\",\"type\":\"ACTION_TYPE\",\"payload\":PAYLOAD_JSON}"
```

3. Parse the response:
   - `{"accepted": true, "event_id": "..."}` → action succeeded
   - `{"accepted": false, "reason": "..."}` → action failed, tell the player why in-world

## Action Types Reference

| type | required payload fields |
|------|------------------------|
| move | `to_room` (room id) |
| say | `content` (string) |
| whisper | `target` (entity_id), `content` |
| gesture | `action` (description), `target`? |
| pick_up | `object_id` |
| drop | `object_id` |
| give | `object_id`, `target` (entity_id) |
| use | `object_id` |
| idle_update | `description` (string) |

## Room IDs
- living_room（客廳）
- kitchen（廚房）
- bedroom（臥室）
- balcony（陽台）
