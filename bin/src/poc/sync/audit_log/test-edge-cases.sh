#!/bin/bash

# Kill any existing servers
killall deno 2>/dev/null || true

# Start WebSocket server in background
echo "Starting WebSocket server..."
deno run --allow-net --allow-env websocket-server-enhanced.ts > server.log 2>&1 &
SERVER_PID=$!

# Wait for server startup
sleep 2

echo "Running edge case tests..."
# Run tests
deno test \
  --no-check \
  --allow-net \
  --allow-read \
  --allow-write \
  --allow-env \
  --v8-flags=--max-old-space-size=512 \
  causal-ddl-edge-cases.test.ts

TEST_RESULT=$?

# Cleanup
echo "Cleaning up..."
kill $SERVER_PID 2>/dev/null || true
killall deno 2>/dev/null || true

exit $TEST_RESULT