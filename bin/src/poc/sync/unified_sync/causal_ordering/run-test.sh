#!/usr/bin/env bash
set -e

echo "Starting WebSocket server..."
deno run --allow-net websocket-server.ts &
SERVER_PID=$!

sleep 2

echo "Running simple causal ordering tests..."
deno test --no-check --allow-net causal-sync-client.test.ts

echo "Tests completed"
kill $SERVER_PID 2>/dev/null || true