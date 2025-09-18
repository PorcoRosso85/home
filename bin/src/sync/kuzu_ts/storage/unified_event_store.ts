/**
 * UnifiedEventStore Implementation
 * Transparently handles both local and archived events
 */

import type { ServerEventStore, EventSnapshot, MutableServerEventStore } from "../types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import type { S3ArchiveAdapter } from "./archive_adapter.ts";
import { validateChecksum } from "../event_sourcing/core.ts";
import { ArchiveExecutor, type ArchiveOperation } from "../event_sourcing/archive_executor.ts";

// Cache statistics interface
export interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  evictions: number;
}

// Unified event store interface
export interface UnifiedEventStore extends ServerEventStore {
  initialize(localStore: MutableServerEventStore, archiveAdapter: S3ArchiveAdapter): Promise<void>;
  archiveOldEvents(): Promise<number>;
  clearCache(): void;
  getCacheStats(): CacheStats;
}

// LRU Cache implementation for archived events
class LRUCache<K, V> {
  private cache = new Map<K, V>();
  private maxSize: number;
  private stats = {
    hits: 0,
    misses: 0,
    evictions: 0
  };

  constructor(maxSize: number = 100) {
    this.maxSize = maxSize;
  }

  get(key: K): V | undefined {
    const value = this.cache.get(key);
    if (value !== undefined) {
      // Move to end (most recently used)
      this.cache.delete(key);
      this.cache.set(key, value);
      this.stats.hits++;
    } else {
      this.stats.misses++;
    }
    return value;
  }

  set(key: K, value: V): void {
    // Remove if already exists
    this.cache.delete(key);
    
    // Evict oldest if at capacity
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey !== undefined) {
        this.cache.delete(firstKey);
        this.stats.evictions++;
      }
    }
    
    this.cache.set(key, value);
  }

  clear(): void {
    this.cache.clear();
    this.stats = { hits: 0, misses: 0, evictions: 0 };
  }

  get size(): number {
    return this.cache.size;
  }

  getStats() {
    return { ...this.stats };
  }
}

export class UnifiedEventStoreImpl implements UnifiedEventStore {
  private localStore!: MutableServerEventStore;
  private archiveAdapter!: S3ArchiveAdapter;
  private archiveExecutor!: ArchiveExecutor;
  private archivedEventsCache = new LRUCache<string, TemplateEvent>(100);
  private archivedEventsList: TemplateEvent[] = [];
  private initialized = false;

  async initialize(localStore: MutableServerEventStore, archiveAdapter: S3ArchiveAdapter): Promise<void> {
    this.localStore = localStore;
    this.archiveAdapter = archiveAdapter;
    
    // Initialize ArchiveExecutor with safe deletion enabled
    this.archiveExecutor = new ArchiveExecutor(archiveAdapter.getStorageAdapter(), {
      verifyAfterUpload: true,
      deleteLocalAfterVerify: false, // We'll handle deletion separately
      batchSize: 10
    });
    
    this.initialized = true;
    
    // Pre-load archived events for synchronous access
    await this.refreshArchivedEventsList();
  }

  private async refreshArchivedEventsList(): Promise<void> {
    this.archivedEventsList = await this.archiveAdapter.listArchivedEvents();
    // Update cache
    for (const event of this.archivedEventsList) {
      this.archivedEventsCache.set(event.id, event);
    }
  }

  private ensureInitialized(): void {
    if (!this.initialized) {
      throw new Error("UnifiedEventStore not initialized");
    }
  }

  async appendEvent(event: TemplateEvent): Promise<void> {
    this.ensureInitialized();
    // Pass through to local store
    await this.localStore.appendEvent(event);
  }

