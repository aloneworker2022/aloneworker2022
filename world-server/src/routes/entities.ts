import { Router } from 'express';
import crypto from 'crypto';
import type { Entity } from '../types.js';
import { getEntity, addEntity, setEntityOnline } from '../world-state.js';
import { getRoom } from '../world-state.js';

export const entitiesRouter = Router();

entitiesRouter.post('/register', (req, res) => {
  const { id, name, type, webhook_url, webhook_token, start_room } = req.body as Partial<Entity> & { start_room?: string };

  if (!id || !name || !type || !webhook_url || !start_room) {
    res.status(400).json({ accepted: false, reason: 'Missing required fields: id, name, type, webhook_url, start_room' });
    return;
  }

  if (!['agent', 'player_avatar', 'npc'].includes(type)) {
    res.status(400).json({ accepted: false, reason: 'type must be agent, player_avatar, or npc' });
    return;
  }

  if (!getRoom(start_room)) {
    res.status(400).json({ accepted: false, reason: `Room '${start_room}' does not exist` });
    return;
  }

  const existing = getEntity(id);
  if (existing) {
    // Re-registration: update webhook and mark online
    existing.webhook_url = webhook_url;
    existing.webhook_token = webhook_token ?? '';
    setEntityOnline(id, true);
    res.json({ accepted: true, auth_token: existing.auth_token, entity: existing });
    return;
  }

  const auth_token = crypto.randomBytes(32).toString('hex');
  const entity: Entity = {
    id, name, type,
    current_room: start_room,
    current_action: '剛剛到達',
    inventory: [],
    webhook_url,
    webhook_token: webhook_token ?? '',
    auth_token,
    online: true,
  };

  addEntity(entity);
  console.log(`[Entities] Registered: ${name} (${id}) in ${start_room}`);
  res.status(201).json({ accepted: true, auth_token, entity });
});
