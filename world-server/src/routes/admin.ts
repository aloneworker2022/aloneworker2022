import { Router } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { getState, setWeather } from '../world-state.js';
import { getWorldTime, formatWorldTime, getTimePeriod, timePeriodName, startClock, advanceWorldTime } from '../clock.js';
import { appendEvent } from '../event-log.js';
import { computePerceptions } from '../perception-filter.js';
import { pushPerception } from '../webhook-pusher.js';
import { scaffoldAgent } from '../scaffold.js';
import type { Weather } from '../types.js';

export const adminRouter = Router();

adminRouter.get('/snapshot', (_req, res) => {
  const state = getState();
  const worldTime = getWorldTime();
  const period = getTimePeriod(worldTime);

  res.json({
    world_time: worldTime,
    time_label: `${timePeriodName(period)} ${formatWorldTime(worldTime)}`,
    environment: state.environment,
    rooms: Object.values(state.rooms).map(room => ({
      id: room.id,
      name: room.name,
      entities: room.current_entities,
      portable_objects: room.current_portable_objects,
      connections: room.connections,
    })),
    entities: Object.values(state.entities).map(e => ({
      id: e.id,
      name: e.name,
      type: e.type,
      room: e.current_room,
      action: e.current_action,
      inventory: e.inventory,
      online: e.online,
    })),
    portable_objects: Object.values(state.portable_objects),
    static_objects: Object.values(state.static_objects),
  });
});

adminRouter.post('/set_weather', (req, res) => {
  const { weather, temperature } = req.body as { weather: Weather; temperature: number };
  if (!weather) { res.status(400).json({ error: 'weather is required' }); return; }
  setWeather(weather, temperature ?? getState().environment.outdoor_temperature);
  res.json({ ok: true });
});

adminRouter.post('/fast_forward', async (req, res) => {
  const { world_minutes } = req.body as { world_minutes: number };
  if (!world_minutes || world_minutes <= 0) {
    res.status(400).json({ error: 'world_minutes must be a positive number' });
    return;
  }

  const fromTime = getWorldTime();
  advanceWorldTime(world_minutes);
  const toTime = getWorldTime();

  const event = {
    event_id: uuidv4(),
    type: 'time_jumped',
    world_time: toTime,
    real_timestamp: new Date().toISOString(),
    actor_id: '__world__',
    actor_room: '__world__',
    payload: { from: fromTime, to: toTime, world_minutes_elapsed: world_minutes },
  };

  appendEvent(event);
  const perceptions = computePerceptions(event);
  await Promise.all(perceptions.map(({ entity, perception }) => pushPerception(entity, perception)));

  startClock();

  res.json({ ok: true, from: fromTime, to: toTime, world_minutes_elapsed: world_minutes });
});

adminRouter.get('/openclaw_agents', (_req, res) => {
  import('fs').then(fs => {
    import('path').then(path => {
      import('os').then(os => {
        const configPath = path.join(os.homedir(), '.openclaw', 'openclaw.json');
        if (!fs.existsSync(configPath)) {
          res.status(404).json({ error: `找不到 ${configPath}` }); return;
        }
        try {
          const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
          const agentsList: { id: string; name: string; workspace: string }[] =
            config?.agents?.list ?? [];

          // Try to extract webhook token from config
          const webhookToken: string =
            config?.hooks?.token ??
            config?.gateway?.token ??
            config?.webhook?.token ??
            '';

          const state = getState();
          const registered = new Set(Object.keys(state.entities));

          res.json({
            agents: agentsList.map(a => ({
              id: a.id,
              name: a.name,
              workspace: a.workspace,
              already_registered: registered.has(a.id),
            })),
            webhook_url: 'http://127.0.0.1:3799/hooks/agent',
            webhook_token: webhookToken,
          });
        } catch (err) {
          res.status(500).json({ error: `讀取失敗：${(err as Error).message}` });
        }
      });
    });
  });
});

adminRouter.get('/body_state/:entity_id', (req, res) => {
  const { entity_id } = req.params;
  const state = getState();
  const entity = state.entities[entity_id];
  if (!entity) { res.status(404).json({ error: 'Entity not found' }); return; }

  // Find workspace path from agents/ folder structure
  import('fs').then(fs => {
    import('path').then(path => {
      const repoRoot = path.resolve(process.cwd(), '..');
      const agentDir = path.join(repoRoot, 'agents', entity_id);
      const bodyStatePath = path.join(agentDir, 'body_state.json');
      if (fs.existsSync(bodyStatePath)) {
        try {
          const data = JSON.parse(fs.readFileSync(bodyStatePath, 'utf8'));
          res.json({ ok: true, entity_id, body_state: data });
        } catch { res.json({ ok: false, reason: 'parse error' }); }
      } else {
        res.json({ ok: false, reason: 'body_state.json not found — agent has not had a tick yet' });
      }
    });
  });
});

adminRouter.post('/scaffold_agent', (req, res) => {
  const { entity_id, name, type, auth_token, world_server_url, workspace_path } = req.body as {
    entity_id: string; name: string; type: string;
    auth_token: string; world_server_url: string; workspace_path?: string;
  };

  if (!entity_id || !name || !type || !auth_token || !world_server_url) {
    res.status(400).json({ error: 'Missing required fields' }); return;
  }

  try {
    const result = scaffoldAgent({
      entity_id, name, auth_token, world_server_url, workspace_path,
      type: type as 'agent' | 'player_avatar' | 'npc',
    });
    res.json({ ok: true, ...result });
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

adminRouter.post('/spawn_object', (req, res) => {
  const { id, name, description, location, affordances, consumable } = req.body as {
    id: string; name: string; description: string;
    location: string; affordances: string[]; consumable: boolean;
  };

  if (!id || !name || !location) {
    res.status(400).json({ error: 'id, name, location are required' });
    return;
  }

  const state = getState();
  if (!state.rooms[location]) {
    res.status(400).json({ error: `Room '${location}' does not exist` });
    return;
  }

  state.portable_objects[id] = {
    id, name,
    description: description ?? '',
    location,
    affordances: affordances ?? [],
    consumable: consumable ?? false,
  };
  state.rooms[location].current_portable_objects.push(id);

  res.status(201).json({ ok: true, object: state.portable_objects[id] });
});
