const CONTAINER_ID = Deno.env.get("CONTAINER_ID") || 'unknown';
const PORT = parseInt(Deno.env.get("PORT") || '3001');

// グレースフルシャットダウンのサポート
let isShuttingDown = false;
let activeConnections = 0;

// セッション管理（簡易実装）
const sessions = new Map();

function generateSessionId() {
  return `${CONTAINER_ID}-${Date.now()}-${crypto.randomUUID().substring(0, 8)}`;
}

// リクエストハンドラー
async function handler(request: Request): Promise<Response> {
  activeConnections++;
  
  try {
    const url = new URL(request.url);
    
    // シャットダウン中チェック
    if (isShuttingDown) {
      return new Response('Server is shutting down', {
        status: 503,
        headers: { 'Connection': 'close' }
      });
    }
    
    // ヘルスチェックエンドポイント
    if (url.pathname === '/health' && request.method === 'GET') {
      if (isShuttingDown) {
        return new Response(JSON.stringify({ status: 'shutting_down' }), {
          status: 503,
          headers: { 'content-type': 'application/json' }
        });
      }
      
      return new Response(JSON.stringify({
        status: 'healthy',
        container: CONTAINER_ID,
        uptime: performance.now() / 1000,
        memory: Deno.memoryUsage(),
        activeConnections
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    // コンテナ識別エンドポイント
    if (url.pathname === '/api/whoami' && request.method === 'GET') {
      return new Response(JSON.stringify({
        container: CONTAINER_ID,
        pid: Deno.pid,
        hostname: Deno.hostname(),
        timestamp: Date.now()
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    // セッション管理エンドポイント
    if (url.pathname === '/api/session' && request.method === 'POST') {
      const sessionId = request.headers.get('x-session-id') || generateSessionId();
      const body = await request.json();
      const { clientId, requestNum } = body;
      
      // セッションデータの保存/更新
      if (!sessions.has(sessionId)) {
        sessions.set(sessionId, {
          clientId,
          container: CONTAINER_ID,
          created: Date.now(),
          requests: []
        });
      }
      
      const session = sessions.get(sessionId);
      session.requests.push({
        requestNum,
        timestamp: Date.now()
      });
      
      return new Response(JSON.stringify({
        sessionId,
        container: CONTAINER_ID,
        requestCount: session.requests.length
      }), {
        headers: {
          'content-type': 'application/json',
          'X-Session-Id': sessionId
        }
      });
    }
    
    // パフォーマンステスト用エンドポイント
    if (url.pathname === '/api/load-test' && request.method === 'GET') {
      // CPUバウンドな処理をシミュレート
      const iterations = parseInt(url.searchParams.get('iterations') || '1000');
      let result = 0;
      
      for (let i = 0; i < iterations; i++) {
        result += Math.sqrt(i);
      }
      
      return new Response(JSON.stringify({
        container: CONTAINER_ID,
        result,
        processingTime: iterations
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    // ルートパス
    if (url.pathname === '/' && request.method === 'GET') {
      return new Response(`<h1>Hello from ${CONTAINER_ID}</h1><p>Active connections: ${activeConnections}</p>`, {
        headers: { 'content-type': 'text/html' }
      });
    }
    
    // 404 Not Found
    return new Response('Not Found', { status: 404 });
  } finally {
    activeConnections--;
  }
}

// サーバー起動
const server = Deno.serve(
  { port: PORT },
  handler
);

console.log(`Container ${CONTAINER_ID} listening on port ${PORT}`);

// グレースフルシャットダウン
Deno.addSignalListener("SIGTERM", () => {
  console.log('SIGTERM received, starting graceful shutdown...');
  isShuttingDown = true;
  
  // サーバーのシャットダウン
  server.shutdown();
  
  // アクティブな接続の完了を待つ
  setTimeout(() => {
    console.log('Forcing shutdown...');
    Deno.exit(0);
  }, 30000); // 最大30秒待つ
});

await server.finished;