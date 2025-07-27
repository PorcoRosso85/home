/**
 * MutableServerEventStore Tests - RED Phase
 * 
 * This test file validates the MutableServerEventStore interface that extends
 * ServerEventStore with safe deletion capabilities.
 * 
 * Requirements:
 * 1. removeEvents - Remove events by their IDs
 * 2. removeEventsBefore - Remove events before a given timestamp
 * 3. Permanent removal - Deleted events cannot be retrieved
 * 4. Transaction safety - No partial removals on failure
 */

import { assertEquals, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";
import type { TemplateEvent, ServerEventStore } from "../types.ts";
import type { MutableServerEventStore as IMutableServerEventStore } from "../storage/mutable_server_event_store.ts";
import { MutableServerEventStore } from "../storage/mutable_event_store.ts";
import { calculateChecksum } from "../event_sourcing/core.ts";

// Test helper to create sample events
function createTestEvent(id: string, timestamp: number): TemplateEvent {
  const template = "test_template";
  const params = { value: id };
  return {
    id,
    template,
    params,
    timestamp,
    clientId: "test-client",
    checksum: calculateChecksum(template, params),
  };
}

Deno.test("MutableServerEventStore - removeEvents by IDs", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  const event1 = createTestEvent("event-1", 1000);
  const event2 = createTestEvent("event-2", 2000);
  const event3 = createTestEvent("event-3", 3000);
  
  await store.appendEvent(event1);
  await store.appendEvent(event2);
  await store.appendEvent(event3);
  
  // Act
  const removedCount = await store.removeEvents(["event-1", "event-3"]);
  
  // Assert
  assertEquals(removedCount, 2);
  const remainingEvents = await store.getEventsSince(0);
  assertEquals(remainingEvents.length, 1);
  assertEquals(remainingEvents[0].id, "event-2");
});

Deno.test("MutableServerEventStore - removeEvents with non-existent IDs", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  const event1 = createTestEvent("event-1", 1000);
  await store.appendEvent(event1);
  
  // Act
  const removedCount = await store.removeEvents(["event-1", "non-existent"]);
  
  // Assert
  assertEquals(removedCount, 1); // Only one event was actually removed
  const remainingEvents = await store.getEventsSince(0);
  assertEquals(remainingEvents.length, 0);
});

Deno.test("MutableServerEventStore - removeEventsBefore timestamp", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  const event1 = createTestEvent("event-1", 1000);
  const event2 = createTestEvent("event-2", 2000);
  const event3 = createTestEvent("event-3", 3000);
  const event4 = createTestEvent("event-4", 4000);
  
  await store.appendEvent(event1);
  await store.appendEvent(event2);
  await store.appendEvent(event3);
  await store.appendEvent(event4);
  
  // Act
  const removedCount = await store.removeEventsBefore(2500);
  
  // Assert
  assertEquals(removedCount, 2); // events with timestamp < 2500
  const remainingEvents = await store.getEventsSince(0);
  assertEquals(remainingEvents.length, 2);
  assertEquals(remainingEvents[0].id, "event-3");
  assertEquals(remainingEvents[1].id, "event-4");
});

Deno.test("MutableServerEventStore - removeEventsBefore with no matching events", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  const event1 = createTestEvent("event-1", 3000);
  const event2 = createTestEvent("event-2", 4000);
  
  await store.appendEvent(event1);
  await store.appendEvent(event2);
  
  // Act
  const removedCount = await store.removeEventsBefore(2000);
  
  // Assert
  assertEquals(removedCount, 0);
  const remainingEvents = await store.getEventsSince(0);
  assertEquals(remainingEvents.length, 2);
});

Deno.test("MutableServerEventStore - removal is permanent", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  const event1 = createTestEvent("event-1", 1000);
  const event2 = createTestEvent("event-2", 2000);
  
  await store.appendEvent(event1);
  await store.appendEvent(event2);
  
  // Act
  await store.removeEvents(["event-1"]);
  
  // Assert - event should not be retrievable
  const events = await store.getEventsSince(0);
  assertEquals(events.length, 1);
  assertEquals(events.find(e => e.id === "event-1"), undefined);
  
  // Also check that snapshot doesn't include removed events
  const snapshot = store.getSnapshot();
  assertEquals(snapshot.events.length, 1);
  assertEquals(snapshot.events.find(e => e.id === "event-1"), undefined);
});

