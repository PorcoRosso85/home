/**
 * TransactionalSyncAdapter Example
 * トランザクショナル同期アダプターの使用例
 * 
 * This example demonstrates how to integrate the TransactionalSyncAdapter
 * with WebSocketSync, EventGroupManager, and TransactionManager.
 */

import { TransactionalSyncAdapter } from "../core/sync/transactional_sync_adapter.ts";
import { WebSocketSyncImpl } from "../core/websocket/sync.ts";
import { EventGroupManager } from "../event_sourcing/event_group_manager.ts";
import { KuzuTransactionManager } from "../transaction/kuzu_transaction_manager.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import type { BrowserKuzuClient } from "../types.ts";

/**
 * Example 1: Basic Transaction Support
 * 基本的なトランザクションサポート
 */
export async function basicTransactionExample(
  client: BrowserKuzuClient,
  webSocketUrl: string
) {
  // Create WebSocket sync with transaction support
  const webSocketSync = new WebSocketSyncImpl();
  const transactionalSync = new TransactionalSyncAdapter(webSocketSync);
  
  // Connect to server
  await transactionalSync.connect(webSocketUrl);
  
  // Begin transaction
  const txId = transactionalSync.beginTransaction();
  
  try {
    // Send events (will be buffered)
    const event1: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_USER",
      params: { id: "user1", name: "Alice", email: "alice@example.com" },
      timestamp: Date.now(),
    };
    
    const event2: TemplateEvent = {
      id: "evt_2",
      template: "CREATE_POST",
      params: { id: "post1", content: "Hello World", authorId: "user1" },
      timestamp: Date.now(),
    };
    
    await transactionalSync.sendEvent(event1);
    await transactionalSync.sendEvent(event2);
    
    // Events are not sent yet - still buffered
    console.log("Events buffered, not sent to server yet");
    
    // Commit transaction - now events are sent
    await transactionalSync.commitTransaction(txId);
    console.log("Transaction committed - events sent to server");
    
  } catch (error) {
    // Rollback on error - buffered events are discarded
    await transactionalSync.rollbackTransaction(txId);
    console.error("Transaction rolled back:", error);
  }
}

/**
 * Example 2: Integration with TransactionManager
 * TransactionManagerとの統合
 */
export async function transactionManagerIntegration(
  client: BrowserKuzuClient,
  webSocketUrl: string
) {
  // Setup
  const transactionManager = new KuzuTransactionManager(client);
  const webSocketSync = new WebSocketSyncImpl();
  const transactionalSync = new TransactionalSyncAdapter(webSocketSync);
  
  // Connect
  await transactionalSync.connect(webSocketUrl);
  
  // Execute in transaction
  const result = await transactionManager.executeInTransaction(async (tx) => {
    // Use transaction ID from TransactionManager
    transactionalSync.setTransactionContext(tx.transactionId);
    
    // Execute templates (these modify the database)
    const event1 = await tx.executeTemplate("CREATE_USER", {
      id: "user1",
      name: "Alice",
      email: "alice@example.com"
    });
    
    const event2 = await tx.executeTemplate("CREATE_POST", {
      id: "post1",
      content: "My first post",
      authorId: "user1"
    });
    
    // Send events for synchronization (buffered until commit)
    await transactionalSync.sendEvent(event1);
    await transactionalSync.sendEvent(event2);
    
    // Clear context before transaction ends
    transactionalSync.clearTransactionContext();
    
    return { event1, event2 };
  });
  
  if (result.success) {
    console.log("Transaction successful - events synchronized");
  } else {
    console.log("Transaction failed - no events sent");
  }
}

/**
 * Example 3: EventGroup with Transactions
 * EventGroupとトランザクションの組み合わせ
 */
export async function eventGroupTransactionExample(
  client: BrowserKuzuClient,
  webSocketUrl: string
) {
  // Setup
  const transactionManager = new KuzuTransactionManager(client);
  const eventGroupManager = new EventGroupManager();
  const webSocketSync = new WebSocketSyncImpl();
  const transactionalSync = new TransactionalSyncAdapter(webSocketSync);
  
  // Connect
  await transactionalSync.connect(webSocketUrl);
  
  // Execute in transaction
  const result = await transactionManager.executeInTransaction(async (tx) => {
    transactionalSync.setTransactionContext(tx.transactionId);
    
    // Create event group
    const events: TemplateEvent[] = [
      {
        id: "evt_1",
        template: "CREATE_USER",
        params: { id: "user1", name: "Alice", email: "alice@example.com" },
        timestamp: Date.now(),
      },
      {
        id: "evt_2",
        template: "CREATE_USER",
        params: { id: "user2", name: "Bob", email: "bob@example.com" },
        timestamp: Date.now(),
      },
      {
        id: "evt_3",
        template: "FOLLOW_USER",
        params: { followerId: "user1", targetId: "user2" },
        timestamp: Date.now(),
      },
    ];
    
    // Create and execute event group
    const eventGroup = await eventGroupManager.createEventGroup(events);
    await tx.executeEventGroup(events);
    
    // Send events for sync (buffered)
    for (const event of events) {
      await transactionalSync.sendEvent(event);
    }
    
    transactionalSync.clearTransactionContext();
    
    return eventGroup;
  });
  
  console.log("Event group transaction result:", result.success);
}

