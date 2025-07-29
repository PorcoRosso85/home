/**
 * Sync KuzuDB Client Statistics Unit Tests
 * Unit tests for statistics functionality without KuzuDB dependency
 */

import { assertEquals, assertExists } from "jsr:@std/assert";
import { SyncKuzuClient } from "../core/sync_kuzu_client.ts";

// Mock BrowserKuzuClientImpl for testing
class MockBrowserKuzuClient {
  async initialize(): Promise<void> {
    // Mock initialization
  }
  
  async executeTemplate(template: string, params: Record<string, any>): Promise<any> {
    // Return a mock event
    return {
      id: `evt_${Date.now()}`,
      template,
      params,
      timestamp: Date.now(),
      clientId: "mock-client"
    };
  }
  
  async applyEvent(event: any): Promise<void> {
    // Mock apply event
  }
  
  onRemoteEvent(handler: (event: any) => void): void {
    // Mock handler registration
  }
}

// Mock SyncClient
class MockSyncClient {
  private clientId: string;
  private eventHandlers: Array<(event: any) => void> = [];
  
  constructor(clientId: string) {
    this.clientId = clientId;
  }
  
  getClientId(): string {
    return this.clientId;
  }
  
  async connect(url: string): Promise<void> {
    // Mock connect
  }
  
  async sendEvent(event: any): Promise<void> {
    // Mock send - just trigger handlers locally for testing
    this.eventHandlers.forEach(handler => handler(event));
  }
  
  onEvent(handler: (event: any) => void): void {
    this.eventHandlers.push(handler);
  }
  
  async close(): Promise<void> {
    // Mock close
  }
}

// Create a test client with mocked dependencies
function createTestClient(clientId: string): SyncKuzuClient {
  const client = new SyncKuzuClient({ clientId, autoReconnect: false });
  // Replace the internal clients with our mocks
  (client as any).kuzuClient = new MockBrowserKuzuClient();
  (client as any).syncClient = new MockSyncClient(clientId);
  
  // Stop the stats reporter to avoid timing issues in tests
  (client as any).stopStatsReporter();
  
  // Re-setup the event handler since we replaced the sync client
  (client as any).syncClient.onEvent(async (event: any) => {
    const incrementStats = (client as any).incrementTemplateStats.bind(client);
    incrementStats(event.template, 'received');
    
    try {
      await (client as any).kuzuClient.applyEvent(event);
      (client as any).dmlStats.applied++;
      incrementStats(event.template, 'applied');
    } catch (error) {
      (client as any).dmlStats.failed++;
      incrementStats(event.template, 'failed');
    }
    
    (client as any).dmlStats.received++;
  });
  
  return client;
}

Deno.test("SyncKuzuClient Stats - Template-specific counters", async () => {
  const client = createTestClient("test-template-stats");
  
  // Execute different template types
  await client.executeTemplate("CREATE_USER", { 
    id: "user1", 
    name: "Test User 1"
  });
  
  await client.executeTemplate("UPDATE_USER", { 
    id: "user1", 
    name: "Updated User 1"
  });
  
  await client.executeTemplate("CREATE_USER", { 
    id: "user2", 
    name: "Test User 2"
  });
  
  // Get detailed stats
  const detailedStats = client.getDetailedStatsByTemplate();
  
  // Verify CREATE_USER stats
  assertExists(detailedStats["CREATE_USER"]);
  assertEquals(detailedStats["CREATE_USER"].sent, 2);
  assertEquals(detailedStats["CREATE_USER"].received, 2); // Mock sends events back
  assertEquals(detailedStats["CREATE_USER"].applied, 2);
  assertEquals(detailedStats["CREATE_USER"].failed, 0);
  assertEquals(detailedStats["CREATE_USER"].successRate, 100);
  
  // Verify UPDATE_USER stats
  assertExists(detailedStats["UPDATE_USER"]);
  assertEquals(detailedStats["UPDATE_USER"].sent, 1);
  assertEquals(detailedStats["UPDATE_USER"].received, 1);
  assertEquals(detailedStats["UPDATE_USER"].applied, 1);
  assertEquals(detailedStats["UPDATE_USER"].failed, 0);
  assertEquals(detailedStats["UPDATE_USER"].successRate, 100);
  
  await client.close();
});

