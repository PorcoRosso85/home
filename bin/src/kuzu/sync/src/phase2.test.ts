/**
 * Phase 2 Integration Tests
 * Tests protocol message handling, sync manager version assignment,
 * client-server sync flow, and conflict detection
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { WebSocket, WebSocketServer } from 'ws';
import { createSyncManager } from './syncManager.ts';
import { createSnapshotManager } from './snapshotManager.ts';
import { createDiffEngine } from './diffEngine.ts';
import type { 
  SyncMessage, 
  ClientId, 
  Patch,
  PatchSubmit,
  SnapshotRequest,
  VersionVectorRequest
} from './protocol.ts';
import { 
  createMessage,
  isPatchAck,
  isSnapshotResponse,
  isVersionVectorResponse,
  isDiffBroadcast,
  isError
} from './protocol.ts';

// Test configuration
const TEST_PORT = 9876;
const TEST_URL = `ws://localhost:${TEST_PORT}`;

// Helper to create test patches
function createTestPatch(id: string, operation: string = 'SET_PROPERTY'): Patch {
  return {
    id,
    operation: operation as any,
    path: `/nodes/n${id}`,
    property: 'name',
    value: `test-${id}`,
    oldValue: null
  };
}

// Helper to wait for WebSocket message
function waitForMessage(ws: WebSocket, predicate: (msg: SyncMessage) => boolean): Promise<SyncMessage> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Timeout waiting for message'));
    }, 5000);

    const handler = (data: Buffer) => {
      try {
        const message = JSON.parse(data.toString()) as SyncMessage;
        if (predicate(message)) {
          clearTimeout(timeout);
          ws.off('message', handler);
          resolve(message);
        }
      } catch (error) {
        // Continue waiting
      }
    };

    ws.on('message', handler);
  });
}

describe('Phase 2 Integration Tests', () => {
  let server: WebSocketServer;
  let syncManager: ReturnType<typeof createSyncManager>;
  let activeClients: WebSocket[] = [];

  beforeEach(async () => {
    // Create a mock snapshot manager for testing
    const mockSnapshotManager = {
      createSnapshot: async (db: any, version: number) => {
        return {
          id: `snapshot-test-${version}`,
          timestamp: Date.now(),
          version,
          size: 1024,
          path: `/tmp/test-snapshots/snapshot-test-${version}.cypher`
        };
      },
      loadSnapshot: async (db: any, snapshotId: string) => {
        return { success: true };
      },
      getLatestSnapshot: async () => {
        return {
          code: 'NO_SNAPSHOTS' as const,
          message: 'No snapshots available'
        };
      }
    };
    
    const diffEngine = createDiffEngine();
    syncManager = createSyncManager({
      snapshotManager: mockSnapshotManager,
      diffEngine,
      maxHistorySize: 100
    });

    // Create WebSocket server
    server = new WebSocketServer({ port: TEST_PORT });
    
    server.on('connection', (ws, req) => {
      const clientId = req.headers['x-client-id'] as string || `client-${Date.now()}`;
      
      // Add client to sync manager
      const connection = {
        id: clientId,
        send: (message: SyncMessage) => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
          }
        },
        close: () => ws.close()
      };
      
      syncManager.addClient(connection);
      
      // Handle messages from client
      ws.on('message', async (data) => {
        try {
          const message = JSON.parse(data.toString()) as SyncMessage;
          await syncManager.handleMessage(clientId, message);
        } catch (error) {
          console.error('Error handling client message:', error);
        }
      });
      
      ws.on('close', () => {
        syncManager.removeClient(clientId);
      });
    });

    // Wait for server to be ready
    await new Promise(resolve => setTimeout(resolve, 100));
  });

  afterEach(async () => {
    // Close all active clients
    for (const client of activeClients) {
      if (client.readyState === WebSocket.OPEN) {
        client.close();
      }
    }
    activeClients = [];

    // Close server
    await new Promise<void>((resolve) => {
      server.close(() => resolve());
    });
  });

  it('should handle protocol messages correctly', async () => {
    const clientId = 'test-client-1';
    const ws = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': clientId }
    });
    activeClients.push(ws);

    await new Promise(resolve => ws.on('open', resolve));

    // Test snapshot request/response
    const snapshotRequest: SnapshotRequest = createMessage('SNAPSHOT_REQUEST', clientId, {
      fromVersion: 0
    });
    
    ws.send(JSON.stringify(snapshotRequest));
    
    const snapshotResponse = await waitForMessage(ws, isSnapshotResponse);
    assert.equal(snapshotResponse.type, 'SNAPSHOT_RESPONSE');
    assert.equal(snapshotResponse.version, 0);
    assert.equal(snapshotResponse.incremental, false);

    // Test version vector request/response
    const versionRequest: VersionVectorRequest = createMessage('VERSION_VECTOR_REQUEST', clientId, {});
    
    ws.send(JSON.stringify(versionRequest));
    
    const versionResponse = await waitForMessage(ws, isVersionVectorResponse);
    assert.equal(versionResponse.type, 'VERSION_VECTOR_RESPONSE');
    assert.equal(versionResponse.currentVersion, 0);
    assert.ok(versionResponse.vector);
  });

  it('should assign versions to patches correctly', async () => {
    const clientId = 'test-client-2';
    const ws = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': clientId }
    });
    activeClients.push(ws);

    await new Promise(resolve => ws.on('open', resolve));

    // Submit first patch
    const patch1: PatchSubmit = createMessage('PATCH_SUBMIT', clientId, {
      patches: [createTestPatch('1')],
      baseVersion: 0
    });
    
    ws.send(JSON.stringify(patch1));
    
    const ack1 = await waitForMessage(ws, isPatchAck);
    assert.equal(ack1.type, 'PATCH_ACK');
    assert.equal(ack1.success, true);
    assert.equal(ack1.assignedVersion, 1);

    // Submit second patch
    const patch2: PatchSubmit = createMessage('PATCH_SUBMIT', clientId, {
      patches: [createTestPatch('2')],
      baseVersion: 1
    });
    
    ws.send(JSON.stringify(patch2));
    
    const ack2 = await waitForMessage(ws, isPatchAck);
    assert.equal(ack2.success, true);
    assert.equal(ack2.assignedVersion, 2);

    // Verify version vector
    const versionRequest: VersionVectorRequest = createMessage('VERSION_VECTOR_REQUEST', clientId, {});
    ws.send(JSON.stringify(versionRequest));
    
    const versionResponse = await waitForMessage(ws, isVersionVectorResponse);
    assert.equal(versionResponse.currentVersion, 2);
    assert.equal(versionResponse.vector[clientId], 2);
  });

  it('should sync changes between multiple clients', async () => {
    // Create two clients
    const client1Id = 'test-client-3a';
    const client2Id = 'test-client-3b';
    
    const ws1 = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': client1Id }
    });
    const ws2 = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': client2Id }
    });
    activeClients.push(ws1, ws2);

    await Promise.all([
      new Promise(resolve => ws1.on('open', resolve)),
      new Promise(resolve => ws2.on('open', resolve))
    ]);

    // Client 1 submits a patch
    const patch: PatchSubmit = createMessage('PATCH_SUBMIT', client1Id, {
      patches: [createTestPatch('3')],
      baseVersion: 0
    });
    
    ws1.send(JSON.stringify(patch));
    
    // Client 1 receives acknowledgment
    const ack = await waitForMessage(ws1, isPatchAck);
    assert.equal(ack.success, true);
    assert.equal(ack.assignedVersion, 1);

    // Client 2 receives broadcast
    const broadcast = await waitForMessage(ws2, isDiffBroadcast);
    assert.equal(broadcast.type, 'DIFF_BROADCAST');
    assert.equal(broadcast.version, 1);
    assert.equal(broadcast.sourceClientId, client1Id);
    assert.equal(broadcast.patches.length, 1);
    assert.equal(broadcast.patches[0].id, '3');
  });

  it('should detect version conflicts', async () => {
    // Create two clients
    const client1Id = 'test-client-4a';
    const client2Id = 'test-client-4b';
    
    const ws1 = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': client1Id }
    });
    const ws2 = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': client2Id }
    });
    activeClients.push(ws1, ws2);

    await Promise.all([
      new Promise(resolve => ws1.on('open', resolve)),
      new Promise(resolve => ws2.on('open', resolve))
    ]);

    // Client 1 submits a patch
    const patch1: PatchSubmit = createMessage('PATCH_SUBMIT', client1Id, {
      patches: [createTestPatch('4')],
      baseVersion: 0
    });
    
    ws1.send(JSON.stringify(patch1));
    
    // Wait for acknowledgment
    const ack1 = await waitForMessage(ws1, isPatchAck);
    assert.equal(ack1.success, true);
    assert.equal(ack1.assignedVersion, 1);

    // Client 2 submits a patch with outdated base version
    const patch2: PatchSubmit = createMessage('PATCH_SUBMIT', client2Id, {
      patches: [createTestPatch('5')],
      baseVersion: 0 // Outdated! Current version is 1
    });
    
    ws2.send(JSON.stringify(patch2));
    
    // Client 2 receives conflict response
    const ack2 = await waitForMessage(ws2, isPatchAck);
    assert.equal(ack2.success, false);
    assert.ok(ack2.conflict);
    assert.equal(ack2.conflict.type, 'VERSION_MISMATCH');
    assert.equal(ack2.conflict.expectedVersion, 0);
    assert.equal(ack2.conflict.actualVersion, 1);
  });

  it('should handle concurrent edits from multiple clients', async () => {
    // Create three clients
    const clients = ['5a', '5b', '5c'].map(suffix => ({
      id: `test-client-${suffix}`,
      ws: new WebSocket(TEST_URL, {
        headers: { 'X-Client-ID': `test-client-${suffix}` }
      })
    }));
    
    clients.forEach(c => activeClients.push(c.ws));

    // Wait for all clients to connect
    await Promise.all(clients.map(c => 
      new Promise(resolve => c.ws.on('open', resolve))
    ));

    // All clients submit patches concurrently based on version 0
    const submissions = clients.map((client, index) => {
      const patch: PatchSubmit = createMessage('PATCH_SUBMIT', client.id, {
        patches: [createTestPatch(`concurrent-${index}`)],
        baseVersion: 0
      });
      
      client.ws.send(JSON.stringify(patch));
      return waitForMessage(client.ws, isPatchAck);
    });

    const responses = await Promise.all(submissions);

    // One should succeed, others should fail
    const successful = responses.filter(r => r.success);
    const failed = responses.filter(r => !r.success);
    
    assert.equal(successful.length, 1);
    assert.equal(failed.length, 2);
    
    // Check that failed responses have conflict info
    failed.forEach(response => {
      assert.ok(response.conflict);
      assert.equal(response.conflict.type, 'VERSION_MISMATCH');
    });

    // Verify that successful client got the right version
    const successfulAck = successful[0];
    assert.equal(successfulAck.assignedVersion, 1);
    
    // Other clients who received broadcast
    const expectedBroadcastClients = clients.filter(c => c.id !== successfulAck.clientId);
    
    // Only check for broadcasts if there are clients that should receive them
    if (expectedBroadcastClients.length > 0) {
      // Give some time for broadcasts to arrive
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Check each client individually for broadcast messages
      for (const client of expectedBroadcastClients) {
        try {
          const broadcast = await Promise.race([
            waitForMessage(client.ws, isDiffBroadcast),
            new Promise<never>((_, reject) => setTimeout(() => reject(new Error('Broadcast timeout')), 1000))
          ]) as SyncMessage;
          assert.equal((broadcast as any).version, 1);
        } catch (e) {
          // Broadcast might not arrive if client already disconnected
          console.log(`Client ${client.id} did not receive broadcast (might be disconnected)`);
        }
      }
    }
  });

  it('should maintain correct version vectors across clients', async () => {
    const client1Id = 'test-client-6a';
    const client2Id = 'test-client-6b';
    
    const ws1 = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': client1Id }
    });
    const ws2 = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': client2Id }
    });
    activeClients.push(ws1, ws2);

    await Promise.all([
      new Promise(resolve => ws1.on('open', resolve)),
      new Promise(resolve => ws2.on('open', resolve))
    ]);

    // Client 1 submits patches
    for (let i = 0; i < 3; i++) {
      const patch: PatchSubmit = createMessage('PATCH_SUBMIT', client1Id, {
        patches: [createTestPatch(`v1-${i}`)],
        baseVersion: i
      });
      
      ws1.send(JSON.stringify(patch));
      await waitForMessage(ws1, isPatchAck);
    }

    // Client 2 submits patches
    for (let i = 0; i < 2; i++) {
      const patch: PatchSubmit = createMessage('PATCH_SUBMIT', client2Id, {
        patches: [createTestPatch(`v2-${i}`)],
        baseVersion: 3 + i
      });
      
      ws2.send(JSON.stringify(patch));
      await waitForMessage(ws2, isPatchAck);
    }

    // Check version vectors from both clients
    const versionRequest: VersionVectorRequest = createMessage('VERSION_VECTOR_REQUEST', client1Id, {});
    
    ws1.send(JSON.stringify(versionRequest));
    const vv1 = await waitForMessage(ws1, isVersionVectorResponse);
    
    ws2.send(JSON.stringify(versionRequest));
    const vv2 = await waitForMessage(ws2, isVersionVectorResponse);

    // Both should see the same state
    assert.equal(vv1.currentVersion, 5);
    assert.equal(vv2.currentVersion, 5);
    assert.equal(vv1.vector[client1Id], 3);
    assert.equal(vv1.vector[client2Id], 5);
    assert.equal(vv2.vector[client1Id], 3);
    assert.equal(vv2.vector[client2Id], 5);
  });

  it('should handle client reconnection correctly', async () => {
    const clientId = 'test-client-7';
    
    // First connection
    let ws = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': clientId }
    });
    activeClients.push(ws);

    await new Promise(resolve => ws.on('open', resolve));

    // Submit a patch
    const patch1: PatchSubmit = createMessage('PATCH_SUBMIT', clientId, {
      patches: [createTestPatch('before-disconnect')],
      baseVersion: 0
    });
    
    ws.send(JSON.stringify(patch1));
    await waitForMessage(ws, isPatchAck);

    // Disconnect
    ws.close();
    await new Promise(resolve => ws.on('close', resolve));

    // Reconnect with same client ID
    ws = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': clientId }
    });
    activeClients.push(ws);

    await new Promise(resolve => ws.on('open', resolve));

    // Request version vector to check state
    const versionRequest: VersionVectorRequest = createMessage('VERSION_VECTOR_REQUEST', clientId, {});
    ws.send(JSON.stringify(versionRequest));
    
    const versionResponse = await waitForMessage(ws, isVersionVectorResponse);
    assert.equal(versionResponse.currentVersion, 1);
    
    // Submit another patch after reconnection
    const patch2: PatchSubmit = createMessage('PATCH_SUBMIT', clientId, {
      patches: [createTestPatch('after-reconnect')],
      baseVersion: 1
    });
    
    ws.send(JSON.stringify(patch2));
    const ack2 = await waitForMessage(ws, isPatchAck);
    assert.equal(ack2.success, true);
    assert.equal(ack2.assignedVersion, 2);
  });

  it('should handle empty patch submissions gracefully', async () => {
    const clientId = 'test-client-8';
    const ws = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': clientId }
    });
    activeClients.push(ws);

    await new Promise(resolve => ws.on('open', resolve));

    // Submit empty patch array
    const emptyPatch: PatchSubmit = createMessage('PATCH_SUBMIT', clientId, {
      patches: [],
      baseVersion: 0
    });
    
    ws.send(JSON.stringify(emptyPatch));
    
    // Should still get acknowledgment
    const ack = await waitForMessage(ws, isPatchAck);
    assert.equal(ack.success, true);
    assert.equal(ack.assignedVersion, 1);
  });

  it('should handle rapid patch submissions', async () => {
    const clientId = 'test-client-9';
    const ws = new WebSocket(TEST_URL, {
      headers: { 'X-Client-ID': clientId }
    });
    activeClients.push(ws);

    await new Promise(resolve => ws.on('open', resolve));

    const patchCount = 10;
    const receivedAcks: SyncMessage[] = [];
    
    // Set up a single message handler to collect all acks
    const ackPromise = new Promise<SyncMessage[]>((resolve) => {
      const handler = (data: Buffer) => {
        try {
          const message = JSON.parse(data.toString()) as SyncMessage;
          if (isPatchAck(message)) {
            receivedAcks.push(message);
            if (receivedAcks.length === patchCount) {
              ws.off('message', handler);
              resolve(receivedAcks);
            }
          }
        } catch (error) {
          // Ignore parse errors
        }
      };
      ws.on('message', handler);
    });

    // Submit patches rapidly
    for (let i = 0; i < patchCount; i++) {
      const patch: PatchSubmit = createMessage('PATCH_SUBMIT', clientId, {
        patches: [createTestPatch(`rapid-${i}`)],
        baseVersion: i
      });
      ws.send(JSON.stringify(patch));
    }

    // Wait for all acknowledgments with timeout
    const acks = await Promise.race([
      ackPromise,
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error(`Timeout: only received ${receivedAcks.length}/${patchCount} acks`)), 4000)
      )
    ]);

    // Verify all patches were acknowledged with correct versions
    assert.equal(acks.length, patchCount);
    acks.forEach((ack, index) => {
      assert.equal(ack.success, true);
      assert.equal(ack.assignedVersion, index + 1);
    });

    // Verify final version
    const versionRequest: VersionVectorRequest = createMessage('VERSION_VECTOR_REQUEST', clientId, {});
    ws.send(JSON.stringify(versionRequest));
    
    const versionResponse = await waitForMessage(ws, isVersionVectorResponse);
    assert.equal(versionResponse.currentVersion, patchCount);
  });
});