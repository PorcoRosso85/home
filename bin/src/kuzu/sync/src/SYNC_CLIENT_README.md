# KuzuDB Sync Client

A Node.js synchronization client for KuzuDB with WebSocket integration and server reconciliation capabilities.

## Features

- **WebSocket Integration**: Real-time bidirectional communication with sync server
- **Optimistic Updates**: Apply changes locally before server confirmation
- **Server Reconciliation**: Handle server state updates and conflict resolution
- **Automatic Reconnection**: Resilient to network interruptions
- **Pending Patch Management**: Track and manage unconfirmed changes
- **Parameterized Queries**: Safe query construction to prevent injection attacks
- **KuzuDB WASM Integration**: Native KuzuDB support in Node.js

## Architecture

The sync client implements a minimal but complete synchronization system:

1. **Local Database**: KuzuDB instance for local graph storage
2. **WebSocket Connection**: Real-time communication channel
3. **Patch Queue**: Manages pending operations
4. **Reconciliation Engine**: Handles server state updates

## Usage

### Basic Setup

```typescript
import { createSyncClient } from './sync-client.js';

const client = await createSyncClient({
  serverUrl: 'ws://localhost:8080/sync',
  clientId: 'client-001',
  databasePath: './local.db', // or ':memory:' for in-memory
  reconnectInterval: 5000,
  heartbeatInterval: 30000
});
```

### Creating Nodes

```typescript
const nodeId = await client.createNode('Person', {
  name: 'Alice',
  age: 30,
  city: 'New York'
});
```

### Updating Properties

```typescript
await client.setProperty('node', nodeId, 'occupation', 'Engineer');
await client.setProperty('node', nodeId, 'skills', ['JavaScript', 'Python']);
```

### Checking Sync Status

```typescript
console.log('Connected:', client.isReady());
console.log('Pending patches:', client.getPendingPatchCount());
console.log('Server version:', client.getServerVersion());
```

### Cleanup

```typescript
await client.close();
```

## Server Protocol

The client communicates using the following message types:

### Client → Server

- `patch`: Send a graph operation
- `sync_request`: Request server state from a specific version
- `heartbeat`: Keep connection alive

### Server → Client

- `patch_broadcast`: New patch from another client
- `patch_response`: Acknowledgment of sent patch
- `sync_state`: Full state snapshot
- `error`: Error message

## Reconciliation Process

1. **Optimistic Update**: Apply patch locally immediately
2. **Send to Server**: Transmit patch over WebSocket
3. **Server Response**: 
   - `accepted`: Patch confirmed
   - `rejected`: Rollback required
   - `ignored`: Already applied
4. **State Sync**: On reconnection, reconcile with server state

## Error Handling

The client handles various error scenarios:

- **Connection Loss**: Automatic reconnection with exponential backoff
- **Patch Rejection**: Rollback local changes
- **Query Errors**: Logged with context
- **Server Errors**: Displayed to user

## Configuration Options

```typescript
interface SyncClientOptions {
  serverUrl: string;         // WebSocket server URL
  clientId: string;          // Unique client identifier
  databasePath?: string;     // Local database path (default: ':memory:')
  bufferSize?: number;       // KuzuDB buffer size (default: 1GB)
  reconnectInterval?: number; // Reconnection delay in ms (default: 5000)
  heartbeatInterval?: number; // Heartbeat interval in ms (default: 30000)
}
```

## Running Examples

```bash
# Run tests
npm run test:sync-client

# Run interactive example
npm run example:sync

# Run with custom server
SYNC_SERVER_URL=ws://your-server:8080/sync npm run example:sync
```

## Security Considerations

- All queries use parameterized statements to prevent injection
- Label and property names are sanitized
- Client IDs should be securely generated
- WebSocket connections should use WSS in production

## Dependencies

- `kuzu-wasm`: KuzuDB WebAssembly bindings
- `ws`: WebSocket client for Node.js
- Node.js 22+ (for experimental TypeScript support)

## Future Enhancements

- [ ] Edge creation and management
- [ ] Complex conflict resolution strategies
- [ ] Batch operations for performance
- [ ] Compression for large payloads
- [ ] Authentication and authorization
- [ ] Metrics and monitoring hooks