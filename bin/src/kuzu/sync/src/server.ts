import { WebSocketServer, WebSocket } from 'ws';
import type { 
  GraphPatch, 
  ClientMessage, 
  ServerMessage, 
  PatchResponse,
  SyncState 
} from './types/protocol.js';

interface ClientConnection {
  ws: WebSocket;
  clientId: string;
  lastSeen: number;
}

export class MinimalSyncServer {
  private wss: WebSocketServer;
  private clients: Map<string, ClientConnection> = new Map();
  private patches: GraphPatch[] = [];
  private currentVersion: number = 0;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(port: number = 8080) {
    this.wss = new WebSocketServer({ port });
    this.setupServer();
    console.log(`MinimalSyncServer listening on port ${port}`);
  }

  private setupServer(): void {
    this.wss.on('connection', (ws: WebSocket, req) => {
      const clientId = this.generateClientId();
      console.log(`Client connected: ${clientId}`);

      const client: ClientConnection = {
        ws,
        clientId,
        lastSeen: Date.now()
      };

      this.clients.set(clientId, client);

      // Send initial sync state to new client
      this.sendSyncState(client);

      ws.on('message', (data: Buffer) => {
        try {
          const message: ClientMessage = JSON.parse(data.toString());
          this.handleClientMessage(client, message);
        } catch (error) {
          console.error('Invalid message from client:', error);
          this.sendError(client, 'Invalid message format');
        }
      });

      ws.on('close', () => {
        console.log(`Client disconnected: ${clientId}`);
        this.clients.delete(clientId);
      });

      ws.on('error', (error) => {
        console.error(`WebSocket error for client ${clientId}:`, error);
        this.clients.delete(clientId);
      });
    });

    // Start heartbeat check
    this.startHeartbeat();
  }

  private handleClientMessage(client: ClientConnection, message: ClientMessage): void {
    client.lastSeen = Date.now();

    switch (message.type) {
      case 'patch':
        if (message.payload && this.isGraphPatch(message.payload)) {
          this.handlePatch(client, message.payload as GraphPatch);
        } else {
          this.sendError(client, 'Invalid patch payload');
        }
        break;

      case 'sync_request':
        if (message.payload && typeof message.payload === 'object' && 'fromVersion' in message.payload) {
          this.handleSyncRequest(client, message.payload.fromVersion);
        } else {
          this.sendError(client, 'Invalid sync request payload');
        }
        break;

      case 'heartbeat':
        // Already updated lastSeen
        break;

      default:
        this.sendError(client, `Unknown message type: ${(message as any).type}`);
    }
  }

  private handlePatch(client: ClientConnection, patch: GraphPatch): void {
    // Assign server version
    this.currentVersion++;
    const versionedPatch = {
      ...patch,
      serverVersion: this.currentVersion
    };

    // Store patch
    this.patches.push(patch);

    // Send response to sender
    const response: PatchResponse = {
      patchId: patch.id,
      status: 'accepted',
      serverVersion: this.currentVersion
    };

    this.sendMessage(client, {
      type: 'patch_response',
      payload: response
    });

    // Broadcast to all other clients
    this.broadcast({
      type: 'patch_broadcast',
      payload: versionedPatch
    }, client.clientId);

    console.log(`Patch ${patch.id} accepted at version ${this.currentVersion}`);
  }

  private handleSyncRequest(client: ClientConnection, fromVersion: number): void {
    const relevantPatches = this.patches.slice(fromVersion);
    
    const syncState: SyncState = {
      version: this.currentVersion,
      patches: relevantPatches
    };

    this.sendMessage(client, {
      type: 'sync_state',
      payload: syncState
    });

    console.log(`Sent sync state to ${client.clientId}: ${relevantPatches.length} patches from version ${fromVersion}`);
  }

  private sendSyncState(client: ClientConnection): void {
    const syncState: SyncState = {
      version: this.currentVersion,
      patches: this.patches
    };

    this.sendMessage(client, {
      type: 'sync_state',
      payload: syncState
    });
  }

  private sendError(client: ClientConnection, message: string): void {
    this.sendMessage(client, {
      type: 'error',
      payload: { message }
    });
  }

  private sendMessage(client: ClientConnection, message: ServerMessage): void {
    if (client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(JSON.stringify(message));
    }
  }

  private broadcast(message: ServerMessage, excludeClientId?: string): void {
    this.clients.forEach((client, clientId) => {
      if (clientId !== excludeClientId && client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(JSON.stringify(message));
      }
    });
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      const now = Date.now();
      const timeout = 60000; // 60 seconds

      this.clients.forEach((client, clientId) => {
        if (now - client.lastSeen > timeout) {
          console.log(`Client ${clientId} timed out`);
          client.ws.terminate();
          this.clients.delete(clientId);
        }
      });
    }, 30000); // Check every 30 seconds
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private isGraphPatch(payload: any): boolean {
    return payload &&
      typeof payload === 'object' &&
      'id' in payload &&
      'op' in payload &&
      'timestamp' in payload &&
      'clientId' in payload;
  }

  public stop(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.clients.forEach(client => {
      client.ws.close();
    });

    this.wss.close();
    console.log('Server stopped');
  }

  public getStats(): { clients: number; patches: number; version: number } {
    return {
      clients: this.clients.size,
      patches: this.patches.length,
      version: this.currentVersion
    };
  }
}

// Start server if run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const port = parseInt(process.env.PORT || '8080', 10);
  const server = new MinimalSyncServer(port);

  process.on('SIGINT', () => {
    console.log('\nShutting down server...');
    server.stop();
    process.exit(0);
  });
}