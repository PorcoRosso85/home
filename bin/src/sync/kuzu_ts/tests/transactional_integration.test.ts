/**
 * Transactional Sync Integration Tests
 * トランザクショナル同期統合テスト
 */

import { assertEquals } from "@std/assert";
import { TransactionalSyncAdapter } from "../core/sync/transactional_sync_adapter.ts";
import { WebSocketSyncImpl } from "../core/websocket/sync.ts";
import { EventGroupManager } from "../event_sourcing/event_group_manager.ts";
import { KuzuTransactionManager } from "../transaction/kuzu_transaction_manager.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import type { BrowserKuzuClient } from "../types.ts";

/**
 * Mock KuzuDB client for testing
 * テスト用のモックKuzuDBクライアント
 */
class MockKuzuClient implements BrowserKuzuClient {
  private executedQueries: Array<{ query: string; params?: any }> = [];
  private templates: Array<{ template: string; params: any }> = [];
  private eventHandlers: Array<(event: TemplateEvent) => void> = [];

  async initialize(): Promise<void> {
    // Mock initialization
  }

  async initializeFromSnapshot(_snapshot: any): Promise<void> {
    // Mock initialization from snapshot
  }

  async getLocalState(): Promise<any> {
    return {
      users: [],
      posts: [],
      follows: [],
    };
  }

  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    this.eventHandlers.push(handler);
  }

  async executeQuery(query: string, params?: any): Promise<any> {
    this.executedQueries.push({ query, params });
    
    // Mock responses for transaction queries
    if (query === "BEGIN TRANSACTION") {
      return { success: true };
    }
    if (query === "COMMIT") {
      return { success: true };
    }
    if (query === "ROLLBACK") {
      return { success: true };
    }
    
    return { rows: [] };
  }

  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    this.templates.push({ template, params });
    return {
      id: `evt_${crypto.randomUUID()}`,
      template,
      params,
      timestamp: Date.now(),
    };
  }

  // Test helpers
  getExecutedQueries(): Array<{ query: string; params?: any }> {
    return [...this.executedQueries];
  }

  getExecutedTemplates(): Array<{ template: string; params: any }> {
    return [...this.templates];
  }

  clearHistory(): void {
    this.executedQueries = [];
    this.templates = [];
  }
}

/**
 * Mock WebSocket server for testing
 * テスト用のモックWebSocketサーバー
 */
class MockWebSocketServer {
  private clients: Set<WebSocket> = new Set();
  private receivedMessages: string[] = [];
  private port: number;
  private server?: Deno.HttpServer;

  constructor(port: number = 8765) {
    this.port = port;
  }

  async start(): Promise<void> {
    this.server = Deno.serve({ port: this.port }, (req) => {
      if (req.headers.get("upgrade") !== "websocket") {
        return new Response("Not a websocket request", { status: 400 });
      }

      const { socket, response } = Deno.upgradeWebSocket(req);
      
      socket.onopen = () => {
        this.clients.add(socket);
        socket.send(JSON.stringify({ type: "connected" }));
      };

      socket.onmessage = (event) => {
        this.receivedMessages.push(event.data);
        // Echo to all other clients
        for (const client of this.clients) {
          if (client !== socket && client.readyState === WebSocket.OPEN) {
            client.send(event.data);
          }
        }
      };

      socket.onclose = () => {
        this.clients.delete(socket);
      };

      return response;
    });
  }

  async stop(): Promise<void> {
    if (this.server) {
      await this.server.shutdown();
      this.server = undefined;
    }
  }

  getReceivedMessages(): string[] {
    return [...this.receivedMessages];
  }

  clearMessages(): void {
    this.receivedMessages = [];
  }
}

