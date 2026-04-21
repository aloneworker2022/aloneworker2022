import { v4 as uuidv4 } from 'uuid';
import type { ActionRequest, ActionResult, WorldEvent } from './types.js';
import {
  getState, getEntity, getRoom, getPortableObject,
  moveEntity, updateEntityAction, pickUpObject,
  dropObject, consumeObject, giveObject,
} from './world-state.js';
import { getWorldTime } from './clock.js';
import { appendEvent } from './event-log.js';
import { computePerceptions } from './perception-filter.js';
import { pushPerception } from './webhook-pusher.js';

function makeEvent(type: string, actorId: string, actorRoom: string, payload: Record<string, unknown>): WorldEvent {
  return {
    event_id: uuidv4(),
    type,
    world_time: getWorldTime(),
    real_timestamp: new Date().toISOString(),
    actor_id: actorId,
    actor_room: actorRoom,
    payload,
  };
}

async function dispatchEvent(event: WorldEvent): Promise<void> {
  appendEvent(event);
  const targets = computePerceptions(event);
  await Promise.all(targets.map(({ entity, perception }) => pushPerception(entity, perception)));
}

function validateAuth(req: ActionRequest): string | null {
  const entity = getEntity(req.entity_id);
  if (!entity) return 'Entity not found';
  if (entity.auth_token !== req.auth_token) return 'Invalid auth token';
  return null;
}

export async function processAction(req: ActionRequest): Promise<ActionResult> {
  const authErr = validateAuth(req);
  if (authErr) return { accepted: false, reason: authErr };

  const entity = getEntity(req.entity_id)!;
  const actorRoom = entity.current_room;

  switch (req.type) {
    case 'move': {
      const toRoomId = req.payload['to_room'] as string;
      const currentRoom = getRoom(actorRoom);
      if (!currentRoom) return { accepted: false, reason: 'Current room not found' };
      if (!getRoom(toRoomId)) return { accepted: false, reason: 'Target room does not exist' };
      if (!currentRoom.connections.includes(toRoomId)) {
        return { accepted: false, reason: 'Rooms are not connected' };
      }

      const event = makeEvent('move', entity.id, actorRoom, { from_room: actorRoom, to_room: toRoomId });
      moveEntity(entity.id, toRoomId);
      await dispatchEvent(event);
      return { accepted: true, event_id: event.event_id };
    }

    case 'say': {
      const content = req.payload['content'] as string;
      if (!content?.trim()) return { accepted: false, reason: 'Content is required' };
      const event = makeEvent('say', entity.id, actorRoom, { content });
      await dispatchEvent(event);
      return { accepted: true, event_id: event.event_id };
    }

    case 'whisper': {
      const targetId = req.payload['target'] as string;
      const content = req.payload['content'] as string;
      if (!content?.trim()) return { accepted: false, reason: 'Content is required' };
      const target = getEntity(targetId);
      if (!target) return { accepted: false, reason: 'Target entity not found' };
      if (target.current_room !== actorRoom) return { accepted: false, reason: 'Target is not in the same room' };
      const event = makeEvent('whisper', entity.id, actorRoom, { target: targetId, content });
      await dispatchEvent(event);
      return { accepted: true, event_id: event.event_id };
    }

    case 'gesture': {
      const action = req.payload['action'] as string;
      const targetId = req.payload['target'] as string | undefined;
      if (targetId) {
        const target = getEntity(targetId);
        if (!target || target.current_room !== actorRoom) {
          return { accepted: false, reason: 'Target is not in the same room' };
        }
      }
      const event = makeEvent('gesture', entity.id, actorRoom, { action, target: targetId });
      await dispatchEvent(event);
      return { accepted: true, event_id: event.event_id };
    }

    case 'pick_up': {
      const objectId = req.payload['object_id'] as string;
      const room = getRoom(actorRoom);
      const obj = getPortableObject(objectId);
      if (!obj) return { accepted: false, reason: 'Object not found' };
      if (!room?.current_portable_objects.includes(objectId)) {
        return { accepted: false, reason: 'Object is not in your room' };
      }
      const event = makeEvent('pick_up', entity.id, actorRoom, { object_id: objectId });
      pickUpObject(entity.id, objectId);
      await dispatchEvent(event);
      return { accepted: true, event_id: event.event_id };
    }

    case 'drop': {
      const objectId = req.payload['object_id'] as string;
      if (!entity.inventory.includes(objectId)) {
        return { accepted: false, reason: 'Object is not in your inventory' };
      }
      const event = makeEvent('drop', entity.id, actorRoom, { object_id: objectId });
      dropObject(entity.id, objectId);
      await dispatchEvent(event);
      return { accepted: true, event_id: event.event_id };
    }

    case 'give': {
      const objectId = req.payload['object_id'] as string;
      const targetId = req.payload['target'] as string;
      if (!entity.inventory.includes(objectId)) {
        return { accepted: false, reason: 'Object is not in your inventory' };
      }
      const target = getEntity(targetId);
      if (!target) return { accepted: false, reason: 'Target entity not found' };
      if (target.current_room !== actorRoom) return { accepted: false, reason: 'Target is not in the same room' };
      const event = makeEvent('give', entity.id, actorRoom, { object_id: objectId, target: targetId });
      giveObject(entity.id, targetId, objectId);
      await dispatchEvent(event);
      return { accepted: true, event_id: event.event_id };
    }

    case 'use': {
      const objectId = req.payload['object_id'] as string;
      const state = getState();
      const portableObj = state.portable_objects[objectId];
      const staticObj = state.static_objects[objectId];

      if (!portableObj && !staticObj) return { accepted: false, reason: 'Object not found' };

      if (portableObj) {
        const inInventory = entity.inventory.includes(objectId);
        const inRoom = getRoom(actorRoom)?.current_portable_objects.includes(objectId);
        if (!inInventory && !inRoom) return { accepted: false, reason: 'Object is not accessible' };

        const event = makeEvent('use', entity.id, actorRoom, { object_id: objectId, object_name: portableObj.name });

        if (portableObj.consumable) {
          consumeObject(objectId, entity.id);
          event.payload['consumed'] = true;
        }
        await dispatchEvent(event);
      } else {
        if (staticObj.location !== actorRoom) return { accepted: false, reason: 'Object is not in your room' };
        const event = makeEvent('use', entity.id, actorRoom, { object_id: objectId, object_name: staticObj.name });
        updateEntityAction(entity.id, `使用${staticObj.name}`);
        await dispatchEvent(event);
      }
      return { accepted: true };
    }

    case 'idle_update': {
      const description = req.payload['description'] as string;
      if (!description?.trim()) return { accepted: false, reason: 'Description is required' };
      updateEntityAction(entity.id, description);
      const event = makeEvent('idle_update', entity.id, actorRoom, { description });
      await dispatchEvent(event);
      return { accepted: true, event_id: event.event_id };
    }

    default:
      return { accepted: false, reason: `Unknown action type: ${req.type}` };
  }
}

export async function emitSystemEvent(
  type: string,
  payload: Record<string, unknown>,
  actorRoom = '__world__'
): Promise<WorldEvent> {
  const event = makeEvent(type, '__world__', actorRoom, payload);
  await dispatchEvent(event);
  return event;
}
