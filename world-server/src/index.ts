import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import { loadState, getState } from './world-state.js';
import { startClock, onTick, getTimePeriod, timePeriodName, formatWorldTime } from './clock.js';
import { initEventLog, appendEvent } from './event-log.js';
import { computePerceptions } from './perception-filter.js';
import { pushPerception } from './webhook-pusher.js';
import { actionsRouter } from './routes/actions.js';
import { entitiesRouter } from './routes/entities.js';
import { stateRouter } from './routes/state.js';
import { adminRouter } from './routes/admin.js';
import type { WorldTime, WorldEvent } from './types.js';

const PORT = parseInt(process.env['PORT'] ?? '3000', 10);

// Boot
const state = loadState();
initEventLog(state.clock.day);
console.log(`[World] Loaded. Current time: ${formatWorldTime(state.clock)}`);

// Express
const app = express();
app.use(express.json());

app.use('/api/actions', actionsRouter);
app.use('/api/entities', entitiesRouter);
app.use('/api/state', stateRouter);
app.use('/api/history', stateRouter);  // stateRouter also handles /history
app.use('/api/admin', adminRouter);

app.get('/health', (_req, res) => res.json({ ok: true }));

// Tick handler
let previousPeriod = getTimePeriod(state.clock);

onTick(async (worldTime: WorldTime, previousTime: WorldTime) => {
  const tickEvent: WorldEvent = {
    event_id: uuidv4(),
    type: 'tick',
    world_time: worldTime,
    real_timestamp: new Date().toISOString(),
    actor_id: '__world__',
    actor_room: '__world__',
    payload: { previous_time: previousTime },
  };
  appendEvent(tickEvent);
  const tickPerceptions = computePerceptions(tickEvent);
  await Promise.all(tickPerceptions.map(({ entity, perception }) => pushPerception(entity, perception)));

  // Check time period change
  const currentPeriod = getTimePeriod(worldTime);
  if (currentPeriod !== previousPeriod) {
    previousPeriod = currentPeriod;
    const periodEvent: WorldEvent = {
      event_id: uuidv4(),
      type: 'time_period_changed',
      world_time: worldTime,
      real_timestamp: new Date().toISOString(),
      actor_id: '__world__',
      actor_room: '__world__',
      payload: { period: currentPeriod, period_name: timePeriodName(currentPeriod) },
    };
    appendEvent(periodEvent);
    const periodPerceptions = computePerceptions(periodEvent);
    await Promise.all(periodPerceptions.map(({ entity, perception }) => pushPerception(entity, perception)));
    console.log(`[Clock] Time period: ${timePeriodName(currentPeriod)} (${formatWorldTime(worldTime)})`);
  }

  // Check day change
  if (worldTime.day !== previousTime.day) {
    initEventLog(worldTime.day);
    const dayEvent: WorldEvent = {
      event_id: uuidv4(),
      type: 'day_changed',
      world_time: worldTime,
      real_timestamp: new Date().toISOString(),
      actor_id: '__world__',
      actor_room: '__world__',
      payload: { day: worldTime.day },
    };
    appendEvent(dayEvent);
    const dayPerceptions = computePerceptions(dayEvent);
    await Promise.all(dayPerceptions.map(({ entity, perception }) => pushPerception(entity, perception)));
    console.log(`[Clock] Day ${worldTime.day} begins.`);
  }
});

app.listen(PORT, '127.0.0.1', () => {
  console.log(`[World] Server started on http://127.0.0.1:${PORT}`);
  startClock();
  console.log(`[World] Clock started. ${Object.keys(getState().entities).length} entities registered.`);
});