/**
 * Example 4: Nested Transactions
 * ネストされたトランザクション
 */
export async function nestedTransactionExample(
  client: BrowserKuzuClient,
  webSocketUrl: string
) {
  const webSocketSync = new WebSocketSyncImpl();
  const transactionalSync = new TransactionalSyncAdapter(webSocketSync);
  
  await transactionalSync.connect(webSocketUrl);
  
  // Outer transaction
  const outerTxId = transactionalSync.beginTransaction();
  
  try {
    // Outer transaction event
    const outerEvent: TemplateEvent = {
      id: "evt_outer",
      template: "CREATE_USER",
      params: { id: "admin", name: "Admin", email: "admin@example.com" },
      timestamp: Date.now(),
    };
    await transactionalSync.sendEvent(outerEvent);
    
    // Inner transaction
    const innerTxId = transactionalSync.beginTransaction();
    
    try {
      // Inner transaction events
      const innerEvent1: TemplateEvent = {
        id: "evt_inner1",
        template: "CREATE_USER",
        params: { id: "user1", name: "User 1", email: "user1@example.com" },
        timestamp: Date.now(),
      };
      const innerEvent2: TemplateEvent = {
        id: "evt_inner2",
        template: "CREATE_USER",
        params: { id: "user2", name: "User 2", email: "user2@example.com" },
        timestamp: Date.now(),
      };
      
      await transactionalSync.sendEvent(innerEvent1);
      await transactionalSync.sendEvent(innerEvent2);
      
      // Commit inner transaction
      await transactionalSync.commitTransaction(innerTxId);
      console.log("Inner transaction committed");
      
    } catch (error) {
      await transactionalSync.rollbackTransaction(innerTxId);
      console.error("Inner transaction rolled back:", error);
      throw error;
    }
    
    // Commit outer transaction - sends all events
    await transactionalSync.commitTransaction(outerTxId);
    console.log("Outer transaction committed - all events sent");
    
  } catch (error) {
    await transactionalSync.rollbackTransaction(outerTxId);
    console.error("Outer transaction rolled back:", error);
  }
}

/**
 * Example 5: Manual Transaction Context Management
 * 手動トランザクションコンテキスト管理
 */
export async function manualContextExample(
  client: BrowserKuzuClient,
  webSocketUrl: string
) {
  const transactionManager = new KuzuTransactionManager(client);
  const webSocketSync = new WebSocketSyncImpl();
  const transactionalSync = new TransactionalSyncAdapter(webSocketSync);
  
  await transactionalSync.connect(webSocketUrl);
  
  // Begin transaction through TransactionManager
  const transaction = await transactionManager.beginTransaction();
  
  try {
    // Set context manually
    transactionalSync.setTransactionContext(transaction.id);
    
    // Do some work with events
    const event: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_USER",
      params: { id: "user1", name: "Test User", email: "test@example.com" },
      timestamp: Date.now(),
    };
    
    await transactionalSync.sendEvent(event);
    
    // Can temporarily clear context to send immediate events
    transactionalSync.clearTransactionContext();
    
    const immediateEvent: TemplateEvent = {
      id: "evt_immediate",
      template: "LOG_EVENT",
      params: { message: "Transaction in progress" },
      timestamp: Date.now(),
    };
    
    await transactionalSync.sendEvent(immediateEvent); // Sent immediately
    
    // Restore context
    transactionalSync.setTransactionContext(transaction.id);
    
    const event2: TemplateEvent = {
      id: "evt_2",
      template: "UPDATE_USER",
      params: { id: "user1", name: "Updated User" },
      timestamp: Date.now(),
    };
    
    await transactionalSync.sendEvent(event2); // Buffered
    
    // Clear context before commit
    transactionalSync.clearTransactionContext();
    
    // Commit through TransactionManager
    await transactionManager.commitTransaction(transaction.id);
    
    console.log("Transaction committed with mixed immediate and buffered events");
    
  } catch (error) {
    transactionalSync.clearTransactionContext();
    await transactionManager.rollbackTransaction(transaction.id);
    console.error("Transaction rolled back:", error);
  }
}

// Usage instructions
if (import.meta.main) {
  console.log(`
TransactionalSyncAdapter Examples
=================================

This file contains examples of how to use the TransactionalSyncAdapter
to add transaction support to WebSocket synchronization.

Key Concepts:
1. Events are buffered during active transactions
2. Events are sent only on commit
3. Events are discarded on rollback
4. Supports nested transactions
5. Integrates with TransactionManager and EventGroupManager

To run these examples, you need:
- A running WebSocket server
- A KuzuDB client instance
- Proper imports configured

Example usage:
  import { basicTransactionExample } from "./transactional_sync_example.ts";
  
  const client = await createKuzuClient();
  await basicTransactionExample(client, "ws://localhost:8080");
`);
}