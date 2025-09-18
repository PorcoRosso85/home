/**
 * POC 04: 単一コンテナの破綻点分析サーバー
 * 
 * 目的: 単一コンテナの限界を科学的に分析し、失敗のメカニズムを理解する
 */

import { startFailureAnalyzer } from "./failure-analyzer.ts";
import { createFailurePredictor } from "./failure-predictor.ts";

// メトリクス収集
interface ServerMetrics {
  requestCount: number;
  errorCount: number;
  activeConnections: number;
  latencies: number[];
  memoryUsage: number;
  cpuStartTime: number;
  startTime: number;
}

class MetricsCollector {
  private metrics: ServerMetrics = {
    requestCount: 0,
    errorCount: 0,
    activeConnections: 0,
    latencies: [],
    memoryUsage: 0,
    cpuStartTime: performance.now(),
    startTime: Date.now()
  };

  recordRequest(latency: number, error: boolean = false) {
    this.metrics.requestCount++;
    if (error) {
      this.metrics.errorCount++;
    }
    this.metrics.latencies.push(latency);
    
    // 最新1000件のみ保持
    if (this.metrics.latencies.length > 1000) {
      this.metrics.latencies.shift();
    }
  }

  incrementConnections() {
    this.metrics.activeConnections++;
  }

  decrementConnections() {
    this.metrics.activeConnections--;
  }

  getMetrics() {
    const memoryUsage = Deno.memoryUsage();
    const uptime = Date.now() - this.metrics.startTime;
    
    // P99レイテンシーの計算
    const sortedLatencies = [...this.metrics.latencies].sort((a, b) => a - b);
    const p99Index = Math.floor(sortedLatencies.length * 0.99);
    const latencyP99 = sortedLatencies[p99Index] || 0;
    
    // CPU使用率の簡易計算
    const cpuTime = performance.now() - this.metrics.cpuStartTime;
    const cpuUsage = Math.min(100, (cpuTime / uptime) * 100);
    
    return {
      requestCount: this.metrics.requestCount,
      errorRate: this.metrics.requestCount > 0 
        ? this.metrics.errorCount / this.metrics.requestCount 
        : 0,
      activeConnections: this.metrics.activeConnections,
      latencyP99,
      memoryUsage: Math.round((memoryUsage.heapUsed / memoryUsage.heapTotal) * 100),
      cpuUsage: Math.round(cpuUsage),
      eventLoopLag: Math.round(performance.now() % 100) // 簡易的なイベントループ遅延
    };
  }
}

// 分析サーバー
class FailureAnalysisServer {
  private metricsCollector = new MetricsCollector();
  private analyzer: any;
  private predictor: any;
  private degradationMode = false;
  private failureStage = 0;

  constructor(private port: number) {}

  async start() {
    // 分析システムの初期化
    this.analyzer = await startFailureAnalyzer();
    this.predictor = await createFailurePredictor();
    
    // 警告リスナーの設定
    this.predictor.onWarning((warning: string) => {
      console.log(`⚠️  WARNING: ${warning}`);
    });
    
    // メトリクス監視の開始
    this.startMetricsMonitoring();
    
    // HTTPサーバーの起動
    const server = Deno.serve({ port: this.port }, async (request) => {
      return this.handleRequest(request);
    });
    
    console.log(`🔬 Failure Analysis Server started on port ${this.port}`);
    console.log(`📊 Monitoring system metrics and failure patterns...`);
    
    return server;
  }

  private async handleRequest(request: Request): Promise<Response> {
    const startTime = performance.now();
    this.metricsCollector.incrementConnections();
    
    try {
      // 負荷に応じた遅延をシミュレート
      await this.simulateLoad();
      
      // 失敗をシミュレート
      if (this.shouldFail()) {
        throw new Error("System overloaded");
      }
      
      const latency = performance.now() - startTime;
      this.metricsCollector.recordRequest(latency);
      
      return new Response(JSON.stringify({
        status: "ok",
        stage: this.failureStage,
        metrics: this.metricsCollector.getMetrics()
      }), {
        headers: { "Content-Type": "application/json" }
      });
      
    } catch (error) {
      const latency = performance.now() - startTime;
      this.metricsCollector.recordRequest(latency, true);
      
      return new Response(JSON.stringify({
        error: error.message,
        stage: this.failureStage
      }), {
        status: 503,
        headers: { "Content-Type": "application/json" }
      });
      
    } finally {
      this.metricsCollector.decrementConnections();
    }
  }

  private async simulateLoad() {
    const metrics = this.metricsCollector.getMetrics();
    
    // Stage 1: 初期劣化（100ms以上の遅延）
    if (metrics.activeConnections > 100) {
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    // Stage 2: 部分的失敗（エラー率上昇）
    if (metrics.activeConnections > 300) {
      this.failureStage = 2;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Stage 3: カスケード失敗
    if (metrics.activeConnections > 500) {
      this.failureStage = 3;
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    // Stage 4: 完全停止
    if (metrics.activeConnections > 700) {
      this.failureStage = 4;
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }

  private shouldFail(): boolean {
    const metrics = this.metricsCollector.getMetrics();
    const random = Math.random();
    
    // 接続数に応じたエラー率
    if (metrics.activeConnections > 700) {
      return random < 0.95; // 95%失敗
    } else if (metrics.activeConnections > 500) {
      return random < 0.3; // 30%失敗
    } else if (metrics.activeConnections > 300) {
      return random < 0.05; // 5%失敗
    }
    
    return false;
  }

  private startMetricsMonitoring() {
    setInterval(async () => {
      const metrics = this.metricsCollector.getMetrics();
      
      // 予測分析
      await this.predictor.analyze();
      
      // メトリクスログ
      if (metrics.requestCount % 100 === 0) {
        console.log(`📊 Metrics: ${JSON.stringify(metrics)}`);
      }
      
      // 失敗段階の検出
      if (metrics.errorRate > 0.9 && this.failureStage !== 4) {
        console.log("💥 STAGE 4: Complete failure detected!");
      } else if (metrics.errorRate > 0.1 && this.failureStage < 3) {
        console.log("🔥 STAGE 3: Cascade failure in progress!");
      } else if (metrics.errorRate > 0.01 && this.failureStage < 2) {
        console.log("⚡ STAGE 2: Partial failures occurring!");
      } else if (metrics.latencyP99 > 100 && this.failureStage < 1) {
        console.log("🐌 STAGE 1: Performance degradation detected!");
        this.failureStage = 1;
      }
      
    }, 1000);
  }
}

// メイン実行
if (import.meta.main) {
  const port = parseInt(Deno.env.get("PORT") || "3000");
  const server = new FailureAnalysisServer(port);
  
  await server.start();
}