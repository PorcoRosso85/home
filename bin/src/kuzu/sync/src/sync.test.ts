import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';
import { WebSocketServer, WebSocket } from 'ws';
import type { 
  GraphPatch, 
  ClientMessage, 
  ServerMessage, 
  SyncState,
  generateId 
} from './types/protocol.js';

// Import generateId properly
const generateId = (type: 'node' | 'edge' | 'patch'): string => {
  const uuid = crypto.randomUUID();
  const prefix = {
    'node': 'n',
    'edge': 'e',
    'patch': 'p'
  }[type];
  return `${prefix}_${uuid}`;
};

// Simple in-memory sync server
class SyncServer {
  private wss: WebSocketServer;
  private clients: Set<WebSocket> = new Set();
  private patches: GraphPatch[] = [];
  private version: number = 0;

  constructor(port: number) {
    this.wss = new WebSocketServer({ port });
    
    this.wss.on('connection', (ws: WebSocket) => {
      console.log('Client connected');
      this.clients.add(ws);
      
      // Send initial sync state
      const syncState: SyncState = {
        version: this.version,
        patches: this.patches
      };
      
      const message: ServerMessage = {
        type: 'sync_state',
        payload: syncState
      };
      
      ws.send(JSON.stringify(message));
      
      ws.on('message', (data: Buffer) => {
        try {
          const msg: ClientMessage = JSON.parse(data.toString());
          this.handleMessage(ws, msg);
        } catch (error) {
          console.error('Invalid message:', error);
        }
      });
      
      ws.on('close', () => {
        console.log('Client disconnected');
        this.clients.delete(ws);
      });
    });
  }
  
  private handleMessage(sender: WebSocket, msg: ClientMessage) {
    switch (msg.type) {
      case 'patch':
        if (msg.payload && 'id' in msg.payload) {
          const patch = msg.payload as GraphPatch;
          this.patches.push(patch);
          this.version++;
          
          // Send response to sender
          const response: ServerMessage = {
            type: 'patch_response',
            payload: {
              patchId: patch.id,
              status: 'accepted',
              serverVersion: this.version
            }
          };
          sender.send(JSON.stringify(response));
          
          // Broadcast to all clients
          const broadcast: ServerMessage = {
            type: 'patch_broadcast',
            payload: patch
          };
          
          for (const client of this.clients) {
            if (client.readyState === WebSocket.OPEN) {
              client.send(JSON.stringify(broadcast));
            }
          }
        }
        break;
        
      case 'sync_request':
        const fromVersion = (msg.payload as { fromVersion: number }).fromVersion;
        const newPatches = this.patches.slice(fromVersion);
        
        const syncState: SyncState = {
          version: this.version,
          patches: newPatches
        };
        
        const syncMessage: ServerMessage = {
          type: 'sync_state',
          payload: syncState
        };
        
        sender.send(JSON.stringify(syncMessage));
        break;
    }
  }
  
  close() {
    return new Promise<void>((resolve) => {
      this.wss.close(() => resolve());
    });
  }
}

// Simple sync client
class SyncClient {
  private ws: WebSocket;
  private clientId: string;
  private nodes: Map<string, any> = new Map();
  private patches: GraphPatch[] = [];
  private messageHandlers: Map<string, (msg: ServerMessage) => void> = new Map();
  
  constructor(url: string, clientId: string) {
    this.clientId = clientId;
    this.ws = new WebSocket(url);
    
    this.ws.on('message', (data: Buffer) => {
      try {
        const msg: ServerMessage = JSON.parse(data.toString());
        this.handleMessage(msg);
      } catch (error) {
        console.error('Client error:', error);
      }
    });
  }
  
  private handleMessage(msg: ServerMessage) {
    // Call any registered handlers
    for (const handler of this.messageHandlers.values()) {
      handler(msg);
    }
    
    switch (msg.type) {
      case 'sync_state':
        const state = msg.payload as SyncState;
        // Apply all patches from sync state
        for (const patch of state.patches) {
          this.applyPatch(patch);
        }
        break;
        
      case 'patch_broadcast':
        const patch = msg.payload as GraphPatch;
        this.applyPatch(patch);
        break;
    }
  }
  
