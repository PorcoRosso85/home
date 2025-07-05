/**
 * Local Sync Types
 * ローカル同期の型定義
 */

// ========== Event Types ==========

export type SyncEvent = {
  id: string;
  clientId: string;
  operation: "CREATE" | "UPDATE" | "DELETE";
  data: any;
  timestamp: number;
  vectorClock: Record<string, number>;
};

export type ConflictResolution = {
  type: "CONFLICT" | "NO_CONFLICT";
  winner?: SyncEvent;
  strategy?: string;
};

export type ServerSnapshot = {
  events: SyncEvent[];
  timestamp: number;
};

export type SyncOptions = {
  filter?: (event: SyncEvent) => boolean;
};

// ========== Function Types ==========

export type ConflictResolver = (a: SyncEvent, b: SyncEvent) => SyncEvent;

export type EventHandler = (data: any) => void;