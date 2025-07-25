/**
 * State Cache Implementation
 * O(1) access to latest computed state with LRU eviction
 */

import type { LocalState, TemplateEvent } from "../../types.ts";

export interface CacheOptions {
  maxSize?: number;
}

export interface CacheStats {
  hits: number;
  misses: number;
}

export interface MemoryStats {
  entries: number;
  estimatedSizeBytes: number;
}

interface CacheEntry {
  state: LocalState;
  timestamp: number;
  size: number;
}

export class StateCache {
  private cache: Map<string, CacheEntry>;
  private lruQueue: string[];
  private stats: CacheStats;
  private options: Required<CacheOptions>;
  private defaultKey = "default";

  constructor(options: CacheOptions = {}) {
    this.cache = new Map();
    this.lruQueue = [];
    this.stats = { hits: 0, misses: 0 };
    this.options = {
      maxSize: options.maxSize ?? 100
    };
  }

  /**
   * Get cached state with O(1) access
   * @param key Optional cache key, defaults to "default"
   * @returns Cached state or null if not found
   */
  getCachedState(key: string = this.defaultKey): LocalState | null {
    const entry = this.cache.get(key);
    
    if (entry) {
      this.stats.hits++;
      // Update LRU queue - move to end
      this.updateLRU(key);
      return entry.state;
    } else {
      this.stats.misses++;
      return null;
    }
  }

  /**
   * Set cached state
   * @param state The state to cache
   * @param key Optional cache key, defaults to "default"
   */
  setCachedState(state: LocalState, key: string = this.defaultKey): void {
    const size = this.estimateSize(state);
    const entry: CacheEntry = {
      state,
      timestamp: Date.now(),
      size
    };

    // If cache is at max size, evict LRU
    if (this.cache.size >= this.options.maxSize && !this.cache.has(key)) {
      this.evictLRU();
    }

    this.cache.set(key, entry);
    this.updateLRU(key);
  }

  /**
   * Invalidate cache when new event arrives
   * @param event The event that invalidates the cache
   */
  invalidateOnEvent(event: TemplateEvent): void {
    // Clear the default cache entry when any event arrives
    this.cache.delete(this.defaultKey);
    
    // Remove from LRU queue
    const index = this.lruQueue.indexOf(this.defaultKey);
    if (index > -1) {
      this.lruQueue.splice(index, 1);
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }

  /**
   * Get memory statistics
   */
  getMemoryStats(): MemoryStats {
    let totalSize = 0;
    for (const entry of this.cache.values()) {
      totalSize += entry.size;
    }

    return {
      entries: this.cache.size,
      estimatedSizeBytes: totalSize + this.getOverheadSize()
    };
  }

  /**
   * Clear all cached entries
   */
  clear(): void {
    this.cache.clear();
    this.lruQueue = [];
  }

  // Private helper methods

  private updateLRU(key: string): void {
    // Remove key from current position
    const index = this.lruQueue.indexOf(key);
    if (index > -1) {
      this.lruQueue.splice(index, 1);
    }
    // Add to end (most recently used)
    this.lruQueue.push(key);
  }

  private evictLRU(): void {
    if (this.lruQueue.length > 0) {
      const keyToEvict = this.lruQueue.shift()!;
      this.cache.delete(keyToEvict);
    }
  }

  private estimateSize(state: LocalState): number {
    // Rough estimation of object size in bytes
    let size = 0;

    // Users
    for (const user of state.users) {
      size += 8; // object overhead
      size += (user.id?.length ?? 0) * 2; // string chars
      size += (user.name?.length ?? 0) * 2;
      size += (user.email?.length ?? 0) * 2;
    }

    // Posts
    for (const post of state.posts) {
      size += 8; // object overhead
      size += (post.id?.length ?? 0) * 2;
      size += (post.content?.length ?? 0) * 2;
      size += (post.authorId?.length ?? 0) * 2;
    }

    // Follows
    for (const follow of state.follows) {
      size += 8; // object overhead
      size += (follow.followerId?.length ?? 0) * 2;
      size += (follow.targetId?.length ?? 0) * 2;
    }

    return size;
  }

  private getOverheadSize(): number {
    // Estimate overhead of the cache structure itself
    return (
      100 + // Base object overhead
      this.lruQueue.length * 50 + // LRU queue overhead
      this.cache.size * 100 // Map entry overhead
    );
  }
}