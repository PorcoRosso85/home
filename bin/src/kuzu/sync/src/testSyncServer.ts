/**
 * Test client for the sync server
 */

import WebSocket from 'ws';
import type { SyncMessage } from './protocol';

const SERVER_URL = 'ws://localhost:3001';

async function testSyncServer() {
  console.log('Connecting to sync server...');
  
  const ws = new WebSocket(SERVER_URL);
  
  ws.on('open', () => {
    console.log('Connected to sync server');
    
    // Test 1: Request version vector
    const versionRequest: SyncMessage = {
      type: 'VERSION_VECTOR_REQUEST',
      clientId: 'test-client',
      timestamp: Date.now()
    };
    
    console.log('Sending version vector request...');
    ws.send(JSON.stringify(versionRequest));
    
    // Test 2: Request snapshot after a delay
    setTimeout(() => {
      const snapshotRequest: SyncMessage = {
        type: 'SNAPSHOT_REQUEST',
        clientId: 'test-client',
        timestamp: Date.now()
      };
      
      console.log('Sending snapshot request...');
      ws.send(JSON.stringify(snapshotRequest));
    }, 1000);
    
    // Test 3: Submit a patch after another delay
    setTimeout(() => {
      const patchSubmit: SyncMessage = {
        type: 'PATCH_SUBMIT',
        clientId: 'test-client',
        timestamp: Date.now(),
        patches: [
          {
            id: 'patch-1',
            operation: 'CREATE_NODE',
            path: '/nodes/test-node',
            value: { label: 'TestNode', properties: { name: 'Test' } }
          }
        ],
        baseVersion: 0
      };
      
      console.log('Sending patch submit...');
      ws.send(JSON.stringify(patchSubmit));
    }, 2000);
  });
  
  ws.on('message', (data: Buffer) => {
    const message = JSON.parse(data.toString()) as SyncMessage;
    console.log('Received message:', message.type);
    console.log('Details:', JSON.stringify(message, null, 2));
  });
  
  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
  
  ws.on('close', () => {
    console.log('Disconnected from sync server');
  });
  
  // Close connection after 5 seconds
  setTimeout(() => {
    console.log('Closing connection...');
    ws.close();
  }, 5000);
}

// Run the test
testSyncServer().catch(console.error);