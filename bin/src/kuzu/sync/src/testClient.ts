import WebSocket from 'ws';
import type { ClientMessage, ServerMessage, GraphPatch } from './types/protocol.js';

class TestClient {
  private ws: WebSocket;
  private clientId: string;

  constructor(url: string = 'ws://localhost:8080') {
    this.clientId = `test_${Date.now()}`;
    this.ws = new WebSocket(url);
    this.setupClient();
  }

  private setupClient(): void {
    this.ws.on('open', () => {
      console.log('Connected to server');
      
      // Send a test patch after connection
      setTimeout(() => {
        this.sendTestPatch();
      }, 1000);
    });

    this.ws.on('message', (data: Buffer) => {
      const message: ServerMessage = JSON.parse(data.toString());
      console.log('Received message:', JSON.stringify(message, null, 2));
    });

    this.ws.on('close', () => {
      console.log('Disconnected from server');
    });

    this.ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  private sendTestPatch(): void {
    const patch: GraphPatch = {
      id: `p_${crypto.randomUUID()}`,
      timestamp: Date.now(),
      clientId: this.clientId,
      op: 'createNode',
      nodeId: `n_${crypto.randomUUID()}`,
      data: {
        label: 'TestNode',
        properties: {
          name: 'Test Node',
          created: new Date().toISOString()
        }
      }
    };

    const message: ClientMessage = {
      type: 'patch',
      payload: patch
    };

    console.log('Sending patch:', JSON.stringify(patch, null, 2));
    this.ws.send(JSON.stringify(message));
  }

  public sendSyncRequest(fromVersion: number = 0): void {
    const message: ClientMessage = {
      type: 'sync_request',
      payload: { fromVersion }
    };

    console.log(`Requesting sync from version ${fromVersion}`);
    this.ws.send(JSON.stringify(message));
  }

  public close(): void {
    this.ws.close();
  }
}

// Run test client if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const client = new TestClient();

  // Send sync request after 2 seconds
  setTimeout(() => {
    client.sendSyncRequest(0);
  }, 2000);

  // Close after 5 seconds
  setTimeout(() => {
    client.close();
    process.exit(0);
  }, 5000);
}