import { expect, test, describe, beforeAll, afterAll } from "bun:test";
import { KuzuSyncClient } from "./bun_client.ts";

describe("KuzuDB Local Storage", () => {
  let client: KuzuSyncClient;

  beforeAll(async () => {
    client = new KuzuSyncClient("storage_test");
    await client.initialize();
  });

  afterAll(() => {
    client.close();
  });

  test("persists events across client restarts", async () => {
    // Use a temporary file for persistent storage
    const dbPath = `/tmp/kuzu_test_${Date.now()}.db`;
    
    // Create client with persistent storage
    const persistentClient = new KuzuSyncClient({
      clientId: "persist_test",
      dbPath: dbPath
    });
    await persistentClient.initialize();
    
    // Store events
    await persistentClient.sendEvent("TEST_EVENT_1", { value: 1 });
    await persistentClient.sendEvent("TEST_EVENT_2", { value: 2 });
    
    // Get events before restart
    const eventsBefore = await persistentClient.getLocalEvents();
    expect(eventsBefore.length).toBeGreaterThanOrEqual(2);
    
    // Close client
    persistentClient.close();
    
    // Create new client with same DB path (simulating restart)
    const newClient = new KuzuSyncClient({
      clientId: "persist_test",
      dbPath: dbPath
    });
    await newClient.initialize();
    
    // Should have same events
    const eventsAfter = await newClient.getLocalEvents();
    expect(eventsAfter.length).toBe(eventsBefore.length);
    expect(eventsAfter[0].template).toBe(eventsBefore[0].template);
    
    newClient.close();
    
    // Clean up - KuzuDB creates a directory, not a file
    await Bun.$`rm -rf ${dbPath}`;
  });

  test("tracks sync status per event", async () => {
    await client.sendEvent("UNSYNCED_EVENT", { data: "test" });
    
    const events = await client.getLocalEvents(1);
    expect(events[0].synced).toBe(false);
    
    // Mark as synced
    await client.markEventSynced(events[0].id);
    const updatedEvents = await client.getLocalEvents(1);
    expect(updatedEvents[0].synced).toBe(true);
  });

  test("provides unsync event queue", async () => {
    // Send multiple events while offline
    await client.sendEvent("OFFLINE_1", { order: 1 });
    await client.sendEvent("OFFLINE_2", { order: 2 });
    await client.sendEvent("OFFLINE_3", { order: 3 });
    
    // Get only unsynced events
    const unsynced = await client.getUnsyncedEvents();
    expect(unsynced.length).toBeGreaterThanOrEqual(3);
    
    // Should be in chronological order
    const offlineEvents = unsynced.filter(e => e.template.startsWith("OFFLINE_"));
    expect(offlineEvents[0].template).toBe("OFFLINE_1");
    expect(offlineEvents[1].template).toBe("OFFLINE_2");
    expect(offlineEvents[2].template).toBe("OFFLINE_3");
  });

  test("handles large event payloads", async () => {
    const largeData = {
      bigArray: Array(1000).fill(0).map((_, i) => ({
        id: i,
        data: `Item ${i}`,
        nested: { value: i * 2 }
      }))
    };
    
    await client.sendEvent("LARGE_EVENT", largeData);
    
    const events = await client.getLocalEvents(1);
    expect(events[0].params.bigArray.length).toBe(1000);
    expect(events[0].params.bigArray[999].id).toBe(999);
  });
});