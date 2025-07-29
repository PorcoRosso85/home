#!/usr/bin/env -S deno run --allow-net --allow-read

/**
 * Statistics Monitoring Example
 * Demonstrates the periodic stats reporter and template-specific counters
 */

import { SyncKuzuClient } from "../core/sync_kuzu_client.ts";

async function main() {
  console.log("🚀 Starting Sync KuzuDB Client with Statistics Monitoring");
  
  const client = new SyncKuzuClient({
    clientId: "stats-demo-client",
    autoReconnect: true,
    reconnectDelay: 2000
  });
  
  try {
    // Initialize the client
    await client.initialize();
    console.log("✅ Client initialized");
    
    // Connect to WebSocket server (if available)
    try {
      await client.connect("ws://localhost:8080");
      console.log("✅ Connected to sync server");
    } catch (error) {
      console.log("⚠️  Could not connect to sync server, running in offline mode");
    }
    
    console.log("\n📊 Statistics will be logged every 5 seconds...\n");
    
    // Simulate various DML operations
    const operations = [
      { template: "CREATE_USER", params: { id: "user1", name: "Alice", email: "alice@example.com" } },
      { template: "CREATE_USER", params: { id: "user2", name: "Bob", email: "bob@example.com" } },
      { template: "UPDATE_USER", params: { id: "user1", name: "Alice Smith" } },
      { template: "CREATE_USER", params: { id: "user3", name: "Charlie", email: "charlie@example.com" } },
      { template: "INCREMENT_COUNTER", params: { counterId: "page_views", amount: 1 } },
      { template: "INCREMENT_COUNTER", params: { counterId: "page_views", amount: 1 } },
      { template: "DELETE_USER_DATA", params: { userId: "user2", reason: "User requested deletion" } },
      { template: "UPDATE_USER", params: { id: "user3", name: "Charles" } },
      { template: "INCREMENT_COUNTER", params: { counterId: "api_calls", amount: 3 } },
    ];
    
    // Execute operations with delays to see periodic reports
    for (const op of operations) {
      console.log(`\n⚡ Executing: ${op.template}`);
      try {
        await client.executeTemplate(op.template, op.params);
        console.log(`✅ ${op.template} executed successfully`);
      } catch (error) {
        console.error(`❌ ${op.template} failed:`, error.message);
      }
      
      // Wait a bit between operations
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Wait a bit more to see final stats report
    console.log("\n⏳ Waiting for final stats report...");
    await new Promise(resolve => setTimeout(resolve, 6000));
    
    // Get and display final detailed stats
    console.log("\n📈 Final Detailed Statistics by Template:");
    const detailedStats = client.getDetailedStatsByTemplate();
    
    for (const [template, stats] of Object.entries(detailedStats)) {
      console.log(`\n📌 ${template}:`);
      console.log(`   Sent: ${stats.sent}`);
      console.log(`   Received: ${stats.received}`);
      console.log(`   Applied: ${stats.applied}`);
      console.log(`   Failed: ${stats.failed}`);
      console.log(`   Success Rate: ${stats.successRate.toFixed(2)}%`);
    }
    
    // Get overall stats
    const overallStats = client.getDMLStats();
    console.log("\n📊 Overall Statistics:");
    console.log(`   Client ID: ${overallStats.clientId}`);
    console.log(`   Total Sent: ${overallStats.sent}`);
    console.log(`   Total Received: ${overallStats.received}`);
    console.log(`   Total Applied: ${overallStats.applied}`);
    console.log(`   Total Failed: ${overallStats.failed}`);
    
  } catch (error) {
    console.error("❌ Error:", error);
  } finally {
    // Clean up
    console.log("\n🔒 Closing client...");
    await client.close();
    console.log("✅ Client closed");
  }
}

// Run the example
if (import.meta.main) {
  await main();
}