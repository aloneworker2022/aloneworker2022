export type TimePeriod = 'dawn' | 'morning' | 'noon' | 'afternoon' | 'evening' | 'night';
export type Weather = 'sunny' | 'cloudy' | 'rainy';
export type NoiseLevel = 'quiet' | 'normal' | 'loud';
export type EntityType = 'agent' | 'player_avatar' | 'npc';

export interface WorldTime {
  day: number;
  hour: number;
  minute: number;
}

export interface RoomProperties {
  light: 'bright' | 'dim' | 'dark';
  temperature: number;
  noise: NoiseLevel;
  outdoor: boolean;
}

export interface StaticObject {
  id: string;
  name: string;
  description: string;
  location: string;
  affordances: string[];
}

export interface PortableObject {
  id: string;
  name: string;
  description: string;
  location: string;
  affordances: string[];
  consumable: boolean;
}

export interface Room {
  id: string;
  name: string;
  description: string;
  connections: string[];
  properties: RoomProperties;
  static_objects: string[];
  current_entities: string[];
  current_portable_objects: string[];
}

export interface Entity {
  id: string;
  name: string;
  type: EntityType;
  current_room: string;
  current_action: string;
  inventory: string[];
  webhook_url: string;
  webhook_token: string;
  auth_token: string;
  online: boolean;
}

export interface Environment {
  weather: Weather;
  outdoor_temperature: number;
  outdoor_noise_level: NoiseLevel;
}

export interface WorldState {
  rooms: Record<string, Room>;
  static_objects: Record<string, StaticObject>;
  portable_objects: Record<string, PortableObject>;
  entities: Record<string, Entity>;
  environment: Environment;
  clock: WorldTime;
  started_at: string;
}

export interface WorldEvent {
  event_id: string;
  type: string;
  world_time: WorldTime;
  real_timestamp: string;
  actor_id: string;
  actor_room: string;
  payload: Record<string, unknown>;
}

export interface PerceptionEvent {
  perception_type: string;
  source_event_id: string;
  world_time: WorldTime;
  actor_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  narrative: string;
}

export interface ActionRequest {
  entity_id: string;
  auth_token: string;
  type: string;
  payload: Record<string, unknown>;
}

export interface ActionResult {
  accepted: boolean;
  event_id?: string;
  reason?: string;
}

export type ActionType =
  | 'move'
  | 'say'
  | 'whisper'
  | 'gesture'
  | 'pick_up'
  | 'drop'
  | 'give'
  | 'use'
  | 'idle_update';
