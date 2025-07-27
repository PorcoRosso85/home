/**
 * Counter Event Tests
 * カウンターイベントのテスト
 */

import { assertEquals, assertExists } from "jsr:@std/assert";
import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";
import { KuzuTransactionManager } from "../transaction/kuzu_transaction_manager.ts";
// import { ServerKuzuClient } from "../core/server/server_kuzu_client.ts"; // Removed: server_kuzu deprecated

Deno.test("Counter events - Client side operations", async () => {
  const client = new BrowserKuzuClientImpl();
  await client.initialize();

  // Test INCREMENT_COUNTER
  const incrementEvent = await client.executeTemplate("INCREMENT_COUNTER", {
    counterId: "test_counter",
    amount: 5
  });

  assertExists(incrementEvent);
  assertEquals(incrementEvent.template, "INCREMENT_COUNTER");
  assertEquals(incrementEvent.params.counterId, "test_counter");
  assertEquals(incrementEvent.params.amount, 5);

  // Query counter value
  const value = await client.queryCounter("test_counter");
  assertEquals(value, 5);

  // Increment again
  await client.executeTemplate("INCREMENT_COUNTER", {
    counterId: "test_counter",
    amount: 3
  });

  const newValue = await client.queryCounter("test_counter");
  assertEquals(newValue, 8);

  // Test counter that doesn't exist
  const nonExistentValue = await client.queryCounter("non_existent");
  assertEquals(nonExistentValue, 0);
});

// Skipped: Server side operations test (server_kuzu deprecated)
// Deno.test("Counter events - Server side operations", async () => {
//   const server = new ServerKuzuClient();
//   await server.initialize();
//
//   // Apply INCREMENT_COUNTER event
//   const event = {
//     id: "evt_test_1",
//     template: "INCREMENT_COUNTER",
//     params: {
//       counterId: "server_counter",
//       amount: 10
//     },
//     timestamp: Date.now()
//   };
//
//   await server.applyEvent(event);
//
//   // Query the counter
//   const result = await server.executeQuery(`
//     MATCH (c:Counter {id: $counterId})
//     RETURN c.value as value
//   `, { counterId: "server_counter" });
//
//   assertEquals(result.length, 1);
//   assertEquals(result[0].value, 10);
//
//   // Apply another increment
//   const event2 = {
//     id: "evt_test_2",
//     template: "INCREMENT_COUNTER",
//     params: {
//       counterId: "server_counter",
//       amount: 15
//     },
//     timestamp: Date.now()
//   };
//
//   await server.applyEvent(event2);
//
//   const result2 = await server.executeQuery(`
//     MATCH (c:Counter {id: $counterId})
//     RETURN c.value as value
//   `, { counterId: "server_counter" });
//
//   assertEquals(result2[0].value, 25);
// });

Deno.test("Counter events - Transaction rollback", async () => {
  const client = new BrowserKuzuClientImpl();
  await client.initialize();
  const txManager = new KuzuTransactionManager(client);

  // Set initial value
  await client.executeTemplate("INCREMENT_COUNTER", {
    counterId: "rollback_test",
    amount: 100
  });

  const initialValue = await client.queryCounter("rollback_test");
  assertEquals(initialValue, 100);

  // Try transaction that will fail
  const result = await txManager.executeInTransaction(async (tx) => {
    await tx.executeTemplate("INCREMENT_COUNTER", {
      counterId: "rollback_test",
      amount: 50
    });

    // Force an error
    throw new Error("Intentional error");
  });

  assertEquals(result.success, false);
  assertExists(result.error);

  // Value should remain unchanged due to rollback
  const finalValue = await client.queryCounter("rollback_test");
  assertEquals(finalValue, 100);
});

Deno.test("Counter events - Concurrent transactions", async () => {
  const client = new BrowserKuzuClientImpl();
  await client.initialize();
  const txManager = new KuzuTransactionManager(client);

  // Initialize counter
  await client.executeTemplate("INCREMENT_COUNTER", {
    counterId: "concurrent_test",
    amount: 0
  });

  // Run multiple transactions concurrently
  const promises = Array.from({ length: 5 }, (_, i) => 
    txManager.executeInTransaction(async (tx) => {
      await tx.executeTemplate("INCREMENT_COUNTER", {
        counterId: "concurrent_test",
        amount: 1
      });
      return i;
    })
  );

  const results = await Promise.all(promises);

  // All should succeed (KuzuDB handles concurrent writes)
  const successCount = results.filter(r => r.success).length;
  assertEquals(successCount, 5);

  // Final value should be 5
  const finalValue = await client.queryCounter("concurrent_test");
  assertEquals(finalValue, 5);
});

Deno.test("Counter events - COALESCE default amount", async () => {
  const client = new BrowserKuzuClientImpl();
  await client.initialize();

  // Increment without specifying amount (should default to 1)
  await client.executeTemplate("INCREMENT_COUNTER", {
    counterId: "default_amount_test"
  });

  const value = await client.queryCounter("default_amount_test");
  assertEquals(value, 1);

  // Increment again without amount
  await client.executeTemplate("INCREMENT_COUNTER", {
    counterId: "default_amount_test"
  });

  const value2 = await client.queryCounter("default_amount_test");
  assertEquals(value2, 2);
});