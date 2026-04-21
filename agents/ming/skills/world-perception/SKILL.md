---
name: world-perception
description: "Triggered when you receive a message starting with 'WORLD_EVENT:'. Process the world event through the three-layer decision system (plant brain → animal brain → rational brain) and decide whether and how to respond."
---

# World Perception Skill

## Step 1: Parse Event

Strip `WORLD_EVENT:` prefix and parse JSON. Extract:
- `perception_type`: you_see / you_hear / addressed_to_you / environment_changed
- `event_type`: move / say / whisper / tick / time_period_changed / etc.
- `world_time`: current world time
- `narrative`: human-readable description

## Step 2: Plant Brain (always run, no LLM)

Call **body-state** skill with the current event to update physiological state.
- tick events → time-based decay
- use events (eat/drink/sleep) → apply effects
- Note the urgencies returned.

## Step 3: Animal Brain (rule-based, no LLM)

Check for automatic responses:

| Situation | Response |
|-----------|----------|
| `addressed_to_you` | MUST respond — escalate to rational brain |
| urgency = "hungry" AND in kitchen | go pick up apple or use apple |
| urgency = "hungry" AND not in kitchen | move to kitchen |
| urgency = "tired" AND hour >= 22 | move to bedroom, use bed (sleep) |
| `you_see` someone enter my room | consider greeting (50% chance) |
| `time_period_changed` to morning | consider going to kitchen for breakfast |
| plain `tick` with no urgencies | do nothing |

If animal brain decides an action, execute it via **world-action** skill and STOP (skip rational brain).

## Step 4: Rational Brain (LLM — only when needed)

Use LLM reasoning when:
- Someone is talking to you (`addressed_to_you`)
- Multiple urgencies conflict
- An interesting situation requires judgment
- You haven't interacted with anyone in > 60 world minutes and someone is present

Prompt yourself with:
1. Current body state summary
2. World event narrative
3. Room context (from world_config or last known state)
4. Question: "What would 小明 naturally do right now?"

Execute the decided action via **world-action** skill.

## Step 5: Cooldown

Don't act more than once every 3 real seconds (enforced by world server).
If an action is rejected with cooldown, wait and don't retry immediately.

## Idle Update

After rational brain decides to stay put and do something, send an `idle_update` action
with a description of what you're doing, so others can see it.
