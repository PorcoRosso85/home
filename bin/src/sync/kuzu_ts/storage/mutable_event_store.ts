/**
 * Mutable Server Event Store Implementation
 * 可変サーバーイベントストア実装
 * 
 * Extends ServerEventStoreImpl to add safe deletion capabilities
 * with transaction safety guarantees.
 */

import { ServerEventStoreImpl } from "./server_event_store.ts";
import type { MutableServerEventStore as IMutableServerEventStore } from "../types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

export class MutableServerEventStore extends ServerEventStoreImpl implements IMutableServerEventStore {
  /**
   * Remove events by their IDs
   * Ensures transaction safety - all or nothing
   * @param eventIds Array of event IDs to remove
   * @returns Number of events actually removed
   */
  async removeEvents(eventIds: string[]): Promise<number> {
    // Create a backup of current events for rollback
    const backup = this.getEventsBackup();
    let removedCount = 0;
    
    try {
      // Filter out events with matching IDs
      const eventsToKeep: TemplateEvent[] = [];
      
      for (const event of this.getEvents()) {
        if (!eventIds.includes(event.id)) {
          eventsToKeep.push(event);
        } else {
          removedCount++;
        }
      }
      
      // Update the events array
      this.setEvents(eventsToKeep);
      
      return removedCount;
    } catch (error) {
      // Rollback on any error
      this.restoreEvents(backup);
      throw error;
    }
  }
  
  /**
   * Remove all events before the specified timestamp
   * Ensures transaction safety - all or nothing
   * @param timestamp Unix timestamp in milliseconds
   * @returns Number of events removed
   */
  async removeEventsBefore(timestamp: number): Promise<number> {
    // Create a backup of current events for rollback
    const backup = this.getEventsBackup();
    let removedCount = 0;
    
    try {
      // Filter out events before the timestamp
      const eventsToKeep: TemplateEvent[] = [];
      
      for (const event of this.getEvents()) {
        if (event.timestamp >= timestamp) {
          eventsToKeep.push(event);
        } else {
          removedCount++;
        }
      }
      
      // Update the events array
      this.setEvents(eventsToKeep);
      
      return removedCount;
    } catch (error) {
      // Rollback on any error
      this.restoreEvents(backup);
      throw error;
    }
  }
  
  // Protected methods for internal state management
  protected getEvents(): TemplateEvent[] {
    // Access the private events array through reflection
    // This is necessary since TypeScript doesn't allow protected access to private parent members
    return (this as any).events;
  }
  
  protected setEvents(events: TemplateEvent[]): void {
    // Update the private events array
    (this as any).events = events;
  }
  
  protected getEventsBackup(): TemplateEvent[] {
    // Create a deep copy of events for backup
    return [...this.getEvents()];
  }
  
  protected restoreEvents(backup: TemplateEvent[]): void {
    // Restore events from backup
    this.setEvents(backup);
  }
}