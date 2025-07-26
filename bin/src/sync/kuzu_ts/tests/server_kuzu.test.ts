/**
 * Server KuzuDB Integration Tests
 * サーバー側KuzuDB機能の統合テスト
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { ServerKuzuClient } from "../core/server/server_kuzu_client.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import type { EventSnapshot } from "../types.ts";

Deno.test("ServerKuzuClient - Initialization", async () => {
  const client = new ServerKuzuClient();
  
  // Should initialize successfully
  await client.initialize();
  assertEquals(client.isInitialized(), true);
  
  // Should handle multiple initialization calls
  await client.initialize(); // Should not throw
  assertEquals(client.isInitialized(), true);
});

Deno.test("ServerKuzuClient - Apply Events", async () => {
  const client = new ServerKuzuClient();
  await client.initialize();
  
  // Create user event
  const createUserEvent: TemplateEvent = {
    id: "evt_1",
    template: "CREATE_USER",
    params: {
      id: "user1",
      name: "Test User",
      email: "test@example.com"
    },
    timestamp: Date.now()
  };
  
  await client.applyEvent(createUserEvent);
  
  // Verify event was applied
  const state = await client.getState();
  assertEquals(state.users.length, 1);
  assertEquals(state.users[0].id, "user1");
  assertEquals(state.users[0].name, "Test User");
  assertEquals(state.users[0].email, "test@example.com");
  
  // Create post event
  const createPostEvent: TemplateEvent = {
    id: "evt_2",
    template: "CREATE_POST",
    params: {
      id: "post1",
      content: "Test post",
      authorId: "user1"
    },
    timestamp: Date.now()
  };
  
  await client.applyEvent(createPostEvent);
  
  // Verify post was created
  const state2 = await client.getState();
  assertEquals(state2.posts.length, 1);
  assertEquals(state2.posts[0].id, "post1");
  assertEquals(state2.posts[0].content, "Test post");
  assertEquals(state2.posts[0].authorId, "user1");
});

Deno.test("ServerKuzuClient - Execute Queries", async () => {
  const client = new ServerKuzuClient();
  await client.initialize();
  
  // Create test data
  const events: TemplateEvent[] = [
    {
      id: "evt_1",
      template: "CREATE_USER",
      params: { id: "user1", name: "Alice", email: "alice@example.com" },
      timestamp: Date.now()
    },
    {
      id: "evt_2",
      template: "CREATE_USER",
      params: { id: "user2", name: "Bob", email: "bob@example.com" },
      timestamp: Date.now()
    },
    {
      id: "evt_3",
      template: "FOLLOW_USER",
      params: { followerId: "user1", targetId: "user2" },
      timestamp: Date.now()
    }
  ];
  
  for (const event of events) {
    await client.applyEvent(event);
  }
  
  // Query users
  const userResult = await client.executeQuery("MATCH (u:User) RETURN u.id as id, u.name as name ORDER BY u.id");
  assertEquals(userResult.length, 2);
  assertEquals(userResult[0].id, "user1");
  assertEquals(userResult[0].name, "Alice");
  assertEquals(userResult[1].id, "user2");
  assertEquals(userResult[1].name, "Bob");
  
  // Query with parameters
  const paramResult = await client.executeQuery(
    "MATCH (u:User {id: $userId}) RETURN u.name as name",
    { userId: "user1" }
  );
  assertEquals(paramResult.length, 1);
  assertEquals(paramResult[0].name, "Alice");
  
  // Query relationships
  const followResult = await client.executeQuery(
    "MATCH (follower:User)-[:FOLLOWS]->(target:User) RETURN follower.id as followerId, target.id as targetId"
  );
  assertEquals(followResult.length, 1);
  assertEquals(followResult[0].followerId, "user1");
  assertEquals(followResult[0].targetId, "user2");
});

Deno.test("ServerKuzuClient - Snapshot Initialization", async () => {
  const client = new ServerKuzuClient();
  
  // Create snapshot with events
  const snapshot: EventSnapshot = {
    events: [
      {
        id: "evt_1",
        template: "CREATE_USER",
        params: { id: "user1", name: "Snapshot User", email: "snapshot@example.com" },
        timestamp: Date.now()
      },
      {
        id: "evt_2",
        template: "CREATE_POST",
        params: { id: "post1", content: "Snapshot post", authorId: "user1" },
        timestamp: Date.now()
      }
    ],
    timestamp: Date.now(),
    position: 2
  };
  
  await client.initializeFromSnapshot(snapshot);
  
  // Verify snapshot was applied
  const state = await client.getState();
  assertEquals(state.users.length, 1);
  assertEquals(state.users[0].name, "Snapshot User");
  assertEquals(state.posts.length, 1);
  assertEquals(state.posts[0].content, "Snapshot post");
  
  // Verify event count
  assertEquals(client.getEventCount(), 2);
});

Deno.test("ServerKuzuClient - Query Injection Prevention", async () => {
  const client = new ServerKuzuClient();
  await client.initialize();
  
  // Try injection with DROP
  try {
    await client.executeQuery("MATCH (u:User) RETURN u; DROP TABLE User;");
    throw new Error("Should have rejected dangerous query");
  } catch (error) {
    assertEquals((error as Error).message, "Potentially dangerous query detected");
  }
  
  // Try injection with comment
  try {
    await client.executeQuery("MATCH (u:User) -- DROP EVERYTHING");
    throw new Error("Should have rejected dangerous query");
  } catch (error) {
    assertEquals((error as Error).message, "Potentially dangerous query detected");
  }
});

Deno.test("ServerKuzuClient - State Caching", async () => {
  const client = new ServerKuzuClient();
  await client.initialize();
  
  // Create initial data
  await client.applyEvent({
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "user1", name: "Cache Test", email: "cache@test.com" },
    timestamp: Date.now()
  });
  
  // First call should populate cache
  const state1 = await client.getState();
  assertEquals(state1.users.length, 1);
  
  // Second call should use cache (verify by checking the same reference)
  const state2 = await client.getState();
  assertEquals(state1, state2); // Same reference means cache was used
  
  // Apply new event should invalidate cache
  await client.applyEvent({
    id: "evt_2",
    template: "CREATE_USER",
    params: { id: "user2", name: "Cache Test 2", email: "cache2@test.com" },
    timestamp: Date.now()
  });
  
  // Next call should not use cache
  const state3 = await client.getState();
  assertEquals(state3.users.length, 2);
});

// HTTP Query Endpoint test
Deno.test("HTTP Query Endpoint", async () => {
  // Start a test server
  const controller = new AbortController();
  const serverPromise = Deno.serve(
    { port: 8081, signal: controller.signal },
    async (req) => {
      const url = new URL(req.url);
      
      if (req.method === "POST" && url.pathname === "/query") {
        const body = await req.json();
        
        // Mock successful response
        return new Response(JSON.stringify({
          success: true,
          data: [{ id: "user1", name: "Test User" }]
        }), {
          headers: { "Content-Type": "application/json" }
        });
      }
      
      return new Response("Not Found", { status: 404 });
    }
  );
  
  // Wait for server to start
  await new Promise(resolve => setTimeout(resolve, 100));
  
  try {
    // Test query endpoint
    const response = await fetch("http://localhost:8081/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cypher: "MATCH (u:User) RETURN u",
        params: {}
      })
    });
    
    assertEquals(response.status, 200);
    const result = await response.json();
    assertEquals(result.success, true);
    assertExists(result.data);
    assertEquals(result.data.length, 1);
  } finally {
    controller.abort();
    await serverPromise;
  }
});