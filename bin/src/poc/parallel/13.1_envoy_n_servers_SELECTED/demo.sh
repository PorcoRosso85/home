#!/usr/bin/env bash
# POC 13.1 デモスクリプト

set -e

echo "🔄 POC 13.1: Envoy N Servers Demo"
echo "================================="
echo ""

# 色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 環境変数設定
export BACKEND_SERVERS="localhost:4001,localhost:4002,localhost:4003,localhost:4004,localhost:4005"
export LB_STRATEGY="round-robin"
export PROXY_PORT=8080
export ADMIN_PORT=9901

echo -e "${BLUE}Configuration:${NC}"
echo "  Backends: 5 servers (4001-4005)"
echo "  Strategy: $LB_STRATEGY"
echo "  Proxy Port: $PROXY_PORT"
echo "  Admin Port: $ADMIN_PORT"
echo ""

# 5台のサーバーを起動
echo -e "${YELLOW}Starting 5 backend servers...${NC}"
./start-n-servers.sh 5 &
SERVERS_PID=$!
sleep 3

# Envoyプロキシを起動
echo -e "${YELLOW}Starting Envoy proxy...${NC}"
deno run --allow-net --allow-env envoy-n-servers.ts &
PROXY_PID=$!
sleep 2

# クリーンアップ関数
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    kill $PROXY_PID 2>/dev/null || true
    kill $SERVERS_PID 2>/dev/null || true
    pkill -f "test-server.ts" || true
    exit 0
}

trap cleanup INT TERM

echo -e "\n${GREEN}✅ System is ready!${NC}"
echo ""

# デモ1: 基本的な動作確認
echo -e "${BLUE}1. Testing basic round-robin distribution:${NC}"
for i in {1..10}; do
    echo -n "Request $i: "
    curl -s http://localhost:8080/ | jq -r .server
done

echo -e "\n${BLUE}2. Checking admin stats:${NC}"
curl -s http://localhost:9901/stats | jq '.distribution'

echo -e "\n${BLUE}3. Health check status:${NC}"
curl -s http://localhost:9901/health | jq .

# デモ2: 異なる戦略をテスト
echo -e "\n${BLUE}4. Testing different strategies:${NC}"
echo "Restarting with 'random' strategy..."
kill $PROXY_PID
export LB_STRATEGY="random"
deno run --allow-net --allow-env envoy-n-servers.ts &
PROXY_PID=$!
sleep 2

echo "Sending 20 requests with random strategy:"
for i in {1..20}; do
    curl -s http://localhost:8080/ | jq -r .server
done | sort | uniq -c

# デモ3: サーバー障害シミュレーション
echo -e "\n${BLUE}5. Simulating server failure:${NC}"
echo "Killing server-3 (port 4003)..."
pkill -f "server-3" || true
sleep 12  # ヘルスチェック間隔を待つ

echo "Requests after server-3 failure:"
for i in {1..8}; do
    echo -n "Request $i: "
    curl -s http://localhost:8080/ | jq -r .server
done

echo -e "\n${BLUE}6. Final stats:${NC}"
curl -s http://localhost:9901/stats | jq .

echo -e "\n${GREEN}Demo completed!${NC}"
echo "Press Ctrl+C to stop all services..."

# 待機
while true; do
    sleep 1
done