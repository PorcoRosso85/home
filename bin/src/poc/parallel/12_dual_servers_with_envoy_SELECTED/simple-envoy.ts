// シンプルなEnvoyプロキシの実装（Deno版）
// POC 12デモ用

const BACKEND_SERVERS = [
  { id: "server-1", url: "http://localhost:4001", partition: "A-M" },
  { id: "server-2", url: "http://localhost:4002", partition: "N-Z" },
];

let roundRobinIndex = 0;
const stats = {
  server1: { requests: 0, errors: 0 },
  server2: { requests: 0, errors: 0 },
  total: { requests: 0, errors: 0 }
};

// ヘルスチェック
async function checkHealth() {
  for (const server of BACKEND_SERVERS) {
    try {
      const res = await fetch(`${server.url}/health`);
      server.healthy = res.ok;
    } catch {
      server.healthy = false;
    }
  }
}

// 10秒ごとにヘルスチェック
setInterval(checkHealth, 10000);
checkHealth(); // 初回実行

// サーバー選択ロジック
function selectBackend(userId?: string | null) {
  // ユーザーIDベースのルーティング
  if (userId) {
    const firstChar = userId[0].toUpperCase();
    if (firstChar >= 'A' && firstChar <= 'M') {
      return BACKEND_SERVERS[0];
    } else if (firstChar >= 'N' && firstChar <= 'Z') {
      return BACKEND_SERVERS[1];
    }
  }
  
  // ラウンドロビン
  const healthyServers = BACKEND_SERVERS.filter(s => s.healthy !== false);
  if (healthyServers.length === 0) {
    throw new Error("No healthy backends");
  }
  
  const server = healthyServers[roundRobinIndex % healthyServers.length];
  roundRobinIndex++;
  return server;
}

console.log("🔄 Simple Envoy Proxy started on :8080");
console.log("📊 Stats available on :9901/stats");

// プロキシサーバー
Deno.serve({ port: 8080 }, async (request) => {
  const url = new URL(request.url);
  const userId = request.headers.get("x-user-id");
  
  stats.total.requests++;
  
  try {
    const backend = selectBackend(userId);
    const targetUrl = `${backend.url}${url.pathname}${url.search}`;
    
    // リクエストをプロキシ
    const backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });
    
    // 統計更新
    if (backend.id === "server-1") {
      stats.server1.requests++;
    } else {
      stats.server2.requests++;
    }
    
    // レスポンスにプロキシ情報を追加
    const responseData = await backendResponse.text();
    const headers = new Headers(backendResponse.headers);
    headers.set("x-envoy-upstream-service", backend.id);
    
    return new Response(responseData, {
      status: backendResponse.status,
      headers,
    });
  } catch (error) {
    stats.total.errors++;
    return new Response(JSON.stringify({ 
      error: "Proxy error", 
      details: error.message 
    }), {
      status: 503,
      headers: { "content-type": "application/json" }
    });
  }
});

// 統計エンドポイント
Deno.serve({ port: 9901 }, (request) => {
  const url = new URL(request.url);
  
  if (url.pathname === "/stats") {
    const healthStatus = BACKEND_SERVERS.map(s => ({
      id: s.id,
      healthy: s.healthy ?? "unknown",
      partition: s.partition
    }));
    
    return new Response(JSON.stringify({
      uptime: Math.floor(performance.now() / 1000),
      backends: healthStatus,
      requests: {
        total: stats.total.requests,
        server1: stats.server1.requests,
        server2: stats.server2.requests,
        errors: stats.total.errors
      },
      distribution: {
        server1: stats.total.requests > 0 
          ? ((stats.server1.requests / stats.total.requests) * 100).toFixed(1) + "%"
          : "0%",
        server2: stats.total.requests > 0
          ? ((stats.server2.requests / stats.total.requests) * 100).toFixed(1) + "%"
          : "0%"
      }
    }, null, 2), {
      headers: { "content-type": "application/json" }
    });
  }
  
  return new Response("Simple Envoy Admin\n\nEndpoints:\n/stats - View statistics\n");
});