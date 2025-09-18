import { WebSocket } from 'ws';
import { createRequire } from 'module';
import type { 
  GraphPatch, 
  ClientMessage, 
  ServerMessage,
  SyncState
} from './types/protocol.ts';

// Use require for Node.js environment
const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

interface ClientSyncOptions {
  serverUrl: string;
  clientId: string;
  databasePath?: string;
}

export class ClientSync {
  private ws: WebSocket | null = null;
  private db: any;
  private conn: any;
  private localVersion: number = 0;
  private serverVersion: number = 0;
  private clientId: string;
  private serverUrl: string;
  private databasePath: string;

  constructor(options: ClientSyncOptions) {
    this.clientId = options.clientId;
    this.serverUrl = options.serverUrl;
    this.databasePath = options.databasePath || ':memory:';
  }

  async connect(): Promise<void> {
    // Initialize local database
    this.db = new kuzu.Database(this.databasePath);
    this.conn = new kuzu.Connection(this.db);

    // Connect to WebSocket server
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.serverUrl, {
        headers: {
          'X-Client-ID': this.clientId
        }
      });

      this.ws.on('open', () => {
        console.log(`Connected to sync server: ${this.serverUrl}`);
        // Request initial snapshot
        this.sendMessage({
          type: 'sync_request',
          payload: { fromVersion: this.localVersion }
        });
        resolve();
      });

      this.ws.on('message', (data) => {
        const message: ServerMessage = JSON.parse(data.toString());
        this.handleMessage(message);
      });

      this.ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      });

      this.ws.on('close', () => {
        console.log('Disconnected from sync server');
      });
    });
  }

  private async handleMessage(message: ServerMessage): Promise<void> {
    switch (message.type) {
      case 'sync_state':
        await this.handleSnapshot(message.payload as SyncState);
        break;
      
      case 'patch_broadcast':
        await this.handleDiff(message.payload as GraphPatch);
        break;
      
      case 'patch_response':
        const response = message.payload as { success: boolean; version?: number; error?: string };
        if (response.success && response.version) {
          this.localVersion = response.version;
          console.log(`Patch accepted, new version: ${this.localVersion}`);
        } else {
          console.error('Patch rejected:', response.error);
        }
        break;
    }
  }

  private async handleSnapshot(state: SyncState): Promise<void> {
    console.log(`Received snapshot at version ${state.version}`);
    
    // Clear local database
    await this.executeQuery('MATCH (n) DETACH DELETE n');
    
    // Apply all patches from snapshot
    for (const patch of state.patches) {
      await this.applyPatch(patch);
    }
    
    // Update version tracking
    this.localVersion = state.version;
    this.serverVersion = state.version;
  }

  private async handleDiff(patch: GraphPatch): Promise<void> {
    console.log(`Received diff: ${patch.type} at version ${patch.version}`);
    
    // Apply patch to local database
    await this.applyPatch(patch);
    
    // Update version
    this.localVersion = patch.version;
  }

  private async applyPatch(patch: GraphPatch): Promise<void> {
    let query: string;
    const params: any = {};

    switch (patch.type) {
      case 'node':
        const nodePatch = patch as any;
        if (nodePatch.operation === 'create') {
          query = `CREATE (n:${nodePatch.label} $props) RETURN n`;
          params.props = nodePatch.properties || {};
        } else if (nodePatch.operation === 'delete') {
          query = `MATCH (n) WHERE id(n) = $id DELETE n`;
          params.id = nodePatch.nodeId;
        }
        break;
      
      case 'edge':
        const edgePatch = patch as any;
        if (edgePatch.operation === 'create') {
          query = `MATCH (a), (b) WHERE id(a) = $fromId AND id(b) = $toId 
                   CREATE (a)-[:${edgePatch.label} $props]->(b)`;
          params.fromId = edgePatch.fromId;
          params.toId = edgePatch.toId;
          params.props = edgePatch.properties || {};
        }
        break;
      
      case 'property':
        const propPatch = patch as any;
        if (propPatch.targetType === 'node') {
          query = `MATCH (n) WHERE id(n) = $id SET n.${propPatch.property} = $value`;
          params.id = propPatch.targetId;
          params.value = propPatch.value;
        }
        break;
      
      default:
        console.warn(`Unknown patch type: ${patch.type}`);
        return;
    }

    if (query!) {
      await this.executeQuery(query, params);
    }
  }

  async submitChange(patch: GraphPatch): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('Not connected to sync server');
    }

    // Apply change locally first (optimistic update)
    await this.applyPatch(patch);

    // Send patch to server
    this.sendMessage({
      type: 'patch',
      payload: patch
    });
  }

  async createNode(label: string, properties: Record<string, any> = {}): Promise<string> {
    const nodeId = `node_${Date.now()}_${Math.random()}`;
    const patch: GraphPatch = {
      id: `patch_${Date.now()}`,
      type: 'node',
      operation: 'create',
      label,
      properties,
      nodeId,
      version: this.localVersion + 1,
      clientId: this.clientId,
      timestamp: Date.now()
    } as any;

    await this.submitChange(patch);
    return nodeId;
  }

  async updateProperty(nodeId: string, property: string, value: any): Promise<void> {
    const patch: GraphPatch = {
      id: `patch_${Date.now()}`,
      type: 'property',
      operation: 'update',
      targetType: 'node',
      targetId: nodeId,
      property,
      value,
      version: this.localVersion + 1,
      clientId: this.clientId,
      timestamp: Date.now()
    } as any;

    await this.submitChange(patch);
  }

  private sendMessage(message: ClientMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  private async executeQuery(query: string, params: Record<string, any> = {}): Promise<any> {
    try {
      // KuzuDB doesn't support parameterized queries in the same way
      // For PoC, we'll do simple string substitution (not production-safe)
      let finalQuery = query;
      for (const [key, value] of Object.entries(params)) {
        if (typeof value === 'string') {
          finalQuery = finalQuery.replace(`$${key}`, `'${value}'`);
        } else if (typeof value === 'object') {
          finalQuery = finalQuery.replace(`$${key}`, JSON.stringify(value));
        } else {
          finalQuery = finalQuery.replace(`$${key}`, value.toString());
        }
      }
      
      const result = await this.conn.execute(finalQuery);
      return result;
    } catch (error) {
      console.error('Query execution error:', error);
      throw error;
    }
  }

  getVersion(): { local: number; server: number } {
    return {
      local: this.localVersion,
      server: this.serverVersion
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    if (this.conn) {
      this.conn.close();
    }
    if (this.db) {
      this.db.close();
    }
  }
}

// Factory function for easy client creation
export async function createClientSync(options: ClientSyncOptions): Promise<ClientSync> {
  const client = new ClientSync(options);
  await client.connect();
  return client;
}