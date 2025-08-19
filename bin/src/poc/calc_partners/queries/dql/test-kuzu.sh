#!/usr/bin/env bash

# KuzuDB test runner with nix shell
# Creates node_modules locally and runs tests

set -e

echo "🚀 Starting KuzuDB test environment..."
echo "─────────────────────────────────────"

# Use nix shell to provide Node.js environment - same version as main project
nix shell nixpkgs#nodejs_22 nixpkgs#nodePackages.npm --command bash << 'EOF'

echo "📦 Node.js version: $(node --version)"
echo "📦 npm version: $(npm --version)"
echo ""

# Check if kuzu-wasm is already installed
if [ ! -d "node_modules/kuzu-wasm" ]; then
  echo "📥 Installing kuzu-wasm..."
  npm install kuzu-wasm@latest
  echo "✅ kuzu-wasm installed"
else
  echo "✅ kuzu-wasm already installed"
fi

echo ""
echo "🧪 Running tests..."
echo "─────────────────────────────────────"

# Count test files
TS_TEST_COUNT=$(ls -1 *.test.ts 2>/dev/null | wc -l)
JS_TEST_COUNT=$(ls -1 *.test.js 2>/dev/null | wc -l)

echo "📊 Found $TS_TEST_COUNT TypeScript test files"
echo "📊 Found $JS_TEST_COUNT JavaScript test files"
echo ""

# Run TypeScript test files if they exist
if [ $TS_TEST_COUNT -gt 0 ]; then
  echo "🔷 Running TypeScript tests..."
  for test_file in *.test.ts; do
    if [ -f "$test_file" ]; then
      echo "  ▶ $test_file"
      node --experimental-strip-types --test "$test_file" || echo "  ⚠️  $test_file failed"
    fi
  done
fi

# Run JavaScript test files if they exist
if [ $JS_TEST_COUNT -gt 0 ]; then
  echo "🔶 Running JavaScript tests..."
  for test_file in *.test.js; do
    if [ -f "$test_file" ]; then
      echo "  ▶ $test_file"
      node --test "$test_file" || echo "  ⚠️  $test_file failed"
    fi
  done
fi

# If no test files found
if [ $TS_TEST_COUNT -eq 0 ] && [ $JS_TEST_COUNT -eq 0 ]; then
  echo "⚠️  No test files found (*.test.ts or *.test.js)"
  echo "📝 Available files:"
  ls -1 *.cypher 2>/dev/null | head -5
fi

echo ""
echo "─────────────────────────────────────"
echo "✨ Test run completed"

EOF