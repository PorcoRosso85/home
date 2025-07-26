/**
 * Counter Flow Demo
 * カウンターフローのデモンストレーション
 * 
 * This demonstrates the complete flow from event reception to DB write:
 * 1. INCREMENT_COUNTER event processing
 * 2. QUERY_COUNTER event processing  
 * 3. Transaction management
 * 4. Error handling
 */

import { createTemplateEvent } from "../event_sourcing/core.ts";
import { TemplateRegistry } from "../event_sourcing/template_event_store.ts";

// Demonstrate the event flow
console.log("=== Counter Event Flow Demo ===\n");

// 1. Create INCREMENT_COUNTER event
console.log("1. Creating INCREMENT_COUNTER event:");
const incrementEvent = createTemplateEvent(
  "INCREMENT_COUNTER",
  { counterId: "page_views", amount: 5 },
  "demo_client"
);
console.log("Event created:", incrementEvent);

// 2. Show template metadata
console.log("\n2. Template metadata:");
const registry = new TemplateRegistry();
const incrementMeta = registry.getTemplateMetadata("INCREMENT_COUNTER");
console.log("INCREMENT_COUNTER metadata:", incrementMeta);

const queryMeta = registry.getTemplateMetadata("QUERY_COUNTER");
console.log("QUERY_COUNTER metadata:", queryMeta);

// 3. Show Cypher queries that would be executed
console.log("\n3. Cypher queries:");
console.log("INCREMENT_COUNTER query:");
console.log(`
  MERGE (c:Counter {id: $counterId})
  ON CREATE SET c.value = COALESCE($amount, 1)
  ON MATCH SET c.value = c.value + COALESCE($amount, 1)
`);

console.log("QUERY_COUNTER query:");
console.log(`
  MATCH (c:Counter {id: $counterId})
  RETURN c.value as value
`);

// 4. Transaction flow
console.log("\n4. Transaction flow:");
console.log("- Begin transaction");
console.log("- Execute INCREMENT_COUNTER");
console.log("- If success: Commit");
console.log("- If error: Rollback");

// 5. Error handling scenarios
console.log("\n5. Error handling:");
console.log("- Missing required parameters → ValidationError");
console.log("- Transaction timeout → TransactionError with TIMEOUT code");
console.log("- Concurrent conflict → TransactionError with SERIALIZATION_FAILURE code");
console.log("- Any other error → Automatic rollback");

// 6. Complete flow summary
console.log("\n6. Complete flow summary:");
console.log(`
Event Reception → Validation → Transaction Begin → 
Cypher Execution → State Update → Transaction Commit → 
Broadcast to Other Clients
`);

export { incrementEvent };