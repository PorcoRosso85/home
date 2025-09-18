/**
 * UnifiedEventStore RED Test
 * Tests transparent retrieval from both local and S3 storage
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.204.0/assert/mod.ts";
import { ServerEventStoreImpl } from "../storage/server_event_store.ts";
import { S3ArchiveAdapter } from "../storage/archive_adapter.ts";
import { InMemoryStorageAdapter } from "../../../storage/s3/mod.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import type { ServerEventStore, EventSnapshot } from "../types.ts";
import { calculateChecksum } from "../event_sourcing/core.ts";
import { UnifiedEventStoreImpl } from "../storage/unified_event_store.ts";
import type { UnifiedEventStore, CacheStats } from "../storage/unified_event_store.ts";


// Helper function to create test events
function createTestEvent(id: string, template: string, timestamp: number): TemplateEvent {
  const params = { data: `test-${id}` };
  return {
    id,
    template,
    params,
    timestamp,
    clientId: "test-client",
    checksum: calculateChecksum(template, params)
  };
}

Deno.test("UnifiedEventStore: should search local storage first before S3", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Add recent events to local store
  const recentEvent1 = createTestEvent("recent-1", "CREATE_USER", Date.now() - 1000);
  const recentEvent2 = createTestEvent("recent-2", "CREATE_POST", Date.now() - 500);
  await localStore.appendEvent(recentEvent1);
  await localStore.appendEvent(recentEvent2);
  
  // Add archived events to S3
  const archivedEvent1 = createTestEvent("archived-1", "CREATE_USER", Date.now() - 86400000 * 8); // 8 days old
  const archivedEvent2 = createTestEvent("archived-2", "CREATE_POST", Date.now() - 86400000 * 10); // 10 days old
  await archiveAdapter.archiveEvent(archivedEvent1);
  await archiveAdapter.archiveEvent(archivedEvent2);
  
  // Initialize unified store
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Act
  const events = await unifiedStore.getEventsSince(0);
  
  // Assert
  assertEquals(events.length, 4);
  // Events should be ordered by timestamp (oldest to newest)
  assertEquals(events[0].id, "archived-2");
  assertEquals(events[1].id, "archived-1");
  assertEquals(events[2].id, "recent-1");
  assertEquals(events[3].id, "recent-2");
});

Deno.test("UnifiedEventStore: should return combined results transparently", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Add mixed events
  const events = [
    createTestEvent("e1", "CREATE_USER", Date.now() - 86400000 * 15), // archived
    createTestEvent("e2", "CREATE_POST", Date.now() - 86400000 * 10), // archived
    createTestEvent("e3", "UPDATE_USER", Date.now() - 86400000 * 5),  // local
    createTestEvent("e4", "CREATE_FOLLOW", Date.now() - 86400000 * 2), // local
    createTestEvent("e5", "CREATE_POST", Date.now() - 1000),          // local
  ];
  
  // Archive old events
  await archiveAdapter.archiveEvent(events[0]);
  await archiveAdapter.archiveEvent(events[1]);
  
  // Add recent events to local
  await localStore.appendEvent(events[2]);
  await localStore.appendEvent(events[3]);
  await localStore.appendEvent(events[4]);
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Act
  const allEvents = await unifiedStore.getEventsSince(0);
  
  // Assert
  assertEquals(allEvents.length, 5);
  assertEquals(allEvents.map(e => e.id), ["e1", "e2", "e3", "e4", "e5"]);
});

Deno.test("UnifiedEventStore: should cache frequently accessed archived events", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Add archived events
  const archivedEvents = Array.from({ length: 10 }, (_, i) => 
    createTestEvent(`archived-${i}`, "CREATE_USER", Date.now() - 86400000 * (20 + i))
  );
  
  for (const event of archivedEvents) {
    await archiveAdapter.archiveEvent(event);
  }
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Clear cache to start fresh
  unifiedStore.clearCache();
  const initialStats = unifiedStore.getCacheStats();
  assertEquals(initialStats.hits, 0);
  assertEquals(initialStats.misses, 0);
  
  // Act - First access (cache miss)
  await unifiedStore.getEventsSince(0);
  const statsAfterFirstAccess = unifiedStore.getCacheStats();
  
  // Second access (should hit cache)
  await unifiedStore.getEventsSince(0);
  const statsAfterSecondAccess = unifiedStore.getCacheStats();
  
  // Assert
  assertEquals(statsAfterFirstAccess.misses, 10); // All archived events are cache misses
  assertEquals(statsAfterFirstAccess.hits, 0);
  assertEquals(statsAfterSecondAccess.hits, 10); // All archived events hit cache
  assertEquals(statsAfterSecondAccess.misses, 10); // No new misses
});

Deno.test("UnifiedEventStore: should maintain event ordering across local and archived", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Create interleaved events with specific timestamps
  const now = Date.now();
  const events = [
    createTestEvent("old-1", "CREATE_USER", now - 86400000 * 30),    // archived
    createTestEvent("old-2", "CREATE_POST", now - 86400000 * 25),    // archived
    createTestEvent("old-3", "UPDATE_USER", now - 86400000 * 20),    // archived
    createTestEvent("recent-1", "CREATE_FOLLOW", now - 86400000 * 5), // local
    createTestEvent("recent-2", "CREATE_POST", now - 86400000 * 2),   // local
    createTestEvent("recent-3", "UPDATE_POST", now - 1000),           // local
  ];
  
  // Archive old events
  await archiveAdapter.archiveEvent(events[0]);
  await archiveAdapter.archiveEvent(events[1]);
  await archiveAdapter.archiveEvent(events[2]);
  
  // Add recent events to local
  await localStore.appendEvent(events[3]);
  await localStore.appendEvent(events[4]);
  await localStore.appendEvent(events[5]);
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Act
  const allEvents = await unifiedStore.getEventsSince(0);
  
  // Assert - Events should be in chronological order
  assertEquals(allEvents.length, 6);
  for (let i = 1; i < allEvents.length; i++) {
    const prevTimestamp = allEvents[i - 1].timestamp;
    const currTimestamp = allEvents[i].timestamp;
    assertEquals(prevTimestamp < currTimestamp, true, 
      `Events not in order: ${allEvents[i - 1].id} (${prevTimestamp}) should come before ${allEvents[i].id} (${currTimestamp})`);
  }
});

Deno.test("UnifiedEventStore: getEventsSince should work with mixed sources", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Create events with positions
  const events = [
    createTestEvent("e1", "CREATE_USER", Date.now() - 86400000 * 20),  // position 0, archived
    createTestEvent("e2", "CREATE_POST", Date.now() - 86400000 * 15),  // position 1, archived
    createTestEvent("e3", "UPDATE_USER", Date.now() - 86400000 * 10),  // position 2, archived
    createTestEvent("e4", "CREATE_FOLLOW", Date.now() - 86400000 * 5), // position 3, local
    createTestEvent("e5", "CREATE_POST", Date.now() - 86400000 * 2),   // position 4, local
    createTestEvent("e6", "UPDATE_POST", Date.now() - 1000),           // position 5, local
  ];
  
  // Archive first 3 events
  for (let i = 0; i < 3; i++) {
    await archiveAdapter.archiveEvent(events[i]);
  }
  
  // Add last 3 events to local
  for (let i = 3; i < 6; i++) {
    await localStore.appendEvent(events[i]);
  }
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Act - Get events from different positions
  const fromStart = await unifiedStore.getEventsSince(0);
  const fromMiddleArchive = await unifiedStore.getEventsSince(2);
  const fromBoundary = await unifiedStore.getEventsSince(3);
  const fromLocal = await unifiedStore.getEventsSince(4);
  
  // Assert
  assertEquals(fromStart.length, 6);
  assertEquals(fromStart.map(e => e.id), ["e1", "e2", "e3", "e4", "e5", "e6"]);
  
  assertEquals(fromMiddleArchive.length, 4);
  assertEquals(fromMiddleArchive.map(e => e.id), ["e3", "e4", "e5", "e6"]);
  
  assertEquals(fromBoundary.length, 3);
  assertEquals(fromBoundary.map(e => e.id), ["e4", "e5", "e6"]);
  
  assertEquals(fromLocal.length, 2);
  assertEquals(fromLocal.map(e => e.id), ["e5", "e6"]);
});

Deno.test("UnifiedEventStore: should handle append operations correctly", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Act - Add new events through unified store
  const newEvent = createTestEvent("new-1", "CREATE_USER", Date.now());
  await unifiedStore.appendEvent(newEvent);
  
  // Assert - Event should be in local store
  const localEvents = await localStore.getEventsSince(0);
  assertEquals(localEvents.length, 1);
  assertEquals(localEvents[0].id, "new-1");
  
  // And should be retrievable through unified store
  const allEvents = await unifiedStore.getEventsSince(0);
  assertEquals(allEvents.length, 1);
  assertEquals(allEvents[0].id, "new-1");
});

Deno.test("UnifiedEventStore: should archive old events based on policy", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Add events of different ages to local store
  const oldEvent1 = createTestEvent("old-1", "CREATE_USER", Date.now() - 86400000 * 35); // 35 days old
  const oldEvent2 = createTestEvent("old-2", "CREATE_POST", Date.now() - 86400000 * 40); // 40 days old
  const recentEvent = createTestEvent("recent-1", "UPDATE_USER", Date.now() - 86400000 * 2); // 2 days old
  
  await localStore.appendEvent(oldEvent1);
  await localStore.appendEvent(oldEvent2);
  await localStore.appendEvent(recentEvent);
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Act - Archive old events
  const archivedCount = await unifiedStore.archiveOldEvents();
  
  // Assert
  assertEquals(archivedCount, 2); // Two events older than 30 days
  
  // Verify old events are now in archive
  const archivedEvents = await archiveAdapter.listArchivedEvents();
  assertEquals(archivedEvents.length, 2);
  assertEquals(archivedEvents.map(e => e.id).sort(), ["old-1", "old-2"]);
  
  // Verify events are still accessible through unified store
  const allEvents = await unifiedStore.getEventsSince(0);
  assertEquals(allEvents.length, 3);
  assertEquals(allEvents.map(e => e.id), ["old-2", "old-1", "recent-1"]);
});

Deno.test("UnifiedEventStore: should handle event notification correctly", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  let notifiedEvent: TemplateEvent | null = null;
  unifiedStore.onNewEvent((event) => {
    notifiedEvent = event;
  });
  
  // Act
  const newEvent = createTestEvent("new-1", "CREATE_USER", Date.now());
  await unifiedStore.appendEvent(newEvent);
  
  // Assert
  assertExists(notifiedEvent);
  assertEquals(notifiedEvent!.id, "new-1");
});

Deno.test("UnifiedEventStore: should validate checksums correctly", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Act & Assert
  const validEvent = createTestEvent("valid-1", "CREATE_USER", Date.now());
  // The checksum is already correct from createTestEvent
  
  const isValid = unifiedStore.validateChecksum(validEvent);
  assertEquals(isValid, true);
});

Deno.test("UnifiedEventStore: getSnapshot should include all events", async () => {
  // Arrange
  const localStore = new ServerEventStoreImpl();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Add archived events
  const archivedEvent = createTestEvent("archived-1", "CREATE_USER", Date.now() - 86400000 * 10);
  await archiveAdapter.archiveEvent(archivedEvent);
  
  // Add local events
  const localEvent = createTestEvent("local-1", "CREATE_POST", Date.now() - 1000);
  await localStore.appendEvent(localEvent);
  
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Act
  const snapshot = unifiedStore.getSnapshot();
  
  // Assert
  assertEquals(snapshot.events.length, 2);
  assertEquals(snapshot.events.map(e => e.id), ["archived-1", "local-1"]);
  assertEquals(snapshot.position, 2);
  assertExists(snapshot.timestamp);
});