Deno.test("SyncKuzuClient Stats - Overall DML statistics", async () => {
  const client = createTestClient("test-overall-stats");
  
  // Execute some templates
  await client.executeTemplate("CREATE_USER", { 
    id: "user1", 
    name: "User for Stats"
  });
  
  await client.executeTemplate("INCREMENT_COUNTER", { 
    counterId: "test_counter",
    amount: 5
  });
  
  await client.executeTemplate("DELETE_USER_DATA", { 
    userId: "user1",
    reason: "Test"
  });
  
  // Get overall stats
  const overallStats = client.getDMLStats();
  
  // Verify overall stats
  assertEquals(overallStats.sent, 3);
  assertEquals(overallStats.received, 3); // Mock sends events back
  assertEquals(overallStats.applied, 3);
  assertEquals(overallStats.failed, 0);
  assertEquals(overallStats.clientId, "test-overall-stats");
  
  await client.close();
});

Deno.test("SyncKuzuClient Stats - Success rate calculation", async () => {
  const client = createTestClient("test-success-rate");
  
  // Simulate received events with different outcomes
  const syncClient = (client as any).syncClient;
  const eventHandlers = (syncClient as any).eventHandlers || [];
  
  // Simulate receiving and applying events
  const mockEvent1 = {
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "user1", name: "User 1" },
    timestamp: Date.now()
  };
  
  const mockEvent2 = {
    id: "evt_2",
    template: "CREATE_USER",
    params: { id: "user2", name: "User 2" },
    timestamp: Date.now()
  };
  
  // Manually trigger the stats counters (since we can't easily trigger the event handler)
  const incrementStats = (client as any).incrementTemplateStats.bind(client);
  
  // Simulate successful events
  incrementStats("CREATE_USER", "received");
  incrementStats("CREATE_USER", "applied");
  incrementStats("CREATE_USER", "received");
  incrementStats("CREATE_USER", "applied");
  
  // Simulate failed event
  incrementStats("CREATE_USER", "received");
  incrementStats("CREATE_USER", "failed");
  
  // Get stats
  const stats = client.getDetailedStatsByTemplate();
  
  // Verify success rate calculation
  // 2 applied, 1 failed = 66.67% success rate
  assertExists(stats["CREATE_USER"]);
  assertEquals(stats["CREATE_USER"].received, 3);
  assertEquals(stats["CREATE_USER"].applied, 2);
  assertEquals(stats["CREATE_USER"].failed, 1);
  assertEquals(Math.round(stats["CREATE_USER"].successRate), 67);
  
  await client.close();
});

Deno.test("SyncKuzuClient Stats - Multiple template types", async () => {
  const client = createTestClient("test-multi-template");
  
  // Execute various templates
  const templates = [
    { name: "CREATE_USER", count: 3 },
    { name: "UPDATE_USER", count: 2 },
    { name: "DELETE_USER_DATA", count: 1 },
    { name: "INCREMENT_COUNTER", count: 4 },
    { name: "CREATE_POST", count: 2 }
  ];
  
  for (const { name, count } of templates) {
    for (let i = 0; i < count; i++) {
      await client.executeTemplate(name, { id: `${name}_${i}` });
    }
  }
  
  // Get detailed stats
  const detailedStats = client.getDetailedStatsByTemplate();
  
  // Verify each template has correct counts
  assertEquals(detailedStats["CREATE_USER"].sent, 3);
  assertEquals(detailedStats["UPDATE_USER"].sent, 2);
  assertEquals(detailedStats["DELETE_USER_DATA"].sent, 1);
  assertEquals(detailedStats["INCREMENT_COUNTER"].sent, 4);
  assertEquals(detailedStats["CREATE_POST"].sent, 2);
  
  // Verify overall stats
  const overallStats = client.getDMLStats();
  assertEquals(overallStats.sent, 12); // Total of all templates
  
  await client.close();
});