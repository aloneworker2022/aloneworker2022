import type { WorldEvent, PerceptionEvent, Entity } from './types.js';
import { getState, getRoom } from './world-state.js';
import { formatWorldTime } from './clock.js';

interface PerceptionTarget {
  entity: Entity;
  perception: PerceptionEvent;
}

function buildNarrative(event: WorldEvent, perceiverRoom: string): string {
  const state = getState();
  const actor = state.entities[event.actor_id];
  const actorName = actor?.name ?? event.actor_id;

  switch (event.type) {
    case 'move': {
      const toRoom = state.rooms[event.payload['to_room'] as string];
      const fromRoom = state.rooms[event.payload['from_room'] as string];
      if (perceiverRoom === event.payload['to_room']) {
        return `${actorName}從${fromRoom?.name ?? '某處'}走了進來。`;
      }
      return `${actorName}走向了${toRoom?.name ?? '某處'}。`;
    }
    case 'say':
      return `${actorName}說：「${event.payload['content'] as string}」`;
    case 'whisper':
      return `${actorName}低聲對${(state.entities[event.payload['target'] as string]?.name ?? event.payload['target'] as string)}說了些什麼，你聽不清楚。`;
    case 'gesture': {
      const target = event.payload['target'] as string | undefined;
      const targetName = target ? (state.entities[target]?.name ?? target) : '';
      return target
        ? `${actorName}向${targetName}做了個動作：${event.payload['action'] as string}。`
        : `${actorName}做了個動作：${event.payload['action'] as string}。`;
    }
    case 'pick_up': {
      const obj = state.portable_objects[event.payload['object_id'] as string];
      return `${actorName}撿起了${obj?.name ?? '某個物品'}。`;
    }
    case 'drop': {
      const obj = state.portable_objects[event.payload['object_id'] as string];
      return `${actorName}放下了${obj?.name ?? '某個物品'}。`;
    }
    case 'give': {
      const obj = state.portable_objects[event.payload['object_id'] as string];
      const target = state.entities[event.payload['target'] as string];
      return `${actorName}把${obj?.name ?? '某個物品'}交給了${target?.name ?? '某人'}。`;
    }
    case 'use': {
      const obj = state.portable_objects[event.payload['object_id'] as string]
        ?? state.static_objects[event.payload['object_id'] as string];
      return `${actorName}正在使用${obj?.name ?? '某個物品'}。`;
    }
    case 'idle_update':
      return `${actorName}現在正在：${event.payload['description'] as string}`;
    case 'tick':
      return `時間流逝：${formatWorldTime(event.world_time)}`;
    case 'time_period_changed':
      return `時段轉換：${event.payload['period_name'] as string}`;
    case 'day_changed':
      return `新的一天開始了（第${event.world_time.day}天）。`;
    case 'weather_changed':
      return `天氣變化：${event.payload['weather'] as string}`;
    case 'time_jumped':
      return `時間快轉了${event.payload['world_minutes_elapsed'] as number}分鐘。`;
    default:
      return `${actorName}做了某件事。`;
  }
}

export function computePerceptions(event: WorldEvent): PerceptionTarget[] {
  const state = getState();
  const results: PerceptionTarget[] = [];
  const actorRoom = event.actor_room;

  for (const entity of Object.values(state.entities)) {
    if (entity.id === event.actor_id) continue;
    if (!entity.online && !['tick', 'time_period_changed', 'day_changed'].includes(event.type)) continue;

    // tick events only go to non-player agents (for body state updates)
    // player_avatar only gets meaningful time events, not every minute tick
    if (event.type === 'tick' && entity.type === 'player_avatar') continue;

    const entityRoom = entity.current_room;
    const actorRoomData = getRoom(actorRoom);
    const sameRoom = entityRoom === actorRoom;
    const adjacent = actorRoomData?.connections.includes(entityRoom) ?? false;

    let perceptionType: string | null = null;

    if (event.type === 'tick' || event.type === 'time_period_changed' || event.type === 'day_changed' || event.type === 'weather_changed' || event.type === 'time_jumped') {
      perceptionType = 'environment_changed';
    } else if (event.type === 'whisper') {
      const target = event.payload['target'] as string;
      if (entity.id === target) {
        perceptionType = 'addressed_to_you';
      } else if (sameRoom) {
        // Others in same room get a vague "you_hear"
        perceptionType = 'you_hear';
      }
    } else if (sameRoom) {
      perceptionType = event.type === 'say' ? 'you_hear' : 'you_see';
      if (event.payload['target'] === entity.id) {
        perceptionType = 'addressed_to_you';
      }
    } else if (adjacent && event.type === 'say') {
      // Muffled sound from adjacent room
      perceptionType = 'you_hear';
    }

    if (!perceptionType) continue;

    const narrative = buildNarrative(event, entityRoom);

    const perception: PerceptionEvent = {
      perception_type: perceptionType,
      source_event_id: event.event_id,
      world_time: event.world_time,
      actor_id: event.actor_id,
      event_type: event.type,
      payload: event.type === 'whisper' && entity.id !== event.payload['target']
        ? { ...event.payload, content: undefined }
        : event.payload,
      narrative,
    };

    results.push({ entity, perception });
  }

  return results;
}
