/**
 * Task Planner - タスク計画生成モジュール
 * Cypherクエリにロジックを委譲した最小限の実装
 */

import type { Database } from 'kuzu';
import { executeDql } from '../../kuzu/query/application/services/unifiedQueryService';

// 型定義のみエクスポート
export interface PlanResult {
  ok: boolean;
  data?: any;
  error?: string;
}

// 実装可能な要件をバッチ取得
export async function getReadyForImplementation(db: Database, batchSize: number = 10): Promise<PlanResult> {
  const result = await executeDql(db, 'requirement_find_ready_for_implementation', { batchSize });
  return {
    ok: result.success,
    data: result.data,
    error: result.error
  };
}

// 実装順序の取得
export async function getImplementationOrder(db: Database): Promise<PlanResult> {
  const result = await executeDql(db, 'requirement_find_implementation_order', {});
  return {
    ok: result.success,
    data: result.data,
    error: result.error
  };
}

// 要件の影響分析
export async function analyzeRequirementImpact(db: Database, requirementId: string): Promise<PlanResult> {
  const result = await executeDql(db, 'analyze_requirement_impact', { requirementId });
  return {
    ok: result.success,
    data: result.data?.[0],
    error: result.error
  };
}

// Claudeへの使用例：
// 「次に実装すべきタスクを知りたい」
// const order = await getImplementationOrder(db);
// if (order.ok && order.data) {
//   // order.data[0] = { id, title, priority, status: 'ready', unimplemented_deps: 0 }
//   console.log('次のタスク:', order.data[0].title);
// }