  private applyPatch(patch: GraphPatch) {
    this.patches.push(patch);
    
    if (patch.op === 'create_node') {
      this.nodes.set(patch.nodeId, {
        id: patch.nodeId,
        label: patch.data?.label,
        properties: patch.data?.properties || {}
      });
    } else if (patch.op === 'update_node') {
      const node = this.nodes.get(patch.nodeId);
      if (node) {
        if (patch.data?.label) node.label = patch.data.label;
        if (patch.data?.properties) {
          Object.assign(node.properties, patch.data.properties);
        }
      }
    } else if (patch.op === 'set_property' && patch.targetType === 'node') {
      const node = this.nodes.get(patch.targetId);
      if (node) {
        node.properties[patch.propertyKey] = patch.propertyValue;
      }
    }
  }
  
  async waitForConnection(): Promise<void> {
    return new Promise((resolve) => {
      if (this.ws.readyState === WebSocket.OPEN) {
        resolve();
      } else {
        this.ws.once('open', () => resolve());
      }
    });
  }
  
  createNode(nodeId: string, label: string, properties: Record<string, any> = {}) {
    const patch: GraphPatch = {
      id: generateId('patch'),
      timestamp: Date.now(),
      clientId: this.clientId,
      op: 'create_node',
      nodeId,
      data: { label, properties }
    };
    
    const msg: ClientMessage = {
      type: 'patch',
      payload: patch
    };
    
    this.ws.send(JSON.stringify(msg));
  }
  
  updateNodeProperty(nodeId: string, key: string, value: any) {
    const patch: GraphPatch = {
      id: generateId('patch'),
      timestamp: Date.now(),
      clientId: this.clientId,
      op: 'set_property',
      targetType: 'node',
      targetId: nodeId,
      propertyKey: key,
      propertyValue: value
    };
    
    const msg: ClientMessage = {
      type: 'patch',
      payload: patch
    };
    
    this.ws.send(JSON.stringify(msg));
  }
  
  getNode(nodeId: string) {
    return this.nodes.get(nodeId);
  }
  
  getAllNodes() {
    return Array.from(this.nodes.values());
  }
  
  onMessage(handler: (msg: ServerMessage) => void) {
    const id = crypto.randomUUID();
    this.messageHandlers.set(id, handler);
    return () => this.messageHandlers.delete(id);
  }
  
  close() {
    this.ws.close();
  }
}

// Helper to wait for condition
async function waitFor(condition: () => boolean, timeout = 5000): Promise<void> {
  const start = Date.now();
  while (!condition()) {
    if (Date.now() - start > timeout) {
      throw new Error('Timeout waiting for condition');
    }
    await new Promise(resolve => setTimeout(resolve, 50));
  }
}

