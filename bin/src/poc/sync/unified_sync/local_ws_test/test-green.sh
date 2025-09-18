#!/usr/bin/env bash
set -e

echo "Starting Green phase test..."

# Kill any existing servers
killall deno 2>/dev/null || true

# Create a temporary server file with port 8082
cp websocket-server.ts websocket-server-8082.ts
sed -i 's/const port = 8081/const port = 8082/' websocket-server-8082.ts

# Start server
echo "Starting WebSocket server on port 8082..."
deno run --allow-net websocket-server-8082.ts &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run tests with modified URLs
echo "Running tests..."
sed -i "s/ws:\/\/localhost:8081/ws:\/\/localhost:8082/g" kuzu-sync-client.test.ts
deno test --no-check --allow-net kuzu-sync-client.test.ts

# Cleanup
kill $SERVER_PID 2>/dev/null || true
# Restore original port
sed -i "s/ws:\/\/localhost:8082/ws:\/\/localhost:8081/g" kuzu-sync-client.test.ts
rm -f websocket-server-8082.ts

echo "Test complete!"