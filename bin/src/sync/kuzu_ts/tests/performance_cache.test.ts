/**
 * Performance Tests for State Cache
 * Demonstrates O(1) performance improvement
 */

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

// Mock KuzuDB for testing
const mockKuzu = {
  init: async () => {},
  setWorkerPath: () => {},
  Database: class {
    constructor(_path: string) {}
  },
  Connection: class {
    query: any;
    constructor(_db: any) {
      // Mock query responses
      this.query = async (query: string) => {
        if (query.includes("CREATE NODE TABLE") || query.includes("CREATE REL TABLE")) {
          return {};
        }
        
        if (query.includes("MATCH (u:User)")) {
          // Simulate a large dataset
          const users = Array.from({ length: 1000 }, (_, i) => ({
            id: `user${i}`,
            name: `User ${i}`,
            email: `user${i}@example.com`
          }));
          return {
            getAllObjects: () => users
          };
        }
        
        if (query.includes("MATCH (p:Post)")) {
          // Simulate a large dataset
          const posts = Array.from({ length: 5000 }, (_, i) => ({
            id: `post${i}`,
            content: `Post content ${i}`,
            authorId: `user${i % 1000}`
          }));
          return {
            getAllObjects: () => posts
          };
        }
        
        if (query.includes("FOLLOWS")) {
          // Simulate a large dataset
          const follows = Array.from({ length: 10000 }, (_, i) => ({
            followerId: `user${i % 1000}`,
            targetId: `user${(i + 1) % 1000}`
          }));
          return {
            getAllObjects: () => follows
          };
        }
        
        return { getAllObjects: () => [] };
      };
    }
  }
};

// Mock the kuzu-wasm import
globalThis.mockKuzuImport = async () => mockKuzu;

Deno.test("Performance - State retrieval without cache (baseline)", async () => {
  const client = new BrowserKuzuClientImpl();
  
  // Override the import to use our mock
  // @ts-ignore - accessing private method for testing
  client.initialize = async function() {
    const kuzu = await globalThis.mockKuzuImport();
    await kuzu.init();
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    await this.createSchema();
  };
  
  await client.initialize();
  
  // Disable cache for baseline measurement
  // @ts-ignore - accessing private property for testing
  client.stateCache.getCachedState = () => null;
  
  // Warm up the queries
  await client.getLocalState();
  
  // Measure time for multiple uncached retrievals
  const iterations = 10;
  const times: number[] = [];
  
  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await client.getLocalState();
    const end = performance.now();
    times.push(end - start);
  }
  
  const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
  console.log(`🐌 Baseline (no cache): Average time ${avgTime.toFixed(2)}ms`);
  
  // Expect baseline to be measurably slower than cached version
  // In real scenario with actual KuzuDB, this would be much slower (500ms+)
  assertEquals(avgTime > 1, true, `Expected baseline to take > 1ms, got ${avgTime}ms`);
});

Deno.test("Performance - State retrieval with cache (optimized)", async () => {
  const client = new BrowserKuzuClientImpl();
  
  // Override the import to use our mock
  // @ts-ignore - accessing private method for testing
  client.initialize = async function() {
    const kuzu = await globalThis.mockKuzuImport();
    await kuzu.init();
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    await this.createSchema();
  };
  
  await client.initialize();
  
  // First call populates the cache
  await client.getLocalState();
  
  // Measure cached retrievals
  const iterations = 100;
  const times: number[] = [];
  
  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await client.getLocalState();
    const end = performance.now();
    times.push(end - start);
  }
  
  const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
  const maxTime = Math.max(...times);
  
  console.log(`🚀 With cache: Average time ${avgTime.toFixed(2)}ms, Max time ${maxTime.toFixed(2)}ms`);
  
  // Assert O(1) performance - should be under 5ms
  assertEquals(avgTime < 5, true, `Expected cached retrieval < 5ms, got ${avgTime}ms`);
  assertEquals(maxTime < 5, true, `Expected max time < 5ms, got ${maxTime}ms`);
});

Deno.test("Performance - Cache invalidation and repopulation", async () => {
  const client = new BrowserKuzuClientImpl();
  
  // Override the import to use our mock
  // @ts-ignore - accessing private method for testing
  client.initialize = async function() {
    const kuzu = await globalThis.mockKuzuImport();
    await kuzu.init();
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    await this.createSchema();
  };
  
  await client.initialize();
  
  // First retrieval (cache miss)
  const firstStart = performance.now();
  await client.getLocalState();
  const firstEnd = performance.now();
  const firstTime = firstEnd - firstStart;
  
  // Second retrieval (cache hit)
  const secondStart = performance.now();
  await client.getLocalState();
  const secondEnd = performance.now();
  const secondTime = secondEnd - secondStart;
  
  // Execute a template to invalidate cache
  await client.executeTemplate("CREATE_USER", {
    id: "new-user",
    name: "New User",
    email: "new@example.com"
  });
  
  // Third retrieval (cache miss after invalidation)
  const thirdStart = performance.now();
  await client.getLocalState();
  const thirdEnd = performance.now();
  const thirdTime = thirdEnd - thirdStart;
  
  // Fourth retrieval (cache hit again)
  const fourthStart = performance.now();
  await client.getLocalState();
  const fourthEnd = performance.now();
  const fourthTime = fourthEnd - fourthStart;
  
  console.log(`⏱️  Performance profile:`);
  console.log(`   First (miss):  ${firstTime.toFixed(2)}ms`);
  console.log(`   Second (hit):  ${secondTime.toFixed(2)}ms`);
  console.log(`   Third (miss):  ${thirdTime.toFixed(2)}ms`);
  console.log(`   Fourth (hit):  ${fourthTime.toFixed(2)}ms`);
  
  // Cache hits should be significantly faster
  assertEquals(secondTime < 5, true, `Expected cached retrieval < 5ms, got ${secondTime}ms`);
  assertEquals(fourthTime < 5, true, `Expected cached retrieval < 5ms, got ${fourthTime}ms`);
  
  // Cache misses should be slower
  assertEquals(firstTime > secondTime, true, "First retrieval should be slower than cached");
  assertEquals(thirdTime > fourthTime, true, "Post-invalidation retrieval should be slower than cached");
});

Deno.test("Performance - Concurrent access performance", async () => {
  const client = new BrowserKuzuClientImpl();
  
  // Override the import to use our mock
  // @ts-ignore - accessing private method for testing
  client.initialize = async function() {
    const kuzu = await globalThis.mockKuzuImport();
    await kuzu.init();
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    await this.createSchema();
  };
  
  await client.initialize();
  
  // Populate cache
  await client.getLocalState();
  
  // Simulate concurrent access
  const concurrentRequests = 50;
  const start = performance.now();
  
  const promises = Array.from({ length: concurrentRequests }, async () => {
    return await client.getLocalState();
  });
  
  await Promise.all(promises);
  const end = performance.now();
  
  const totalTime = end - start;
  const avgTimePerRequest = totalTime / concurrentRequests;
  
  console.log(`🔄 Concurrent access: ${concurrentRequests} requests in ${totalTime.toFixed(2)}ms`);
  console.log(`   Average per request: ${avgTimePerRequest.toFixed(2)}ms`);
  
  // Even with concurrent access, cached retrieval should be fast
  assertEquals(avgTimePerRequest < 5, true, `Expected avg time < 5ms, got ${avgTimePerRequest}ms`);
});