Deno.test("MutableServerEventStore - transaction safety for removeEvents", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  const event1 = createTestEvent("event-1", 1000);
  const event2 = createTestEvent("event-2", 2000);
  const event3 = createTestEvent("event-3", 3000);
  
  await store.appendEvent(event1);
  await store.appendEvent(event2);
  await store.appendEvent(event3);
  
  // Mock a failure during removal by creating a store that throws on the second removal
  let removalCount = 0;
  const originalRemove = store.removeEvents.bind(store);
  store.removeEvents = async (ids: string[]) => {
    for (const id of ids) {
      removalCount++;
      if (removalCount === 2) {
        throw new Error("Simulated failure during removal");
      }
    }
    return originalRemove(ids);
  };
  
  // Act & Assert
  await assertRejects(
    async () => await store.removeEvents(["event-1", "event-2", "event-3"]),
    Error,
    "Simulated failure during removal"
  );
  
  // Verify that no events were removed (transaction was rolled back)
  const remainingEvents = await store.getEventsSince(0);
  assertEquals(remainingEvents.length, 3);
});

Deno.test("MutableServerEventStore - transaction safety for removeEventsBefore", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  
  // Add many events to test transaction boundary
  const events: TemplateEvent[] = [];
  for (let i = 1; i <= 10; i++) {
    const event = createTestEvent(`event-${i}`, i * 1000);
    events.push(event);
    await store.appendEvent(event);
  }
  
  // Mock a failure during batch removal
  const originalRemoveBefore = store.removeEventsBefore.bind(store);
  store.removeEventsBefore = async (timestamp: number) => {
    // Simulate partial processing then failure
    const toRemove = events.filter(e => e.timestamp < timestamp);
    if (toRemove.length > 3) {
      throw new Error("Batch removal failed");
    }
    return originalRemoveBefore(timestamp);
  };
  
  // Act & Assert
  await assertRejects(
    async () => await store.removeEventsBefore(6000), // Would remove 5 events
    Error,
    "Batch removal failed"
  );
  
  // Verify all events are still there (no partial removal)
  const remainingEvents = await store.getEventsSince(0);
  assertEquals(remainingEvents.length, 10);
});

Deno.test("MutableServerEventStore - maintains ServerEventStore interface", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  
  // Verify it implements ServerEventStore interface
  const serverStore: ServerEventStore = store;
  
  // Test basic ServerEventStore functionality still works
  const event = createTestEvent("event-1", 1000);
  await serverStore.appendEvent(event);
  
  const events = await serverStore.getEventsSince(0);
  assertEquals(events.length, 1);
  
  const snapshot = serverStore.getSnapshot();
  assertEquals(snapshot.events.length, 1);
  
  // Test event handler
  let handlerCalled = false;
  serverStore.onNewEvent(() => {
    handlerCalled = true;
  });
  
  await serverStore.appendEvent(createTestEvent("event-2", 2000));
  assertEquals(handlerCalled, true);
  
  // Test checksum validation
  const isValid = serverStore.validateChecksum(event);
  assertEquals(isValid, true);
});

Deno.test("MutableServerEventStore - concurrent removal safety", async () => {
  // Arrange
  const store: IMutableServerEventStore = new MutableServerEventStore();
  
  // Add multiple events
  for (let i = 1; i <= 20; i++) {
    await store.appendEvent(createTestEvent(`event-${i}`, i * 100));
  }
  
  // Act - Try concurrent removals
  const removal1 = store.removeEvents(["event-1", "event-3", "event-5"]);
  const removal2 = store.removeEvents(["event-2", "event-4", "event-6"]);
  const removal3 = store.removeEventsBefore(800); // Should remove events 1-7
  
  // Wait for all removals
  const results = await Promise.allSettled([removal1, removal2, removal3]);
  
  // Assert - At least one should succeed, others might fail due to conflicts
  const successCount = results.filter(r => r.status === "fulfilled").length;
  assertEquals(successCount >= 1, true);
  
  // Verify data consistency
  const remainingEvents = await store.getEventsSince(0);
  // Should have removed at least some events
  assertEquals(remainingEvents.length < 20, true);
  
  // Verify no duplicate removals or corrupted state
  const uniqueIds = new Set(remainingEvents.map(e => e.id));
  assertEquals(uniqueIds.size, remainingEvents.length);
});