  async getEventsSince(position: number): Promise<TemplateEvent[]> {
    this.ensureInitialized();
    
    // Get all archived events
    const archivedEvents = await this.getArchivedEvents();
    
    // Get all local events
    const localEvents = await this.localStore.getEventsSince(0);
    
    // Create a map to deduplicate events by ID
    const eventMap = new Map<string, TemplateEvent>();
    
    // Add archived events first (they have priority)
    for (const event of archivedEvents) {
      eventMap.set(event.id, event);
    }
    
    // Add local events (won't overwrite if already in map)
    for (const event of localEvents) {
      if (!eventMap.has(event.id)) {
        eventMap.set(event.id, event);
      }
    }
    
    // Convert back to array and sort by timestamp
    const allEvents = Array.from(eventMap.values());
    allEvents.sort((a, b) => a.timestamp - b.timestamp);
    
    // Return events from the requested position
    return allEvents.slice(position);
  }

  private async getArchivedEvents(): Promise<TemplateEvent[]> {
    // Check cache first
    const cached: TemplateEvent[] = [];
    
    // Get all archived events from S3
    const archivedEvents = await this.archiveAdapter.listArchivedEvents();
    
    // Update cache with fetched events
    for (const event of archivedEvents) {
      // Check if in cache
      const cachedEvent = this.archivedEventsCache.get(event.id);
      if (cachedEvent) {
        cached.push(cachedEvent);
      } else {
        // Add to cache
        this.archivedEventsCache.set(event.id, event);
        cached.push(event);
      }
    }
    
    return archivedEvents;
  }

  getSnapshot(): EventSnapshot {
    this.ensureInitialized();
    
    // Get local events
    const localSnapshot = this.localStore.getSnapshot();
    
    // Create a map to deduplicate events by ID
    const eventMap = new Map<string, TemplateEvent>();
    
    // Add archived events first (they have priority)
    for (const event of this.archivedEventsList) {
      eventMap.set(event.id, event);
    }
    
    // Add local events (won't overwrite if already in map)
    for (const event of localSnapshot.events) {
      if (!eventMap.has(event.id)) {
        eventMap.set(event.id, event);
      }
    }
    
    // Convert back to array and sort by timestamp
    const allEvents = Array.from(eventMap.values());
    allEvents.sort((a, b) => a.timestamp - b.timestamp);
    
    return {
      events: allEvents,
      position: allEvents.length,
      timestamp: Date.now()
    };
  }

  onNewEvent(handler: (event: TemplateEvent) => void): void {
    this.ensureInitialized();
    // Pass through to local store
    this.localStore.onNewEvent(handler);
  }

  validateChecksum(event: TemplateEvent): boolean {
    // Use the same validation logic
    return validateChecksum(event);
  }

  async getArchivableEvents(): Promise<TemplateEvent[]> {
    this.ensureInitialized();
    // Pass through to local store
    return this.localStore.getArchivableEvents();
  }

  async archiveOldEvents(): Promise<number> {
    this.ensureInitialized();
    
    // Get archivable events from local store
    const archivableEvents = await this.localStore.getArchivableEvents();
    
    if (archivableEvents.length === 0) {
      return 0;
    }
    
    // Prepare archive operations
    const operations: ArchiveOperation[] = archivableEvents.map(event => ({
      event,
      localPath: `memory://event-${event.id}` // Virtual path for in-memory events
    }));
    
    try {
      // Use ArchiveExecutor for transactional archiving
      // We'll create a custom version that doesn't need local files
      const eventIds: string[] = [];
      
      // Archive events individually with error handling
      for (const event of archivableEvents) {
        try {
          await this.archiveAdapter.archiveEvent(event);
          eventIds.push(event.id);
        } catch (error) {
          console.error(`Failed to archive event ${event.id}:`, error);
          // Continue with other events
        }
      }
      
      if (eventIds.length === 0) {
        return 0;
      }
      
      // Remove successfully archived events from local store
      const removedCount = await this.localStore.removeEvents(eventIds);
      
      // Update our cached list of archived events
      await this.refreshArchivedEventsList();
      
      return removedCount;
    } catch (error) {
      console.error("Archive operation failed:", error);
      throw error;
    }
  }

  clearCache(): void {
    this.archivedEventsCache.clear();
  }

  getCacheStats(): CacheStats {
    const stats = this.archivedEventsCache.getStats();
    return {
      ...stats,
      size: this.archivedEventsCache.size
    };
  }
}