/**
 * State Cache Tests
 * Tests for O(1) latest state retrieval cache
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { StateCache } from "../core/cache/state_cache.ts";
import type { LocalState, TemplateEvent } from "../types.ts";

// Helper function to create a mock event
function createMockEvent(template: string, params: Record<string, any>): TemplateEvent {
  return {
    id: crypto.randomUUID(),
    template,
    params,
    timestamp: Date.now(),
    clientId: "test-client",
    version: 1,
    checksum: "mock-checksum"
  };
}

// Helper function to create a mock state
function createMockState(): LocalState {
  return {
    users: [
      { id: "user1", name: "Alice", email: "alice@example.com" },
      { id: "user2", name: "Bob", email: "bob@example.com" }
    ],
    posts: [
      { id: "post1", content: "Hello World", authorId: "user1" }
    ],
    follows: [
      { followerId: "user2", targetId: "user1" }
    ]
  };
}

Deno.test("StateCache - should return cached state on hit", async () => {
  const cache = new StateCache();
  const mockState = createMockState();
  
  // Set cached state
  cache.setCachedState(mockState);
  
  // Get cached state
  const startTime = performance.now();
  const cachedState = cache.getCachedState();
  const endTime = performance.now();
  
  // Assert state matches
  assertExists(cachedState);
  assertEquals(cachedState, mockState);
  
  // Assert performance - should be under 5ms
  const duration = endTime - startTime;
  assertEquals(duration < 5, true, `Cache retrieval took ${duration}ms, expected < 5ms`);
});

Deno.test("StateCache - should return null on cache miss", () => {
  const cache = new StateCache();
  
  const cachedState = cache.getCachedState();
  assertEquals(cachedState, null);
});

Deno.test("StateCache - should invalidate cache on new event", () => {
  const cache = new StateCache();
  const mockState = createMockState();
  
  // Set cached state
  cache.setCachedState(mockState);
  
  // Verify cache is set
  assertExists(cache.getCachedState());
  
  // Invalidate with new event
  const newEvent = createMockEvent("CREATE_USER", { 
    id: "user3", 
    name: "Charlie", 
    email: "charlie@example.com" 
  });
  cache.invalidateOnEvent(newEvent);
  
  // Cache should be invalidated
  assertEquals(cache.getCachedState(), null);
});

Deno.test("StateCache - should track cache statistics", () => {
  const cache = new StateCache();
  const mockState = createMockState();
  
  // Initial stats
  let stats = cache.getStats();
  assertEquals(stats.hits, 0);
  assertEquals(stats.misses, 0);
  
  // Cache miss
  cache.getCachedState();
  stats = cache.getStats();
  assertEquals(stats.hits, 0);
  assertEquals(stats.misses, 1);
  
  // Set cache
  cache.setCachedState(mockState);
  
  // Cache hit
  cache.getCachedState();
  stats = cache.getStats();
  assertEquals(stats.hits, 1);
  assertEquals(stats.misses, 1);
  
  // Another hit
  cache.getCachedState();
  stats = cache.getStats();
  assertEquals(stats.hits, 2);
  assertEquals(stats.misses, 1);
});

Deno.test("StateCache - should implement LRU eviction for memory management", () => {
  const cache = new StateCache({ maxSize: 2 });
  
  const state1 = createMockState();
  const state2 = { ...createMockState(), users: [] };
  const state3 = { ...createMockState(), posts: [] };
  
  // Add states with different keys
  cache.setCachedState(state1, "key1");
  cache.setCachedState(state2, "key2");
  
  // Both should be cached
  assertEquals(cache.getCachedState("key1"), state1);
  assertEquals(cache.getCachedState("key2"), state2);
  
  // Add third state - should evict least recently used (key1)
  cache.setCachedState(state3, "key3");
  
  // key1 should be evicted, key2 and key3 should remain
  assertEquals(cache.getCachedState("key1"), null);
  assertEquals(cache.getCachedState("key2"), state2);
  assertEquals(cache.getCachedState("key3"), state3);
});

Deno.test("StateCache - should measure memory usage", () => {
  const cache = new StateCache();
  const mockState = createMockState();
  
  // Initial memory should be minimal
  let memoryStats = cache.getMemoryStats();
  assertEquals(memoryStats.entries, 0);
  assertEquals(memoryStats.estimatedSizeBytes < 1000, true);
  
  // Add state
  cache.setCachedState(mockState);
  
  // Memory should increase
  memoryStats = cache.getMemoryStats();
  assertEquals(memoryStats.entries, 1);
  assertEquals(memoryStats.estimatedSizeBytes > 0, true);
});

Deno.test("StateCache - performance test with multiple operations", async () => {
  const cache = new StateCache();
  const mockState = createMockState();
  
  // Set cache
  cache.setCachedState(mockState);
  
  // Perform 1000 cache retrievals
  const iterations = 1000;
  const startTime = performance.now();
  
  for (let i = 0; i < iterations; i++) {
    cache.getCachedState();
  }
  
  const endTime = performance.now();
  const totalDuration = endTime - startTime;
  const avgDuration = totalDuration / iterations;
  
  // Average time per retrieval should be well under 1ms
  assertEquals(avgDuration < 1, true, `Average retrieval took ${avgDuration}ms, expected < 1ms`);
  
  // Total time for 1000 retrievals should be under 100ms
  assertEquals(totalDuration < 100, true, `Total time for ${iterations} retrievals was ${totalDuration}ms`);
});

Deno.test("StateCache - should handle concurrent access safely", async () => {
  const cache = new StateCache();
  const mockState = createMockState();
  
  cache.setCachedState(mockState);
  
  // Simulate concurrent access
  const promises = Array.from({ length: 100 }, async (_, i) => {
    if (i % 10 === 0) {
      // Every 10th operation invalidates
      cache.invalidateOnEvent(createMockEvent("UPDATE_USER", { id: "user1", name: "Updated" }));
    } else if (i % 5 === 0) {
      // Every 5th operation sets new state
      cache.setCachedState(createMockState());
    } else {
      // Most operations read
      cache.getCachedState();
    }
  });
  
  // Should not throw any errors
  await Promise.all(promises);
  
  // Cache should still be functional
  const stats = cache.getStats();
  assertExists(stats);
  assertEquals(stats.hits >= 0, true);
  assertEquals(stats.misses >= 0, true);
});