Deno.test("Transactional Sync Integration - EventGroupManager with TransactionManager", async (t) => {
  await t.step("should sync events only after transaction commit", async () => {
    const mockServer = new MockWebSocketServer();
    await mockServer.start();

    try {
      // Setup
      const mockClient = new MockKuzuClient();
      const transactionManager = new KuzuTransactionManager(mockClient);
      const eventGroupManager = new EventGroupManager();
      const webSocketSync = new WebSocketSyncImpl();
      const transactionalSync = new TransactionalSyncAdapter(webSocketSync);

      // Connect to mock server
      await transactionalSync.connect("ws://localhost:8765");

      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 100));

      // Execute in transaction
      const result = await transactionManager.executeInTransaction(async (tx) => {
        // Set transaction context in sync adapter
        transactionalSync.setTransactionContext(tx.transactionId);

        // Create events through event group
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
        ];

        const eventGroup = await eventGroupManager.createEventGroup(events);

        // Send events (should be buffered)
        for (const event of events) {
          await transactionalSync.sendEvent(event);
        }

        // No messages should be sent yet
        await new Promise(resolve => setTimeout(resolve, 50));
        assertEquals(mockServer.getReceivedMessages().length, 1); // Only connected message

        // Execute templates
        await tx.executeEventGroup(events);

        // Clear transaction context before commit
        transactionalSync.clearTransactionContext();

        return eventGroup;
      });

      // Events should be sent after commit
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const messages = mockServer.getReceivedMessages();
      // Should have: 1 connected message + 2 event messages
      assertEquals(messages.length, 3);

      // Verify event messages
      const eventMessages = messages.slice(1).map(msg => JSON.parse(msg));
      assertEquals(eventMessages.length, 2);
      assertEquals(eventMessages[0].type, "event");
      assertEquals(eventMessages[0].payload.template, "CREATE_USER");
      assertEquals(eventMessages[1].type, "event");
      assertEquals(eventMessages[1].payload.template, "CREATE_USER");

      // Verify transaction was successful
      assertEquals(result.success, true);
      assertEquals(result.data?.status, "committed");

      // Cleanup
      transactionalSync.disconnect();
    } finally {
      await mockServer.stop();
    }
  });

  await t.step("should not sync events on transaction rollback", async () => {
    const mockServer = new MockWebSocketServer();
    await mockServer.start();

    try {
      // Setup
      const mockClient = new MockKuzuClient();
      const transactionManager = new KuzuTransactionManager(mockClient);
      const webSocketSync = new WebSocketSyncImpl();
      const transactionalSync = new TransactionalSyncAdapter(webSocketSync);

      // Connect to mock server
      await transactionalSync.connect("ws://localhost:8765");

      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 100));

      // Execute in transaction that will fail
      const result = await transactionManager.executeInTransaction(async (tx) => {
        // Set transaction context in sync adapter
        transactionalSync.setTransactionContext(tx.transactionId);

        // Create event
        const event: TemplateEvent = {
          id: "evt_1",
          template: "CREATE_USER",
          params: { id: "user1", name: "Alice", email: "alice@example.com" },
          timestamp: Date.now(),
        };

        // Send event (should be buffered)
        await transactionalSync.sendEvent(event);

        // Clear context
        transactionalSync.clearTransactionContext();

        // Throw error to trigger rollback
        throw new Error("Simulated error");
      });

      // Wait to ensure no events are sent
      await new Promise(resolve => setTimeout(resolve, 100));

      const messages = mockServer.getReceivedMessages();
      // Should only have connected message
      assertEquals(messages.length, 1);
      assertEquals(JSON.parse(messages[0]).type, "connected");

      // Verify transaction was rolled back
      assertEquals(result.success, false);
      assertEquals(result.transaction.status, "rolled_back");

      // Cleanup
      transactionalSync.disconnect();
    } finally {
      await mockServer.stop();
    }
  });

  await t.step("should handle nested transactions with event groups", async () => {
    const mockServer = new MockWebSocketServer();
    await mockServer.start();

    try {
      // Setup
      const mockClient = new MockKuzuClient();
      const transactionManager = new KuzuTransactionManager(mockClient);
      const eventGroupManager = new EventGroupManager();
      const webSocketSync = new WebSocketSyncImpl();
      const transactionalSync = new TransactionalSyncAdapter(webSocketSync);

      // Connect to mock server
      await transactionalSync.connect("ws://localhost:8765");

      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 100));

      // Outer transaction
      const outerResult = await transactionManager.executeInTransaction(async (outerTx) => {
        transactionalSync.setTransactionContext(outerTx.transactionId);

        // Create outer event
        const outerEvent: TemplateEvent = {
          id: "evt_outer",
          template: "CREATE_USER",
          params: { id: "user1", name: "Alice", email: "alice@example.com" },
          timestamp: Date.now(),
        };

        await transactionalSync.sendEvent(outerEvent);

        // Inner transaction (simulated - in real usage would be another executeInTransaction)
        const innerTxId = transactionalSync.beginTransaction();
        
        const innerEvent: TemplateEvent = {
          id: "evt_inner",
          template: "CREATE_POST",
          params: { id: "post1", content: "Hello", authorId: "user1" },
          timestamp: Date.now(),
        };

        await transactionalSync.sendEvent(innerEvent);

        // Commit inner transaction
        await transactionalSync.commitTransaction(innerTxId);

        // Clear context and return
        transactionalSync.clearTransactionContext();

        return { outerEvent, innerEvent };
      });

      // Wait for events to be sent
      await new Promise(resolve => setTimeout(resolve, 100));

      const messages = mockServer.getReceivedMessages();
      // Should have: 1 connected message + 2 event messages
      assertEquals(messages.length, 3);

      // Verify both events were sent
      const eventMessages = messages.slice(1).map(msg => JSON.parse(msg));
      const templates = eventMessages.map(msg => msg.payload.template);
      assertEquals(templates.includes("CREATE_USER"), true);
      assertEquals(templates.includes("CREATE_POST"), true);

      // Cleanup
      transactionalSync.disconnect();
    } finally {
      await mockServer.stop();
    }
  });

  await t.step("should handle transaction timeout correctly", async () => {
    const mockServer = new MockWebSocketServer();
    await mockServer.start();

    try {
      // Setup
      const mockClient = new MockKuzuClient();
      const transactionManager = new KuzuTransactionManager(mockClient);
      const webSocketSync = new WebSocketSyncImpl();
      const transactionalSync = new TransactionalSyncAdapter(webSocketSync);

      // Connect to mock server
      await transactionalSync.connect("ws://localhost:8765");

      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 100));

      // Execute transaction with timeout
      const result = await transactionManager.executeInTransaction(async (tx) => {
        transactionalSync.setTransactionContext(tx.transactionId);

        // Send event
        const event: TemplateEvent = {
          id: "evt_1",
          template: "CREATE_USER",
          params: { id: "user1", name: "Alice", email: "alice@example.com" },
          timestamp: Date.now(),
        };

        await transactionalSync.sendEvent(event);

        // Simulate long operation
        await new Promise(resolve => setTimeout(resolve, 200));

        transactionalSync.clearTransactionContext();
        return event;
      }, { timeout: 100 }); // 100ms timeout

      // Transaction should have timed out
      assertEquals(result.success, false);
      assertEquals(result.transaction.status, "rolled_back");

      // Wait to ensure no events are sent
      await new Promise(resolve => setTimeout(resolve, 100));

      const messages = mockServer.getReceivedMessages();
      // Should only have connected message (no events sent due to rollback)
      assertEquals(messages.length, 1);

      // Cleanup
      transactionalSync.disconnect();
    } finally {
      await mockServer.stop();
    }
  });
});