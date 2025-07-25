/**
 * TransactionalSyncAdapter Tests
 * トランザクショナル同期アダプターのテスト
 */

import { assertEquals, assertRejects } from "@std/assert";
import { TransactionalSyncAdapter } from "../core/sync/transactional_sync_adapter.ts";
import type { WebSocketSync } from "../core/websocket/types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

/**
 * Mock WebSocketSync for testing
 * テスト用のモックWebSocketSync
 */
class MockWebSocketSync implements WebSocketSync {
  sentEvents: TemplateEvent[] = [];
  connected = false;
  eventHandlers: Array<(event: TemplateEvent) => void> = [];
  pendingEvents: TemplateEvent[] = [];

  async connect(_url: string): Promise<void> {
    this.connected = true;
  }

  async sendEvent(event: TemplateEvent): Promise<void> {
    if (!this.connected) {
      this.pendingEvents.push(event);
      return;
    }
    this.sentEvents.push(event);
  }

  onEvent(handler: (event: TemplateEvent) => void): void {
    this.eventHandlers.push(handler);
  }

  disconnect(): void {
    this.connected = false;
  }

  isConnected(): boolean {
    return this.connected;
  }

  async getPendingEvents(): Promise<TemplateEvent[]> {
    return [...this.pendingEvents];
  }

  // Test helper to simulate receiving events
  simulateReceiveEvent(event: TemplateEvent): void {
    this.eventHandlers.forEach(handler => handler(event));
  }

  // Test helper to clear sent events
  clearSentEvents(): void {
    this.sentEvents = [];
  }
}

// Test helpers
function createMockAdapter() {
  const mockWebSocket = new MockWebSocketSync();
  const adapter = new TransactionalSyncAdapter(mockWebSocket);
  return { mockWebSocket, adapter };
}

Deno.test("TransactionalSyncAdapter - Basic functionality", async (t) => {
  await t.step("should forward connect/disconnect calls to underlying WebSocket", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    
    await adapter.connect("ws://localhost:8080");
    assertEquals(mockWebSocket.connected, true);

    adapter.disconnect();
    assertEquals(mockWebSocket.connected, false);
  });

  await t.step("should forward isConnected calls", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    
    assertEquals(adapter.isConnected(), false);
    
    await adapter.connect("ws://localhost:8080");
    assertEquals(adapter.isConnected(), true);
  });

  await t.step("should forward onEvent registrations", () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    
    let receivedEvent: TemplateEvent | null = null;
    adapter.onEvent((event) => {
      receivedEvent = event;
    });

    const testEvent: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test" } },
      timestamp: Date.now(),
    };

    mockWebSocket.simulateReceiveEvent(testEvent);
    assertEquals(receivedEvent, testEvent);
  });

  await t.step("should forward getPendingEvents calls", async () => {
    const { adapter } = createMockAdapter();
    
    const pendingEvents = await adapter.getPendingEvents();
    assertEquals(pendingEvents, []);
  });
});

