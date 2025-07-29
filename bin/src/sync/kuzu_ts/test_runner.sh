#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Running KuzuTsClient Tests..."
echo "================================"

# Set environment to skip integration tests since persistence/kuzu_ts is not available
export SKIP_KUZU_TS_INTEGRATION=true

# Run tests
deno test tests/kuzu_ts_client.test.ts tests/kuzu_ts_client_schema.test.ts --no-check --allow-all

echo ""
echo "✅ Tests completed!"