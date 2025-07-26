/**
 * TransactionManager Tests (TDD RED Phase)
 * トランザクションマネージャーのテスト（TDD REDフェーズ）
 */

import { assertEquals, assert, assertThrows, assertRejects } from "jsr:@std/assert@^1.0.0";
import type { 
  TransactionManager, 
  Transaction, 
  TransactionStatus,
  TransactionOptions,
  TransactionContext
} from "./types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import type { BrowserKuzuClient, LocalState, EventSnapshot } from "../types.ts";
import { TransactionError, TransactionErrorCode } from "./types.ts";

// TransactionManager is not yet implemented - this will cause tests to fail
import { KuzuTransactionManager } from "./kuzu_transaction_manager.ts";

// Minimal test double for BrowserKuzuClient
class TestKuzuClient implements BrowserKuzuClient {
  private conflictCounter = 0;
  private conflictTargetId?: string;

  async initialize(): Promise<void> {
    // No-op for tests
  }

  async initializeFromSnapshot(snapshot: EventSnapshot): Promise<void> {
    // No-op for tests
  }

  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    // Simulate conflict for specific test case
    if (template === "UPDATE_USER" && params.id === "user-conflict") {
      if (!this.conflictTargetId) {
        this.conflictTargetId = params.id;
        this.conflictCounter = 0;
      }
      
      this.conflictCounter++;
      
      // First update succeeds, second one fails
      if (this.conflictCounter > 1) {
        throw new Error("Serialization conflict: concurrent update");
      }
    }

    return {
      id: `evt_${crypto.randomUUID()}`,
      template,
      params,
      timestamp: Date.now(),
    };
  }

  async getLocalState(): Promise<LocalState> {
    return {
      users: [],
      posts: [],
      follows: []
    };
  }

  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    // No-op for tests
  }

  async executeQuery(cypher: string, params?: Record<string, any>): Promise<any> {
    // Handle transaction commands
    if (cypher === "BEGIN TRANSACTION" || cypher === "COMMIT" || cypher === "ROLLBACK") {
      return { success: true };
    }

    // Return mock result for queries
    if (cypher.includes("MATCH") && params?.id) {
      return {
        getAllObjects: () => [{ name: "Test User", email: "test@example.com" }]
      };
    }

    return { success: true };
  }
}

Deno.test("TransactionManager - should begin a new transaction", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act
  const transaction = await manager.beginTransaction();

  // Assert
  assert(transaction.id, "Transaction should have an ID");
  assertEquals(transaction.status, "active");
  assert(transaction.startTime > 0, "Transaction should have a start time");
  assertEquals(transaction.endTime, undefined, "Active transaction should not have end time");
});

Deno.test("TransactionManager - should commit a successful transaction", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);
  const transaction = await manager.beginTransaction();

  // Act
  await manager.commitTransaction(transaction.id);

  // Assert
  const status = manager.getTransactionStatus(transaction.id);
  assertEquals(status, "committed");
  
  const history = manager.getTransactionHistory();
  const committedTx = history.find((tx: Transaction) => tx.id === transaction.id);
  assert(committedTx?.endTime, "Committed transaction should have end time");
});

Deno.test("TransactionManager - should rollback transaction on error", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);
  const transaction = await manager.beginTransaction();

  // Act
  await manager.rollbackTransaction(transaction.id, "Test rollback");

  // Assert
  const status = manager.getTransactionStatus(transaction.id);
  assertEquals(status, "rolled_back");
  
  const history = manager.getTransactionHistory();
  const rolledBackTx = history.find((tx: Transaction) => tx.id === transaction.id);
  assert(rolledBackTx?.endTime, "Rolled back transaction should have end time");
});

Deno.test("TransactionManager - should auto-rollback on unhandled error", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act & Assert
  const result = await manager.executeInTransaction(async (tx: TransactionContext) => {
    // Simulate an error during transaction
    throw new Error("Simulated database error");
  });

  assertEquals(result.success, false);
  assert(result.error);
  assertEquals(result.error.message, "Simulated database error");
  assertEquals(result.transaction.status, "rolled_back");
});

Deno.test("TransactionManager - should execute template within transaction", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act
  const result = await manager.executeInTransaction(async (tx: TransactionContext) => {
    const event = await tx.executeTemplate("CREATE_USER", {
      id: "user-1",
      name: "Alice",
      email: "alice@example.com"
    });
    return event;
  });

  // Assert
  assertEquals(result.success, true);
  assert(result.data);
  assertEquals(result.data.template, "CREATE_USER");
  assertEquals(result.transaction.status, "committed");
});

Deno.test("TransactionManager - should handle nested event groups", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act
  const result = await manager.executeInTransaction(async (tx: TransactionContext) => {
    const events: TemplateEvent[] = [
      {
        id: "event-1",
        template: "CREATE_USER",
        params: { id: "user-1", name: "Bob", email: "bob@example.com" },
        timestamp: Date.now(),
      },
      {
        id: "event-2",
        template: "CREATE_USER",
        params: { id: "user-2", name: "Carol", email: "carol@example.com" },
        timestamp: Date.now(),
      },
      {
        id: "event-3",
        template: "FOLLOW_USER",
        params: { followerId: "user-1", targetId: "user-2" },
        timestamp: Date.now(),
      },
    ];

    const eventGroup = await tx.executeEventGroup(events);
    return eventGroup;
  });

  // Assert
  assertEquals(result.success, true);
  assert(result.data);
  assertEquals(result.data.events.length, 3);
  assertEquals(result.data.status, "committed");
});

