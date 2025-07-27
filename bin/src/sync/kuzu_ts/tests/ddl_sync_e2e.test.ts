/**
 * End-to-End DDL Synchronization Test
 * DDL同期のエンドツーエンドテスト
 */

import { assertEquals, assertExists } from "jsr:@std/assert";
// import { ServerKuzuClient } from "../core/server/server_kuzu_client.ts"; // Removed: server_kuzu deprecated
import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";

// Skipped: E2E tests requiring ServerKuzuClient (server_kuzu deprecated)
// Deno.test("DDL Sync E2E - Server and Browser Client Integration", async () => {
  // Initialize clients
  const serverClient = new ServerKuzuClient("server-1");
  const browserClient = new BrowserKuzuClientImpl();
  
  await serverClient.initialize();
  await browserClient.initialize();
  
  console.log("Testing DDL synchronization between server and browser clients...");
  
  // 1. Create a new table via server client
  const createTableEvent = await serverClient.createDDLEvent(
    "CREATE_NODE_TABLE",
    {
      tableName: "Customer",
      columns: [
        { name: "id", type: "STRING" },
        { name: "name", type: "STRING" },
        { name: "email", type: "STRING" }
      ],
      primaryKey: "id"
    }
  );
  
  await serverClient.applyEvent(createTableEvent);
  
  // Verify table exists on server
  const serverHasTable = await serverClient.hasTable("Customer");
  assertEquals(serverHasTable, true);
  
  // 2. Simulate event propagation to browser client
  // Note: In real implementation, this would happen via WebSocket
  // For now, we'll manually apply the DDL event through executeTemplate
  await browserClient.executeTemplate("CREATE_NODE_TABLE", {
    tableName: "Customer",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING" },
      { name: "email", type: "STRING" }
    ],
    primaryKey: "id"
  // });
  
  // Verify table exists on browser
  const browserHasTable = await browserClient.hasTable("Customer");
  assertEquals(browserHasTable, true);
  
  // 3. Add column via browser client
  const addColumnEvent = await browserClient.createDDLEvent(
    "ADD_COLUMN",
    {
      tableName: "Customer",
      columnName: "phone",
      columnType: "STRING",
      nullable: true
    }
  );
  
  await browserClient.applyDDLEvent(addColumnEvent);
  
  // Verify column exists on browser
  const browserHasColumn = await browserClient.hasColumn("Customer", "phone");
  assertEquals(browserHasColumn, true);
  
  // 4. Propagate to server
  await serverClient.applyEvent(addColumnEvent);
  
  // Verify column exists on server
  const serverHasColumn = await serverClient.hasColumn("Customer", "phone");
  assertEquals(serverHasColumn, true);
  
  // 5. Verify schema versions match
  const serverSchemaState = await serverClient.getSchemaState();
  const browserSchemaState = await browserClient.getSchemaState();
  
  assertEquals(serverSchemaState.version, browserSchemaState.version);
  assertEquals(serverSchemaState.version, 2); // 2 DDL operations
  
  // 6. Test DML operations on the new schema
  const customerEvent = {
    id: "cust-001",
    template: "CREATE_CUSTOMER",
    params: {
      id: "c1",
      name: "Alice",
      email: "alice@example.com",
      phone: "+1234567890"
    },
    clientId: "test-client",
    timestamp: Date.now()
  };
  
  // Register the DML template
  const createCustomerTemplate = `
    CREATE (c:Customer {
      id: $id,
      name: $name,
      email: $email,
      phone: $phone
    })
  `;
  
  // Apply on both clients
  await serverClient.applyEvent({
    ...customerEvent,
    template: "CREATE",
    params: {
      query: createCustomerTemplate,
      ...customerEvent.params
    }
  // });
  
  // 7. Query to verify data
  const serverResult = await serverClient.executeQuery(
    "MATCH (c:Customer {id: $id}) RETURN c.name as name, c.phone as phone",
    { id: "c1" }
  );
  
  assertEquals(serverResult.length, 1);
  assertEquals(serverResult[0].name, "Alice");
  assertEquals(serverResult[0].phone, "+1234567890");
  
  console.log("✅ DDL synchronization test completed successfully!");
  console.log(`   - Schema version: ${serverSchemaState.version}`);
  console.log(`   - Tables created: Customer`);
  console.log(`   - Columns added: phone`);
  console.log(`   - DML operations: CREATE Customer`);
// });

Deno.test("DDL Sync E2E - Concurrent Schema Changes", async () => {
  const client1 = new ServerKuzuClient("client-1");
  const client2 = new ServerKuzuClient("client-2");
  
  await client1.initialize();
  await client2.initialize();
  
  console.log("Testing concurrent DDL operations...");
  
  // Both clients create tables
  const table1Event = await client1.createDDLEvent(
    "CREATE_NODE_TABLE",
    {
      tableName: "Orders",
      columns: [
        { name: "id", type: "STRING" },
        { name: "total", type: "DOUBLE" }
      ],
      primaryKey: "id"
    }
  );
  
  const table2Event = await client2.createDDLEvent(
    "CREATE_NODE_TABLE",
    {
      tableName: "Products",
      columns: [
        { name: "id", type: "STRING" },
        { name: "price", type: "DOUBLE" }
      ],
      primaryKey: "id"
    }
  );
  
  // Apply locally
  await client1.applyEvent(table1Event);
  await client2.applyEvent(table2Event);
  
  // Cross-sync
  await client1.applyEvent(table2Event);
  await client2.applyEvent(table1Event);
  
  // Verify both have both tables
  assertEquals(await client1.hasTable("Orders"), true);
  assertEquals(await client1.hasTable("Products"), true);
  assertEquals(await client2.hasTable("Orders"), true);
  assertEquals(await client2.hasTable("Products"), true);
  
  // Verify schema versions
  const state1 = await client1.getSchemaState();
  const state2 = await client2.getSchemaState();
  
  assertEquals(state1.version, 2);
  assertEquals(state2.version, 2);
  
  console.log("✅ Concurrent DDL operations handled successfully!");
// });

Deno.test("DDL Sync E2E - Dependency Management", async () => {
  const client = new ServerKuzuClient("dep-test");
  await client.initialize();
  
  console.log("Testing DDL dependency management...");
  
  // Create events with dependencies
  const userTableEvent = await client.createDDLEvent(
    "CREATE_NODE_TABLE",
    {
      tableName: "User",
      columns: [
        { name: "id", type: "STRING" },
        { name: "name", type: "STRING" }
      ],
      primaryKey: "id"
    }
  );
  
  const postTableEvent = await client.createDDLEvent(
    "CREATE_NODE_TABLE",
    {
      tableName: "Post",
      columns: [
        { name: "id", type: "STRING" },
        { name: "content", type: "STRING" },
        { name: "authorId", type: "STRING" }
      ],
      primaryKey: "id"
    }
  );
  
  const relationEvent = await client.createDDLEvent(
    "CREATE_EDGE_TABLE",
    {
      tableName: "AUTHORED",
      fromTable: "User",
      toTable: "Post"
    }
  );
  
  // Set dependencies manually
  relationEvent.dependsOn = [userTableEvent.id, postTableEvent.id];
  
  // Apply in wrong order - relation first
  await client.applyEvent(relationEvent);
  
  // Should be pending
  const pendingBefore = await client.getPendingDDLs();
  assertEquals(pendingBefore.length, 1);
  assertEquals(pendingBefore[0].id, relationEvent.id);
  
  // Apply dependencies
  await client.applyEvent(userTableEvent);
  await client.applyEvent(postTableEvent);
  
  // Should automatically process pending
  const pendingAfter = await client.getPendingDDLs();
  assertEquals(pendingAfter.length, 0);
  
  // Verify all exist
  assertEquals(await client.hasTable("User"), true);
  assertEquals(await client.hasTable("Post"), true);
  // Note: Edge table verification would require checking rel table info
  
  const schemaState = await client.getSchemaState();
  assertEquals(schemaState.version, 3);
  
  console.log("✅ DDL dependency management working correctly!");
// });