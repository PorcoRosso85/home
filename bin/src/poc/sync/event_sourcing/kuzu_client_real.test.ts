/**
 * Real KuzuDB WASM Client Tests (ESM)
 * 規約準拠: test_{機能}_{条件}_{結果}
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";
import { KuzuEventClient } from "./kuzu_client_real.ts";

Deno.test("test_kuzu_client_initialization_creates_schema", async () => {
  const client = new KuzuEventClient("client1");
  await client.initialize();
  
  // Verify schema by trying to query empty tables
  const users = await client.getUsers();
  assertEquals(users.length, 0);
  
  const posts = await client.getPosts();
  assertEquals(posts.length, 0);
});

Deno.test("test_executeTemplate_with_create_user_stores_in_kuzu", async () => {
  const client = new KuzuEventClient("client1");
  await client.initialize();
  
  const event = await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: new Date().toISOString()
  });
  
  // Verify event generated
  assertEquals(event.template, "CREATE_USER");
  assertEquals(event.params.name, "Alice");
  assert(event.id.startsWith("evt_"));
  
  // Verify stored in KuzuDB
  const users = await client.getUsers();
  assertEquals(users.length, 1);
  assertEquals(users[0]["u.name"], "Alice");
  assertEquals(users[0]["u.email"], "alice@example.com");
});

Deno.test("test_executeTemplate_with_update_user_modifies_data", async () => {
  const client = new KuzuEventClient("client1");
  await client.initialize();
  
  // Create user
  await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: new Date().toISOString()
  });
  
  // Update user
  await client.executeTemplate("UPDATE_USER", {
    id: "u1",
    name: "Alice Updated",
    email: "alice.updated@example.com"
  });
  
  // Verify update
  const users = await client.getUsers();
  assertEquals(users.length, 1);
  assertEquals(users[0]["u.name"], "Alice Updated");
  assertEquals(users[0]["u.email"], "alice.updated@example.com");
});

Deno.test("test_executeTemplate_with_follow_creates_relationship", async () => {
  const client = new KuzuEventClient("client1");
  await client.initialize();
  
  // Create users
  await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: new Date().toISOString()
  });
  
  await client.executeTemplate("CREATE_USER", {
    id: "u2",
    name: "Bob",
    email: "bob@example.com",
    createdAt: new Date().toISOString()
  });
  
  // Create follow relationship
  await client.executeTemplate("FOLLOW_USER", {
    followerId: "u1",
    targetId: "u2",
    since: new Date().toISOString()
  });
  
  // Verify relationship
  const followers = await client.getFollowers("u2");
  assertEquals(followers.length, 1);
  assertEquals(followers[0]["follower.name"], "Alice");
});

Deno.test("test_executeTemplate_with_create_post_links_to_author", async () => {
  const client = new KuzuEventClient("client1");
  await client.initialize();
  
  // Create user
  await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: new Date().toISOString()
  });
  
  // Create post
  const event = await client.executeTemplate("CREATE_POST", {
    id: "p1",
    content: "Hello KuzuDB!",
    authorId: "u1",
    createdAt: new Date().toISOString()
  });
  
  // Verify post
  const posts = await client.getPosts();
  assertEquals(posts.length, 1);
  assertEquals(posts[0]["p.content"], "Hello KuzuDB!");
  assertEquals(posts[0]["p.authorId"], "u1");
});

Deno.test("test_executeTemplate_with_delete_post_removes_node", async () => {
  const client = new KuzuEventClient("client1");
  await client.initialize();
  
  // Create post
  await client.executeTemplate("CREATE_POST", {
    id: "p1",
    content: "To be deleted",
    authorId: "u1",
    createdAt: new Date().toISOString()
  });
  
  // Verify created
  let posts = await client.getPosts();
  assertEquals(posts.length, 1);
  
  // Delete post
  await client.executeTemplate("DELETE_POST", { id: "p1" });
  
  // Verify deleted
  posts = await client.getPosts();
  assertEquals(posts.length, 0);
});

Deno.test("test_getEvents_returns_all_executed_events", async () => {
  const client = new KuzuEventClient("client1");
  await client.initialize();
  
  // Execute multiple templates
  await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: new Date().toISOString()
  });
  
  await client.executeTemplate("CREATE_POST", {
    id: "p1",
    content: "Test post",
    authorId: "u1",
    createdAt: new Date().toISOString()
  });
  
  const events = client.getEvents();
  assertEquals(events.length, 2);
  assertEquals(events[0].template, "CREATE_USER");
  assertEquals(events[1].template, "CREATE_POST");
  
  // Verify hasExecutedTemplate
  assert(client.hasExecutedTemplate("CREATE_USER"));
  assert(client.hasExecutedTemplate("CREATE_POST"));
  assert(!client.hasExecutedTemplate("DELETE_POST"));
});

Deno.test("test_event_checksum_is_consistent", async () => {
  const client1 = new KuzuEventClient("client1");
  const client2 = new KuzuEventClient("client2");
  
  await client1.initialize();
  await client2.initialize();
  
  const params = {
    id: "u1",
    name: "Alice",
    email: "alice@example.com",
    createdAt: "2024-01-01T00:00:00Z"
  };
  
  const event1 = await client1.executeTemplate("CREATE_USER", params);
  const event2 = await client2.executeTemplate("CREATE_USER", params);
  
  // Same template and params should produce same checksum
  assertEquals(event1.checksum, event2.checksum);
});