---
name: world-action
description: "Send an action to the world server. Used internally after deciding what to do. Reads entity_id and auth_token from world_config.json."
---

# World Action Skill

## Steps

1. Read `~/.openclaw/workspace/world_config.json` to get entity_id and auth_token
2. POST the action:

```bash
curl -s -X POST http://127.0.0.1:3000/api/actions \
  -H "Content-Type: application/json" \
  -d '{"entity_id":"ENTITY_ID","auth_token":"AUTH_TOKEN","type":"ACTION_TYPE","payload":PAYLOAD_JSON}'
```

3. Check result: `accepted: true` = done. `accepted: false` = log reason, don't retry immediately.

## Action Types

| type | payload |
|------|---------|
| move | `{"to_room": "room_id"}` |
| say | `{"content": "text"}` |
| whisper | `{"target": "entity_id", "content": "text"}` |
| gesture | `{"action": "description", "target": "entity_id?"}` |
| pick_up | `{"object_id": "id"}` |
| drop | `{"object_id": "id"}` |
| give | `{"object_id": "id", "target": "entity_id"}` |
| use | `{"object_id": "id"}` |
| idle_update | `{"description": "text describing current activity"}` |

## Room IDs
living_room, kitchen, bedroom, balcony
