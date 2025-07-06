#!/usr/bin/env bash
set -e

echo "Testing single DML propagation..."

# Kill any existing servers
killall deno 2>/dev/null || true

# Start server
echo "Starting WebSocket server on port 8081..."
deno run --allow-net websocket-server.ts &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run single test
echo "Running single test..."
deno test --no-check --allow-net kuzu-sync-client.test.ts --filter "single client DML" 2>&1 | head -200

# Cleanup
kill $SERVER_PID 2>/dev/null || true

echo "Test complete!"