Deno.test("TransactionalSyncAdapter - Transaction handling", async (t) => {
  await t.step("should buffer events during a transaction", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");
    
    // Begin transaction
    const txId = adapter.beginTransaction();

    // Send events during transaction
    const event1: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test1" } },
      timestamp: Date.now(),
    };
    const event2: TemplateEvent = {
      id: "evt_2",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test2" } },
      timestamp: Date.now(),
    };

    await adapter.sendEvent(event1);
    await adapter.sendEvent(event2);

    // Events should not be sent to WebSocket yet
    assertEquals(mockWebSocket.sentEvents.length, 0);

    // Commit transaction
    await adapter.commitTransaction(txId);

    // Now events should be sent
    assertEquals(mockWebSocket.sentEvents.length, 2);
    assertEquals(mockWebSocket.sentEvents[0], event1);
    assertEquals(mockWebSocket.sentEvents[1], event2);
  });

  await t.step("should discard buffered events on rollback", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");
    
    // Begin transaction
    const txId = adapter.beginTransaction();

    // Send events during transaction
    const event1: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test1" } },
      timestamp: Date.now(),
    };

    await adapter.sendEvent(event1);

    // Events should not be sent to WebSocket yet
    assertEquals(mockWebSocket.sentEvents.length, 0);

    // Rollback transaction
    await adapter.rollbackTransaction(txId);

    // Events should still not be sent
    assertEquals(mockWebSocket.sentEvents.length, 0);

    // Future events should work normally
    const event2: TemplateEvent = {
      id: "evt_2",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test2" } },
      timestamp: Date.now(),
    };

    await adapter.sendEvent(event2);
    assertEquals(mockWebSocket.sentEvents.length, 1);
    assertEquals(mockWebSocket.sentEvents[0], event2);
  });

  await t.step("should handle nested transactions", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");
    
    // Begin outer transaction
    const outerTxId = adapter.beginTransaction();

    const event1: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test1" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event1);

    // Begin inner transaction
    const innerTxId = adapter.beginTransaction();

    const event2: TemplateEvent = {
      id: "evt_2",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test2" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event2);

    // No events sent yet
    assertEquals(mockWebSocket.sentEvents.length, 0);

    // Commit inner transaction
    await adapter.commitTransaction(innerTxId);

    // Still no events sent (outer transaction still active)
    assertEquals(mockWebSocket.sentEvents.length, 0);

    // Commit outer transaction
    await adapter.commitTransaction(outerTxId);

    // Now all events should be sent
    assertEquals(mockWebSocket.sentEvents.length, 2);
    assertEquals(mockWebSocket.sentEvents[0], event1);
    assertEquals(mockWebSocket.sentEvents[1], event2);
  });

  await t.step("should handle rollback of inner transaction", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");
    
    // Begin outer transaction
    const outerTxId = adapter.beginTransaction();

    const event1: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test1" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event1);

    // Begin inner transaction
    const innerTxId = adapter.beginTransaction();

    const event2: TemplateEvent = {
      id: "evt_2",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test2" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event2);

    // Rollback inner transaction
    await adapter.rollbackTransaction(innerTxId);

    // Commit outer transaction
    await adapter.commitTransaction(outerTxId);

    // Only event from outer transaction should be sent
    assertEquals(mockWebSocket.sentEvents.length, 1);
    assertEquals(mockWebSocket.sentEvents[0], event1);
  });

  await t.step("should send events immediately when no transaction is active", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");

    const event: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test" } },
      timestamp: Date.now(),
    };

    await adapter.sendEvent(event);

    // Event should be sent immediately
    assertEquals(mockWebSocket.sentEvents.length, 1);
    assertEquals(mockWebSocket.sentEvents[0], event);
  });

  await t.step("should throw error when committing non-existent transaction", async () => {
    const { adapter } = createMockAdapter();
    
    await assertRejects(
      async () => await adapter.commitTransaction("non-existent"),
      Error,
      "Transaction not found"
    );
  });

  await t.step("should throw error when rolling back non-existent transaction", async () => {
    const { adapter } = createMockAdapter();
    
    await assertRejects(
      async () => await adapter.rollbackTransaction("non-existent"),
      Error,
      "Transaction not found"
    );
  });

  await t.step("should handle multiple independent transactions", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");
    
    // Begin first transaction
    const tx1Id = adapter.beginTransaction();

    const event1: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test1" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event1);

    // Begin second transaction
    const tx2Id = adapter.beginTransaction();

    const event2: TemplateEvent = {
      id: "evt_2",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test2" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event2);

    // Commit second transaction first
    await adapter.commitTransaction(tx2Id);

    // No events sent yet (tx1 still active)
    assertEquals(mockWebSocket.sentEvents.length, 0);

    // Commit first transaction
    await adapter.commitTransaction(tx1Id);

    // All events should be sent in order
    assertEquals(mockWebSocket.sentEvents.length, 2);
    assertEquals(mockWebSocket.sentEvents[0], event1);
    assertEquals(mockWebSocket.sentEvents[1], event2);
  });
});

Deno.test("TransactionalSyncAdapter - Connection state handling", async (t) => {
  await t.step("should buffer events when disconnected during transaction", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");
    
    // Begin transaction
    const txId = adapter.beginTransaction();

    const event1: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test1" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event1);

    // Disconnect
    adapter.disconnect();

    // Commit transaction while disconnected
    await adapter.commitTransaction(txId);

    // Events should be pending in WebSocket
    assertEquals(mockWebSocket.sentEvents.length, 0);
    assertEquals(mockWebSocket.pendingEvents.length, 1);

    // Reconnect
    await adapter.connect("ws://localhost:8080");

    // Simulate WebSocket sending pending events
    mockWebSocket.sentEvents = [...mockWebSocket.pendingEvents];
    mockWebSocket.pendingEvents = [];

    assertEquals(mockWebSocket.sentEvents.length, 1);
    assertEquals(mockWebSocket.sentEvents[0], event1);
  });
});

Deno.test("TransactionalSyncAdapter - Integration with TransactionManager", async (t) => {
  await t.step("should allow external transaction ID management", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");
    
    // Begin transaction with external ID
    const externalTxId = "tx_external_123";
    adapter.beginTransaction(externalTxId);

    const event: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event);

    // No events sent yet
    assertEquals(mockWebSocket.sentEvents.length, 0);

    // Commit using external ID
    await adapter.commitTransaction(externalTxId);

    // Event should be sent
    assertEquals(mockWebSocket.sentEvents.length, 1);
    assertEquals(mockWebSocket.sentEvents[0], event);
  });

  await t.step("should handle transaction context switching", async () => {
    const { mockWebSocket, adapter } = createMockAdapter();
    await adapter.connect("ws://localhost:8080");
    
    // Set transaction context
    adapter.setTransactionContext("tx_123");

    const event1: TemplateEvent = {
      id: "evt_1",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test1" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event1);

    // No events sent yet
    assertEquals(mockWebSocket.sentEvents.length, 0);

    // Clear transaction context
    adapter.clearTransactionContext();

    const event2: TemplateEvent = {
      id: "evt_2",
      template: "CREATE_NODE",
      params: { label: "User", properties: { name: "Test2" } },
      timestamp: Date.now(),
    };
    await adapter.sendEvent(event2);

    // Second event sent immediately
    assertEquals(mockWebSocket.sentEvents.length, 1);
    assertEquals(mockWebSocket.sentEvents[0], event2);

    // First event still buffered
    adapter.setTransactionContext("tx_123");
    await adapter.commitTransaction("tx_123");

    // Now first event should be sent
    assertEquals(mockWebSocket.sentEvents.length, 2);
    assertEquals(mockWebSocket.sentEvents[1], event1);
  });
});