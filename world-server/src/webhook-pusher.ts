import type { Entity, PerceptionEvent } from './types.js';

const RETRY_DELAYS_MS = [1000, 2000, 4000];

async function postWithRetry(url: string, token: string, body: object): Promise<boolean> {
  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) return true;
      console.warn(`[Webhook] ${url} responded ${res.status}`);
    } catch (err) {
      console.warn(`[Webhook] ${url} attempt ${attempt + 1} failed: ${(err as Error).message}`);
    }

    if (attempt < RETRY_DELAYS_MS.length) {
      await new Promise(r => setTimeout(r, RETRY_DELAYS_MS[attempt]));
    }
  }
  return false;
}

export async function pushPerception(entity: Entity, perception: PerceptionEvent): Promise<void> {
  if (!entity.webhook_url || !entity.online) return;

  const message = `WORLD_EVENT:${JSON.stringify(perception)}`;
  const body: Record<string, string> = { message, channel: 'world' };
  if (entity.openclaw_agent_id) body['agentId'] = entity.openclaw_agent_id;

  const ok = await postWithRetry(entity.webhook_url, entity.webhook_token, body);
  if (!ok) {
    console.warn(`[Webhook] Entity ${entity.id} appears offline, marking as such`);
  }
}
