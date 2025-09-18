/**
 * コアモジュール - 01を拡張した高性能版
 */

import { createMetricsManager } from "../01_single_container_10_clients/core.ts";
import type { ExtendedServerConfig, MetricsData } from "./types.ts";
import { Pool } from "./worker-pool.ts";
import { LRUCache } from "./cache.ts";

// リクエスト制限管理
export function createRequestLimiter(maxConcurrent: number) {
  let activeRequests = 0;

  return {
    canAccept: () => activeRequests < maxConcurrent,
    increment: () => activeRequests++,
    decrement: () => activeRequests--,
    getActive: () => activeRequests,
  };
}

// 拡張メトリクスマネージャー
export function createExtendedMetricsManager(config: ExtendedServerConfig) {
  const baseManager = createMetricsManager(config);
  let cacheHits = 0;
  let cacheMisses = 0;

  return {
    ...baseManager,
    recordCacheHit: () => cacheHits++,
    recordCacheMiss: () => cacheMisses++,
    getCacheStats: () => ({
      hits: cacheHits,
      misses: cacheMisses,
      hitRate: cacheHits + cacheMisses > 0 
        ? cacheHits / (cacheHits + cacheMisses) 
        : 0,
    }),
    getExtendedMetrics: (): MetricsData & { cache: any } => {
      const baseMetrics = baseManager.getMetrics();
      return {
        ...baseMetrics,
        cache: {
          hits: cacheHits,
          misses: cacheMisses,
          hitRate: cacheHits + cacheMisses > 0 
            ? cacheHits / (cacheHits + cacheMisses) 
            : 0,
        },
      };
    },
  };
}

// 拡張サーバー作成
export function createExtendedServer(config: ExtendedServerConfig) {
  const metricsManager = createExtendedMetricsManager(config);
  const requestLimiter = createRequestLimiter(
    config.maxConcurrentRequests || 50
  );
  const cache = new LRUCache<any>(
    config.cacheSize || 1000,
    config.cacheTTL || 60000
  );
  const workerPool = config.numWorkers 
    ? new Pool(config.numWorkers, "./worker.ts")
    : null;

  // カスタムハンドラーまたはデフォルトハンドラー
  const baseHandler = config.customHandler || createDefaultHandler(
    metricsManager,
    requestLimiter,
    cache,
    workerPool
  );

  const handler = async (request: Request): Promise<Response> => {
    // リクエスト制限チェック
    if (!requestLimiter.canAccept()) {
      return new Response(
        JSON.stringify({
          error: "Server too busy",
          retry_after: 1,
        }),
        {
          status: 503,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    requestLimiter.increment();
    
    try {
      const response = await baseHandler(request);
      if (response.status === 200) {
        metricsManager.recordSuccess(10);
      } else {
        metricsManager.recordError();
      }
      return response;
    } catch (error) {
      console.error("Request handler error:", error);
      metricsManager.recordError();
      return new Response(
        JSON.stringify({ 
          error: "Internal server error",
          details: error instanceof Error ? error.message : String(error)
        }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }
      );
    } finally {
      requestLimiter.decrement();
    }
  };

  return {
    start: () => {
      console.log(`🚀 Extended server starting on port ${config.port}`);
      console.log(`📊 Max concurrent requests: ${config.maxConcurrentRequests || 50}`);
      console.log(`💾 Cache size: ${config.cacheSize || 1000}`);
      console.log(`👷 Worker pool: ${config.numWorkers || 0} workers`);
      
      return Deno.serve({
        port: config.port,
        handler,
        onListen: ({ port, hostname }) => {
          console.log(`✅ Server running at http://${hostname}:${port}/`);
        },
      });
    },
    stop: () => {
      if (workerPool) {
        workerPool.terminate();
      }
    },
  };
}

// デフォルトハンドラー作成
function createDefaultHandler(
  metricsManager: ReturnType<typeof createExtendedMetricsManager>,
  requestLimiter: ReturnType<typeof createRequestLimiter>,
  cache: LRUCache<any>,
  workerPool: Pool | null,
) {
  return async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    
    // ヘルスチェック
    if (url.pathname === "/api/health") {
      return new Response(
        JSON.stringify({
          status: "healthy",
          timestamp: new Date().toISOString(),
          uptime: performance.now() / 1000,
          activeRequests: requestLimiter.getActive(),
          cacheSize: cache.size,
        }),
        {
          headers: { "Content-Type": "application/json" },
        }
      );
    }
    
    // メトリクス
    if (url.pathname === "/api/metrics") {
      return new Response(
        JSON.stringify(metricsManager.getExtendedMetrics()),
        {
          headers: { "Content-Type": "application/json" },
        }
      );
    }
    
    // データエンドポイント
    const dataMatch = url.pathname.match(/^\/api\/data\/(.+)$/);
    if (dataMatch) {
      const clientId = dataMatch[1];
      const cacheKey = `data:${clientId}`;
      
      // キャッシュチェック
      let data = cache.get(cacheKey);
      if (data) {
        metricsManager.recordCacheHit();
      } else {
        metricsManager.recordCacheMiss();
        
        // ワーカープールで生成
        if (workerPool) {
          data = await workerPool.run("generateData", clientId);
        } else {
          // ワーカーなしの場合はインライン生成
          data = {
            id: clientId,
            value: Math.random() * 1000,
            timestamp: Date.now(),
            items: Array(10).fill(0).map((_, i) => ({
              index: i,
              data: `Item ${i} for client ${clientId}`,
            })),
          };
        }
        
        cache.set(cacheKey, data);
      }
      
      return new Response(JSON.stringify(data), {
        headers: { "Content-Type": "application/json" },
      });
    }
    
    return new Response("Not Found", { status: 404 });
  };
}