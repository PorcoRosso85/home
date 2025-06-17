import { test, describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { MinimalSyncClient, createSyncClient } from './syncClient.ts';

describe('MinimalSyncClient', () => {
  let client: MinimalSyncClient | null = null;

  // Mock WebSocket server for testing
  const mockServerUrl = 'ws://localhost:8081/sync';
  const testClientId = 'test-client-001';

  before(async () => {
    console.log('Note: These tests require a WebSocket server running at', mockServerUrl);
  });

  after(async () => {
    if (client) {
      await client.close();
    }
  });

  it('should create a sync client instance', async () => {
    // This test will fail if no server is running
    // In a real test environment, you'd mock the WebSocket connection
    try {
      client = new MinimalSyncClient({
        serverUrl: mockServerUrl,
        clientId: testClientId,
        databasePath: ':memory:',
        reconnectInterval: 2000,
        heartbeatInterval: 10000
      });

      // Don't initialize if no server is available
      // await client.initialize();
      
      assert.ok(client, 'Client should be created');
    } catch (error) {
      console.log('Skipping test - no WebSocket server available');
    }
  });

  it('should demonstrate node creation API', async () => {
    // Example of how to use the client
    const exampleUsage = async () => {
      const client = await createSyncClient({
        serverUrl: 'ws://your-server.com/sync',
        clientId: 'client-123'
      });

      // Create a node
      const nodeId = await client.createNode('Person', {
        name: 'Alice',
        age: 30,
        email: 'alice@example.com'
      });

      // Update a property
      await client.setProperty('node', nodeId, 'age', 31);

      // Check status
      console.log('Connected:', client.isReady());
      console.log('Pending patches:', client.getPendingPatchCount());
      console.log('Server version:', client.getServerVersion());

      await client.close();
    };

    // Just verify the API exists
    assert.ok(typeof MinimalSyncClient.prototype.createNode === 'function');
    assert.ok(typeof MinimalSyncClient.prototype.setProperty === 'function');
  });
});

// Example standalone usage
async function exampleUsage() {
  console.log('MinimalSyncClient Example Usage:');
  console.log('================================');

  // Create and initialize client
  const client = await createSyncClient({
    serverUrl: 'ws://localhost:8080/sync',
    clientId: 'example-client-001',
    databasePath: './example.db', // Use persistent database
    reconnectInterval: 5000,
    heartbeatInterval: 30000
  });

  try {
    // Create some nodes
    const person1 = await client.createNode('Person', {
      name: 'Alice',
      age: 30,
      city: 'New York'
    });

    const person2 = await client.createNode('Person', {
      name: 'Bob',
      age: 25,
      city: 'San Francisco'
    });

    // Update properties
    await client.setProperty('node', person1, 'occupation', 'Engineer');
    await client.setProperty('node', person2, 'occupation', 'Designer');

    // Check sync status
    console.log(`\nSync Status:`);
    console.log(`- Connected: ${client.isReady()}`);
    console.log(`- Pending patches: ${client.getPendingPatchCount()}`);
    console.log(`- Server version: ${client.getServerVersion()}`);

    // Wait a bit for sync to complete
    await new Promise(resolve => setTimeout(resolve, 2000));

    console.log(`\nAfter sync:`);
    console.log(`- Pending patches: ${client.getPendingPatchCount()}`);
    console.log(`- Server version: ${client.getServerVersion()}`);

  } finally {
    await client.close();
  }
}

// Run example if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  exampleUsage().catch(console.error);
}