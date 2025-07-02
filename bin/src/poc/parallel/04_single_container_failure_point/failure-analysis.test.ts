/**
 * 破綻点分析テスト - TDD Red Phase
 * これらのテストは現在の実装では失敗することが期待される
 */

import { assertEquals, assert, assertExists } from "@std/assert";
import { delay } from "@std/async";
import { startFailureAnalyzer } from "./failure-analyzer.ts";
import { createFailurePredictor, simulateLoad, _setGlobalPredictor, simulateLoadWithPredictor, FailurePredictorImpl } from "./failure-predictor.ts";

// 失敗段階の型定義
interface FailureStage {
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

interface FailureAnalysisResult {
  breakingPoint: number;
  failureStages: FailureStage[];
  firstBottleneck: string;
  cascadeStartTime: number;
  totalFailureTime: number;
  recoveryTime: number | null;
}

Deno.test("test_failure_stages_detection_should_identify_4_stages", async () => {
  // 失敗の4段階を検出できるはず
  const analyzer = await startFailureAnalyzer();
  
  // 段階的に負荷を増加
  const result = await analyzer.runAnalysis({
    startClients: 100,
    endClients: 1000,
    incrementStep: 100,
    monitoringInterval: 100,
  });
  
  // 4つの失敗段階が検出されるべき
  assertEquals(
    result.failureStages.length,
    4,
    "Expected to detect exactly 4 failure stages"
  );
  
  // Stage 1: 初期劣化
  const stage1 = result.failureStages[0];
  assertEquals(stage1.stage, 1);
  assert(
    stage1.metrics.latencyP99 > 100 && stage1.metrics.latencyP99 < 500,
    `Stage 1 P99 latency should be 100-500ms, got ${stage1.metrics.latencyP99}ms`
  );
  
  // Stage 2: 部分的失敗
  const stage2 = result.failureStages[1];
  assertEquals(stage2.stage, 2);
  assert(
    stage2.metrics.errorRate > 0.01 && stage2.metrics.errorRate < 0.1,
    `Stage 2 error rate should be 1-10%, got ${stage2.metrics.errorRate * 100}%`
  );
  
  // Stage 3: カスケード失敗
  const stage3 = result.failureStages[2];
  assertEquals(stage3.stage, 3);
  assert(
    stage3.metrics.errorRate > 0.1 && stage3.metrics.errorRate < 0.5,
    `Stage 3 error rate should be 10-50%, got ${stage3.metrics.errorRate * 100}%`
  );
  
  // Stage 4: 完全停止
  const stage4 = result.failureStages[3];
  assertEquals(stage4.stage, 4);
  assert(
    stage4.metrics.errorRate > 0.9,
    `Stage 4 error rate should be >90%, got ${stage4.metrics.errorRate * 100}%`
  );
});

Deno.test("test_bottleneck_identification_should_detect_event_loop_first", async () => {
  // 最初のボトルネックはイベントループであるべき
  const analyzer = await startFailureAnalyzer();
  
  const result = await analyzer.runAnalysis({
    startClients: 300,
    endClients: 600,
    incrementStep: 50,
    monitoringInterval: 200,
  });
  
  assertEquals(
    result.firstBottleneck,
    "event_loop",
    "Expected event loop to be the first bottleneck"
  );
  
  // イベントループ遅延が最初に閾値を超えるはず
  const eventLoopBottleneck = result.failureStages.find(
    (stage: FailureStage) => stage.metrics.eventLoopLag > 50
  );
  
  assertExists(
    eventLoopBottleneck,
    "Event loop lag should exceed 50ms threshold"
  );
});

Deno.test("test_cascade_failure_timing_should_occur_within_30_seconds", async () => {
  // カスケード失敗は負荷開始から30秒以内に発生するはず
  const analyzer = await startFailureAnalyzer();
  const startTime = Date.now();
  
  const result = await analyzer.runAnalysis({
    startClients: 400,
    endClients: 800,
    incrementStep: 100,
    monitoringInterval: 100,
  });
  
  assert(
    result.cascadeStartTime > 0,
    "Cascade failure should be detected"
  );
  
  const timeToFailure = result.cascadeStartTime - startTime;
  assert(
    timeToFailure < 30000,
    `Cascade failure should occur within 30s, took ${timeToFailure}ms`
  );
  
  // カスケード失敗から完全停止までの時間
  assert(
    result.totalFailureTime < 10000,
    `Total failure should occur within 10s of cascade, took ${result.totalFailureTime}ms`
  );
});

Deno.test("test_resource_exhaustion_pattern_should_follow_predictable_order", async () => {
  // リソース枯渇は予測可能な順序で発生するはず
  const analyzer = await startFailureAnalyzer();
  
  const metrics = await analyzer.collectResourceMetrics({
    duration: 60000,
    sampleInterval: 1000,
    targetLoad: 600,
  });
  
  // 枯渇順序: 1.イベントループ → 2.CPU → 3.メモリ → 4.ファイルディスクリプタ
  const exhaustionOrder = analyzer.getResourceExhaustionOrder(metrics);
  
  assertEquals(exhaustionOrder[0], "event_loop");
  assertEquals(exhaustionOrder[1], "cpu");
  assertEquals(exhaustionOrder[2], "memory");
  assertEquals(exhaustionOrder[3], "file_descriptors");
});

Deno.test("test_failure_prediction_should_provide_early_warning", async () => {
  // 失敗の予兆を事前に検出できるはず
  const predictor = await createFailurePredictor();
  
  // リアルタイムメトリクスをフィード
  const warnings: string[] = [];
  predictor.onWarning((warning: string) => {
    warnings.push(warning);
  });
  
  // 負荷を段階的に増加
  for (let clients = 100; clients <= 500; clients += 50) {
    await simulateLoadWithPredictor(clients, 5000, predictor);
    await predictor.analyze();
  }
  
  // 実際の失敗前に警告が発生するはず
  assert(
    warnings.length > 0,
    "Should have received early warnings before failure"
  );
  
  // 最初の警告は300クライアント以下で発生するはず
  const firstWarningLoad = predictor.getLoadAtFirstWarning();
  assert(
    firstWarningLoad <= 300,
    `First warning should occur at ≤300 clients, occurred at ${firstWarningLoad}`
  );
});

Deno.test("test_recovery_analysis_should_show_non_recoverable_after_stage3", async () => {
  // Stage 3以降は回復不能であることを示すべき
  const analyzer = await startFailureAnalyzer();
  
  // Stage 3まで負荷を上げてから下げる
  const result = await analyzer.runRecoveryTest({
    peakLoad: 600,
    reducedLoad: 100,
    recoveryWaitTime: 30000,
  });
  
  assertEquals(
    result.recoveryTime,
    null,
    "System should not recover after reaching Stage 3"
  );
  
  // メトリクスが正常値に戻らないことを確認
  assert(
    result.finalMetrics.errorRate > 0.05,
    "Error rate should remain elevated after load reduction"
  );
  
  assert(
    result.finalMetrics.latencyP99 > 200,
    "Latency should remain elevated after load reduction"
  );
});

