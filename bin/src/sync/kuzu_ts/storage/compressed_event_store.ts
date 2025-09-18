/**
 * Compressed Event Store Implementation
 * 圧縮イベントストア実装
 * 
 * Extends ServerEventStore to add automatic compression for old events
 */

import { gzip, gunzip } from "https://deno.land/x/compress@v0.4.5/gzip/mod.ts";
import type { ServerEventStore, EventSnapshot } from "../types.ts";
import type { TemplateEvent, StoredEvent } from "../event_sourcing/types.ts";
import { validateChecksum } from "../event_sourcing/core.ts";

// Compression threshold: 30 days in milliseconds
const COMPRESSION_THRESHOLD_MS = 30 * 24 * 60 * 60 * 1000;

type CompressedStoredEvent = {
  id: string;
  compressed: true;
  data: Uint8Array;
  originalSize: number;
  compressedSize: number;
  timestamp: number;
  position: number;
};

type UncompressedStoredEvent = StoredEvent & {
  compressed: false;
};

type InternalStoredEvent = CompressedStoredEvent | UncompressedStoredEvent;

export class CompressedEventStore implements ServerEventStore {
  private events: InternalStoredEvent[] = [];
  private position = 0;
  private eventHandlers: Array<(event: TemplateEvent) => void> = [];
  private eventIndex: Map<string, number> = new Map(); // id -> index mapping

  async appendEvent(event: TemplateEvent): Promise<void> {
    // Validate checksum
    if (!this.validateChecksum(event)) {
      throw new Error("Invalid checksum");
    }

    const storedEvent: StoredEvent = {
      ...event,
      position: this.position
    };

    // Check if event should be compressed
    const eventAge = Date.now() - event.timestamp;
    if (eventAge > COMPRESSION_THRESHOLD_MS) {
      // Compress the event
      const compressedEvent = this.compressEvent(storedEvent);
      this.events.push(compressedEvent);
      this.eventIndex.set(event.id, this.events.length - 1);
    } else {
      // Store uncompressed
      const uncompressedEvent: UncompressedStoredEvent = {
        ...storedEvent,
        compressed: false
      };
      this.events.push(uncompressedEvent);
      this.eventIndex.set(event.id, this.events.length - 1);
    }

    this.position++;

    // Notify handlers
    this.eventHandlers.forEach(handler => handler(event));
  }

  async getEventsSince(position: number): Promise<TemplateEvent[]> {
    return this.events
      .filter(event => this.getEventPosition(event) >= position)
      .map(event => this.decompressEvent(event));
  }

  getSnapshot(): EventSnapshot {
    const decompressedEvents = this.events.map(event => this.decompressEvent(event));
    return {
      events: decompressedEvents,
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

  // Compression-specific methods

  async getCompressionStatus(): Promise<{ compressedCount: number; uncompressedCount: number }> {
    let compressedCount = 0;
    let uncompressedCount = 0;

    for (const event of this.events) {
      if (event.compressed) {
        compressedCount++;
      } else {
        uncompressedCount++;
      }
    }

    return { compressedCount, uncompressedCount };
  }

  async isEventCompressed(eventId: string): Promise<boolean> {
    const index = this.eventIndex.get(eventId);
    if (index === undefined) {
      return false;
    }
    const event = this.events[index];
    return event.compressed;
  }

  async getStorageStats(): Promise<{ originalSize: number; compressedSize: number }> {
    let originalSize = 0;
    let compressedSize = 0;

    for (const event of this.events) {
      if (event.compressed) {
        originalSize += event.originalSize;
        compressedSize += event.compressedSize;
      } else {
        const eventString = JSON.stringify(event);
        const size = new TextEncoder().encode(eventString).length;
        originalSize += size;
        compressedSize += size;
      }
    }

    return { originalSize, compressedSize };
  }

  async runBatchCompression(): Promise<{ compressedCount: number; skippedCount: number }> {
    let compressedCount = 0;
    let skippedCount = 0;
    const threshold = Date.now() - COMPRESSION_THRESHOLD_MS;

    for (let i = 0; i < this.events.length; i++) {
      const event = this.events[i];
      
      if (!event.compressed && event.timestamp < threshold) {
        // Compress this event
        const uncompressedEvent = event as UncompressedStoredEvent;
        const compressedEvent = this.compressEvent(uncompressedEvent);
        this.events[i] = compressedEvent;
        compressedCount++;
      } else {
        skippedCount++;
      }
    }

    return { compressedCount, skippedCount };
  }

  // Private helper methods

  private compressEvent(event: StoredEvent): CompressedStoredEvent {
    const eventString = JSON.stringify(event);
    const originalData = new TextEncoder().encode(eventString);
    const compressedData = gzip(originalData);

    return {
      id: event.id,
      compressed: true,
      data: compressedData,
      originalSize: originalData.length,
      compressedSize: compressedData.length,
      timestamp: event.timestamp,
      position: event.position
    };
  }

  private decompressEvent(event: InternalStoredEvent): TemplateEvent {
    if (!event.compressed) {
      // Remove internal fields for uncompressed events
      const { compressed, position, ...templateEvent } = event;
      return templateEvent;
    }

    // Decompress the event
    const decompressedData = gunzip(event.data);
    const eventString = new TextDecoder().decode(decompressedData);
    const storedEvent: StoredEvent = JSON.parse(eventString);
    
    // Remove position field to return TemplateEvent
    const { position, ...templateEvent } = storedEvent;
    return templateEvent;
  }

  private getEventPosition(event: InternalStoredEvent): number {
    if (event.compressed) {
      return event.position;
    }
    return event.position;
  }
}