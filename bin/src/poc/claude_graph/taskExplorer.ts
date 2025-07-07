/**
 * Task Explorer - KuzuDBグラフ探索モジュール
 * Cypherクエリテンプレートを使用した最小限の実装
 */

import type { Database } from 'kuzu';
import { executeDql } from '../../kuzu/query/application/services/unifiedQueryService';

// 型定義のみエクスポート
export interface TaskNode {
  id: string;
  type: 'requirement' | 'code' | 'test';
  title?: string;
  description?: string;
  priority?: string;
  status?: 'pending' | 'implemented' | 'tested';
}

export interface ExplorationResult {
  ok: boolean;
  data?: any;
  error?: string;
}

// クエリ実行と最小限の型変換のみ
export async function exploreRequirement(db: Database, requirementId: string): Promise<ExplorationResult> {
  const result = await executeDql(db, 'requirement_explore_complete_graph', { requirementId });
  return {
    ok: result.success,
    data: result.data?.[0],
    error: result.error
  };
}

export async function findUnimplementedRequirements(db: Database): Promise<ExplorationResult> {
  const result = await executeDql(db, 'requirement_find_all_unimplemented', {});
  return {
    ok: result.success,
    data: result.data,
    error: result.error
  };
}

export async function findUntestedRequirements(db: Database): Promise<ExplorationResult> {
  const result = await executeDql(db, 'requirement_find_all_untested', {});
  return {
    ok: result.success,
    data: result.data,
    error: result.error
  };
}

export async function exploreByLocation(db: Database, uriPath: string): Promise<ExplorationResult> {
  const result = await executeDql(db, 'requirement_find_by_location_uri', { uriPath });
  return {
    ok: result.success,
    data: result.data,
    error: result.error
  };
}

// Claudeへの使用例：
// const result = await exploreRequirement(db, 'req_auth_api');
// if (result.ok && result.data) {
//   // result.dataにはCypherクエリの結果がそのまま入っている
//   console.log(result.data.r.title); // 要件タイトル
//   console.log(result.data.implementations); // 実装一覧
// }