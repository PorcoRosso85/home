#!/bin/bash

echo "================================"
echo "KuzuDB Sync Test"
echo "================================"
echo ""

# Check if dependencies are installed
if [ ! -d "node_modules/ws" ]; then
    echo "Installing dependencies..."
    pnpm install
    echo ""
fi

# Run the sync test
echo "Running sync test..."
echo ""
pnpm run test:sync

# Optional: Run with verbose output
# node --test --experimental-strip-types --test-reporter=spec src/sync.test.ts