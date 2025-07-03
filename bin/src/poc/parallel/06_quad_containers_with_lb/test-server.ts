/**
 * 4コンテナ + 高度ロードバランサーのテストサーバー
 * 複数のロードバランシングアルゴリズムをシミュレート
 */

import { delay } from "https://deno.land/std@0.208.0/async/mod.ts";

// コンテナの状態管理
interface Container {
  id: string;
  port: number;
  weight: number;
  connections: number;
  totalRequests: number;
  totalErrors: number;
  responseTimeSum: number;
  isHealthy: boolean;
  cpuLoad: number;
  memoryUsage: number;
}

// ロードバランサーのアルゴリズム
type Algorithm = 'round_robin' | 'least_conn' | 'least_response_time' | 'weighted_response_time' | 'adaptive';

class LoadBalancer {
  private containers: Map<string, Container> = new Map();
  private algorithm: Algorithm = 'round_robin';
  private roundRobinIndex = 0;
  private requestCount = 0;
  private dynamicWeightingEnabled = false;
  private sessionMap = new Map<string, string>();

  constructor() {
    // 4つのコンテナを初期化
    const configs = [
      { id: 'app-1', port: 3001, weight: 10, cpuLimit: 1.0, memoryLimit: 1024 },
      { id: 'app-2', port: 3002, weight: 10, cpuLimit: 1.0, memoryLimit: 1024 },
      { id: 'app-3', port: 3003, weight: 5, cpuLimit: 0.5, memoryLimit: 512 },  // 低性能
      { id: 'app-4', port: 3004, weight: 15, cpuLimit: 1.5, memoryLimit: 1536 }, // 高性能
    ];

    for (const config of configs) {
      this.containers.set(config.id, {
        id: config.id,
        port: config.port,
        weight: config.weight,
        connections: 0,
        totalRequests: 0,
        totalErrors: 0,
        responseTimeSum: 0,
        isHealthy: true,
        cpuLoad: 0,
        memoryUsage: 0
      });
    }
  }

  setAlgorithm(algorithm: Algorithm) {
    this.algorithm = algorithm;
    console.log(`Switched to ${algorithm} algorithm`);
  }

  enableDynamicWeighting() {
    this.dynamicWeightingEnabled = true;
    // 動的重み付けの定期更新を開始
    this.startDynamicWeightAdjustment();
  }

  private startDynamicWeightAdjustment() {
    setInterval(() => {
      if (!this.dynamicWeightingEnabled) return;

      for (const [id, container] of this.containers) {
        if (!container.isHealthy) continue;

        // パフォーマンススコアを計算
        const avgResponseTime = container.totalRequests > 0 
          ? container.responseTimeSum / container.totalRequests 
          : 100;
        const errorRate = container.totalRequests > 0
          ? container.totalErrors / container.totalRequests
          : 0;

        // スコアに基づいて重みを調整
        let performanceScore = 100;
        performanceScore -= Math.min(40, (avgResponseTime / 100) * 40);
        performanceScore -= errorRate * 30;
        performanceScore -= Math.min(20, container.cpuLoad);
        performanceScore -= Math.min(10, (container.memoryUsage / 100) * 10);

        // 新しい重みを計算（段階的に調整）
        const targetWeight = Math.round((performanceScore / 100) * 20);
        const currentWeight = container.weight;
        const adjustment = Math.sign(targetWeight - currentWeight) * 2;
        
        container.weight = Math.max(1, Math.min(20, currentWeight + adjustment));
      }
    }, 5000); // 5秒ごとに調整
  }

  async selectContainer(): Promise<Container | null> {
    const healthyContainers = Array.from(this.containers.values()).filter(c => c.isHealthy);
    if (healthyContainers.length === 0) return null;

    this.requestCount++;

    switch (this.algorithm) {
      case 'round_robin':
        this.roundRobinIndex = (this.roundRobinIndex + 1) % healthyContainers.length;
        return healthyContainers[this.roundRobinIndex];

      case 'least_conn':
        return healthyContainers.reduce((min, c) => 
          c.connections < min.connections ? c : min
        );

      case 'least_response_time':
        return healthyContainers.reduce((best, c) => {
          const avgRT = c.totalRequests > 0 ? c.responseTimeSum / c.totalRequests : 0;
          const bestRT = best.totalRequests > 0 ? best.responseTimeSum / best.totalRequests : 0;
          return avgRT < bestRT ? c : best;
        });

      case 'weighted_response_time':
        // 重み付きレスポンスタイム
        const totalWeight = healthyContainers.reduce((sum, c) => sum + c.weight, 0);
        let random = Math.random() * totalWeight;
        
        for (const container of healthyContainers) {
          random -= container.weight;
          if (random <= 0) return container;
        }
        return healthyContainers[0];

      case 'adaptive':
        // 適応的アルゴリズム（複数の要因を考慮）
        const scores = healthyContainers.map(c => {
          const avgRT = c.totalRequests > 0 ? c.responseTimeSum / c.totalRequests : 100;
          const errorRate = c.totalRequests > 0 ? c.totalErrors / c.totalRequests : 0;
          
          let score = 100;
          score -= Math.min(30, c.connections * 2); // 接続数
          score -= Math.min(30, (avgRT / 100) * 30); // レスポンスタイム
          score -= errorRate * 20; // エラー率
          score -= Math.min(20, c.cpuLoad / 2); // CPU負荷
          
          return { container: c, score };
        });
        
        scores.sort((a, b) => b.score - a.score);
        return scores[0].container;

      default:
        return healthyContainers[0];
    }
  }

