/**
 * Counter Event Example with Transaction Management
 * カウンターイベントとトランザクション管理の例
 */

import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";
import { KuzuTransactionManager } from "../transaction/kuzu_transaction_manager.ts";
import * as telemetry from "../telemetry_log.ts";

async function runCounterExample() {
  telemetry.info("=== Counter Event Example ===");

  // Initialize client
  const client = new BrowserKuzuClientImpl();
  await client.initialize();

  // Create transaction manager
  const txManager = new KuzuTransactionManager(client);

  // Example 1: Increment counter with transaction
  telemetry.info("\n1. Increment counter with transaction:");
  const incrementResult = await txManager.executeInTransaction(async (tx) => {
    // Increment counter by 5
    const event = await tx.executeTemplate("INCREMENT_COUNTER", {
      counterId: "visitor_count",
      amount: 5
    });
    
    telemetry.debug("Event created:", { event });
    
    // Query the counter value within the same transaction
    const result = await tx.query(`
      MATCH (c:Counter {id: $counterId})
      RETURN c.value as value
    `, { counterId: "visitor_count" });
    
    const value = result.getAll()[0]?.[0] ?? 0;
    telemetry.info("Counter value after increment:", { value });
    
    return { event, value };
  });

  if (incrementResult.success) {
    telemetry.info("Transaction committed successfully");
    telemetry.info("Final counter value:", { value: incrementResult.data?.value });
  } else {
    telemetry.error("Transaction failed:", { error: incrementResult.error });
  }

  // Example 2: Multiple increments in a single transaction
  telemetry.info("\n2. Multiple increments in a single transaction:");
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
    
    telemetry.info(`Created ${events.length} increment events`);
    return events;
  });

  if (batchResult.success) {
    telemetry.info("Batch increment successful");
  }

  // Example 3: Error handling with automatic rollback
  telemetry.info("\n3. Error handling with automatic rollback:");
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
    telemetry.info("Transaction rolled back due to error:", { error: errorResult.error?.message });
  }

  // Example 4: Query counter without transaction
  telemetry.info("\n4. Query counter value directly:");
  const visitorCount = await client.queryCounter("visitor_count");
  telemetry.info("Visitor count:", { count: visitorCount });

  // Example 5: Transaction timeout
  telemetry.info("\n5. Transaction with timeout:");
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
    telemetry.info("Transaction timed out:", { error: timeoutResult.error?.message });
  }

  // Display all counters
  telemetry.info("\n6. All counter values:");
  const counters = await client.executeQuery(`
    MATCH (c:Counter)
    RETURN c.id as id, c.value as value
    ORDER BY c.id
  `);
  
  telemetry.info("Counters in database:");
  for (const row of counters.getAll()) {
    telemetry.info(`  ${row[0]}: ${row[1]}`);
  }
}

// Run the example
if (import.meta.main) {
  runCounterExample().catch((err) => telemetry.error("Failed to run counter example", { error: err }));
}

export { runCounterExample };