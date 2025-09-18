/**
 * Event Compression Tests
 * イベント圧縮機能のテスト
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { CompressedEventStore } from "../storage/compressed_event_store.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import { calculateChecksum } from "../event_sourcing/core.ts";

// Helper function to create test events
function createTestEvent(daysAgo: number): TemplateEvent {
  const timestamp = Date.now() - (daysAgo * 24 * 60 * 60 * 1000);
  const template = "CREATE_USER";
  const params = {
    name: `User ${daysAgo}`,
    email: `user${daysAgo}@example.com`,
    bio: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. ".repeat(10)
  };
  
  return {
    id: `event-${timestamp}`,
    template,
    params,
    timestamp,
    clientId: "test-client",
    checksum: calculateChecksum(template, params)
  };
}

Deno.test("CompressedEventStore - events older than 30 days are compressed", async () => {
  const store = new CompressedEventStore();
  
  // Add old event (40 days ago)
  const oldEvent = createTestEvent(40);
  await store.appendEvent(oldEvent);
  
  // Add recent event (10 days ago)
  const recentEvent = createTestEvent(10);
  await store.appendEvent(recentEvent);
  
  // Check compression status
  const compressionStatus = await store.getCompressionStatus();
  
  assertEquals(compressionStatus.compressedCount, 1, "Should have 1 compressed event");
  assertEquals(compressionStatus.uncompressedCount, 1, "Should have 1 uncompressed event");
  
  // Verify old event is compressed
  const isOldEventCompressed = await store.isEventCompressed(oldEvent.id);
  assertEquals(isOldEventCompressed, true, "Old event should be compressed");
  
  // Verify recent event is not compressed
  const isRecentEventCompressed = await store.isEventCompressed(recentEvent.id);
  assertEquals(isRecentEventCompressed, false, "Recent event should not be compressed");
});

Deno.test("CompressedEventStore - compressed events can be decompressed transparently", async () => {
  const store = new CompressedEventStore();
  
  // Add old event that will be compressed
  const originalEvent = createTestEvent(40);
  await store.appendEvent(originalEvent);
  
  // Retrieve the event (should be transparently decompressed)
  const events = await store.getEventsSince(0);
  
  assertEquals(events.length, 1, "Should retrieve 1 event");
  const retrievedEvent = events[0];
  
  // Verify all properties match
  assertEquals(retrievedEvent.id, originalEvent.id);
  assertEquals(retrievedEvent.template, originalEvent.template);
  assertEquals(retrievedEvent.params, originalEvent.params);
  assertEquals(retrievedEvent.timestamp, originalEvent.timestamp);
  assertEquals(retrievedEvent.clientId, originalEvent.clientId);
  assertEquals(retrievedEvent.checksum, originalEvent.checksum);
});

Deno.test("CompressedEventStore - compression ratio is at least 70%", async () => {
  const store = new CompressedEventStore();
  
  // Create a large event with repetitive data (good for compression)
  const template = "CREATE_USER";
  const params = {
    data: "AAAAAAAAAA".repeat(1000), // 10KB of repetitive data
    moreData: "BBBBBBBBBB".repeat(1000),
    evenMoreData: "CCCCCCCCCC".repeat(1000)
  };
  const largeEvent: TemplateEvent = {
    id: `event-large`,
    template,
    params,
    timestamp: Date.now() - (40 * 24 * 60 * 60 * 1000), // 40 days ago
    clientId: "test-client",
    checksum: calculateChecksum(template, params)
  };
  
  await store.appendEvent(largeEvent);
  
  // Get storage statistics
  const stats = await store.getStorageStats();
  
  assertExists(stats.originalSize, "Should have original size");
  assertExists(stats.compressedSize, "Should have compressed size");
  
  const compressionRatio = 1 - (stats.compressedSize / stats.originalSize);
  
  assertEquals(
    compressionRatio >= 0.7,
    true,
    `Compression ratio should be at least 70%, got ${(compressionRatio * 100).toFixed(2)}%`
  );
});

Deno.test("CompressedEventStore - maintains ServerEventStore interface compatibility", async () => {
  const store = new CompressedEventStore();
  
  // Test standard ServerEventStore methods work
  const event = createTestEvent(5);
  await store.appendEvent(event);
  
  // Test getSnapshot
  const snapshot = store.getSnapshot();
  assertEquals(snapshot.events.length, 1);
  assertEquals(snapshot.position, 1);
  assertExists(snapshot.timestamp);
  
  // Test event handler
  let handlerCalled = false;
  store.onNewEvent(() => {
    handlerCalled = true;
  });
  
  await store.appendEvent(createTestEvent(3));
  assertEquals(handlerCalled, true, "Event handler should be called");
  
  // Test checksum validation
  const isValid = store.validateChecksum(event);
  assertEquals(isValid, true, "Should validate checksum");
});

Deno.test("CompressedEventStore - automatic compression on append for old events", async () => {
  const store = new CompressedEventStore();
  
  // Simulate adding an event with old timestamp
  const oldEvent = createTestEvent(35);
  await store.appendEvent(oldEvent);
  
  // Verify it was compressed immediately
  const isCompressed = await store.isEventCompressed(oldEvent.id);
  assertEquals(isCompressed, true, "Event older than 30 days should be compressed on append");
});

Deno.test("CompressedEventStore - batch compression for existing events", async () => {
  const store = new CompressedEventStore();
  
  // Add multiple events of varying ages
  // Note: Events older than 30 days are automatically compressed on append
  const events = [
    createTestEvent(45), // Auto-compressed on append
    createTestEvent(35), // Auto-compressed on append
    createTestEvent(25), // Should NOT be compressed (< 30 days)
    createTestEvent(15), // Should NOT be compressed (< 30 days)
    createTestEvent(5),  // Should NOT be compressed (< 30 days)
  ];
  
  for (const event of events) {
    await store.appendEvent(event);
  }
  
  // Run batch compression
  // Since old events were already compressed on append, batch should find nothing to compress
  const compressionResult = await store.runBatchCompression();
  
  assertEquals(compressionResult.compressedCount, 0, "Should compress 0 events (already compressed on append)");
  assertEquals(compressionResult.skippedCount, 5, "Should skip all 5 events");
});