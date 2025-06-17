import { WebSocket } from 'ws';
import { createRequire } from 'module';
import type { 
  GraphPatch, 
  ClientMessage, 
  ServerMessage, 
  PatchResponse,
  SyncState,
  NodePatch,
  PropertyPatch
} from './types/protocol.ts';
import { generateId } from './types/protocol.ts';
import { patchToCypher } from './patch-to-cypher.ts';
import type { CypherQuery } from './patch-to-cypher.ts';

// Use require for Node.js environment
const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

export interface SyncClientOptions {
  serverUrl: string;
  clientId: string;
  databasePath?: string;
  bufferSize?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
}

export interface PendingPatch {
  patch: GraphPatch;
  query: CypherQuery;
  status: 'pending' | 'sent' | 'acknowledged';
}

export class MinimalSyncClient {
  private ws: WebSocket | null = null;
  private db: any;
  private conn: any;
  private options: Required<SyncClientOptions>;
  private pendingPatches: Map<string, PendingPatch> = new Map();
  private serverVersion: number = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isConnected: boolean = false;

  constructor(options: SyncClientOptions) {
    this.options = {
      databasePath: ':memory:',
      bufferSize: 1 << 30,
      reconnectInterval: 5000,
      heartbeatInterval: 30000,
      ...options
    };
  }

  async initialize(): Promise<void> {
    // Initialize KuzuDB
    this.db = new kuzu.Database(this.options.databasePath, this.options.bufferSize);
    this.conn = new kuzu.Connection(this.db, 4);
    
    // Connect to WebSocket server
    await this.connect();
  }

