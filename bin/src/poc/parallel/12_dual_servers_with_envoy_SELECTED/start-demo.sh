#!/usr/bin/env bash
# POC 12 デモ起動スクリプト

set -e

echo "🚀 Starting POC 12: Dual Servers with Envoy"
echo "=========================================="

# プロセスIDを保存
PIDS=()

# クリーンアップ関数
cleanup() {
    echo -e "\n🛑 Stopping all services..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
        fi
    done
    exit 0
}

# Ctrl+Cでクリーンアップ
trap cleanup INT TERM

# テストサーバー1を起動
echo "📦 Starting Server 1 (A-M partition)..."
SERVER_NAME=server-1 PORT=4001 deno run --allow-net --allow-env - <<'EOF' &
const port = parseInt(Deno.env.get("PORT") || "4001");
const serverName = Deno.env.get("SERVER_NAME") || "server-1";

console.log(`${serverName} listening on port ${port}`);

Deno.serve({ port }, (request) => {
  const url = new URL(request.url);
  const userId = request.headers.get("x-user-id");
  
  if (url.pathname === "/health") {
    return new Response(JSON.stringify({ 
      status: "healthy",
      server: serverName,
      partition: "A-M",
      timestamp: Date.now()
    }), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }
  
  return new Response(JSON.stringify({
    message: `Hello from ${serverName}`,
    server: serverName,
    partition: "A-M",
    userId: userId,
    path: url.pathname,
    timestamp: Date.now()
  }), {
    headers: { "content-type": "application/json" }
  });
});
EOF
PIDS+=($!)

# テストサーバー2を起動
echo "📦 Starting Server 2 (N-Z partition)..."
SERVER_NAME=server-2 PORT=4002 deno run --allow-net --allow-env - <<'EOF' &
const port = parseInt(Deno.env.get("PORT") || "4002");
const serverName = Deno.env.get("SERVER_NAME") || "server-2";

console.log(`${serverName} listening on port ${port}`);

Deno.serve({ port }, (request) => {
  const url = new URL(request.url);
  const userId = request.headers.get("x-user-id");
  
  if (url.pathname === "/health") {
    return new Response(JSON.stringify({ 
      status: "healthy",
      server: serverName,
      partition: "N-Z",
      timestamp: Date.now()
    }), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }
  
  return new Response(JSON.stringify({
    message: `Hello from ${serverName}`,
    server: serverName,
    partition: "N-Z",
    userId: userId,
    path: url.pathname,
    timestamp: Date.now()
  }), {
    headers: { "content-type": "application/json" }
  });
});
EOF
PIDS+=($!)

# サーバーの起動を待つ
sleep 2

# Envoyを起動（Deno版）
echo "🔄 Starting Envoy proxy (Deno implementation)..."
deno run --allow-net simple-envoy.ts &
PIDS+=($!)

# 起動完了を待つ
sleep 3

echo ""
echo "✅ All services started!"
echo ""
echo "📍 Service Endpoints:"
echo "  - Server 1:    http://localhost:4001"
echo "  - Server 2:    http://localhost:4002"
echo "  - Envoy Proxy: http://localhost:8080"
echo "  - Envoy Admin: http://localhost:9901"
echo ""
echo "🧪 Test Commands:"
echo "  # Test user-based routing (A-M to server1)"
echo "  curl -H 'x-user-id: alice' http://localhost:8080/"
echo ""
echo "  # Test user-based routing (N-Z to server2)"
echo "  curl -H 'x-user-id: nancy' http://localhost:8080/"
echo ""
echo "  # Test round-robin (no user-id)"
echo "  curl http://localhost:8080/"
echo ""
echo "  # Check health"
echo "  curl http://localhost:8080/health"
echo ""
echo "  # View Envoy stats"
echo "  curl http://localhost:9901/stats/prometheus | grep cluster"
echo ""
echo "Press Ctrl+C to stop all services..."

# 無限ループで待機
while true; do
    sleep 1
done