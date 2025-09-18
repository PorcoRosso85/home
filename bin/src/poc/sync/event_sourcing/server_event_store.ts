/**
 * Server Event Store
 * サーバー側のイベント保存と配信機能
 */

export interface StoredEvent {
  id: string;
  template: string;
  params: Record<string, any>;
  timestamp: number;
  clientId?: string;
  checksum?: string;
  position: number;
}

export class ServerEventStore {
  private events: StoredEvent[] = [];
  private subscribers = new Map<string, (event: StoredEvent) => void>();

  async appendEvent(event: Omit<StoredEvent, 'position'>): Promise<StoredEvent> {
    // Validate event
    if (!event.id || !event.template || !event.params || !event.timestamp) {
      throw new Error("Invalid event format");
    }

    // Store with position
    const storedEvent: StoredEvent = {
      ...event,
      position: this.events.length + 1
    };
    
    this.events.push(storedEvent);
    
    // Broadcast to subscribers
    this.broadcast(storedEvent, event.clientId);
    
    return storedEvent;
  }

  getEventsSince(position: number): StoredEvent[] {
    return this.events.filter(e => e.position > position);
  }

  getLatestEvents(count: number): StoredEvent[] {
    return this.events.slice(-count);
  }

  getEventCount(): number {
    return this.events.length;
  }

  subscribe(clientId: string, callback: (event: StoredEvent) => void): void {
    this.subscribers.set(clientId, callback);
  }

  unsubscribe(clientId: string): void {
    this.subscribers.delete(clientId);
  }

  private broadcast(event: StoredEvent, excludeClientId?: string): void {
    for (const [clientId, callback] of this.subscribers) {
      if (clientId !== excludeClientId) {
        callback(event);
      }
    }
  }

  // For testing
  clear(): void {
    this.events = [];
  }
}