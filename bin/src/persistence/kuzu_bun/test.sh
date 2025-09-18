#!/usr/bin/env bash
set -e

echo "🧪 KuzuDB Bun Test Suite"
echo "========================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in Nix environment
if [ -z "$IN_NIX_SHELL" ]; then
    echo "⚠️  Not in Nix shell. Running 'nix develop' first..."
    exec nix develop -c bash "$0" "$@"
fi

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies with Bun..."
    bun install
fi

# Test Node.js/Bun example
echo ""
echo "1️⃣ Testing Node.js/Bun example..."
echo "-----------------------------------"
if bun examples/nodejs_example.js; then
    echo -e "${GREEN}✅ Node.js/Bun test passed${NC}"
else
    echo -e "${RED}❌ Node.js/Bun test failed${NC}"
    exit 1
fi

# Browser test instructions
echo ""
echo "2️⃣ Browser Testing Instructions:"
echo "---------------------------------"
echo "To test browser examples:"
echo ""
echo "  1. Start the HTTP server:"
echo "     $ python3 -m http.server 8000"
echo ""
echo "  2. Open in browser:"
echo "     - http://localhost:8000/examples/browser_example.html"
echo "     - http://localhost:8000/examples/browser_in_memory.html"
echo ""
echo "  3. Check browser console for results"
echo ""

echo -e "${GREEN}🎉 Local tests completed successfully!${NC}"