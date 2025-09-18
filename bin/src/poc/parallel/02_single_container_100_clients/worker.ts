/**
 * ワーカースレッド - CPU集約的なタスク処理
 */

import type { WorkerMessage, WorkerResponse } from "./types.ts";

// データ生成関数
function generateData(clientId: string): any {
  return {
    id: clientId,
    value: Math.random() * 1000,
    workerId: self.name,
    timestamp: Date.now(),
    items: Array(10).fill(0).map((_, i) => ({
      index: i,
      data: `Item ${i} for client ${clientId}`,
      hash: crypto.getRandomValues(new Uint8Array(8)).join(""),
    })),
  };
}

// メトリクス計算関数
function calculateMetrics(data: any): any {
  const responseTimes = data.responseTimes || [];
  if (responseTimes.length === 0) {
    return {
      p50: 0,
      p95: 0,
      p99: 0,
      mean: 0,
      count: 0,
    };
  }

  const sorted = [...responseTimes].sort((a, b) => a - b);
  return {
    p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
    p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
    p99: sorted[Math.floor(sorted.length * 0.99)] || 0,
    mean: sorted.reduce((a, b) => a + b, 0) / sorted.length || 0,
    count: sorted.length,
  };
}

// ワーカーメッセージハンドラー
self.onmessage = (e: MessageEvent<WorkerMessage>) => {
  const { id, method, args } = e.data;
  
  try {
    let result: any;
    
    switch (method) {
      case "generateData":
        result = generateData(args[0] as string);
        break;
        
      case "calculateMetrics":
        result = calculateMetrics(args[0]);
        break;
        
      case "processHeavyTask":
        // CPU集約的なタスクの例
        const iterations = (args[0] as number) || 1000000;
        let sum = 0;
        for (let i = 0; i < iterations; i++) {
          sum += Math.sqrt(i);
        }
        result = { sum, iterations };
        break;
        
      default:
        throw new Error(`Unknown method: ${method}`);
    }
    
    const response: WorkerResponse = {
      id,
      result,
    };
    
    self.postMessage(response);
  } catch (error) {
    const response: WorkerResponse = {
      id,
      error: error instanceof Error ? error.message : String(error),
    };
    
    self.postMessage(response);
  }
};