#!/bin/bash
# Test runner for multi-browser sync
# サーバー起動してテスト実行

set -e

echo "=== Starting WebSocket server ==="
# サーバーをバックグラウンドで起動
deno run --allow-net websocket-server.ts &
SERVER_PID=$!

# サーバー起動を待つ
sleep 2

echo "=== Running tests ==="
# テスト実行
deno test --allow-net test_multi_browser_sync_spec.ts || TEST_RESULT=$?

echo "=== Stopping server ==="
# サーバー停止
kill $SERVER_PID

# テスト結果を返す
exit ${TEST_RESULT:-0}