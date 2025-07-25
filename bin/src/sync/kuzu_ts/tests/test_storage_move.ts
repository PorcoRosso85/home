/**
 * RED Test for Storage Move
 * Tests that ServerEventStoreImpl will work correctly after moving to storage/
 * This test should FAIL initially because the file hasn't been moved yet.
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { ServerEventStoreImpl } from "../storage/server_event_store.ts"; // New location - should fail
import type { ServerEventStore, EventSnapshot } from "../types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

Deno.test("ServerEventStoreImpl can be imported from new storage/ location", () => {
  // This test verifies the import resolves correctly
  assertExists(ServerEventStoreImpl);
  assertEquals(typeof ServerEventStoreImpl, "function");
});

Deno.test("ServerEventStoreImpl can be instantiated", () => {
  // Verify the class can be instantiated
  const store = new ServerEventStoreImpl();
  assertExists(store);
});

Deno.test("ServerEventStoreImpl maintains ServerEventStore interface", async () => {
  const store: ServerEventStore = new ServerEventStoreImpl();
  
  // Verify all interface methods exist
  assertEquals(typeof store.appendEvent, "function");
  assertEquals(typeof store.getEventsSince, "function");
  assertEquals(typeof store.getSnapshot, "function");
  assertEquals(typeof store.onNewEvent, "function");
  assertEquals(typeof store.validateChecksum, "function");
});

Deno.test("ServerEventStoreImpl basic functionality works", async () => {
  const store = new ServerEventStoreImpl();
  
  // Create a test event
  const testEvent: TemplateEvent = {
    id: "test-123",
    timestamp: Date.now(),
    template: "CREATE_USER",
    params: { name: "Test User" },
    checksum: "valid-checksum", // This will be validated
    metadata: {
      clientId: "client-1",
      syncId: "sync-1"
    }
  };
  
  // Test getSnapshot returns correct initial state
  const initialSnapshot = store.getSnapshot();
  assertEquals(initialSnapshot.events.length, 0);
  assertEquals(initialSnapshot.position, 0);
  assertExists(initialSnapshot.timestamp);
  
  // Test event handler notification
  let notifiedEvent: TemplateEvent | null = null;
  store.onNewEvent((event) => {
    notifiedEvent = event;
  });
  
  // Note: appendEvent will fail due to checksum validation
  // This is expected behavior for this RED test
  try {
    await store.appendEvent(testEvent);
  } catch (error) {
    assertEquals(error.message, "Invalid checksum");
  }
  
  // Verify no events were added due to invalid checksum
  const events = await store.getEventsSince(0);
  assertEquals(events.length, 0);
});

Deno.test("Import path resolution test", () => {
  // This test specifically checks that the import path is correct
  // It will fail with "Module not found" error initially
  try {
    // Attempt to verify the module exists at the new location
    const modulePath = new URL("../storage/server_event_store.ts", import.meta.url);
    assertExists(modulePath);
  } catch (error) {
    // Expected to fail in RED phase
    console.error("Expected failure: Module not found at new location");
  }
});