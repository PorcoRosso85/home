/**
 * Archive Adapter for Event Storage
 * Uses storage/s3 module's InMemoryStorageAdapter for testing
 */

import { createStorageAdapter, type StorageAdapter } from "../../storage/s3/mod.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

export interface ArchiveAdapter {
  archiveEvent(event: TemplateEvent): Promise<void>;
  retrieveEvent(eventId: string): Promise<TemplateEvent | null>;
  listArchivedEvents(options?: { prefix?: string; limit?: number }): Promise<TemplateEvent[]>;
}

export class S3ArchiveAdapter implements ArchiveAdapter {
  private storage: StorageAdapter;
  private bucketPrefix = "events/";

  constructor() {
    // Use in-memory adapter for testing
    this.storage = createStorageAdapter({});
  }

  async archiveEvent(event: TemplateEvent): Promise<void> {
    const key = `${this.bucketPrefix}${event.timestamp}/${event.id}.json`;
    const content = JSON.stringify(event);
    
    await this.storage.upload(key, content, {
      contentType: "application/json",
      metadata: {
        template: event.template,
        clientId: event.clientId || "",
        timestamp: event.timestamp.toString()
      }
    });
  }

  async retrieveEvent(eventId: string): Promise<TemplateEvent | null> {
    // List all events to find the one with matching ID
    const listResult = await this.storage.list({ prefix: this.bucketPrefix });
    
    for (const obj of listResult.objects) {
      if (obj.key.endsWith(`${eventId}.json`)) {
        const result = await this.storage.download(obj.key);
        const content = new TextDecoder().decode(result.content);
        return JSON.parse(content) as TemplateEvent;
      }
    }
    
    return null;
  }

  async listArchivedEvents(options?: { prefix?: string; limit?: number }): Promise<TemplateEvent[]> {
    const listResult = await this.storage.list({
      prefix: this.bucketPrefix + (options?.prefix || ""),
      maxKeys: options?.limit
    });
    
    const events: TemplateEvent[] = [];
    
    for (const obj of listResult.objects) {
      if (obj.key.endsWith(".json")) {
        const result = await this.storage.download(obj.key);
        const content = new TextDecoder().decode(result.content);
        events.push(JSON.parse(content) as TemplateEvent);
      }
    }
    
    return events.sort((a, b) => a.timestamp - b.timestamp);
  }
}