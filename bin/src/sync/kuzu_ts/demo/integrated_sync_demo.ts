#!/usr/bin/env -S deno run --allow-env --allow-net --allow-run --allow-read

/**
 * Integrated Sync Demo with Native KuzuDB
 * ネイティブKuzuDBを使用した統合同期デモ
 */

import { SyncKuzuClient } from "../core/sync_kuzu_client.ts";
import * as telemetry from "../telemetry_log.ts";

async function main() {
  telemetry.info("=== Integrated Sync Demo with Native KuzuDB ===");
  
  // Create two clients
  const client1 = new SyncKuzuClient({ clientId: "client1" });
  const client2 = new SyncKuzuClient({ clientId: "client2" });
  
  try {
    // Initialize both clients
    telemetry.info("Initializing client1...");
    await client1.initialize();
    
    telemetry.info("Initializing client2...");
    await client2.initialize();
    
    // Connect to WebSocket server (assuming server is running)
    telemetry.info("Connecting to sync server...");
    await client1.connect("ws://localhost:8080");
    await client2.connect("ws://localhost:8080");
    
    // Wait for connections to establish
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Client1 creates a user
    telemetry.info("\n=== Client1 creating user ===");
    await client1.executeTemplate("CREATE_USER", {
      id: "user1",
      name: "Alice",
      email: "alice@example.com"
    });
    
    // Wait for sync
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Client2 creates another user
    telemetry.info("\n=== Client2 creating user ===");
    await client2.executeTemplate("CREATE_USER", {
      id: "user2",
      name: "Bob",
      email: "bob@example.com"
    });
    
    // Wait for sync
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Client1 creates a post
    telemetry.info("\n=== Client1 creating post ===");
    await client1.executeTemplate("CREATE_POST", {
      id: "post1",
      content: "Hello from synchronized KuzuDB!",
      authorId: "user1"
    });
    
    // Wait for sync
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Client2 creates a follow relationship
    telemetry.info("\n=== Client2 creating follow ===");
    await client2.executeTemplate("FOLLOW_USER", {
      followerId: "user2",
      targetId: "user1"
    });
    
    // Wait for final sync
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Get final statistics
    telemetry.info("\n=== Final Statistics ===");
    
    const stats1 = client1.getDMLStats();
    telemetry.info("Client1 DML Stats", stats1);
    
    const stats2 = client2.getDMLStats();
    telemetry.info("Client2 DML Stats", stats2);
    
    // Get detailed stats by template
    telemetry.info("\n=== Detailed Stats by Template ===");
    telemetry.info("Client1 Template Stats", client1.getDetailedStatsByTemplate());
    telemetry.info("Client2 Template Stats", client2.getDetailedStatsByTemplate());
    
    telemetry.info("\n✅ Integrated sync demo completed successfully!");
    
  } catch (error) {
    telemetry.error("Demo failed", { 
      error: error instanceof Error ? error.message : String(error) 
    });
  } finally {
    // Cleanup
    telemetry.info("\nClosing clients...");
    await client1.close();
    await client2.close();
  }
}

if (import.meta.main) {
  await main();
}