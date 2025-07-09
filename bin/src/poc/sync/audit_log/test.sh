#!/usr/bin/env bash
set -e

# Kill any existing servers
killall deno 2>/dev/null || true

# Start server
deno run --allow-net websocket-server.ts &
SERVER_PID=$!

# Wait for server
sleep 2

# Run tests
deno test --no-check --allow-net --v8-flags=--max-old-space-size=512
TEST_RESULT=$?

# Cleanup
kill $SERVER_PID 2>/dev/null || true

exit $TEST_RESULT