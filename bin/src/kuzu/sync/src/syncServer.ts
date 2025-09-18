/**
 * Minimal WebSocket Server for KuzuDB Sync Protocol Phase 2
 * Handles client connections and integrates with syncManager
 */

import { WebSocketServer, WebSocket } from 'ws';
import { createSyncManager, type ClientConnection } from './syncManager';
import { createSnapshotManager } from './snapshotManager';
import { createDiffEngine } from './diffEngine';
import type { SyncMessage, ClientId } from './protocol';

// Server configuration
const PORT = 3001;
const HOST = '0.0.0.0';

// Create dependencies
const snapshotManager = createSnapshotManager('./snapshots');

const diffEngine = createDiffEngine();

// Create sync manager
const syncManager = createSyncManager({
  snapshotManager,
  diffEngine,
  maxHistorySize: 1000
});

// Create WebSocket server
const wss = new WebSocketServer({ 
  port: PORT,
  host: HOST
});

// Client tracking
const clientMap = new Map<WebSocket, ClientId>();
let clientCounter = 0;

// Handle new connections
wss.on('connection', (ws: WebSocket) => {
  // Generate unique client ID
  const clientId: ClientId = `client_${++clientCounter}_${Date.now()}`;
  clientMap.set(ws, clientId);
  
  console.log(`Client connected: ${clientId}`);
  
  // Create client connection wrapper
  const clientConnection: ClientConnection = {
    id: clientId,
    send: (message: SyncMessage) => {
      if (ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify(message));
        } catch (error) {
          console.error(`Failed to send message to ${clientId}:`, error);
        }
      }
    },
    close: () => ws.close()
  };
  
  // Register client with sync manager
  syncManager.addClient(clientConnection);
  
  // Handle incoming messages
  ws.on('message', async (data: Buffer) => {
    try {
      const message = JSON.parse(data.toString()) as SyncMessage;
      await syncManager.handleMessage(clientId, message);
    } catch (error) {
      console.error(`Error handling message from ${clientId}:`, error);
      
      // Send error response
      const errorMessage: SyncMessage = {
        type: 'ERROR',
        clientId,
        timestamp: Date.now(),
        code: 'INVALID_MESSAGE',
        message: error instanceof Error ? error.message : 'Invalid message format'
      };
      
      clientConnection.send(errorMessage);
    }
  });
  
  // Handle disconnection
  ws.on('close', () => {
    console.log(`Client disconnected: ${clientId}`);
    syncManager.removeClient(clientId);
    clientMap.delete(ws);
  });
  
  // Handle errors
  ws.on('error', (error) => {
    console.error(`WebSocket error for ${clientId}:`, error);
  });
});

// Server error handling
wss.on('error', (error) => {
  console.error('WebSocket server error:', error);
});

// Server started
wss.on('listening', () => {
  console.log(`Sync server listening on ws://${HOST}:${PORT}`);
  console.log(`Current version: ${syncManager.getCurrentVersion()}`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\nShutting down sync server...');
  
  // Close all client connections
  wss.clients.forEach((ws) => {
    ws.close();
  });
  
  // Close server
  wss.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

// Export for testing
export { wss, syncManager };