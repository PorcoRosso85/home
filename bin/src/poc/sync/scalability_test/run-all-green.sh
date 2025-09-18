#!/usr/bin/env bash
set -e

echo "🟢 Running all Green phase tests..."
echo ""

# Kill any existing servers
killall deno 2>/dev/null || true

# Start server
deno run --allow-net websocket-server.ts &
SERVER_PID=$!
sleep 2

echo "✅ Testing basic causal ordering..."
deno test --no-check --allow-net causal-sync-client.test.ts

echo ""
echo "✅ Testing diamond dependencies..."
deno run --allow-net simple-diamond-test.ts

echo ""
echo "✅ Testing circular dependencies..."
deno run --allow-net test-circular.ts

echo ""
echo "✅ Testing network partitions..."
deno run --allow-net test-partition.ts

echo ""
echo "✅ Testing transactions..."
deno run --allow-net test-transaction.ts

echo ""
echo "🎉 All tests completed successfully!"

# Cleanup
kill $SERVER_PID 2>/dev/null || true