/**
 * Tests for extracting archivable events from the event store
 * イベントストアからアーカイブ可能なイベントを抽出するテスト
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { ServerEventStoreImpl } from "../storage/server_event_store.ts";
import { shouldArchive } from "../storage/archive_policy.ts";
import { calculateChecksum } from "../event_sourcing/core.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

Deno.test("ServerEventStore getArchivableEvents - returns events older than 30 days sorted by timestamp", async () => {
  // Arrange
  const store = new ServerEventStoreImpl();
  const currentTime = Date.now();
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  
  // Create events with different ages
  const events: TemplateEvent[] = [
    {
      id: "event-1",
      template: "CREATE_USER",
      params: { name: "User 1" },
      timestamp: currentTime - (35 * millisecondsPerDay), // 35 days old
      checksum: calculateChecksum("CREATE_USER", { name: "User 1" })
    },
    {
      id: "event-2",
      template: "CREATE_USER",
      params: { name: "User 2" },
      timestamp: currentTime - (10 * millisecondsPerDay), // 10 days old
      checksum: calculateChecksum("CREATE_USER", { name: "User 2" })
    },
    {
      id: "event-3",
      template: "CREATE_POST",
      params: { content: "Post 1" },
      timestamp: currentTime - (45 * millisecondsPerDay), // 45 days old
      checksum: calculateChecksum("CREATE_POST", { content: "Post 1" })
    },
    {
      id: "event-4",
      template: "CREATE_USER",
      params: { name: "User 3" },
      timestamp: currentTime - (30 * millisecondsPerDay), // Exactly 30 days old
      checksum: calculateChecksum("CREATE_USER", { name: "User 3" })
    },
    {
      id: "event-5",
      template: "CREATE_POST",
      params: { content: "Post 2" },
      timestamp: currentTime - (5 * millisecondsPerDay), // 5 days old
      checksum: calculateChecksum("CREATE_POST", { content: "Post 2" })
    }
  ];
  
  // Append events to store
  for (const event of events) {
    await store.appendEvent(event);
  }
  
  // Act
  const archivableEvents = await store.getArchivableEvents();
  
  // Assert
  assertExists(archivableEvents);
  assertEquals(archivableEvents.length, 3); // Events 1, 3, and 4 are archivable
  
  // Verify all returned events are archivable using shouldArchive
  for (const event of archivableEvents) {
    assertEquals(shouldArchive(event, currentTime), true);
  }
  
  // Verify events are sorted by timestamp (oldest first)
  assertEquals(archivableEvents[0].id, "event-3"); // 45 days old
  assertEquals(archivableEvents[1].id, "event-1"); // 35 days old
  assertEquals(archivableEvents[2].id, "event-4"); // 30 days old
});

Deno.test("ServerEventStore getArchivableEvents - handles empty store", async () => {
  // Arrange
  const store = new ServerEventStoreImpl();
  
  // Act
  const archivableEvents = await store.getArchivableEvents();
  
  // Assert
  assertExists(archivableEvents);
  assertEquals(archivableEvents.length, 0);
});

Deno.test("ServerEventStore getArchivableEvents - handles store with only recent events", async () => {
  // Arrange
  const store = new ServerEventStoreImpl();
  const currentTime = Date.now();
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  
  // Create only recent events
  const recentEvents: TemplateEvent[] = [
    {
      id: "recent-1",
      template: "CREATE_USER",
      params: { name: "Recent User 1" },
      timestamp: currentTime - (5 * millisecondsPerDay),
      checksum: calculateChecksum("CREATE_USER", { name: "Recent User 1" })
    },
    {
      id: "recent-2",
      template: "CREATE_POST",
      params: { content: "Recent Post" },
      timestamp: currentTime - (1 * millisecondsPerDay),
      checksum: calculateChecksum("CREATE_POST", { content: "Recent Post" })
    }
  ];
  
  for (const event of recentEvents) {
    await store.appendEvent(event);
  }
  
  // Act
  const archivableEvents = await store.getArchivableEvents();
  
  // Assert
  assertExists(archivableEvents);
  assertEquals(archivableEvents.length, 0);
});

Deno.test("ServerEventStore getArchivableEvents - performance test with 1000 events", async () => {
  // Arrange
  const store = new ServerEventStoreImpl();
  const currentTime = Date.now();
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  
  // Create 1000 events with varying ages
  const events: TemplateEvent[] = [];
  for (let i = 0; i < 1000; i++) {
    // Distribute events across 0-60 days old
    const daysOld = i % 60;
    const template = i % 2 === 0 ? "CREATE_USER" : "CREATE_POST";
    const params = { data: `Data ${i}` };
    events.push({
      id: `event-${i}`,
      template,
      params,
      timestamp: currentTime - (daysOld * millisecondsPerDay),
      checksum: calculateChecksum(template, params)
    });
  }
  
  // Append all events
  for (const event of events) {
    await store.appendEvent(event);
  }
  
  // Act
  const startTime = performance.now();
  const archivableEvents = await store.getArchivableEvents();
  const endTime = performance.now();
  const executionTime = endTime - startTime;
  
  // Assert
  assertExists(archivableEvents);
  
  // About 490 events should be archivable (those 30-59 days old)
  // Days 30-39: 17 occurrences each = 170 events
  // Days 40-59: 16 occurrences each = 320 events
  // Total: 490 events
  assertEquals(archivableEvents.length, 490);
  
  // Verify all returned events are actually archivable
  for (const event of archivableEvents) {
    assertEquals(shouldArchive(event, currentTime), true);
  }
  
  // Performance assertion: should complete within 100ms
  assertEquals(executionTime < 100, true, `Execution took ${executionTime}ms, should be under 100ms`);
  
  // Verify sorting
  for (let i = 1; i < archivableEvents.length; i++) {
    assertEquals(
      archivableEvents[i-1].timestamp <= archivableEvents[i].timestamp,
      true,
      "Events should be sorted by timestamp (oldest first)"
    );
  }
});

Deno.test("ServerEventStore getArchivableEvents - uses current time for shouldArchive", async () => {
  // Arrange
  const store = new ServerEventStoreImpl();
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  
  // Create an event that's 31 days old relative to a fixed time
  const fixedTime = 1700000000000; // Fixed timestamp
  const oldEvent: TemplateEvent = {
    id: "old-event",
    template: "CREATE_USER",
    params: { name: "Old User" },
    timestamp: fixedTime - (31 * millisecondsPerDay),
    checksum: calculateChecksum("CREATE_USER", { name: "Old User" })
  };
  
  await store.appendEvent(oldEvent);
  
  // Act
  const archivableEvents = await store.getArchivableEvents();
  
  // Assert
  // The actual archivability depends on the current time when getArchivableEvents is called
  const currentTime = Date.now();
  const expectedArchivable = shouldArchive(oldEvent, currentTime);
  
  if (expectedArchivable) {
    assertEquals(archivableEvents.length, 1);
    assertEquals(archivableEvents[0].id, "old-event");
  } else {
    assertEquals(archivableEvents.length, 0);
  }
});