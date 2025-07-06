#!/bin/bash
set -e

echo "[LOCAL-WS-TEST] 🔌 Starting Local WebSocket Client-Server Test"
echo "[LOCAL-WS-TEST] Port: WebSocket=8081"
echo ""

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# websocket-server.tsをコピーしてポート8081で起動
cp websocket-server.ts websocket-server-8081.ts
sed -i 's/const port = 8080/const port = 8081/' websocket-server-8081.ts

echo "[LOCAL-WS-TEST] Starting server on port 8081..."
deno run --allow-net websocket-server-8081.ts &
SERVER_PID=$!

sleep 2

# テスト実行
echo "[LOCAL-WS-TEST] Running WebSocket client tests..."
deno run --allow-net test-minimal.ts
EXIT_CODE=$?

# クリーンアップ
echo "[LOCAL-WS-TEST] Cleaning up..."
kill $SERVER_PID 2>/dev/null || true
rm -f websocket-server-8081.ts

if [ $EXIT_CODE -eq 0 ]; then
  echo "[LOCAL-WS-TEST] ✅ Test PASSED"
else
  echo "[LOCAL-WS-TEST] ❌ Test FAILED"
  exit 1
fi