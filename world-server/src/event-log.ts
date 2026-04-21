import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import type { WorldEvent } from './types.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, '..', 'data');
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB

const recentEvents: WorldEvent[] = [];
const MAX_RECENT = 1000;

let currentDay = 1;
let currentLogFile = '';
let currentPartIndex = 1;

function getLogFilePath(day: number, part: number): string {
  return part === 1
    ? path.join(DATA_DIR, `world_log_day_${day}.jsonl`)
    : path.join(DATA_DIR, `world_log_day_${day}_part_${part}.jsonl`);
}

function getCurrentLogSize(): number {
  try {
    return fs.statSync(currentLogFile).size;
  } catch {
    return 0;
  }
}

export function initEventLog(day: number): void {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  currentDay = day;
  currentPartIndex = 1;
  currentLogFile = getLogFilePath(day, 1);

  // Find existing part files and continue from the last one
  while (fs.existsSync(currentLogFile) && getCurrentLogSize() >= MAX_FILE_SIZE_BYTES) {
    currentPartIndex++;
    currentLogFile = getLogFilePath(day, currentPartIndex);
  }

  // Load recent events from current file into memory cache
  if (fs.existsSync(currentLogFile)) {
    const lines = fs.readFileSync(currentLogFile, 'utf-8').trim().split('\n').filter(Boolean);
    const last = lines.slice(-MAX_RECENT);
    for (const line of last) {
      try { recentEvents.push(JSON.parse(line) as WorldEvent); } catch { /* skip */ }
    }
  }
}

export function appendEvent(event: WorldEvent): void {
  // Rotate if needed
  if (getCurrentLogSize() >= MAX_FILE_SIZE_BYTES) {
    currentPartIndex++;
    currentLogFile = getLogFilePath(currentDay, currentPartIndex);
  }

  // Handle day rollover
  if (event.world_time.day !== currentDay) {
    currentDay = event.world_time.day;
    currentPartIndex = 1;
    currentLogFile = getLogFilePath(currentDay, 1);
  }

  fs.appendFileSync(currentLogFile, JSON.stringify(event) + '\n', 'utf-8');

  recentEvents.push(event);
  if (recentEvents.length > MAX_RECENT) {
    recentEvents.shift();
  }
}

export interface QueryOptions {
  entity_id?: string;
  since?: string;
  limit?: number;
}

export function queryEvents(opts: QueryOptions): WorldEvent[] {
  const { entity_id, since, limit = 50 } = opts;

  let events = [...recentEvents];

  if (since) {
    const idx = events.findIndex(e => e.event_id === since);
    if (idx !== -1) {
      events = events.slice(idx + 1);
    } else {
      // since event not in cache; filter by real_timestamp
      events = events.filter(e => e.real_timestamp > since);
    }
  }

  if (entity_id) {
    events = events.filter(e =>
      e.actor_id === entity_id ||
      (e.payload['target'] === entity_id) ||
      (e.payload['perceived_by'] as string[] | undefined)?.includes(entity_id)
    );
  }

  return events.slice(-limit);
}
