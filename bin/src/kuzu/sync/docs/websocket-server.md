# WebSocket Sync Server

## Overview

The MinimalSyncServer provides real-time synchronization capabilities for KuzuDB using WebSockets. It manages client connections, version control, and patch broadcasting.

## Features

- WebSocket server running on port 8080 (configurable)
- Sequential version numbering for patches
- Automatic patch broadcasting to all connected clients
- Client heartbeat monitoring
- Sync state management

## Usage

### Starting the Server

```bash
# Default port 8080
pnpm start:server

# Custom port
PORT=9000 pnpm start:server
```

### Server API

The server handles three types of client messages:

1. **Patch Message**
   ```json
   {
     "type": "patch",
     "payload": {
       "id": "p_uuid",
       "timestamp": 1234567890,
       "clientId": "client_123",
       "op": "create_node",
       "nodeId": "n_uuid",
       "data": {
         "label": "Person",
         "properties": { "name": "John" }
       }
     }
   }
   ```

2. **Sync Request**
   ```json
   {
     "type": "sync_request",
     "payload": { "fromVersion": 10 }
   }
   ```

3. **Heartbeat**
   ```json
   {
     "type": "heartbeat",
     "payload": null
   }
   ```

### Server Responses

1. **Patch Response** (to sender)
   ```json
   {
     "type": "patch_response",
     "payload": {
       "patchId": "p_uuid",
       "status": "accepted",
       "serverVersion": 42
     }
   }
   ```

2. **Patch Broadcast** (to all other clients)
   ```json
   {
     "type": "patch_broadcast",
     "payload": { /* patch with serverVersion */ }
   }
   ```

3. **Sync State**
   ```json
   {
     "type": "sync_state",
     "payload": {
       "version": 42,
       "patches": [ /* array of patches */ ]
     }
   }
   ```

## Testing

Run the test client to verify server functionality:

```bash
# Start server in one terminal
pnpm start:server

# Run test client in another terminal
pnpm test:client
```

## Implementation Details

- Patches are stored in memory (not persisted)
- Each patch receives a sequential version number
- Clients that don't send heartbeats for 60 seconds are disconnected
- The server broadcasts patches to all clients except the sender