/**
 * Local Sync Server Implementation
 * ローカル同期サーバーの実装
 */

// ========== 型定義 ==========

export interface SyncEvent {
  id: string;
  clientId: string;
  operation: "CREATE" | "UPDATE" | "DELETE";
  data: any;
  timestamp: number;
  vectorClock: Record<string, number>;
}

export interface ConflictResolution {
  type: "CONFLICT" | "NO_CONFLICT";
  winner?: SyncEvent;
  strategy?: string;
}

export interface ServerSnapshot {
  events: SyncEvent[];
  timestamp: number;
}

export interface SyncOptions {
  filter?: (event: SyncEvent) => boolean;
}

export type ConflictResolver = (a: SyncEvent, b: SyncEvent) => SyncEvent;

// ========== Client Class ==========

export class SyncClient {
  private clientId: string;
  private server: LocalSyncServer;
  private vectorClock: Record<string, number> = {};
  private lastSync: number = 0;

  constructor(clientId: string, server: LocalSyncServer) {
    this.clientId = clientId;
    this.server = server;
    this.vectorClock[clientId] = 0;
  }

  send(data: { operation: "CREATE" | "UPDATE" | "DELETE"; data: any }): SyncEvent {
    // Increment own clock
    this.vectorClock[this.clientId]++;
    
    const event: SyncEvent = {
      id: `evt_${crypto.randomUUID()}`,
      clientId: this.clientId,
      operation: data.operation,
      data: data.data,
      timestamp: Date.now(),
      vectorClock: { ...this.vectorClock }
    };

    this.server.appendEvent(event, this.clientId);
    return event;
  }

  async sync(lastSync?: number): Promise<SyncEvent[]> {
    const syncFrom = lastSync || this.lastSync;
    const events = this.server.getEventsSince(syncFrom, this.clientId);
    
    // Update vector clock with received events
    for (const event of events) {
      for (const [clientId, clock] of Object.entries(event.vectorClock)) {
        this.vectorClock[clientId] = Math.max(this.vectorClock[clientId] || 0, clock);
      }
    }
    
    this.lastSync = Date.now();
    return events;
  }

  on(event: string, handler: (data: any) => void): void {
    this.server.addListener(this.clientId, event, handler);
  }

  subscribe(options: SyncOptions): void {
    this.server.subscribeClient(this.clientId, options);
  }

  getVectorClock(): Record<string, number> {
    return { ...this.vectorClock };
  }
}

// ========== Server Class ==========

export class LocalSyncServer {
  private events: SyncEvent[] = [];
  private clients: Map<string, SyncClient> = new Map();
  private conflictStrategy: string = "LAST_WRITE_WINS";
  private conflictResolver?: ConflictResolver;
  private listeners: Map<string, Map<string, (data: any) => void>> = new Map();
  private subscriptions: Map<string, SyncOptions> = new Map();
  private maxMemoryEvents: number = 1000;
  private persistedEvents: SyncEvent[] = [];

  connect(clientId: string): SyncClient {
    const client = new SyncClient(clientId, this);
    this.clients.set(clientId, client);
    return client;
  }

  appendEvent(event: SyncEvent, senderId: string): void {
    this.events.push(event);
    
    // Memory management
    if (this.events.length > this.maxMemoryEvents) {
      const toPersist = this.events.splice(0, this.events.length - this.maxMemoryEvents);
      this.persistedEvents.push(...toPersist);
    }
    
    // Notify other clients
    this.notifyClients(event, senderId);
  }

  getEventsSince(timestamp: number, clientId: string): SyncEvent[] {
    const allEvents = [...this.persistedEvents, ...this.events];
    const subscription = this.subscriptions.get(clientId);
    
    let events = allEvents.filter(e => 
      e.timestamp > timestamp && e.clientId !== clientId
    );
    
    if (subscription?.filter) {
      events = events.filter(subscription.filter);
    }
    
    return events;
  }

