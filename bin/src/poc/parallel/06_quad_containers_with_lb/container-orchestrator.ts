/**
 * コンテナオーケストレーター
 * 4コンテナの協調制御と動的重み付けを実装
 */

export class ContainerOrchestrator {
  private containers: Map<string, any> = new Map();
  private weights: Map<string, number> = new Map();
  private dynamicWeighting: boolean = false;
  
  constructor(options: any = {}) {
    this.dynamicWeighting = options.dynamicWeighting || false;
  }
  
  async initialize() {
    // コンテナの初期化
    const containerConfigs = [
      { id: 'app-1', port: 3001, weight: 10 },
      { id: 'app-2', port: 3002, weight: 10 },
      { id: 'app-3', port: 3003, weight: 5 },
      { id: 'app-4', port: 3004, weight: 15 }
    ];
    
    for (const config of containerConfigs) {
      await this.addContainer(config);
    }
    
    if (this.dynamicWeighting) {
      this.startDynamicWeighting();
    }
  }
  
  async addContainer(config: any) {
    this.containers.set(config.id, {
      id: config.id,
      port: config.port,
      weight: config.weight,
      status: 'running',
      metrics: {
        requests: 0,
        errors: 0,
        responseTime: [],
        cpu: 0,
        memory: 0
      }
    });
    
    this.weights.set(config.id, config.weight);
  }
  
  startDynamicWeighting() {
    setInterval(() => {
      const performanceScores = this.calculatePerformanceScores();
      
      for (const [id, score] of performanceScores) {
        const currentWeight = this.weights.get(id) || 10;
        const targetWeight = Math.round((score / 100) * 20);
        const adjustment = Math.sign(targetWeight - currentWeight) * 2;
        const newWeight = Math.max(1, Math.min(20, currentWeight + adjustment));
        
        if (Math.abs(newWeight - currentWeight) > 1) {
          this.weights.set(id, newWeight);
          console.log(`Weight adjusted: ${id} from ${currentWeight} to ${newWeight}`);
        }
      }
    }, 10000); // 10秒ごと
  }
  
  private calculatePerformanceScores(): Map<string, number> {
    const scores = new Map();
    
    for (const [id, container] of this.containers) {
      if (container.status !== 'running') continue;
      
      let score = 100;
      const metrics = container.metrics;
      
      // レスポンスタイム（40%）
      const avgResponseTime = this.average(metrics.responseTime);
      score -= Math.min(40, (avgResponseTime / 100) * 40);
      
      // エラー率（30%）
      const errorRate = metrics.errors / (metrics.requests || 1);
      score -= errorRate * 30;
      
      // CPU使用率（20%）
      score -= Math.min(20, (metrics.cpu / 100) * 20);
      
      // メモリ使用率（10%）
      score -= Math.min(10, (metrics.memory / 100) * 10);
      
      scores.set(id, Math.max(0, score));
    }
    
    return scores;
  }
  
  private average(arr: number[]): number {
    if (arr.length === 0) return 0;
    return arr.reduce((a, b) => a + b) / arr.length;
  }
  
  async updateContainerMetrics(containerId: string, newMetrics: any) {
    const container = this.containers.get(containerId);
    if (!container) return;
    
    container.metrics.requests = newMetrics.requests;
    container.metrics.errors = newMetrics.errors;
    container.metrics.cpu = newMetrics.cpu;
    container.metrics.memory = newMetrics.memory;
    
    container.metrics.responseTime.push(newMetrics.avgResponseTime);
    if (container.metrics.responseTime.length > 60) {
      container.metrics.responseTime.shift();
    }
  }
  
  getAggregatedMetrics() {
    const aggregated = {
      totalRequests: 0,
      totalErrors: 0,
      avgResponseTime: 0,
      avgCpu: 0,
      avgMemory: 0,
      containerMetrics: {} as any
    };
    
    let responseTimeSum = 0;
    let responseTimeCount = 0;
    
    for (const [id, container] of this.containers) {
      if (container.status !== 'running') continue;
      
      aggregated.totalRequests += container.metrics.requests;
      aggregated.totalErrors += container.metrics.errors;
      aggregated.avgCpu += container.metrics.cpu;
      aggregated.avgMemory += container.metrics.memory;
      
      const avgRT = this.average(container.metrics.responseTime);
      responseTimeSum += avgRT;
      responseTimeCount++;
      
      aggregated.containerMetrics[id] = {
        ...container.metrics,
        avgResponseTime: avgRT,
        weight: this.weights.get(id)
      };
    }
    
    aggregated.avgResponseTime = responseTimeCount > 0 
      ? responseTimeSum / responseTimeCount 
      : 0;
    aggregated.avgCpu /= this.containers.size;
    aggregated.avgMemory /= this.containers.size;
    
    return aggregated;
  }
}