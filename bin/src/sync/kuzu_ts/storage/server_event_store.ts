/**
 * Server Event Store Implementation
 * サーバーイベントストア実装
 */

import type { ServerEventStore, EventSnapshot } from "../types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import { validateChecksum } from "../event_sourcing/core.ts";
import { shouldArchive } from "./archive_policy.ts";

export class ServerEventStoreImpl implements ServerEventStore {
  private events: TemplateEvent[] = [];
  private position = 0;
  private eventHandlers: Array<(event: TemplateEvent) => void> = [];

  async appendEvent(event: TemplateEvent): Promise<void> {
    // Validate checksum
    if (!this.validateChecksum(event)) {
      throw new Error("Invalid checksum");
    }
    
    // Store event
    this.events.push(event);
    this.position++;
    
    // Notify handlers
    this.eventHandlers.forEach(handler => handler(event));
  }

  async getEventsSince(position: number): Promise<TemplateEvent[]> {
    return this.events.slice(position);
  }

  getSnapshot(): EventSnapshot {
    return {
      events: [...this.events],
      position: this.position,
      timestamp: Date.now()
    };
  }

  onNewEvent(handler: (event: TemplateEvent) => void): void {
    this.eventHandlers.push(handler);
  }

  validateChecksum(event: TemplateEvent): boolean {
    return validateChecksum(event);
  }

  async getArchivableEvents(): Promise<TemplateEvent[]> {
    const currentTime = Date.now();
    
    // Filter events that should be archived
    const archivableEvents = this.events.filter(event => 
      shouldArchive(event, currentTime)
    );
    
    // Sort by timestamp (oldest first)
    archivableEvents.sort((a, b) => a.timestamp - b.timestamp);
    
    return archivableEvents;
  }
}