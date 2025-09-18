/**
 * Unified Sync Types
 * 統合同期の型定義
 */

import type { TemplateEvent } from "../event_sourcing/types.ts";

// ========== Client Types ==========

export type BrowserKuzuClient = {
  initialize(): Promise<void>;
  initializeFromSnapshot(snapshot: EventSnapshot): Promise<void>;
  executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent>;
  getLocalState(): Promise<LocalState>;
  onRemoteEvent(handler: (event: TemplateEvent) => void): void;
};

export type LocalState = {
  users: Array<{ id: string; name: string; email?: string }>;
  posts: Array<{ id: string; content: string; authorId: string }>;
  follows: Array<{ followerId: string; targetId: string }>;
};

// ========== WebSocket Types ==========

export type WebSocketSync = {
  connect(url: string): Promise<void>;
  sendEvent(event: TemplateEvent): Promise<void>;
  onEvent(handler: (event: TemplateEvent) => void): void;
  disconnect(): void;
  isConnected(): boolean;
  getPendingEvents(): Promise<TemplateEvent[]>;
};

export type WebSocketMessage = {
  type: "event" | "sync" | "error" | "connected";
  payload?: any;
  error?: string;
};

// ========== Server Types ==========

export type ServerEventStore = {
  appendEvent(event: TemplateEvent): Promise<void>;
  getEventsSince(position: number): Promise<TemplateEvent[]>;
  getSnapshot(): EventSnapshot;
  onNewEvent(handler: (event: TemplateEvent) => void): void;
  validateChecksum(event: TemplateEvent): boolean;
};

export type EventSnapshot = {
  events: TemplateEvent[];
  position: number;
  timestamp: number;
};

// ========== Conflict Resolution Types ==========

export type ConflictResolver = {
  resolve(events: TemplateEvent[]): ConflictResolution;
};

export type ConflictResolution = {
  strategy: string;
  winner: TemplateEvent;
  conflicts: TemplateEvent[];
};

// ========== Metrics Types ==========

export type MetricsCollector = {
  startTracking(client: BrowserKuzuClient): void;
  trackEvent(event: TemplateEvent): void;
  getStats(): MetricsStats;
};

export type MetricsStats = {
  totalEvents: number;
  eventTypes: Record<string, number>;
  averageLatency: number;
  errors: number;
};