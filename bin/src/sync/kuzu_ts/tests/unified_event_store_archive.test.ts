/**
 * Test suite for UnifiedEventStore archive functionality
 * Verifies that events are properly removed from local storage after successful archiving
 */

import { assertEquals, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { UnifiedEventStoreImpl } from "../storage/unified_event_store.ts";
import { MutableServerEventStore } from "../storage/mutable_event_store.ts";
import { S3ArchiveAdapter } from "../storage/archive_adapter.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import { calculateChecksum } from "../event_sourcing/core.ts";

// Helper to create test events
function createTestEvent(id: string, timestamp: number, template = "test-template"): TemplateEvent {
  const params = { test: true };
  return {
    id,
    template,
    params,
    timestamp,
    clientId: "test-client",
    checksum: calculateChecksum(template, params)
  };
}

Deno.test("UnifiedEventStore - archiveOldEvents removes events from local storage", async () => {
  // Create instances
  const localStore = new MutableServerEventStore();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Initialize unified store
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Add some events to local store
  const now = Date.now();
  const oldEvent1 = createTestEvent("event-1", now - 31 * 24 * 60 * 60 * 1000); // 31 days old
  const oldEvent2 = createTestEvent("event-2", now - 35 * 24 * 60 * 60 * 1000); // 35 days old
  const recentEvent = createTestEvent("event-3", now - 1 * 24 * 60 * 60 * 1000); // 1 day old
  
  await localStore.appendEvent(oldEvent1);
  await localStore.appendEvent(oldEvent2);
  await localStore.appendEvent(recentEvent);
  
  // Verify initial state
  const initialEvents = await localStore.getEventsSince(0);
  assertEquals(initialEvents.length, 3);
  
  // Archive old events
  const archivedCount = await unifiedStore.archiveOldEvents();
  assertEquals(archivedCount, 2, "Should archive 2 old events");
  
  // Verify events were removed from local store
  const remainingLocalEvents = await localStore.getEventsSince(0);
  assertEquals(remainingLocalEvents.length, 1, "Only recent event should remain in local store");
  assertEquals(remainingLocalEvents[0].id, "event-3");
  
  // Verify archived events are still accessible through unified store
  const allEvents = await unifiedStore.getEventsSince(0);
  assertEquals(allEvents.length, 3, "All events should still be accessible through unified store");
  
  // Verify archived events are in S3
  const archivedEvents = await archiveAdapter.listArchivedEvents();
  assertEquals(archivedEvents.length, 2);
  assertEquals(archivedEvents.map(e => e.id).sort(), ["event-1", "event-2"]);
});

Deno.test("UnifiedEventStore - archiveOldEvents handles partial failures gracefully", async () => {
  // Create instances
  const localStore = new MutableServerEventStore();
  
  // Create a custom S3ArchiveAdapter that fails for specific events
  const archiveAdapter = new S3ArchiveAdapter();
  const originalArchiveEvent = archiveAdapter.archiveEvent.bind(archiveAdapter);
  archiveAdapter.archiveEvent = async (event: TemplateEvent) => {
    if (event.id === "event-fail") {
      throw new Error("Simulated archive failure");
    }
    return originalArchiveEvent(event);
  };
  
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Initialize unified store
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Add events to local store
  const now = Date.now();
  const oldEvent1 = createTestEvent("event-1", now - 31 * 24 * 60 * 60 * 1000);
  const oldEvent2 = createTestEvent("event-fail", now - 35 * 24 * 60 * 60 * 1000);
  const oldEvent3 = createTestEvent("event-3", now - 40 * 24 * 60 * 60 * 1000);
  
  await localStore.appendEvent(oldEvent1);
  await localStore.appendEvent(oldEvent2);
  await localStore.appendEvent(oldEvent3);
  
  // Archive old events - should succeed for 2 valid events
  const archivedCount = await unifiedStore.archiveOldEvents();
  assertEquals(archivedCount, 2, "Should archive 2 valid events despite 1 failure");
  
  // Verify only valid events were removed from local store
  const remainingLocalEvents = await localStore.getEventsSince(0);
  assertEquals(remainingLocalEvents.length, 1);
  assertEquals(remainingLocalEvents[0].id, "event-fail");
});

Deno.test("UnifiedEventStore - archiveOldEvents returns 0 when no archivable events", async () => {
  // Create instances
  const localStore = new MutableServerEventStore();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Initialize unified store
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Add only recent events
  const now = Date.now();
  const recentEvent1 = createTestEvent("event-1", now - 1 * 24 * 60 * 60 * 1000); // 1 day old
  const recentEvent2 = createTestEvent("event-2", now - 2 * 24 * 60 * 60 * 1000); // 2 days old
  
  await localStore.appendEvent(recentEvent1);
  await localStore.appendEvent(recentEvent2);
  
  // Archive old events - should find none
  const archivedCount = await unifiedStore.archiveOldEvents();
  assertEquals(archivedCount, 0);
  
  // Verify no events were removed
  const remainingLocalEvents = await localStore.getEventsSince(0);
  assertEquals(remainingLocalEvents.length, 2);
});

Deno.test("UnifiedEventStore - getEventsSince deduplicates between local and archived", async () => {
  // Create instances
  const localStore = new MutableServerEventStore();
  const archiveAdapter = new S3ArchiveAdapter();
  const unifiedStore = new UnifiedEventStoreImpl();
  
  // Initialize unified store
  await unifiedStore.initialize(localStore, archiveAdapter);
  
  // Create an event
  const now = Date.now();
  const event = createTestEvent("event-1", now - 8 * 24 * 60 * 60 * 1000);
  
  // Add to local store
  await localStore.appendEvent(event);
  
  // Also add directly to archive (simulating a duplicate)
  await archiveAdapter.archiveEvent(event);
  
  // Get events through unified store
  const allEvents = await unifiedStore.getEventsSince(0);
  
  // Should only have one instance of the event
  assertEquals(allEvents.length, 1);
  assertEquals(allEvents[0].id, "event-1");
});

Deno.test("UnifiedEventStore - throws error if not initialized", async () => {
  const unifiedStore = new UnifiedEventStoreImpl();
  
  await assertRejects(
    async () => await unifiedStore.archiveOldEvents(),
    Error,
    "UnifiedEventStore not initialized"
  );
});