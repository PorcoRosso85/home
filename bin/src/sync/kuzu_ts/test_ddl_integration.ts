#!/usr/bin/env -S deno run --allow-read --allow-write --allow-env --allow-ffi --allow-sys

/**
 * Test DDL Integration with ServerKuzuClient
 * ServerKuzuClientでのDDL統合のテスト
 */

import { ServerKuzuClient } from "./core/server/server_kuzu_client.ts";
import type { TemplateEvent } from "./event_sourcing/types.ts";
import type { DDLTemplateEvent } from "./event_sourcing/ddl_types.ts";

async function runTest() {
  console.log("=== Testing DDL Integration in ServerKuzuClient ===\n");

  // Initialize client
  const client = new ServerKuzuClient("test_client");
  await client.initialize();

  console.log("1. Testing backward compatibility with DML events...");
  
  // Test DML events (backward compatibility)
  const dmlEvents: TemplateEvent[] = [
    {
      id: "evt1",
      template: "CREATE_USER",
      params: { id: "user1", name: "Alice", email: "alice@example.com" },
      timestamp: Date.now()
    },
    {
      id: "evt2",
      template: "CREATE_USER",
      params: { id: "user2", name: "Bob", email: "bob@example.com" },
      timestamp: Date.now()
    },
    {
      id: "evt3",
      template: "FOLLOW_USER",
      params: { followerId: "user1", targetId: "user2" },
      timestamp: Date.now()
    }
  ];

  for (const event of dmlEvents) {
    await client.applyEvent(event);
    console.log(`  ✓ Applied DML event: ${event.template}`);
  }

  // Check state
  const state = await client.getState();
  console.log(`\nCurrent state: ${state.users.length} users, ${state.follows.length} follows`);

  console.log("\n2. Testing DDL events...");

  // Test schema version
  console.log(`  Current schema version: ${client.getSchemaVersion()}`);

  // Create a DDL event
  const ddlEvent = client.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "TestTable",
    columns: [
      { name: "id", type: "STRING" },
      { name: "value", type: "INT64" }
    ],
    primaryKey: ["id"]
  });

  console.log(`  Created DDL event: ${ddlEvent.id}`);

  // Validate DDL
  const validation = client.validateDDL(ddlEvent);
  console.log(`  Validation: ${validation.valid ? "✓ Valid" : "✗ Invalid"}`);
  if (!validation.valid) {
    console.log(`  Errors: ${validation.errors.join(", ")}`);
  }

  // Apply DDL event
  try {
    await client.applyDDLEvent(ddlEvent);
    console.log("  ✓ Applied DDL event successfully");
  } catch (error) {
    console.error("  ✗ Failed to apply DDL:", error);
  }

  // Check if table exists
  console.log(`  Table 'TestTable' exists: ${client.hasTable("TestTable")}`);

  console.log("\n3. Testing template registry...");
  
  // Test template detection
  console.log(`  'CREATE_USER' is DML: ${client.isDMLTemplate("CREATE_USER")}`);
  console.log(`  'CREATE_NODE_TABLE' is DDL: ${client.isDDLTemplate("CREATE_NODE_TABLE")}`);
  console.log(`  Has template 'FOLLOW_USER': ${client.hasTemplate("FOLLOW_USER")}`);

  // Get template metadata
  const userMetadata = client.getTemplateMetadata("CREATE_USER");
  console.log(`  CREATE_USER metadata:`, userMetadata);

  console.log("\n4. Testing schema queries...");
  
  // Query schema state
  const schemaState = client.getSchemaState();
  console.log(`  Node tables: ${Object.keys(schemaState.nodeTables).join(", ")}`);
  console.log(`  Edge tables: ${Object.keys(schemaState.edgeTables).join(", ")}`);

  // Check specific tables
  console.log(`  Has 'User' table: ${client.hasTable("User")}`);
  console.log(`  Has 'User.name' column: ${client.hasColumn("User", "name")}`);

  // Get sync state
  const syncState = client.getSchemaSyncState();
  console.log(`\n  Schema sync state:`);
  console.log(`    Version: ${syncState.version}`);
  console.log(`    Pending DDLs: ${syncState.pendingDDLs.length}`);
  console.log(`    Conflicts: ${syncState.conflicts.length}`);

  console.log("\n=== All tests completed ===");
}

// Run the test
if (import.meta.main) {
  try {
    await runTest();
  } catch (error) {
    console.error("Test failed:", error);
    Deno.exit(1);
  }
}