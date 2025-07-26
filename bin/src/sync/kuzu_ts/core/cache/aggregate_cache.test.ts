/**
 * Aggregate Cache Tests
 * Tests for caching aggregate values with incremental updates
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { AggregateCache, type AggregateType, type AggregateDefinition } from "./aggregate_cache.ts";
import type { TemplateEvent } from "../../event_sourcing/types.ts";

Deno.test("AggregateCache - should initialize with empty aggregates", () => {
  const cache = new AggregateCache();
  
  const result = cache.getValue("user_count");
  assertEquals(result, null);
});

Deno.test("AggregateCache - should define and get aggregate values", () => {
  const cache = new AggregateCache();
  
  // Define a simple count aggregate
  const definition: AggregateDefinition = {
    name: "user_count",
    type: "COUNT",
    target: "users"
  };
  
  cache.defineAggregate(definition);
  cache.setValue("user_count", 10);
  
  const result = cache.getValue("user_count");
  assertEquals(result, 10);
});

Deno.test("AggregateCache - should support COUNT aggregates", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "post_count",
    type: "COUNT",
    target: "posts"
  });
  
  // Process events that create posts
  const event1: TemplateEvent = {
    id: "e1",
    template: "CREATE_POST",
    params: { id: "p1", content: "Hello", authorId: "u1" },
    timestamp: Date.now()
  };
  
  const event2: TemplateEvent = {
    id: "e2",
    template: "CREATE_POST",
    params: { id: "p2", content: "World", authorId: "u1" },
    timestamp: Date.now()
  };
  
  cache.processEvent(event1);
  cache.processEvent(event2);
  
  assertEquals(cache.getValue("post_count"), 2);
});

Deno.test("AggregateCache - should support SUM aggregates", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "total_likes",
    type: "SUM",
    target: "likes",
    field: "count"
  });
  
  const event1: TemplateEvent = {
    id: "e1",
    template: "ADD_LIKES",
    params: { postId: "p1", count: 5 },
    timestamp: Date.now()
  };
  
  const event2: TemplateEvent = {
    id: "e2",
    template: "ADD_LIKES",
    params: { postId: "p2", count: 3 },
    timestamp: Date.now()
  };
  
  cache.processEvent(event1);
  cache.processEvent(event2);
  
  assertEquals(cache.getValue("total_likes"), 8);
});

Deno.test("AggregateCache - should support AVG aggregates", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "avg_post_length",
    type: "AVG",
    target: "posts",
    field: "content_length"
  });
  
  // For AVG, we need to track sum and count internally
  const event1: TemplateEvent = {
    id: "e1",
    template: "CREATE_POST",
    params: { id: "p1", content: "Hello", content_length: 5 },
    timestamp: Date.now()
  };
  
  const event2: TemplateEvent = {
    id: "e2",
    template: "CREATE_POST",
    params: { id: "p2", content: "Hello World", content_length: 11 },
    timestamp: Date.now()
  };
  
  cache.processEvent(event1);
  cache.processEvent(event2);
  
  assertEquals(cache.getValue("avg_post_length"), 8); // (5 + 11) / 2
});

Deno.test("AggregateCache - should support MIN aggregates", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "min_timestamp",
    type: "MIN",
    target: "events",
    field: "timestamp"
  });
  
  const event1: TemplateEvent = {
    id: "e1",
    template: "EVENT",
    params: { timestamp: 1000 },
    timestamp: 1000
  };
  
  const event2: TemplateEvent = {
    id: "e2",
    template: "EVENT",
    params: { timestamp: 500 },
    timestamp: 500
  };
  
  cache.processEvent(event1);
  cache.processEvent(event2);
  
  assertEquals(cache.getValue("min_timestamp"), 500);
});

Deno.test("AggregateCache - should support MAX aggregates", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "max_likes",
    type: "MAX",
    target: "posts",
    field: "like_count"
  });
  
  const event1: TemplateEvent = {
    id: "e1",
    template: "UPDATE_LIKES",
    params: { postId: "p1", like_count: 10 },
    timestamp: Date.now()
  };
  
  const event2: TemplateEvent = {
    id: "e2",
    template: "UPDATE_LIKES",
    params: { postId: "p2", like_count: 25 },
    timestamp: Date.now()
  };
  
  cache.processEvent(event1);
  cache.processEvent(event2);
  
  assertEquals(cache.getValue("max_likes"), 25);
});

Deno.test("AggregateCache - should support conditional aggregates with predicates", () => {
  const cache = new AggregateCache();
  
  // Count only active users
  cache.defineAggregate({
    name: "active_user_count",
    type: "COUNT",
    target: "users",
    predicate: (event) => event.params.status === "active"
  });
  
  const event1: TemplateEvent = {
    id: "e1",
    template: "CREATE_USER",
    params: { id: "u1", status: "active" },
    timestamp: Date.now()
  };
  
  const event2: TemplateEvent = {
    id: "e2",
    template: "CREATE_USER",
    params: { id: "u2", status: "inactive" },
    timestamp: Date.now()
  };
  
  const event3: TemplateEvent = {
    id: "e3",
    template: "CREATE_USER",
    params: { id: "u3", status: "active" },
    timestamp: Date.now()
  };
  
  cache.processEvent(event1);
  cache.processEvent(event2);
  cache.processEvent(event3);
  
  assertEquals(cache.getValue("active_user_count"), 2);
});

Deno.test("AggregateCache - should handle delete events for COUNT", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "user_count",
    type: "COUNT",
    target: "users"
  });
  
  const createEvent: TemplateEvent = {
    id: "e1",
    template: "CREATE_USER",
    params: { id: "u1" },
    timestamp: Date.now()
  };
  
  const deleteEvent: TemplateEvent = {
    id: "e2",
    template: "DELETE_USER",
    params: { id: "u1" },
    timestamp: Date.now()
  };
  
  cache.processEvent(createEvent);
  assertEquals(cache.getValue("user_count"), 1);
  
  cache.processEvent(deleteEvent);
  assertEquals(cache.getValue("user_count"), 0);
});

Deno.test("AggregateCache - should provide O(1) retrieval", () => {
  const cache = new AggregateCache();
  
  // Define multiple aggregates
  for (let i = 0; i < 1000; i++) {
    cache.defineAggregate({
      name: `aggregate_${i}`,
      type: "COUNT",
      target: "items"
    });
    cache.setValue(`aggregate_${i}`, i);
  }
  
  // Retrieval should be constant time regardless of cache size
  const start = performance.now();
  const value = cache.getValue("aggregate_500");
  const duration = performance.now() - start;
  
  assertEquals(value, 500);
  // Should be very fast (less than 1ms)
  assertEquals(duration < 1, true);
});

Deno.test("AggregateCache - should return aggregate statistics", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "user_count",
    type: "COUNT",
    target: "users"
  });
  
  cache.defineAggregate({
    name: "total_revenue",
    type: "SUM",
    target: "orders",
    field: "amount"
  });
  
  cache.setValue("user_count", 100);
  cache.setValue("total_revenue", 5000);
  
  const stats = cache.getStats();
  assertExists(stats);
  assertEquals(stats.aggregateCount, 2);
  assertEquals(stats.cacheHits, 0);
  assertEquals(stats.cacheMisses, 0);
});

Deno.test("AggregateCache - should track cache hits and misses", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "counter",
    type: "COUNT",
    target: "items"
  });
  
  // Miss
  cache.getValue("counter");
  let stats = cache.getStats();
  assertEquals(stats.cacheMisses, 1);
  assertEquals(stats.cacheHits, 0);
  
  // Set value
  cache.setValue("counter", 10);
  
  // Hit
  cache.getValue("counter");
  stats = cache.getStats();
  assertEquals(stats.cacheMisses, 1);
  assertEquals(stats.cacheHits, 1);
});

Deno.test("AggregateCache - should clear all aggregates", () => {
  const cache = new AggregateCache();
  
  cache.defineAggregate({
    name: "count1",
    type: "COUNT",
    target: "items"
  });
  
  cache.defineAggregate({
    name: "count2",
    type: "COUNT",
    target: "users"
  });
  
  cache.setValue("count1", 10);
  cache.setValue("count2", 20);
  
  cache.clear();
  
  assertEquals(cache.getValue("count1"), null);
  assertEquals(cache.getValue("count2"), null);
  
  const stats = cache.getStats();
  assertEquals(stats.aggregateCount, 0);
});

Deno.test("AggregateCache - should estimate memory usage", () => {
  const cache = new AggregateCache();
  
  // Add some aggregates
  for (let i = 0; i < 10; i++) {
    cache.defineAggregate({
      name: `aggregate_${i}`,
      type: "COUNT",
      target: "items"
    });
    cache.setValue(`aggregate_${i}`, i * 100);
  }
  
  const memoryStats = cache.getMemoryStats();
  assertExists(memoryStats);
  assertEquals(memoryStats.aggregateCount, 10);
  // Memory usage should be reasonable (not zero, not huge)
  assertEquals(memoryStats.estimatedSizeBytes > 0, true);
  assertEquals(memoryStats.estimatedSizeBytes < 10000, true);
});