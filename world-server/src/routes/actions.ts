import { Router } from 'express';
import type { ActionRequest } from '../types.js';
import { enqueueAction } from '../action-queue.js';

export const actionsRouter = Router();

// Cooldown: minimum ms between accepted actions per entity
const COOLDOWN_MS = 3000;
const lastActionAt = new Map<string, number>();

actionsRouter.post('/', async (req, res) => {
  const body = req.body as Partial<ActionRequest>;

  if (!body.entity_id || !body.auth_token || !body.type) {
    res.status(400).json({ accepted: false, reason: 'Missing required fields: entity_id, auth_token, type' });
    return;
  }

  const actionReq: ActionRequest = {
    entity_id: body.entity_id,
    auth_token: body.auth_token,
    type: body.type,
    payload: body.payload ?? {},
  };

  const now = Date.now();
  const last = lastActionAt.get(actionReq.entity_id) ?? 0;
  if (now - last < COOLDOWN_MS && actionReq.type !== 'idle_update') {
    const waitMs = COOLDOWN_MS - (now - last);
    res.status(429).json({ accepted: false, reason: `Cooldown active, wait ${waitMs}ms` });
    return;
  }

  const result = await enqueueAction(actionReq);

  if (result.accepted) {
    lastActionAt.set(actionReq.entity_id, Date.now());
  }

  res.status(result.accepted ? 200 : 422).json(result);
});
