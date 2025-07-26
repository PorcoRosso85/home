/**
 * Counter Event Example with Transaction Management
 * カウンターイベントとトランザクション管理の例
 */

import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";
import { KuzuTransactionManager } from "../transaction/kuzu_transaction_manager.ts";

async function runCounterExample() {
  console.log("=== Counter Event Example ===");

  // Initialize client
  const client = new BrowserKuzuClientImpl();
  await client.initialize();

  // Create transaction manager
  const txManager = new KuzuTransactionManager(client);

  // Example 1: Increment counter with transaction
  console.log("\n1. Increment counter with transaction:");
  const incrementResult = await txManager.executeInTransaction(async (tx) => {
    // Increment counter by 5
    const event = await tx.executeTemplate("INCREMENT_COUNTER", {
      counterId: "visitor_count",
      amount: 5
    });
    
    console.log("Event created:", event);
    
    // Query the counter value within the same transaction
    const result = await tx.query(`
      MATCH (c:Counter {id: $counterId})
      RETURN c.value as value
    `, { counterId: "visitor_count" });
    
    const value = result.getAll()[0]?.[0] ?? 0;
    console.log("Counter value after increment:", value);
    
    return { event, value };
  });

  if (incrementResult.success) {
    console.log("Transaction committed successfully");
    console.log("Final counter value:", incrementResult.data?.value);
  } else {
    console.error("Transaction failed:", incrementResult.error);
  }

  // Example 2: Multiple increments in a single transaction
  console.log("\n2. Multiple increments in a single transaction:");
  const batchResult = await txManager.executeInTransaction(async (tx) => {
    const events = [];
    
    // Increment multiple counters
    for (const counterId of ["page_views", "api_calls", "user_actions"]) {
      const event = await tx.executeTemplate("INCREMENT_COUNTER", {
        counterId,
        amount: 1
      });
      events.push(event);
    }
    
    console.log(`Created ${events.length} increment events`);
    return events;
  });

  if (batchResult.success) {
    console.log("Batch increment successful");
  }

  // Example 3: Error handling with automatic rollback
  console.log("\n3. Error handling with automatic rollback:");
  const errorResult = await txManager.executeInTransaction(async (tx) => {
    // Increment counter
    await tx.executeTemplate("INCREMENT_COUNTER", {
      counterId: "error_test",
      amount: 10
    });
    
    // Simulate an error
    throw new Error("Simulated error - should trigger rollback");
  });

  if (!errorResult.success) {
    console.log("Transaction rolled back due to error:", errorResult.error?.message);
  }

  // Example 4: Query counter without transaction
  console.log("\n4. Query counter value directly:");
  const visitorCount = await client.queryCounter("visitor_count");
  console.log("Visitor count:", visitorCount);

  // Example 5: Transaction timeout
  console.log("\n5. Transaction with timeout:");
  const timeoutResult = await txManager.executeInTransaction(async (tx) => {
    await tx.executeTemplate("INCREMENT_COUNTER", {
      counterId: "timeout_test",
      amount: 1
    });
    
    // Simulate long-running operation
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return "Should timeout";
  }, { timeout: 1000 }); // 1 second timeout

  if (!timeoutResult.success) {
    console.log("Transaction timed out:", timeoutResult.error?.message);
  }

  // Display all counters
  console.log("\n6. All counter values:");
  const counters = await client.executeQuery(`
    MATCH (c:Counter)
    RETURN c.id as id, c.value as value
    ORDER BY c.id
  `);
  
  console.log("Counters in database:");
  for (const row of counters.getAll()) {
    console.log(`  ${row[0]}: ${row[1]}`);
  }
}

// Run the example
if (import.meta.main) {
  runCounterExample().catch(console.error);
}

export { runCounterExample };