/**
 * Unified KuzuDB Sync Client Interface
 * Works with Bun runtime
 */

export interface SyncClientOptions {
  clientId?: string;
  dbPath?: string;
  wsUrl?: string;
}

export interface SyncEvent {
  id: string;
  template: string;
  params: any;
  timestamp: number;
  synced: boolean;
  clientId?: string;
}

export interface ISyncClient {
  // Lifecycle
  initialize(): Promise<void>;
  connect(url?: string): Promise<void>;
  close(): void;
  
  // Event operations
  sendEvent(template: string, params: any): Promise<void>;
  getLocalEvents(limit?: number): Promise<SyncEvent[]>;
  getUnsyncedEvents(limit?: number): Promise<SyncEvent[]>;
  markEventSynced(eventId: string): Promise<void>;
  
  // Sync operations
  syncPendingEvents(): Promise<void>;
}

/**
 * Creates a sync client for Bun runtime
 */
export async function createSyncClient(options?: SyncClientOptions): Promise<ISyncClient> {
  const { KuzuSyncClient } = await import("./bun_client.ts");
  return new KuzuSyncClient(options);
}

/**
 * Result type for error handling
 */
export type Result<T, E = Error> = 
  | { ok: true; value: T }
  | { ok: false; error: E };

/**
 * Helper to create Result types
 */
export const Result = {
  ok<T>(value: T): Result<T> {
    return { ok: true, value };
  },
  
  err<E = Error>(error: E): Result<never, E> {
    return { ok: false, error };
  }
};

/**
 * Wraps async operations in Result type
 */
export async function tryCatch<T>(
  fn: () => Promise<T>
): Promise<Result<T>> {
  try {
    const value = await fn();
    return Result.ok(value);
  } catch (error) {
    return Result.err(error as Error);
  }
}