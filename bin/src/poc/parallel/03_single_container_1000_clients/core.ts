/**
 * 極限最適化コア - 1000クライアント挑戦
 */

import { LRUCache } from "./cache.ts";
import type { ExtremeServerConfig, PerformanceCounters } from "./types.ts";
import { ExtremeBufferPool } from "./buffer-pool.ts";
import { ExtremeConnectionPool } from "./connection-pool.ts";

// パフォーマンスカウンター
const performanceCounters: PerformanceCounters = {
  totalConnections: 0,
  activeConnections: 0,
  rejectedConnections: 0,
  totalRequests: 0,
  queuedRequests: 0,
  droppedRequests: 0,
  avgProcessingTime: 0,
  gcCount: 0,
  lastGcTime: Date.now(),
};

// リクエストキュー（バックプレッシャー制御）
class RequestQueue {
  private queue: Array<() => Promise<void>> = [];
  private processing = 0;
  private readonly maxConcurrent: number;
  private readonly maxQueued: number;
  
  constructor(maxConcurrent: number, maxQueued: number) {
    this.maxConcurrent = maxConcurrent;
    this.maxQueued = maxQueued;
  }
  
  async enqueue(task: () => Promise<void>): Promise<boolean> {
    if (this.queue.length >= this.maxQueued) {
      performanceCounters.droppedRequests++;
      return false;
    }
    
    performanceCounters.queuedRequests++;
    this.queue.push(task);
    this.process();
    return true;
  }
  
  private async process(): Promise<void> {
    while (this.processing < this.maxConcurrent && this.queue.length > 0) {
      const task = this.queue.shift();
      if (!task) break;
      
      this.processing++;
      performanceCounters.queuedRequests--;
      
      task().finally(() => {
        this.processing--;
        this.process();
      });
    }
  }
}

// メトリクスマネージャー（ローカル実装）
function createMetricsManager(config: ExtremeServerConfig) {
  const metrics = {
    requestCount: 0,
    errorCount: 0,
    responseTimes: [] as number[],
    cacheHits: 0,
    cacheMisses: 0,
  };

  return {
    recordSuccess(responseTime: number): void {
      metrics.requestCount++;
      metrics.responseTimes.push(responseTime);
      
      if (metrics.responseTimes.length > config.maxMetricsSize) {
        metrics.responseTimes.shift();
      }
    },
    
    recordError(): void {
      metrics.errorCount++;
    },
    
    recordCacheHit(): void {
      metrics.cacheHits++;
    },
    
    recordCacheMiss(): void {
      metrics.cacheMisses++;
    },
    
    getMetrics() {
      const sorted = [...metrics.responseTimes].sort((a, b) => a - b);
      return {
        requestCount: metrics.requestCount,
        errorCount: metrics.errorCount,
        responseTimes: metrics.responseTimes,
        responseTime: {
          p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
          p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
          p99: sorted[Math.floor(sorted.length * 0.99)] || 0,
          mean: sorted.length > 0 
            ? sorted.reduce((a, b) => a + b, 0) / sorted.length 
            : 0,
        },
        memory: Deno.memoryUsage(),
        cache: {
          hits: metrics.cacheHits,
          misses: metrics.cacheMisses,
          hitRate: metrics.cacheHits + metrics.cacheMisses > 0
            ? metrics.cacheHits / (metrics.cacheHits + metrics.cacheMisses)
            : 0,
        },
      };
    },
  };
}