describe('KuzuDB Sync Test', () => {
  let server: SyncServer;
  let clientA: SyncClient;
  let clientB: SyncClient;
  const port = 8080;
  
  before(async () => {
    // Start server
    server = new SyncServer(port);
    console.log(`WebSocket server started on port ${port}`);
    
    // Create and connect clients
    clientA = new SyncClient(`ws://localhost:${port}`, 'client-a');
    clientB = new SyncClient(`ws://localhost:${port}`, 'client-b');
    
    // Wait for both clients to connect
    await Promise.all([
      clientA.waitForConnection(),
      clientB.waitForConnection()
    ]);
    
    console.log('Both clients connected');
  });
  
  after(async () => {
    // Cleanup
    clientA.close();
    clientB.close();
    await server.close();
    console.log('Test cleanup complete');
  });
  
  it('should sync node creation from client A to client B', async () => {
    const nodeId = generateId('node');
    const label = 'Person';
    const properties = { name: 'Alice', age: 30 };
    
    // Client A creates a node
    clientA.createNode(nodeId, label, properties);
    
    // Wait for client B to receive the node
    await waitFor(() => clientB.getNode(nodeId) !== undefined);
    
    // Verify client B has the node
    const nodeInB = clientB.getNode(nodeId);
    assert.strictEqual(nodeInB.id, nodeId);
    assert.strictEqual(nodeInB.label, label);
    assert.deepStrictEqual(nodeInB.properties, properties);
    
    console.log('✓ Node creation synced successfully');
  });
  
  it('should handle concurrent property updates', async () => {
    const nodeId = generateId('node');
    const label = 'Document';
    
    // Create initial node from client A
    clientA.createNode(nodeId, label, { title: 'Initial Title', version: 1 });
    
    // Wait for both clients to have the node
    await waitFor(() => clientA.getNode(nodeId) !== undefined);
    await waitFor(() => clientB.getNode(nodeId) !== undefined);
    
    // Both clients update different properties concurrently
    clientA.updateNodeProperty(nodeId, 'lastEditedBy', 'Client A');
    clientB.updateNodeProperty(nodeId, 'timestamp', Date.now());
    
    // Also update the same property
    clientA.updateNodeProperty(nodeId, 'version', 2);
    clientB.updateNodeProperty(nodeId, 'version', 3);
    
    // Wait for all updates to propagate
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Verify both clients have all updates
    const nodeInA = clientA.getNode(nodeId);
    const nodeInB = clientB.getNode(nodeId);
    
    // Both should have the same state
    assert.strictEqual(nodeInA.properties.lastEditedBy, 'Client A');
    assert.strictEqual(nodeInB.properties.lastEditedBy, 'Client A');
    assert.ok(nodeInA.properties.timestamp);
    assert.ok(nodeInB.properties.timestamp);
    
    // Last write wins for conflicting property
    assert.strictEqual(nodeInA.properties.version, 3);
    assert.strictEqual(nodeInB.properties.version, 3);
    
    console.log('✓ Concurrent updates handled correctly');
  });
  
  it('should maintain consistency across multiple nodes', async () => {
    const nodeIds = [
      generateId('node'),
      generateId('node'),
      generateId('node')
    ];
    
    // Client A creates multiple nodes
    for (let i = 0; i < nodeIds.length; i++) {
      clientA.createNode(nodeIds[i], 'Item', { index: i, created: 'by-A' });
    }
    
    // Wait for all nodes to sync to client B
    await waitFor(() => clientB.getAllNodes().length >= nodeIds.length);
    
    // Client B updates all nodes
    for (const nodeId of nodeIds) {
      clientB.updateNodeProperty(nodeId, 'updated', 'by-B');
    }
    
    // Wait for updates to propagate back to client A
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Verify consistency
    for (const nodeId of nodeIds) {
      const nodeInA = clientA.getNode(nodeId);
      const nodeInB = clientB.getNode(nodeId);
      
      assert.deepStrictEqual(nodeInA.properties, nodeInB.properties);
      assert.strictEqual(nodeInA.properties.created, 'by-A');
      assert.strictEqual(nodeInA.properties.updated, 'by-B');
    }
    
    console.log('✓ Multi-node consistency maintained');
  });
  
  it('should handle rapid sequential updates', async () => {
    const nodeId = generateId('node');
    
    // Create node
    clientA.createNode(nodeId, 'Counter', { value: 0 });
    
    // Wait for initial sync
    await waitFor(() => clientB.getNode(nodeId) !== undefined);
    
    // Rapid updates from both clients
    const updateCount = 10;
    const updates: Promise<void>[] = [];
    
    // Track when all updates are processed
    let processedCount = 0;
    const removeHandlerA = clientA.onMessage((msg) => {
      if (msg.type === 'patch_broadcast' || msg.type === 'patch_response') {
        processedCount++;
      }
    });
    const removeHandlerB = clientB.onMessage((msg) => {
      if (msg.type === 'patch_broadcast' || msg.type === 'patch_response') {
        processedCount++;
      }
    });
    
    // Send updates
    for (let i = 1; i <= updateCount; i++) {
      if (i % 2 === 0) {
        clientA.updateNodeProperty(nodeId, 'value', i);
        clientA.updateNodeProperty(nodeId, 'lastClient', 'A');
      } else {
        clientB.updateNodeProperty(nodeId, 'value', i);
        clientB.updateNodeProperty(nodeId, 'lastClient', 'B');
      }
    }
    
    // Wait for all updates to be processed
    await waitFor(() => processedCount >= updateCount * 2);
    
    // Clean up handlers
    removeHandlerA();
    removeHandlerB();
    
    // Verify final state is consistent
    const finalA = clientA.getNode(nodeId);
    const finalB = clientB.getNode(nodeId);
    
    assert.strictEqual(finalA.properties.value, finalB.properties.value);
    assert.strictEqual(finalA.properties.lastClient, finalB.properties.lastClient);
    assert.strictEqual(finalA.properties.value, updateCount);
    
    console.log('✓ Rapid sequential updates synchronized');
  });
});