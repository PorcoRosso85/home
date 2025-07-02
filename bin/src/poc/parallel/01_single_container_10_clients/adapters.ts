/**
 * 外部依存 - HTTPサーバーとミドルウェア
 */

import type { HandlerResult, ServerConfig, MemoryUsage } from "./types.ts";
import { 
  createMetricsManager, 
  createHealthResponse, 
  createMetricsResponse 
} from "./core.ts";

/**
 * メモリ使用量を取得（Deno固有）
 * @returns メモリ使用量
 */
export function getMemoryUsage(): MemoryUsage {
  const usage = Deno.memoryUsage();
  return {
    rss: usage.rss,
    heapTotal: usage.heapTotal,
    heapUsed: usage.heapUsed,
  };
}

/**
 * HTTPサーバーを作成する高階関数
 * @param config サーバー設定
 * @returns サーバー起動関数
 */
export function createServer(config: ServerConfig) {
  const metricsManager = createMetricsManager(config);
  const startTime = performance.now();

  /**
   * リクエストハンドラー
   * @param req HTTPリクエスト
   * @returns ハンドラー結果
   */
  async function handleRequest(req: Request): Promise<HandlerResult> {
    const url = new URL(req.url);
    
    try {
      if (url.pathname === "/api/health" && req.method === "GET") {
        const health = createHealthResponse(startTime);
        return {
          ok: true,
          data: new Response(JSON.stringify(health), {
            headers: { "content-type": "application/json" },
          })
        };
      }
      
      if (url.pathname === "/api/metrics" && req.method === "GET") {
        const metrics = metricsManager.getMetrics();
        const memoryUsage = getMemoryUsage();
        const metricsResponse = createMetricsResponse(metrics, memoryUsage);
        
        return {
          ok: true,
          data: new Response(JSON.stringify(metricsResponse), {
            headers: { "content-type": "application/json" },
          })
        };
      }
      
      return {
        ok: true,
        data: new Response("Not Found", { status: 404 })
      };
    } catch (error) {
      return {
        ok: false,
        error: error instanceof Error ? error : new Error(String(error))
      };
    }
  }

  /**
   * レスポンスタイム計測ミドルウェア
   * @param req HTTPリクエスト
   * @returns HTTPレスポンス
   */
  async function measureResponseTime(req: Request): Promise<Response> {
    const start = Date.now();
    
    const result = await handleRequest(req);
    const duration = Date.now() - start;
    
    if (result.ok) {
      metricsManager.recordSuccess(duration);
      return result.data;
    } else {
      metricsManager.recordError();
      // エラーレスポンスを返す（例外は投げない）
      return new Response(
        JSON.stringify({ error: result.error.message }), 
        { 
          status: 500,
          headers: { "content-type": "application/json" }
        }
      );
    }
  }

  return {
    /**
     * サーバーを起動
     * @returns サーバーインスタンス
     */
    start() {
      const server = Deno.serve(
        { port: config.port },
        measureResponseTime
      );
      
      console.log(`Server running on port ${config.port}`);
      console.log(`Process ID: ${Deno.pid}`);
      console.log(`Deno version: ${Deno.version.deno}`);
      
      return server;
    }
  };
}

/**
 * グレースフルシャットダウンを設定
 * @param abortController 中断コントローラー
 */
export function setupGracefulShutdown(abortController: AbortController): void {
  Deno.addSignalListener("SIGTERM", () => {
    console.log("\nReceived SIGTERM, shutting down gracefully...");
    abortController.abort();
  });

  Deno.addSignalListener("SIGINT", () => {
    console.log("\nReceived SIGINT, shutting down gracefully...");
    abortController.abort();
  });
}