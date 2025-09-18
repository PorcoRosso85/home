#!/usr/bin/env bash
set -e

echo "Starting WebSocket server..."
deno run --allow-net websocket-server.ts &
SERVER_PID=$!

sleep 2

echo "Running only diamond test..."
deno test --no-check --allow-net complex-scenarios.test.ts --filter "diamond"

echo "Tests completed"
kill $SERVER_PID 2>/dev/null || true