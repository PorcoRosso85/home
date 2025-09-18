/**
 * WebSocket Types
 * WebSocket関連の型定義
 */

import type { TemplateEvent } from "../../event_sourcing/types.ts";

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