  updateMetrics(container: Container, responseTime: number, error: boolean) {
    container.totalRequests++;
    container.responseTimeSum += responseTime;
    if (error) container.totalErrors++;
    
    // CPU/メモリ使用率をシミュレート
    container.cpuLoad = Math.min(95, 20 + container.connections * 2 + Math.random() * 10);
    container.memoryUsage = Math.min(90, 30 + container.connections + Math.random() * 5);
  }

  getMetrics() {
    const metrics: any = {
      totalRequests: 0,
      algorithm: this.algorithm,
      containers: {}
    };

    for (const [id, container] of this.containers) {
      metrics.totalRequests += container.totalRequests;
      metrics.containers[id] = {
        weight: container.weight,
        connections: container.connections,
        requests: container.totalRequests,
        errors: container.totalErrors,
        avgResponseTime: container.totalRequests > 0 
          ? container.responseTimeSum / container.totalRequests 
          : 0,
        cpuLoad: container.cpuLoad,
        memoryUsage: container.memoryUsage,
        isHealthy: container.isHealthy
      };
    }

    return metrics;
  }
}

// グローバルロードバランサー
const loadBalancer = new LoadBalancer();

// アプリケーションハンドラー
async function createAppHandler(containerId: string, port: number, performanceMode: string = 'normal') {
  const container = loadBalancer['containers'].get(containerId);
  
  return async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    const startTime = performance.now();
    
    // 性能特性に応じた遅延
    let baseDelay = 10;
    if (performanceMode === 'low') baseDelay = 30;
    if (performanceMode === 'high') baseDelay = 5;
    
    // 負荷に応じた追加遅延
    const loadDelay = container ? container.connections * 2 : 0;
    await delay(baseDelay + loadDelay);
    
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ 
        status: 'healthy', 
        container: containerId,
        connections: container?.connections || 0,
        cpuLoad: container?.cpuLoad || 0
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    if (url.pathname === '/metrics') {
      return new Response(JSON.stringify({
        container: containerId,
        requests: container?.totalRequests || 0,
        errors: container?.totalErrors || 0,
        avgResponseTime: container && container.totalRequests > 0 
          ? container.responseTimeSum / container.totalRequests 
          : 0,
        cpu: container?.cpuLoad || 0,
        memory: container?.memoryUsage || 0
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    if (url.pathname === '/api/whoami') {
      // エラーをシミュレート（高負荷時）
      if (container && container.connections > 50 && Math.random() < 0.05) {
        return new Response('Service Unavailable', { status: 503 });
      }
      
      return new Response(JSON.stringify({
        container: containerId,
        timestamp: Date.now(),
        connections: container?.connections || 0
      }), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    return new Response('Not Found', { status: 404 });
  };
}

// コンテナサーバーを起動
async function startContainerServers() {
  const servers = [];
  
  // App-1: 通常性能
  const handler1 = await createAppHandler('app-1', 3001, 'normal');
  const server1 = Deno.serve({ port: 3001 }, async (req) => {
    const container = loadBalancer['containers'].get('app-1')!;
    container.connections++;
    try {
      return await handler1(req);
    } finally {
      container.connections--;
    }
  });
  servers.push(server1);
  
  // App-2: 通常性能
  const handler2 = await createAppHandler('app-2', 3002, 'normal');
  const server2 = Deno.serve({ port: 3002 }, async (req) => {
    const container = loadBalancer['containers'].get('app-2')!;
    container.connections++;
    try {
      return await handler2(req);
    } finally {
      container.connections--;
    }
  });
  servers.push(server2);
  
  // App-3: 低性能
  const handler3 = await createAppHandler('app-3', 3003, 'low');
  const server3 = Deno.serve({ port: 3003 }, async (req) => {
    const container = loadBalancer['containers'].get('app-3')!;
    container.connections++;
    try {
      return await handler3(req);
    } finally {
      container.connections--;
    }
  });
  servers.push(server3);
  
  // App-4: 高性能
  const handler4 = await createAppHandler('app-4', 3004, 'high');
  const server4 = Deno.serve({ port: 3004 }, async (req) => {
    const container = loadBalancer['containers'].get('app-4')!;
    container.connections++;
    try {
      return await handler4(req);
    } finally {
      container.connections--;
    }
  });
  servers.push(server4);
  
  return servers;
}

// ロードバランサーサーバー
async function startLoadBalancerServer() {
  const server = Deno.serve({ port: 8080 }, async (request) => {
    const url = new URL(request.url);
    const startTime = performance.now();
    
    if (url.pathname === '/health') {
      return new Response('healthy\n');
    }
    
    if (url.pathname === '/metrics') {
      return new Response(JSON.stringify(loadBalancer.getMetrics()), {
        headers: { 'content-type': 'application/json' }
      });
    }
    
    if (url.pathname === '/admin/algorithm') {
      const algorithm = url.searchParams.get('type') as Algorithm;
      if (algorithm) {
        loadBalancer.setAlgorithm(algorithm);
        return new Response(`Switched to ${algorithm}\n`);
      }
      return new Response('Invalid algorithm\n', { status: 400 });
    }
    
    if (url.pathname === '/admin/enable-dynamic-weighting') {
      loadBalancer.enableDynamicWeighting();
      return new Response('Dynamic weighting enabled\n');
    }
    
    // コンテナを選択してリクエストをプロキシ
    const container = await loadBalancer.selectContainer();
    if (!container) {
      return new Response('No healthy containers available', { status: 503 });
    }
    
    try {
      const backendUrl = `http://localhost:${container.port}${url.pathname}${url.search}`;
      const backendResponse = await fetch(backendUrl, {
        method: request.method,
        headers: request.headers,
        body: request.method !== 'GET' ? await request.text() : undefined,
        signal: AbortSignal.timeout(5000)
      });
      
      const responseTime = performance.now() - startTime;
      loadBalancer.updateMetrics(container, responseTime, !backendResponse.ok);
      
      return new Response(await backendResponse.text(), {
        status: backendResponse.status,
        headers: backendResponse.headers
      });
    } catch (error) {
      const responseTime = performance.now() - startTime;
      loadBalancer.updateMetrics(container, responseTime, true);
      
      // コンテナを一時的に無効化
      container.isHealthy = false;
      setTimeout(() => { container.isHealthy = true; }, 30000); // 30秒後に復旧
      
      // 別のコンテナで再試行
      const alternateContainer = await loadBalancer.selectContainer();
      if (alternateContainer && alternateContainer.id !== container.id) {
        try {
          const backendUrl = `http://localhost:${alternateContainer.port}${url.pathname}${url.search}`;
          const backendResponse = await fetch(backendUrl, {
            method: request.method,
            headers: request.headers,
            body: request.method !== 'GET' ? await request.text() : undefined,
            signal: AbortSignal.timeout(5000)
          });
          
          return new Response(await backendResponse.text(), {
            status: backendResponse.status,
            headers: backendResponse.headers
          });
        } catch {
          return new Response('Service Unavailable', { status: 503 });
        }
      }
      
      return new Response('Service Unavailable', { status: 503 });
    }
  });
  
  return server;
}

// メイン実行
if (import.meta.main) {
  console.log('Starting 4-container system with advanced load balancer...\n');
  
  const containerServers = await startContainerServers();
  const lbServer = await startLoadBalancerServer();
  
  console.log('✅ All servers started:');
  console.log('   - Load Balancer: http://localhost:8080');
  console.log('   - App-1 (normal): http://localhost:3001');
  console.log('   - App-2 (normal): http://localhost:3002');
  console.log('   - App-3 (low perf): http://localhost:3003');
  console.log('   - App-4 (high perf): http://localhost:3004');
  console.log('\nAdmin endpoints:');
  console.log('   - /admin/algorithm?type=[round_robin|least_conn|least_response_time|weighted_response_time|adaptive]');
  console.log('   - /admin/enable-dynamic-weighting');
  console.log('   - /metrics');
  console.log('\nPress Ctrl+C to stop\n');
  
  // グレースフルシャットダウン
  Deno.addSignalListener("SIGINT", () => {
    console.log('\nShutting down servers...');
    containerServers.forEach(s => s.shutdown());
    lbServer.shutdown();
    Deno.exit(0);
  });
  
  // サーバーの完了を待つ
  await Promise.all([
    ...containerServers.map(s => s.finished),
    lbServer.finished
  ]);
}