/**
 * テスト用のローカルサーバー
 * 2つのアプリケーションとロードバランサーをシミュレート
 */

// アプリケーションサーバー1
async function startApp1() {
  const handler = async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ 
        status: 'healthy', 
        container: 'app-1' 
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    if (url.pathname === '/api/whoami') {
      return new Response(JSON.stringify({
        container: 'app-1',
        timestamp: Date.now()
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    if (url.pathname === '/api/session' && request.method === 'POST') {
      const sessionId = request.headers.get('x-session-id') || 'new-session';
      return new Response(JSON.stringify({
        sessionId,
        container: 'app-1',
        requestCount: 1
      }), {
        headers: { 
          'content-type': 'application/json',
          'x-session-id': sessionId
        }
      });
    }
    
    return new Response('Not Found', { status: 404 });
  };
  
  const server = Deno.serve({ port: 3001 }, handler);
  console.log('App-1 listening on port 3001');
  return server;
}

// アプリケーションサーバー2
async function startApp2() {
  const handler = async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ 
        status: 'healthy', 
        container: 'app-2' 
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    if (url.pathname === '/api/whoami') {
      return new Response(JSON.stringify({
        container: 'app-2',
        timestamp: Date.now()
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    if (url.pathname === '/api/session' && request.method === 'POST') {
      const sessionId = request.headers.get('x-session-id') || 'new-session';
      return new Response(JSON.stringify({
        sessionId,
        container: 'app-2',
        requestCount: 1
      }), {
        headers: { 
          'content-type': 'application/json',
          'x-session-id': sessionId
        }
      });
    }
    
    return new Response('Not Found', { status: 404 });
  };
  
  const server = Deno.serve({ port: 3002 }, handler);
  console.log('App-2 listening on port 3002');
  return server;
}

// 簡易ロードバランサー
async function startLoadBalancer() {
  let requestCount = 0;
  const sessionMap = new Map<string, string>(); // sessionId -> container
  
  const handler = async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    
    if (url.pathname === '/health') {
      return new Response('healthy\n');
    }
    
    // セッションベースのルーティング
    const sessionId = request.headers.get('x-session-id');
    let targetPort: number;
    
    if (sessionId && sessionMap.has(sessionId)) {
      // 既存セッションは同じコンテナへ
      const container = sessionMap.get(sessionId)!;
      targetPort = container === 'app-1' ? 3001 : 3002;
    } else {
      // 新規リクエストはラウンドロビン
      requestCount++;
      targetPort = requestCount % 2 === 0 ? 3001 : 3002;
      
      if (sessionId) {
        sessionMap.set(sessionId, targetPort === 3001 ? 'app-1' : 'app-2');
      }
    }
    
    // バックエンドへプロキシ
    try {
      const backendUrl = `http://localhost:${targetPort}${url.pathname}${url.search}`;
      const backendResponse = await fetch(backendUrl, {
        method: request.method,
        headers: request.headers,
        body: request.method !== 'GET' ? await request.text() : undefined
      });
      
      return new Response(await backendResponse.text(), {
        status: backendResponse.status,
        headers: backendResponse.headers
      });
    } catch (error) {
      // フェイルオーバー: もう一方のポートへ
      const alternatePort = targetPort === 3001 ? 3002 : 3001;
      try {
        const backendUrl = `http://localhost:${alternatePort}${url.pathname}${url.search}`;
        const backendResponse = await fetch(backendUrl, {
          method: request.method,
          headers: request.headers,
          body: request.method !== 'GET' ? await request.text() : undefined
        });
        
        return new Response(await backendResponse.text(), {
          status: backendResponse.status,
          headers: backendResponse.headers
        });
      } catch {
        return new Response('Service Unavailable', { status: 503 });
      }
    }
  };
  
  const server = Deno.serve({ port: 8080 }, handler);
  console.log('Load Balancer listening on port 8080');
  return server;
}

// メイン実行
if (import.meta.main) {
  // 全サーバーを起動
  const app1 = await startApp1();
  const app2 = await startApp2();
  const lb = await startLoadBalancer();
  
  console.log('\n✅ All servers started:');
  console.log('   - Load Balancer: http://localhost:8080');
  console.log('   - App-1: http://localhost:3001');
  console.log('   - App-2: http://localhost:3002');
  console.log('\nPress Ctrl+C to stop all servers\n');
  
  // グレースフルシャットダウン
  Deno.addSignalListener("SIGINT", () => {
    console.log('\nShutting down servers...');
    app1.shutdown();
    app2.shutdown();
    lb.shutdown();
    Deno.exit(0);
  });
  
  // サーバーの完了を待つ
  await Promise.all([
    app1.finished,
    app2.finished,
    lb.finished
  ]);
}