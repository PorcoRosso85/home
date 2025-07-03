#!/usr/bin/env bash
# Envoy動作確認スクリプト

echo "🧪 Testing Envoy Load Balancing"
echo "=============================="
echo ""

# 色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ヘルスチェック
echo -e "${BLUE}1. Health Check:${NC}"
curl -s http://localhost:8080/health | jq .
echo ""

# ユーザーベースルーティング（A-M）
echo -e "${BLUE}2. User-based routing (A-M → Server 1):${NC}"
for user in alice bob mike; do
    echo -n "  User $user: "
    curl -s -H "x-user-id: $user" http://localhost:8080/ | jq -r .server
done
echo ""

# ユーザーベースルーティング（N-Z）
echo -e "${BLUE}3. User-based routing (N-Z → Server 2):${NC}"
for user in nancy oscar zoe; do
    echo -n "  User $user: "
    curl -s -H "x-user-id: $user" http://localhost:8080/ | jq -r .server
done
echo ""

# ラウンドロビン（ユーザーIDなし）
echo -e "${BLUE}4. Round-robin (no user-id):${NC}"
for i in {1..6}; do
    echo -n "  Request $i: "
    curl -s http://localhost:8080/ | jq -r .server
done
echo ""

# Envoy統計情報
echo -e "${BLUE}5. Envoy Cluster Statistics:${NC}"
curl -s http://localhost:9901/clusters | grep -E "server[12]_cluster::|backend_cluster::" | head -20
echo ""

# 負荷分散テスト
echo -e "${BLUE}6. Load Distribution Test (100 requests):${NC}"
echo "  Sending 100 requests without user-id..."
{
    for i in {1..100}; do
        curl -s http://localhost:8080/ | jq -r .server
    done
} | sort | uniq -c
echo ""

# レスポンスタイム測定
echo -e "${BLUE}7. Response Time Test:${NC}"
for i in {1..5}; do
    time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8080/)
    echo "  Request $i: ${time}s"
done
echo ""

echo -e "${GREEN}✅ Test completed!${NC}"