Deno.test({
  name: "TransactionManager - should respect transaction timeout",
  sanitizeResources: false,
  sanitizeOps: false,
  fn: async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);
  const options: TransactionOptions = {
    timeout: 100, // 100ms timeout
  };

  // Act & Assert
  const result = await manager.executeInTransaction(async (tx: TransactionContext) => {
    // Create an abortable delay
    const controller = new AbortController();
    const signal = controller.signal;
    
    try {
      // This will be aborted when the transaction times out
      await new Promise<void>((resolve, reject) => {
        const timeoutId = setTimeout(() => resolve(), 200);
        
        signal.addEventListener('abort', () => {
          clearTimeout(timeoutId);
          reject(new Error('Aborted'));
        });
      });
      
      return "Should not reach here";
    } catch (e) {
      // Expected - transaction timed out
      throw e;
    }
  }, options);

  assertEquals(result.success, false);
  assert(result.error);
  assert(result.error instanceof TransactionError);
  assertEquals((result.error as TransactionError).code, TransactionErrorCode.TIMEOUT);
  assertEquals(result.transaction.status, "rolled_back");
}});

Deno.test("TransactionManager - should prevent double commit", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);
  const transaction = await manager.beginTransaction();

  // Act
  await manager.commitTransaction(transaction.id);

  // Assert
  await assertRejects(
    async () => await manager.commitTransaction(transaction.id),
    TransactionError,
    "already committed"
  );
});

Deno.test("TransactionManager - should prevent operations on non-existent transaction", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act & Assert
  await assertRejects(
    async () => await manager.commitTransaction("non-existent-tx"),
    TransactionError,
    "not found"
  );
});

Deno.test("TransactionManager - should track active transactions", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act
  const tx1 = await manager.beginTransaction();
  const tx2 = await manager.beginTransaction();
  
  const activeTransactions = manager.getActiveTransactions();
  
  // Assert
  assertEquals(activeTransactions.length, 2);
  assert(activeTransactions.some((tx: Transaction) => tx.id === tx1.id));
  assert(activeTransactions.some((tx: Transaction) => tx.id === tx2.id));

  // Cleanup
  await manager.commitTransaction(tx1.id);
  await manager.rollbackTransaction(tx2.id);
  
  const activeAfterCleanup = manager.getActiveTransactions();
  assertEquals(activeAfterCleanup.length, 0);
});

Deno.test("TransactionManager - should execute raw Cypher queries in transaction", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act
  const result = await manager.executeInTransaction(async (tx: TransactionContext) => {
    // Create a node using raw Cypher
    await tx.query(`
      CREATE (u:User {
        id: $id,
        name: $name,
        email: $email
      })
    `, {
      id: "user-raw-1",
      name: "Dave",
      email: "dave@example.com"
    });

    // Query the created node
    const queryResult = await tx.query(`
      MATCH (u:User {id: $id})
      RETURN u.name as name, u.email as email
    `, { id: "user-raw-1" });

    return queryResult;
  });

  // Assert
  assertEquals(result.success, true);
  assert(result.data);
  // The actual result structure will depend on KuzuDB's query response format
});

Deno.test("TransactionManager - should handle serialization conflicts", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Start two concurrent transactions
  const tx1Promise = manager.executeInTransaction(async (tx: TransactionContext) => {
    await tx.executeTemplate("UPDATE_USER", {
      id: "user-conflict",
      name: "Update from TX1"
    });
    // Simulate some processing time
    await new Promise(resolve => setTimeout(resolve, 50));
    return "TX1";
  });

  const tx2Promise = manager.executeInTransaction(async (tx: TransactionContext) => {
    await tx.executeTemplate("UPDATE_USER", {
      id: "user-conflict",
      name: "Update from TX2"
    });
    return "TX2";
  });

  // Act
  const [result1, result2] = await Promise.all([tx1Promise, tx2Promise]);

  // Assert - One should succeed, one should fail with serialization error
  const successCount = [result1.success, result2.success].filter(s => s).length;
  assertEquals(successCount, 1, "Exactly one transaction should succeed");

  const failedResult = result1.success ? result2 : result1;
  assert(failedResult.error instanceof TransactionError);
  assertEquals(
    (failedResult.error as TransactionError).code,
    TransactionErrorCode.SERIALIZATION_FAILURE
  );
});

Deno.test("TransactionManager - should provide transaction context status", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act
  await manager.executeInTransaction(async (tx: TransactionContext) => {
    // Check status during transaction
    const statusDuring = tx.getStatus();
    assertEquals(statusDuring, "active");

    // Execute some operations
    await tx.executeTemplate("CREATE_USER", {
      id: "user-status-test",
      name: "Eve",
      email: "eve@example.com"
    });

    // Status should still be active
    const statusAfterOp = tx.getStatus();
    assertEquals(statusAfterOp, "active");
  });
});

Deno.test("TransactionManager - should support transaction isolation levels", async () => {
  // Arrange
  const client = new TestKuzuClient();
  await client.initialize();
  const manager = new KuzuTransactionManager(client);

  // Act
  const result = await manager.executeInTransaction(async (tx: TransactionContext) => {
    // Transaction should use specified isolation level
    return "Success with serializable isolation";
  }, {
    isolationLevel: "serializable"
  });

  // Assert
  assertEquals(result.success, true);
  assertEquals(result.data, "Success with serializable isolation");
});