  detectConflicts(events: SyncEvent[]): ConflictResolution[] {
    const conflicts: ConflictResolution[] = [];
    const eventsByTarget = new Map<string, SyncEvent[]>();
    
    // Group events by target
    for (const event of events) {
      const targetId = event.data?.id || event.data?.targetId;
      if (targetId) {
        const existing = eventsByTarget.get(targetId) || [];
        existing.push(event);
        eventsByTarget.set(targetId, existing);
      }
    }
    
    // Find conflicts
    for (const [targetId, targetEvents] of eventsByTarget) {
      if (targetEvents.length > 1) {
        // Check for concurrent updates
        for (let i = 0; i < targetEvents.length - 1; i++) {
          for (let j = i + 1; j < targetEvents.length; j++) {
            const a = targetEvents[i];
            const b = targetEvents[j];
            
            // Events are concurrent if neither happens-before the other
            if (!this.happensBefore(a.vectorClock, b.vectorClock) &&
                !this.happensBefore(b.vectorClock, a.vectorClock)) {
              conflicts.push({
                type: "CONFLICT",
                winner: this.resolveConflict(a, b),
                strategy: this.conflictStrategy
              });
            }
          }
        }
      }
    }
    
    return conflicts;
  }

  private happensBefore(a: Record<string, number>, b: Record<string, number>): boolean {
    let lessThanOrEqual = true;
    let strictlyLess = false;
    
    for (const clientId of new Set([...Object.keys(a), ...Object.keys(b)])) {
      const aVal = a[clientId] || 0;
      const bVal = b[clientId] || 0;
      
      if (aVal > bVal) {
        lessThanOrEqual = false;
        break;
      }
      if (aVal < bVal) {
        strictlyLess = true;
      }
    }
    
    return lessThanOrEqual && strictlyLess;
  }

  resolveConflict(a: SyncEvent, b: SyncEvent): SyncEvent {
    if (this.conflictResolver) {
      return this.conflictResolver(a, b);
    }
    
    // Default: Last Write Wins
    return a.timestamp > b.timestamp ? a : b;
  }

  setConflictStrategy(strategy: string): void {
    this.conflictStrategy = strategy;
  }

  setConflictResolver(resolver: ConflictResolver): void {
    this.conflictResolver = resolver;
  }

  createSnapshot(): ServerSnapshot {
    return {
      events: [...this.events],
      timestamp: Date.now()
    };
  }

  private notifyClients(event: SyncEvent, senderId: string): void {
    for (const [clientId, listeners] of this.listeners) {
      if (clientId !== senderId) {
        // Notify all event types
        for (const [eventType, handler] of listeners) {
          if (eventType === "event" || eventType === "sync") {
            handler(event);
          }
        }
      }
    }
  }

  addListener(clientId: string, event: string, handler: (data: any) => void): void {
    if (!this.listeners.has(clientId)) {
      this.listeners.set(clientId, new Map());
    }
    this.listeners.get(clientId)!.set(event, handler);
  }

  subscribeClient(clientId: string, options: SyncOptions): void {
    this.subscriptions.set(clientId, options);
  }

  sendBatch(events: SyncEvent[]): void {
    const start = Date.now();
    
    for (const event of events) {
      this.events.push(event);
    }
    
    const duration = Date.now() - start;
    if (duration > 100) {
      console.warn(`Batch processing took ${duration}ms`);
    }
  }

  getAllEvents(): SyncEvent[] {
    return [...this.persistedEvents, ...this.events];
  }

  setMaxMemoryEvents(max: number): void {
    this.maxMemoryEvents = max;
  }

  validateEvent(event: any): void {
    if (!event.operation || !["CREATE", "UPDATE", "DELETE"].includes(event.operation)) {
      throw new Error("Invalid operation type");
    }
    
    if (!event.data) {
      throw new Error("Event data is required");
    }
  }

  async syncWithTimeout(clientId: string, timeout: number): Promise<SyncEvent[]> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error("Sync timeout"));
      }, timeout);
      
      // Simulate some delay
      setTimeout(() => {
        clearTimeout(timer);
        const client = this.clients.get(clientId);
        if (client) {
          client.sync().then(resolve).catch(reject);
        } else {
          reject(new Error("Client not found"));
        }
      }, timeout > 50 ? 50 : 0);
    });
  }

  setSyncDelay(delay: number): void {
    // This would be used in a real implementation to simulate network delays
    // For now, it's a no-op
  }
}