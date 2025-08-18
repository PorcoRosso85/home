#!/usr/bin/env bash
# Quick test for cypher loader integration

echo "🧪 Testing Cypher Loader Integration"
echo "===================================="

# Check if we're in nix develop
if ! command -v npm &> /dev/null; then
    echo "❌ Not in nix develop environment"
    echo "Run: nix develop"
    exit 1
fi

# Create a simple test file
cat > test-loader-simple.mjs << 'EOF'
// Simple loader test
import { loadQuery } from './infrastructure/cypherLoader.js'

console.log('Testing cypherLoader...')

// Test loading ping query
const result = await loadQuery('dql', 'ping')

if (result.success) {
  console.log('✅ Query loaded successfully')
  console.log('Content:', result.data)
  
  // Check if it contains expected content
  if (result.data.includes("RETURN 'pong'")) {
    console.log('✅ Query content is correct')
  } else {
    console.log('❌ Query content is incorrect')
  }
} else {
  console.log('❌ Failed to load query:', result.error)
}
EOF

# Run the test
echo "Running loader test..."
node test-loader-simple.mjs

# Cleanup
rm -f test-loader-simple.mjs

echo "Test complete!"