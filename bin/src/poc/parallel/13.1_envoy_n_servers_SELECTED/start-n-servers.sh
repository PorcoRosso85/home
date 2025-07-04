#!/usr/bin/env bash
# N台のテストサーバーを起動するスクリプト

set -e

N=${1:-3}  # デフォルト3台
echo "🚀 Starting $N test servers..."

# 既存のサーバープロセスをクリーンアップ
pkill -f "test-server.ts" || true
sleep 1

PIDS=()

# クリーンアップ関数
cleanup() {
    echo -e "\n🛑 Stopping all servers..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
        fi
    done
    exit 0
}

trap cleanup INT TERM

# N台のサーバーを起動
for i in $(seq 1 $N); do
    PORT=$((4000 + i))
    
    # テストサーバーを起動
    SERVER_NAME="server-$i" PORT=$PORT deno run --allow-net --allow-env - <<'EOF' &
const port = parseInt(Deno.env.get("PORT") || "4001");
const serverName = Deno.env.get("SERVER_NAME") || "server-1";

console.log(`${serverName} listening on port ${port}`);

Deno.serve({ port }, (request) => {
  const url = new URL(request.url);
  
  if (url.pathname === "/health") {
    return new Response(JSON.stringify({ 
      status: "healthy",
      server: serverName,
      timestamp: Date.now()
    }), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }
  
  return new Response(JSON.stringify({
    message: `Hello from ${serverName}`,
    server: serverName,
    path: url.pathname,
    timestamp: Date.now()
  }), {
    headers: { "content-type": "application/json" }
  });
});
EOF
    PIDS+=($!)
    echo "✅ Started server-$i on port $PORT (PID: ${PIDS[-1]})"
done

echo -e "\n📊 All servers started!"
echo "Press Ctrl+C to stop all servers..."

# 無限ループで待機
while true; do
    sleep 1
done