import type { WorldTime, TimePeriod } from './types.js';
import { getState, advanceClock } from './world-state.js';

const TICK_INTERVAL_MS = 6000;
const WORLD_MINUTES_PER_TICK = 1;

type TickCallback = (worldTime: WorldTime, previousTime: WorldTime) => void;

let tickTimer: ReturnType<typeof setInterval> | null = null;
const tickCallbacks: TickCallback[] = [];

export function onTick(cb: TickCallback): void {
  tickCallbacks.push(cb);
}

export function startClock(): void {
  if (tickTimer) return;

  tickTimer = setInterval(() => {
    const previous = { ...getState().clock };
    advanceClock(WORLD_MINUTES_PER_TICK);
    const current = getState().clock;

    for (const cb of tickCallbacks) {
      cb(current, previous);
    }
  }, TICK_INTERVAL_MS);

  console.log(`[Clock] Started. Tick every ${TICK_INTERVAL_MS / 1000}s = ${WORLD_MINUTES_PER_TICK} world minute(s).`);
}

export function stopClock(): void {
  if (tickTimer) {
    clearInterval(tickTimer);
    tickTimer = null;
  }
}

export function getWorldTime(): WorldTime {
  return { ...getState().clock };
}

export function formatWorldTime(t: WorldTime): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `第${t.day}天 ${pad(t.hour)}:${pad(t.minute)}`;
}

export function getTimePeriod(t: WorldTime): TimePeriod {
  const h = t.hour;
  if (h >= 0 && h <= 5) return 'dawn';
  if (h >= 6 && h <= 10) return 'morning';
  if (h >= 11 && h <= 13) return 'noon';
  if (h >= 14 && h <= 17) return 'afternoon';
  if (h >= 18 && h <= 19) return 'evening';
  return 'night';
}

export function timePeriodName(period: TimePeriod): string {
  const names: Record<TimePeriod, string> = {
    dawn: '凌晨', morning: '早晨', noon: '中午',
    afternoon: '下午', evening: '傍晚', night: '夜晚',
  };
  return names[period];
}

export function advanceWorldTime(worldMinutes: number): WorldTime[] {
  // Returns list of (worldTime, wasNewDay, periodChanged) for fast_forward
  stopClock();
  const checkpoints: WorldTime[] = [];
  const prev = { ...getState().clock };
  advanceClock(worldMinutes);
  checkpoints.push({ ...getState().clock });
  // Restart after caller resolves events
  return checkpoints;
}
