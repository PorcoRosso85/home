#!/bin/bash
# ロードテスト実行スクリプト

echo "🚀 Starting POC 05 Load Test"
echo "=========================="
echo ""

# サーバーを起動
echo "Starting test servers..."
nix develop -c deno run --allow-net test-server.ts &
SERVER_PID=$!

# サーバーの起動を待つ
echo "Waiting for servers to start..."
sleep 3

# ヘルスチェック
echo "Checking server health..."
curl -s http://localhost:8080/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Load balancer is healthy"
else
    echo "❌ Load balancer is not responding"
    kill $SERVER_PID
    exit 1
fi

# ロードテストを実行
echo ""
echo "Running load test..."
nix develop -c deno run --allow-net load-test.ts

# フェイルオーバーテストも実行
echo ""
echo "Running failover test..."
nix develop -c deno run --allow-net load-test.ts --failover

# サーバーを停止
echo ""
echo "Stopping servers..."
kill $SERVER_PID

echo ""
echo "✅ Load test completed!"