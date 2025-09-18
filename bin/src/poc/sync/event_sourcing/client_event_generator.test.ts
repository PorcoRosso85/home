/**
 * Client Event Generator Tests
 * 規約準拠: TypeScript命名規則 <target_file_name>.test.ts
 */

import { assertEquals, assert } from "@std/assert";
import { ClientEventGenerator, MockKuzuClient } from "./client_event_generator.ts";

// テスト命名規則: test_{テスト対象の機能}_{テストの条件}_{期待される結果}

Deno.test("test_generateEvent_with_valid_params_returns_complete_event", () => {
  const generator = new ClientEventGenerator("client1");
  
  const event = generator.generateEvent("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com"
  });
  
  assert(event.id.startsWith("evt_"));
  assertEquals(event.template, "CREATE_USER");
  assertEquals(event.params.name, "Alice");
  assertEquals(event.clientId, "client1");
  assert(event.timestamp > 0);
  assert(event.checksum);
});

Deno.test("test_generateEvent_with_different_templates_creates_unique_ids", () => {
  const generator = new ClientEventGenerator("client1");
  
  const event1 = generator.generateEvent("CREATE_USER", { id: "u1" });
  const event2 = generator.generateEvent("UPDATE_USER", { id: "u1" });
  
  assert(event1.id !== event2.id);
});

Deno.test("test_mockKuzuClient_executeTemplate_stores_event_locally", async () => {
  const client = new MockKuzuClient("client1");
  
  const event = await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com"
  });
  
  const events = client.getEvents();
  assertEquals(events.length, 1);
  assertEquals(events[0].id, event.id);
});

Deno.test("test_mockKuzuClient_with_create_user_updates_local_state", async () => {
  const client = new MockKuzuClient("client1");
  
  await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com"
  });
  
  const state = client.getLocalState();
  const user = state.get("user:u1");
  assertEquals(user.name, "Alice");
  assertEquals(user.email, "alice@example.com");
});

Deno.test("test_mockKuzuClient_with_update_user_modifies_existing_state", async () => {
  const client = new MockKuzuClient("client1");
  
  // Create user
  await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com"
  });
  
  // Update user
  await client.executeTemplate("UPDATE_USER", {
    id: "u1",
    name: "Alice Smith"
  });
  
  const state = client.getLocalState();
  const user = state.get("user:u1");
  assertEquals(user.name, "Alice Smith");
  assertEquals(user.email, "alice@example.com"); // Email should be preserved
});

Deno.test("test_mockKuzuClient_with_follow_user_creates_relationship", async () => {
  const client = new MockKuzuClient("client1");
  
  // Create users first
  await client.executeTemplate("CREATE_USER", { id: "u1", name: "Alice" });
  await client.executeTemplate("CREATE_USER", { id: "u2", name: "Bob" });
  
  // Create follow relationship
  await client.executeTemplate("FOLLOW_USER", {
    followerId: "u1",
    targetId: "u2",
    followedAt: new Date().toISOString()
  });
  
  const state = client.getLocalState();
  const follow = state.get("follow:u1:u2");
  assert(follow);
  assertEquals(follow.followerId, "u1");
  assertEquals(follow.targetId, "u2");
});

Deno.test("test_eventGenerator_checksum_is_deterministic", () => {
  const generator1 = new ClientEventGenerator("client1");
  const generator2 = new ClientEventGenerator("client2");
  
  const params = { id: "u1", name: "Alice" };
  const event1 = generator1.generateEvent("CREATE_USER", params);
  const event2 = generator2.generateEvent("CREATE_USER", params);
  
  // Same template and params should produce same checksum
  assertEquals(event1.checksum, event2.checksum);
});