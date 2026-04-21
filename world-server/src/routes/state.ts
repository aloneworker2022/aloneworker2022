import { Router } from 'express';
import { getState, getEntity, getRoom } from '../world-state.js';
import { queryEvents } from '../event-log.js';
import { getWorldTime, formatWorldTime, getTimePeriod, timePeriodName } from '../clock.js';

export const stateRouter = Router();

stateRouter.get('/me', (req, res) => {
  const { entity_id, auth_token } = req.query as Record<string, string>;

  if (!entity_id) {
    res.status(400).json({ error: 'entity_id is required' });
    return;
  }

  const entity = getEntity(entity_id);
  if (!entity) {
    res.status(404).json({ error: 'Entity not found' });
    return;
  }
  if (auth_token && entity.auth_token !== auth_token) {
    res.status(403).json({ error: 'Invalid auth token' });
    return;
  }

  const state = getState();
  const room = getRoom(entity.current_room)!;
  const worldTime = getWorldTime();
  const period = getTimePeriod(worldTime);

  const inventoryDetails = entity.inventory.map(id => state.portable_objects[id]).filter(Boolean);
  const roomEntities = room.current_entities
    .filter(id => id !== entity_id)
    .map(id => {
      const e = state.entities[id];
      return e ? { id: e.id, name: e.name, current_action: e.current_action } : null;
    })
    .filter(Boolean);
  const roomObjects = room.current_portable_objects
    .map(id => state.portable_objects[id])
    .filter(Boolean);
  const staticObjects = room.static_objects
    .map(id => state.static_objects[id])
    .filter(Boolean);
  const exits = room.connections.map(id => ({ id, name: state.rooms[id]?.name ?? id }));

  res.json({
    entity: {
      id: entity.id,
      name: entity.name,
      type: entity.type,
      current_action: entity.current_action,
      inventory: inventoryDetails,
    },
    room: {
      id: room.id,
      name: room.name,
      description: room.description,
      properties: room.properties,
      entities_present: roomEntities,
      portable_objects: roomObjects,
      static_objects: staticObjects,
      exits,
    },
    world_time: worldTime,
    time_label: `${timePeriodName(period)} ${formatWorldTime(worldTime)}`,
    environment: state.environment,
  });
});

stateRouter.get('/history', (req, res) => {
  const { entity_id, since, limit } = req.query as Record<string, string>;

  const events = queryEvents({
    entity_id: entity_id || undefined,
    since: since || undefined,
    limit: limit ? parseInt(limit, 10) : 50,
  });

  res.json({ events, count: events.length });
});
