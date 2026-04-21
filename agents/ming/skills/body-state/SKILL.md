---
name: body-state
description: "Read or update 小明's body and mental state. Use this skill when processing tick events (plant brain layer) or when you need to know your current physical/emotional state before making a decision."
---

# Body State Skill

Manages `~/.openclaw/workspace/body_state.json`.

## State Schema

```json
{
  "hunger": 0,
  "thirst": 0,
  "fatigue": 0,
  "mood": 50,
  "social_need": 30,
  "boredom": 20,
  "last_tick_world_time": {"day": 1, "hour": 7, "minute": 0},
  "last_ate_at": null,
  "last_slept_at": null,
  "last_chatted_at": null
}
```

All values 0–100 except mood (−100 to 100).

## Plant Brain: Tick Update

When a `tick` event arrives (1 world minute passed), update state:

```
hunger += 0.15 per minute  (full day without eating ≈ +216 → capped at 100)
thirst += 0.2 per minute
fatigue += 0.08 per minute (awake all day ≈ +115 → capped at 100)
boredom += 0.1 per minute
social_need += 0.05 per minute
mood: decays 0.02/min toward 0 if extreme
```

If sleeping (fatigue action noted):
```
fatigue -= 1.5 per minute
hunger += 0.05 (slower while sleeping)
```

## Plant Brain: Action Effects

| Action | Effect |
|--------|--------|
| Ate food | hunger = 0, last_ate_at = now |
| Drank water | thirst = 0 |
| Slept (8h) | fatigue = 0, last_slept_at = now |
| Said something to someone | social_need -= 15, mood += 5 |
| Was addressed | social_need -= 10, mood += 3 |
| Read book | boredom -= 20 |
| Watched TV | boredom -= 15 |

## Animal Brain: Urgency Check

After updating state, check urgency:

| Condition | Response |
|-----------|----------|
| hunger > 90 | URGENT: find food immediately |
| hunger > 70 | feel hungry, consider going to kitchen |
| fatigue > 85 and hour >= 22 | go to bed |
| fatigue > 95 | go to bed immediately regardless of time |
| boredom > 80 | seek stimulation (go to living room, chat, read) |
| social_need > 75 | feel lonely, want to interact |

Return: `{ "state": {...}, "urgencies": ["hungry", "tired", ...] }`

## Steps

1. Read body_state.json (create with defaults if missing)
2. Apply tick updates or action effects
3. Write updated state back to body_state.json
4. Check urgency thresholds
5. Return summary for rational brain to use
