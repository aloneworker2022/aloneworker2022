import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import type { WorldState, Entity, Room, PortableObject } from './types.js';
import { createInitialWorldState } from './world-init.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, '..', 'data');
const STATE_FILE = path.join(DATA_DIR, 'world-state.json');
const STATE_TMP = path.join(DATA_DIR, 'world-state.tmp.json');

let state: WorldState;

export function loadState(): WorldState {
  fs.mkdirSync(DATA_DIR, { recursive: true });

  if (fs.existsSync(STATE_FILE)) {
    const raw = fs.readFileSync(STATE_FILE, 'utf-8');
    state = JSON.parse(raw) as WorldState;
  } else {
    state = createInitialWorldState();
    saveState();
  }
  return state;
}

export function saveState(): void {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(STATE_TMP, JSON.stringify(state, null, 2), 'utf-8');
  fs.renameSync(STATE_TMP, STATE_FILE);
}

export function getState(): WorldState {
  return state;
}

export function getRoom(roomId: string): Room | undefined {
  return state.rooms[roomId];
}

export function getEntity(entityId: string): Entity | undefined {
  return state.entities[entityId];
}

export function getPortableObject(objectId: string): PortableObject | undefined {
  return state.portable_objects[objectId];
}

export function addEntity(entity: Entity): void {
  state.entities[entity.id] = entity;

  const room = state.rooms[entity.current_room];
  if (room && !room.current_entities.includes(entity.id)) {
    room.current_entities.push(entity.id);
  }
  saveState();
}

export function moveEntity(entityId: string, toRoomId: string): void {
  const entity = state.entities[entityId];
  if (!entity) return;

  const fromRoom = state.rooms[entity.current_room];
  if (fromRoom) {
    fromRoom.current_entities = fromRoom.current_entities.filter(id => id !== entityId);
  }

  const toRoom = state.rooms[toRoomId];
  if (toRoom && !toRoom.current_entities.includes(entityId)) {
    toRoom.current_entities.push(entityId);
  }

  entity.current_room = toRoomId;
  saveState();
}

export function updateEntityAction(entityId: string, action: string): void {
  const entity = state.entities[entityId];
  if (!entity) return;
  entity.current_action = action;
  saveState();
}

export function setEntityOnline(entityId: string, online: boolean): void {
  const entity = state.entities[entityId];
  if (!entity) return;
  entity.online = online;
  saveState();
}

export function pickUpObject(entityId: string, objectId: string): void {
  const entity = state.entities[entityId];
  const obj = state.portable_objects[objectId];
  if (!entity || !obj) return;

  const room = state.rooms[entity.current_room];
  if (room) {
    room.current_portable_objects = room.current_portable_objects.filter(id => id !== objectId);
  }

  obj.location = entityId;
  if (!entity.inventory.includes(objectId)) {
    entity.inventory.push(objectId);
  }
  saveState();
}

export function dropObject(entityId: string, objectId: string): void {
  const entity = state.entities[entityId];
  const obj = state.portable_objects[objectId];
  if (!entity || !obj) return;

  entity.inventory = entity.inventory.filter(id => id !== objectId);
  obj.location = entity.current_room;

  const room = state.rooms[entity.current_room];
  if (room && !room.current_portable_objects.includes(objectId)) {
    room.current_portable_objects.push(objectId);
  }
  saveState();
}

export function consumeObject(objectId: string, holderEntityId: string): void {
  const obj = state.portable_objects[objectId];
  if (!obj || !obj.consumable) return;

  const entity = state.entities[holderEntityId];
  if (entity) {
    entity.inventory = entity.inventory.filter(id => id !== objectId);
  }

  const room = state.rooms[obj.location];
  if (room) {
    room.current_portable_objects = room.current_portable_objects.filter(id => id !== objectId);
  }

  delete state.portable_objects[objectId];
  saveState();
}

export function giveObject(fromEntityId: string, toEntityId: string, objectId: string): void {
  const from = state.entities[fromEntityId];
  const to = state.entities[toEntityId];
  const obj = state.portable_objects[objectId];
  if (!from || !to || !obj) return;

  from.inventory = from.inventory.filter(id => id !== objectId);
  obj.location = toEntityId;
  if (!to.inventory.includes(objectId)) {
    to.inventory.push(objectId);
  }
  saveState();
}

export function advanceClock(minutes: number): void {
  let total = state.clock.day * 24 * 60 + state.clock.hour * 60 + state.clock.minute + minutes;
  state.clock.day = Math.floor(total / (24 * 60));
  total = total % (24 * 60);
  state.clock.hour = Math.floor(total / 60);
  state.clock.minute = total % 60;
  saveState();
}

export function setWeather(weather: WorldState['environment']['weather'], temperature: number): void {
  state.environment.weather = weather;
  state.environment.outdoor_temperature = temperature;
  saveState();
}
