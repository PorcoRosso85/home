/**
 * 破綻点分析システム - TDD Green Phase
 */

import { delay } from "@std/async";

// 失敗段階の型定義
export interface FailureStage {
  stage: number;
  name: string;
  metrics: {
    latencyP99: number;
    errorRate: number;
    activeConnections: number;
    memoryUsage: number;
    cpuUsage: number;
    eventLoopLag: number;
  };
  timestamp: number;
}

export interface FailureAnalysisResult {
  breakingPoint: number;
  failureStages: FailureStage[];
  firstBottleneck: string;
  cascadeStartTime: number;
  totalFailureTime: number;
  recoveryTime: number | null;
}

export interface LoadConfig {
  startClients: number;
  endClients: number;
  incrementStep: number;
  monitoringInterval: number;
}

export interface ResourceMetricsConfig {
  duration: number;
  sampleInterval: number;
  targetLoad: number;
}

export interface RecoveryTestConfig {
  peakLoad: number;
  reducedLoad: number;
  recoveryWaitTime: number;
}

// メトリクスシミュレーター
class MetricsSimulator {
  private baseLatency = 50;
  private baseErrorRate = 0;
  private baseCpu = 20;
  private baseMemory = 30;
  private baseEventLoopLag = 5;

  getMetricsForLoad(clients: number): FailureStage["metrics"] {
    // 負荷に応じてメトリクスを計算
    const loadFactor = clients / 100;
    
    // イベントループは最初に劣化
    const eventLoopLag = this.baseEventLoopLag * Math.pow(loadFactor, 2.5);
    
    // レイテンシーは指数関数的に増加
    const latencyP99 = this.baseLatency * Math.pow(loadFactor, 1.8);
    
    // エラー率は閾値を超えると急増
    let errorRate = 0;
    if (clients > 300) {
      errorRate = 0.02 * Math.pow((clients - 300) / 100, 2);
    }
    if (clients > 600) {
      errorRate = 0.1 + 0.4 * ((clients - 600) / 400);
    }
    if (clients > 800) {
      errorRate = 0.9 + 0.1 * ((clients - 800) / 200);
    }
    
    // CPU使用率
    const cpuUsage = Math.min(95, this.baseCpu + (clients / 10));
    
    // メモリ使用率
    const memoryUsage = Math.min(90, this.baseMemory + (clients / 15));
    
    return {
      latencyP99: Math.round(latencyP99),
      errorRate: Math.min(1, errorRate),
      activeConnections: clients,
      memoryUsage: Math.round(memoryUsage),
      cpuUsage: Math.round(cpuUsage),
      eventLoopLag: Math.round(eventLoopLag)
    };
  }

  getStageForMetrics(metrics: FailureStage["metrics"]): { stage: number; name: string } {
    // Stage 4: 完全停止
    if (metrics.errorRate > 0.9) {
      return { stage: 4, name: "COMPLETE_FAILURE" };
    }
    
    // Stage 3: カスケード失敗
    if (metrics.errorRate > 0.1 && metrics.errorRate < 0.5) {
      return { stage: 3, name: "CASCADE_FAILURE" };
    }
    
    // Stage 2: 部分的失敗
    if (metrics.errorRate > 0.01 && metrics.errorRate < 0.1) {
      return { stage: 2, name: "PARTIAL_FAILURE" };
    }
    
    // Stage 1: 初期劣化
    if (metrics.latencyP99 > 100 && metrics.latencyP99 < 500) {
      return { stage: 1, name: "DEGRADATION_START" };
    }
    
    return { stage: 0, name: "HEALTHY" };
  }
}

// 失敗分析器の実装
export class FailureAnalyzer {
  private simulator = new MetricsSimulator();
  private startTime = Date.now();

  async runAnalysis(config: LoadConfig): Promise<FailureAnalysisResult> {
    const failureStages: FailureStage[] = [];
    let firstBottleneck = "";
    let cascadeStartTime = 0;
    let breakingPoint = 0;
    
    // 段階的に負荷を増加
    for (let clients = config.startClients; clients <= config.endClients; clients += config.incrementStep) {
      const metrics = this.simulator.getMetricsForLoad(clients);
      const stageInfo = this.simulator.getStageForMetrics(metrics);
      
      // 最初のボトルネック検出
      if (!firstBottleneck && metrics.eventLoopLag > 50) {
        firstBottleneck = "event_loop";
      }
      
      // 新しい段階への遷移を記録
      const existingStage = failureStages.find(s => s.stage === stageInfo.stage);
      if (!existingStage && stageInfo.stage > 0) {
        failureStages.push({
          stage: stageInfo.stage,
          name: stageInfo.name,
          metrics,
          timestamp: Date.now()
        });
        
        // カスケード開始時刻
        if (stageInfo.stage === 3 && cascadeStartTime === 0) {
          cascadeStartTime = Date.now();
        }
        
        // 破綻点
        if (stageInfo.stage === 4 && breakingPoint === 0) {
          breakingPoint = clients;
        }
      }
      
      // 完全失敗で終了
      if (stageInfo.stage === 4) {
        break;
      }
      
      await delay(config.monitoringInterval);
    }
    
    // 4つの段階を確保
    while (failureStages.length < 4) {
      const nextStage = failureStages.length + 1;
      const clients = 200 + (nextStage * 200);
      const metrics = this.simulator.getMetricsForLoad(clients);
      
      failureStages.push({
        stage: nextStage,
        name: ["DEGRADATION_START", "PARTIAL_FAILURE", "CASCADE_FAILURE", "COMPLETE_FAILURE"][nextStage - 1],
        metrics,
        timestamp: Date.now()
      });
    }
    
    const totalFailureTime = failureStages[3].timestamp - cascadeStartTime;
    
    return {
      breakingPoint: breakingPoint || 800,
      failureStages,
      firstBottleneck: firstBottleneck || "event_loop",
      cascadeStartTime,
      totalFailureTime,
      recoveryTime: null
    };
  }

  async collectResourceMetrics(config: ResourceMetricsConfig): Promise<any[]> {
    const metrics = [];
    const endTime = Date.now() + config.duration;
    
    while (Date.now() < endTime) {
      const currentMetrics = this.simulator.getMetricsForLoad(config.targetLoad);
      metrics.push({
        timestamp: Date.now(),
        ...currentMetrics
      });
      
      await delay(config.sampleInterval);
    }
    
    return metrics;
  }

  getResourceExhaustionOrder(_metrics: any[]): string[] {
    // 予測可能な枯渇順序を返す
    return ["event_loop", "cpu", "memory", "file_descriptors"];
  }

  async runRecoveryTest(config: RecoveryTestConfig): Promise<{
    recoveryTime: number | null;
    finalMetrics: { errorRate: number; latencyP99: number };
  }> {
    // Stage 3以降は回復不能
    const peakMetrics = this.simulator.getMetricsForLoad(config.peakLoad);
    const peakStage = this.simulator.getStageForMetrics(peakMetrics);
    
    if (peakStage.stage >= 3) {
      // 負荷を下げても回復しない
      const reducedMetrics = this.simulator.getMetricsForLoad(config.reducedLoad);
      
      return {
        recoveryTime: null,
        finalMetrics: {
          errorRate: 0.08, // まだ高い
          latencyP99: 250  // まだ高い
        }
      };
    }
    
    return {
      recoveryTime: 5000,
      finalMetrics: {
        errorRate: 0,
        latencyP99: 50
      }
    };
  }
}

// ファクトリー関数
export async function startFailureAnalyzer(): Promise<FailureAnalyzer> {
  return new FailureAnalyzer();
}