// 極限最適化サーバー作成
export function createExtremeServer(config: ExtremeServerConfig) {
  const metricsManager = createMetricsManager(config);
  const cache = new LRUCache<any>(
    config.cacheSize || 2000, // より大きなキャッシュ
    config.cacheTTL || 120000 // 2分
  );
  
  // バッファプールとコネクションプール
  const bufferPool = new ExtremeBufferPool(
    config.preallocateBuffers || 1500,
    4096 // 4KB per buffer
  );
  
  const connectionPool = new ExtremeConnectionPool(
    1200, // 最大1200接続
    config.maxConnectionsPerIP || 50
  );
  
  // リクエストキュー
  const requestQueue = new RequestQueue(
    config.maxConcurrentRequests || 200,
    config.requestQueueSize || 1000
  );
  
  // 定期的なクリーンアップ
  const cleanupInterval = setInterval(() => {
    const stale = connectionPool.cleanupStale(30000); // 30秒でタイムアウト
    if (stale > 0) {
      console.log(`🧹 Cleaned up ${stale} stale connections`);
    }
    
    bufferPool.cleanup(60000); // 1分未使用のバッファをクリーン
    
    // GCヒント
    const now = Date.now();
    if (now - performanceCounters.lastGcTime > 30000) {
      // Denoには明示的なGC APIがないが、メモリプレッシャーを示唆
      performanceCounters.gcCount++;
      performanceCounters.lastGcTime = now;
    }
  }, 5000); // 5秒ごと
  
  // TCPサーバー作成（低レベル制御）
  async function startTCPServer(port: number) {
    const listener = Deno.listen({ 
      port,
      // Linuxでのみ有効なオプション（SO_REUSEPORT相当）
      reusePort: true,
    });
    
    console.log(`🚀 Extreme server listening on port ${port}`);
    console.log(`💪 Target: 1000 concurrent connections`);
    console.log(`🔧 Buffer pool: ${config.preallocateBuffers} buffers`);
    console.log(`📊 Request queue: ${config.requestQueueSize} max`);
    
    // 接続受付ループ
    for await (const conn of listener) {
      handleConnection(conn).catch(console.error);
    }
  }
  
  // 接続ハンドラー
  async function handleConnection(conn: Deno.Conn) {
    performanceCounters.totalConnections++;
    
    // 接続制限チェック
    if (!connectionPool.canAccept(conn.remoteAddr)) {
      performanceCounters.rejectedConnections++;
      conn.close();
      return;
    }
    
    // バッファ取得
    const buffer = bufferPool.acquire();
    if (!buffer) {
      performanceCounters.rejectedConnections++;
      conn.close();
      return;
    }
    
    const connId = connectionPool.add(conn, buffer);
    performanceCounters.activeConnections++;
    
    try {
      // TCP最適化
      if (config.tcpNoDelay) {
        // Deno doesn't expose TCP_NODELAY directly
      }
      
      const decoder = new TextDecoder();
      const encoder = new TextEncoder();
      
      // リクエスト処理ループ
      for await (const chunk of conn.readable) {
        const connection = connectionPool.get(connId);
        if (!connection) break;
        
        connection.lastActivity = Date.now();
        
        // HTTPリクエストの簡易パース
        const data = decoder.decode(chunk);
        
        // リクエストキューに追加
        const queued = await requestQueue.enqueue(async () => {
          const startTime = Date.now();
          
          try {
            const response = await handleRequest(data);
            await conn.write(encoder.encode(response));
            
            // 処理時間の記録
            const duration = Date.now() - startTime;
            performanceCounters.avgProcessingTime = 
              (performanceCounters.avgProcessingTime * 0.9) + (duration * 0.1);
            
            performanceCounters.totalRequests++;
            metricsManager.recordSuccess(duration);
          } catch (error) {
            console.error("Request error:", error);
            metricsManager.recordError();
          }
        });
        
        if (!queued) {
          // キューが満杯
          const errorResponse = "HTTP/1.1 503 Service Unavailable\r\n" +
                              "Content-Length: 21\r\n" +
                              "Retry-After: 5\r\n" +
                              "\r\n" +
                              "Server overloaded";
          await conn.write(encoder.encode(errorResponse));
        }
      }
    } catch (error) {
      if (!(error instanceof Deno.errors.BadResource)) {
        console.error("Connection error:", error);
      }
    } finally {
      performanceCounters.activeConnections--;
      connectionPool.remove(connId);
      bufferPool.release(buffer);
    }
  }
  
  // HTTPリクエストハンドラー（超軽量）
  async function handleRequest(data: string): Promise<string> {
    // 最小限のHTTPパース
    if (data.includes("GET /api/health")) {
      return "HTTP/1.1 200 OK\r\n" +
             "Content-Type: application/json\r\n" +
             "Content-Length: 52\r\n" +
             "Connection: keep-alive\r\n" +
             "\r\n" +
             `{"status":"healthy","active":${performanceCounters.activeConnections}}`;
    }
    
    if (data.includes("GET /api/metrics")) {
      const metrics = {
        ...metricsManager.getMetrics(),
        performance: performanceCounters,
        pools: {
          buffer: bufferPool.getStats(),
          connection: connectionPool.getStats(),
        },
      };
      
      const json = JSON.stringify(metrics);
      return `HTTP/1.1 200 OK\r\n` +
             `Content-Type: application/json\r\n` +
             `Content-Length: ${json.length}\r\n` +
             `Connection: keep-alive\r\n` +
             `\r\n` +
             json;
    }
    
    // データエンドポイント（キャッシュ使用）
    const dataMatch = data.match(/GET \/api\/data\/([^ ]+)/);
    if (dataMatch) {
      const clientId = dataMatch[1];
      const cacheKey = `data:${clientId}`;
      
      let responseData = cache.get(cacheKey);
      if (responseData) {
        metricsManager.recordCacheHit();
      } else {
        metricsManager.recordCacheMiss();
        responseData = {
          id: clientId,
          value: Math.random() * 1000,
          timestamp: Date.now(),
          server: "extreme-03",
        };
        cache.set(cacheKey, responseData);
      }
      
      const json = JSON.stringify(responseData);
      return `HTTP/1.1 200 OK\r\n` +
             `Content-Type: application/json\r\n` +
             `Content-Length: ${json.length}\r\n` +
             `Connection: keep-alive\r\n` +
             `\r\n` +
             json;
    }
    
    return "HTTP/1.1 404 Not Found\r\n" +
           "Content-Length: 0\r\n" +
           "\r\n";
  }
  
  return {
    start: () => startTCPServer(config.port),
    stop: () => {
      clearInterval(cleanupInterval);
    },
  };
}