  private async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.options.serverUrl, {
          headers: {
            'X-Client-ID': this.options.clientId
          }
        });

        this.ws.on('open', () => {
          console.log(`Connected to sync server at ${this.options.serverUrl}`);
          this.isConnected = true;
          
          // Request initial sync state
          this.sendMessage({
            type: 'sync_request',
            payload: { fromVersion: this.serverVersion }
          });

          // Start heartbeat
          this.startHeartbeat();
          
          // Send any pending patches
          this.resendPendingPatches();
          
          resolve();
        });

        this.ws.on('message', async (data) => {
          try {
            const message: ServerMessage = JSON.parse(data.toString());
            await this.handleServerMessage(message);
          } catch (error) {
            console.error('Error handling server message:', error);
          }
        });

        this.ws.on('close', () => {
          console.log('Disconnected from sync server');
          this.isConnected = false;
          this.stopHeartbeat();
          this.scheduleReconnect();
        });

        this.ws.on('error', (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  private async handleServerMessage(message: ServerMessage): Promise<void> {
    switch (message.type) {
      case 'patch_broadcast':
        await this.handlePatchBroadcast(message.payload as GraphPatch);
        break;
        
      case 'patch_response':
        await this.handlePatchResponse(message.payload as PatchResponse);
        break;
        
      case 'sync_state':
        await this.handleSyncState(message.payload as SyncState);
        break;
        
      case 'error':
        console.error('Server error:', (message.payload as { message: string }).message);
        break;
    }
  }

  private async handlePatchBroadcast(patch: GraphPatch): Promise<void> {
    // Check if this is our own patch that was acknowledged
    if (this.pendingPatches.has(patch.id)) {
      return;
    }

    // Apply the patch to local database
    try {
      const query = patchToCypher(patch);
      await this.executeQuery(query);
      console.log(`Applied remote patch ${patch.id}`);
    } catch (error) {
      console.error(`Failed to apply remote patch ${patch.id}:`, error);
    }
  }

  private async handlePatchResponse(response: PatchResponse): Promise<void> {
    const pending = this.pendingPatches.get(response.patchId);
    if (!pending) {
      return;
    }

    this.serverVersion = response.serverVersion;

    switch (response.status) {
      case 'accepted':
        console.log(`Patch ${response.patchId} accepted`);
        this.pendingPatches.delete(response.patchId);
        break;
        
      case 'rejected':
        console.error(`Patch ${response.patchId} rejected: ${response.reason}`);
        // Rollback the patch
        await this.rollbackPatch(pending.patch);
        this.pendingPatches.delete(response.patchId);
        break;
        
      case 'ignored':
        console.warn(`Patch ${response.patchId} ignored: ${response.reason}`);
        this.pendingPatches.delete(response.patchId);
        break;
    }
  }

  private async handleSyncState(syncState: SyncState): Promise<void> {
    console.log(`Received sync state, version: ${syncState.version}`);
    this.serverVersion = syncState.version;

    // Rollback all pending patches
    await this.rollbackAllPendingPatches();

    // Apply server patches
    for (const patch of syncState.patches) {
      try {
        const query = patchToCypher(patch);
        await this.executeQuery(query);
      } catch (error) {
        console.error(`Failed to apply patch ${patch.id} from sync state:`, error);
      }
    }

    // Reapply pending patches
    await this.reapplyPendingPatches();
  }

  // Public API methods

  async createNode(label: string, properties?: Record<string, any>): Promise<string> {
    const nodeId = generateId('node');
    const patch: NodePatch = {
      id: generateId('patch'),
      op: 'createNode',
      nodeId,
      timestamp: Date.now(),
      clientId: this.options.clientId,
      baseVersion: this.serverVersion,
      data: {
        label,
        properties
      }
    };

    await this.applyPatch(patch);
    return nodeId;
  }

  async setProperty(targetType: 'node' | 'edge', targetId: string, key: string, value: any): Promise<void> {
    const patch: PropertyPatch = {
      id: generateId('patch'),
      op: 'setProperty',
      targetType,
      targetId,
      propertyKey: key,
      propertyValue: value,
      timestamp: Date.now(),
      clientId: this.options.clientId,
      baseVersion: this.serverVersion
    };

    await this.applyPatch(patch);
  }

  private async applyPatch(patch: GraphPatch): Promise<void> {
    const query = patchToCypher(patch);
    
    // Store as pending
    this.pendingPatches.set(patch.id, {
      patch,
      query,
      status: 'pending'
    });

    try {
      // Apply locally (optimistic update)
      await this.executeQuery(query);
      
      // Send to server if connected
      if (this.isConnected) {
        this.sendPatch(patch);
      }
    } catch (error) {
      console.error(`Failed to apply patch ${patch.id}:`, error);
      this.pendingPatches.delete(patch.id);
      throw error;
    }
  }

  private sendPatch(patch: GraphPatch): void {
    const pending = this.pendingPatches.get(patch.id);
    if (pending) {
      pending.status = 'sent';
    }

    this.sendMessage({
      type: 'patch',
      payload: patch
    });
  }

  private sendMessage(message: ClientMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  private async executeQuery(query: CypherQuery): Promise<void> {
    // KuzuDB doesn't support parameterized queries in the same way as Neo4j
    // We need to construct the query with parameters embedded
    // This is safe because we're using sanitized values from patchToCypher
    let statement = query.statement;
    
    // Replace parameters in the statement
    for (const [key, value] of Object.entries(query.parameters)) {
      const placeholder = `$${key}`;
      let replacement: string;
      
      if (typeof value === 'string') {
        replacement = `'${value.replace(/'/g, "''")}'`;
      } else if (value === null || value === undefined) {
        replacement = 'NULL';
      } else {
        replacement = String(value);
      }
      
      statement = statement.replace(new RegExp(`\\$${key}\\b`, 'g'), replacement);
    }

    const result = await this.conn.query(statement);
    await result.close();
  }

  private async rollbackPatch(patch: GraphPatch): Promise<void> {
    // Simple rollback strategy - this would need to be more sophisticated
    // in a production system to handle complex dependencies
    console.log(`Rolling back patch ${patch.id}`);
    
    // For now, we'll just log the rollback
    // In a real system, you'd generate inverse operations
  }

  private async rollbackAllPendingPatches(): Promise<void> {
    const patches = Array.from(this.pendingPatches.values())
      .filter(p => p.status === 'pending' || p.status === 'sent')
      .reverse(); // Rollback in reverse order
    
    for (const pending of patches) {
      await this.rollbackPatch(pending.patch);
    }
  }

  private async reapplyPendingPatches(): Promise<void> {
    const patches = Array.from(this.pendingPatches.values())
      .filter(p => p.status === 'pending' || p.status === 'sent');
    
    for (const pending of patches) {
      try {
        await this.executeQuery(pending.query);
        if (this.isConnected) {
          this.sendPatch(pending.patch);
        }
      } catch (error) {
        console.error(`Failed to reapply patch ${pending.patch.id}:`, error);
        this.pendingPatches.delete(pending.patch.id);
      }
    }
  }

  private resendPendingPatches(): void {
    const patches = Array.from(this.pendingPatches.values())
      .filter(p => p.status === 'pending' || p.status === 'sent');
    
    for (const pending of patches) {
      this.sendPatch(pending.patch);
    }
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.sendMessage({
        type: 'heartbeat',
        payload: null
      });
    }, this.options.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(async () => {
      console.log('Attempting to reconnect...');
      try {
        await this.connect();
      } catch (error) {
        console.error('Reconnection failed:', error);
        this.scheduleReconnect();
      }
    }, this.options.reconnectInterval);
  }

  async close(): Promise<void> {
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    if (this.conn) {
      await this.conn.close();
    }

    if (this.db) {
      await this.db.close();
    }

    await kuzu.close();
  }

  // Utility methods

  isReady(): boolean {
    return this.isConnected;
  }

  getPendingPatchCount(): number {
    return this.pendingPatches.size;
  }

  getServerVersion(): number {
    return this.serverVersion;
  }
}

// Example usage
export async function createSyncClient(options: SyncClientOptions): Promise<MinimalSyncClient> {
  const client = new MinimalSyncClient(options);
  await client.initialize();
  return client;
}