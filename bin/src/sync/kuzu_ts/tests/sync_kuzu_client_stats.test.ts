/**
 * Sync KuzuDB Client Statistics Tests
 * Tests for periodic stats reporting and template-specific counters
 */

import { assertEquals, assertExists } from "jsr:@std/assert";
import { delay } from "jsr:@std/async/delay";
import { SyncKuzuClient } from "../core/sync_kuzu_client.ts";

Deno.test("SyncKuzuClient - Template-specific statistics tracking", async () => {
  const client = new SyncKuzuClient({ clientId: "test-stats-client" });
  await client.initialize();
  
  // Execute different template types
  await client.executeTemplate("CREATE_USER", { 
    id: "user1", 
    name: "Test User 1",
    email: "user1@test.com"
  });
  
  await client.executeTemplate("UPDATE_USER", { 
    id: "user1", 
    name: "Updated User 1"
  });
  
  await client.executeTemplate("CREATE_USER", { 
    id: "user2", 
    name: "Test User 2",
    email: "user2@test.com"
  });
  
  // Get detailed stats
  const detailedStats = client.getDetailedStatsByTemplate();
  
  // Verify CREATE_USER stats
  assertExists(detailedStats["CREATE_USER"]);
  assertEquals(detailedStats["CREATE_USER"].sent, 2);
  assertEquals(detailedStats["CREATE_USER"].received, 0); // No remote events in this test
  assertEquals(detailedStats["CREATE_USER"].applied, 0);
  assertEquals(detailedStats["CREATE_USER"].failed, 0);
  
  // Verify UPDATE_USER stats
  assertExists(detailedStats["UPDATE_USER"]);
  assertEquals(detailedStats["UPDATE_USER"].sent, 1);
  assertEquals(detailedStats["UPDATE_USER"].received, 0);
  assertEquals(detailedStats["UPDATE_USER"].applied, 0);
  assertEquals(detailedStats["UPDATE_USER"].failed, 0);
  
  await client.close();
});

Deno.test("SyncKuzuClient - Overall DML statistics", async () => {
  const client = new SyncKuzuClient({ 
    clientId: "test-overall-stats",
    autoReconnect: false // Disable auto-reconnect for test
  });
  await client.initialize();
  
  // Execute some templates
  await client.executeTemplate("CREATE_USER", { 
    id: "user1", 
    name: "User for Stats"
  });
  
  await client.executeTemplate("INCREMENT_COUNTER", { 
    counterId: "test_counter",
    amount: 5
  });
  
  // Get overall stats
  const overallStats = client.getDMLStats();
  
  // Verify overall stats
  assertEquals(overallStats.sent, 2);
  assertEquals(overallStats.received, 0);
  assertEquals(overallStats.applied, 0);
  assertEquals(overallStats.failed, 0);
  assertEquals(overallStats.clientId, "test-overall-stats");
  
  await client.close();
});

Deno.test("SyncKuzuClient - Success rate calculation", async () => {
  const client = new SyncKuzuClient({ clientId: "test-success-rate" });
  await client.initialize();
  
  // Execute some templates
  await client.executeTemplate("DELETE_USER_DATA", { 
    userId: "user1",
    reason: "Test deletion"
  });
  
  // Get stats to verify success rate calculation
  const stats = client.getDetailedStatsByTemplate();
  
  // With no applied or failed, success rate should be 0
  assertEquals(stats["DELETE_USER_DATA"].successRate, 0);
  
  await client.close();
});

Deno.test("SyncKuzuClient - Stats reporter starts and stops properly", async () => {
  const client = new SyncKuzuClient({ 
    clientId: "test-reporter-lifecycle",
    autoReconnect: false
  });
  
  // Initialize should start the stats reporter
  await client.initialize();
  
  // Execute a template to generate some stats
  await client.executeTemplate("CREATE_USER", { 
    id: "user1", 
    name: "Test User"
  });
  
  // Stats should be available
  const stats = client.getDMLStats();
  assertEquals(stats.sent, 1);
  
  // Close should stop the stats reporter
  await client.close();
  
  // After close, stats should still be retrievable (final stats)
  const finalStats = client.getDMLStats();
  assertEquals(finalStats.sent, 1);
});