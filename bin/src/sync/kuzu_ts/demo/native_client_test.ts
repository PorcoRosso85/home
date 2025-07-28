#!/usr/bin/env -S deno run --allow-env --allow-net --allow-run --allow-read

/**
 * Native KuzuDB Client Test
 * ネイティブKuzuDBクライアントの動作確認
 */

import { KuzuNativeClientImpl } from "../core/client/kuzu_native_client.ts";
import * as telemetry from "../telemetry_log.ts";

async function main() {
  telemetry.info("Starting Native KuzuDB Client Test");
  
  const client = new KuzuNativeClientImpl();
  
  try {
    // Initialize client
    telemetry.info("Initializing native client...");
    await client.initialize();
    telemetry.info("Native client initialized successfully");
    
    // Create test data
    telemetry.info("Creating test users...");
    
    await client.executeTemplate("CREATE_USER", {
      id: "user1",
      name: "Alice",
      email: "alice@example.com"
    });
    
    await client.executeTemplate("CREATE_USER", {
      id: "user2", 
      name: "Bob",
      email: "bob@example.com"
    });
    
    telemetry.info("Users created successfully");
    
    // Create post
    telemetry.info("Creating test post...");
    await client.executeTemplate("CREATE_POST", {
      id: "post1",
      content: "Hello from native KuzuDB!",
      authorId: "user1"
    });
    
    // Create follow relationship
    telemetry.info("Creating follow relationship...");
    await client.executeTemplate("FOLLOW_USER", {
      followerId: "user1",
      targetId: "user2"
    });
    
    // Test counter
    telemetry.info("Testing counter functionality...");
    await client.executeTemplate("INCREMENT_COUNTER", {
      counterId: "test_counter",
      amount: 5
    });
    
    const counterValue = await client.queryCounter("test_counter");
    telemetry.info("Counter value", { value: counterValue });
    
    // Get and display state
    telemetry.info("Getting local state...");
    const state = await client.getLocalState();
    
    telemetry.info("=== Current Database State ===");
    telemetry.info("Users", { count: state.users.length, users: state.users });
    telemetry.info("Posts", { count: state.posts.length, posts: state.posts });
    telemetry.info("Follows", { count: state.follows.length, follows: state.follows });
    
    // Test raw query execution
    telemetry.info("Testing raw query execution...");
    const result = await client.executeQuery(`
      MATCH (u:User)
      RETURN count(u) as userCount
    `);
    telemetry.info("Raw query result", { result });
    
    telemetry.info("✅ Native KuzuDB client test completed successfully!");
    
  } catch (error) {
    telemetry.error("Test failed", { 
      error: error instanceof Error ? error.message : String(error) 
    });
    Deno.exit(1);
  } finally {
    // Cleanup
    telemetry.info("Closing client...");
    await client.close();
  }
}

if (import.meta.main) {
  await main();
}