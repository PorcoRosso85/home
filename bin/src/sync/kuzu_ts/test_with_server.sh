#!/usr/bin/env bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Starting test environment...${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
    if [ ! -z "${SERVER_PID:-}" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    exit ${1:-0}
}

# Set trap for cleanup
trap 'cleanup $?' EXIT INT TERM

# Start server in background
echo -e "${GREEN}📡 Starting WebSocket server...${NC}"
deno run --allow-net --allow-read --allow-env server.ts &
SERVER_PID=$!

# Wait for server to be ready
echo -e "${YELLOW}⏳ Waiting for server to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Server failed to start${NC}"
        exit 1
    fi
    sleep 0.5
done

# Run tests
echo -e "${GREEN}🧪 Running tests...${NC}"
if deno test --allow-all ${@:-}; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    cleanup 0
else
    echo -e "${RED}❌ Tests failed${NC}"
    cleanup 1
fi