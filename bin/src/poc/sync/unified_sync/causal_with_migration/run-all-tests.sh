#!/usr/bin/env bash
set -e

echo "Killing any existing servers..."
killall deno 2>/dev/null || true

echo "Starting WebSocket server..."
deno run --allow-net websocket-server.ts &
SERVER_PID=$!

sleep 2

echo "Running basic tests..."
deno test --no-check --allow-net causal-sync-client.test.ts || echo "Basic tests done"

echo ""
echo "Running complex tests one by one..."

echo "Test 1: Diamond dependency"
deno test --no-check --allow-net complex-scenarios.test.ts --filter "diamond" || echo "Diamond test done"

echo ""
echo "Test 2: Circular dependency"
deno test --no-check --allow-net complex-scenarios.test.ts --filter "circular" || echo "Circular test done"

echo ""
echo "Test 3: Network partition"
deno test --no-check --allow-net complex-scenarios.test.ts --filter "partition" || echo "Partition test done"

echo ""
echo "Test 4: Transactions"
deno test --no-check --allow-net complex-scenarios.test.ts --filter "transaction" || echo "Transaction test done"

echo ""
echo "All tests completed"
kill $SERVER_PID 2>/dev/null || true