/**
 * Server Event Store Tests
 * 規約準拠: TypeScript命名規則 <target_file_name>.test.ts
 */

import { assertEquals, assert, assertThrows } from "@std/assert";
import { ServerEventStore } from "./server_event_store.ts";

// テスト命名規則: test_{テスト対象の機能}_{テストの条件}_{期待される結果}

Deno.test("test_appendEvent_with_valid_event_returns_stored_event", async () => {
  const store = new ServerEventStore();
  
  const event = {
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "u1", name: "Alice" },
    timestamp: Date.now(),
    clientId: "client1"
  };
  
  const stored = await store.appendEvent(event);
  
  assertEquals(stored.id, event.id);
  assertEquals(stored.position, 1);
});

Deno.test("test_appendEvent_with_invalid_event_throws_error", () => {
  const store = new ServerEventStore();
  
  assertThrows(
    () => {
      // Use synchronous version since the async is causing issues
      store.appendEvent({
        // Missing required fields
        template: "CREATE_USER",
        params: {}
      } as any);
    },
    Error,
    "Invalid event format"
  );
});

Deno.test("test_getEventsSince_with_position_returns_newer_events", async () => {
  const store = new ServerEventStore();
  
  // Add 5 events
  for (let i = 1; i <= 5; i++) {
    await store.appendEvent({
      id: `evt_${i}`,
      template: "CREATE_USER",
      params: { id: `u${i}` },
      timestamp: Date.now()
    });
  }
  
  const events = store.getEventsSince(3);
  assertEquals(events.length, 2);
  assertEquals(events[0].id, "evt_4");
  assertEquals(events[1].id, "evt_5");
});

Deno.test("test_getLatestEvents_with_count_returns_last_n_events", async () => {
  const store = new ServerEventStore();
  
  // Add 10 events
  for (let i = 1; i <= 10; i++) {
    await store.appendEvent({
      id: `evt_${i}`,
      template: "CREATE_USER",
      params: { id: `u${i}` },
      timestamp: Date.now()
    });
  }
  
  const latest = store.getLatestEvents(3);
  assertEquals(latest.length, 3);
  assertEquals(latest[0].id, "evt_8");
  assertEquals(latest[1].id, "evt_9");
  assertEquals(latest[2].id, "evt_10");
});

Deno.test("test_subscribe_with_new_event_broadcasts_to_others", async () => {
  const store = new ServerEventStore();
  const received: any[] = [];
  
  // Subscribe client2
  store.subscribe("client2", (event) => {
    received.push(event);
  });
  
  // Client1 sends event
  await store.appendEvent({
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "u1" },
    timestamp: Date.now(),
    clientId: "client1"
  });
  
  // Client2 should receive it
  assertEquals(received.length, 1);
  assertEquals(received[0].id, "evt_1");
});

Deno.test("test_subscribe_with_same_client_excludes_sender", async () => {
  const store = new ServerEventStore();
  const client1Received: any[] = [];
  const client2Received: any[] = [];
  
  store.subscribe("client1", (event) => client1Received.push(event));
  store.subscribe("client2", (event) => client2Received.push(event));
  
  // Client1 sends event
  await store.appendEvent({
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "u1" },
    timestamp: Date.now(),
    clientId: "client1"
  });
  
  // Client1 should not receive its own event
  assertEquals(client1Received.length, 0);
  // Client2 should receive it
  assertEquals(client2Received.length, 1);
});

Deno.test("test_unsubscribe_removes_client_from_broadcasts", async () => {
  const store = new ServerEventStore();
  const received: any[] = [];
  
  store.subscribe("client1", (event) => received.push(event));
  store.unsubscribe("client1");
  
  await store.appendEvent({
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "u1" },
    timestamp: Date.now(),
    clientId: "client2"
  });
  
  // Should not receive after unsubscribe
  assertEquals(received.length, 0);
});

Deno.test("test_getEventCount_returns_total_events", async () => {
  const store = new ServerEventStore();
  
  assertEquals(store.getEventCount(), 0);
  
  await store.appendEvent({
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "u1" },
    timestamp: Date.now()
  });
  
  assertEquals(store.getEventCount(), 1);
});