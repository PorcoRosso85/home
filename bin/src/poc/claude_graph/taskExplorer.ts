/**
 * Task Explorer - KuzuDBグラフ探索モジュール
 * Cypherクエリテンプレートを使用した最小限の実装
 */

// import type { Database } from 'kuzu';
// import { executeDql } from '../../kuzu/query/application/services/unifiedQueryService';

// 仮の型定義（テスト用）
type Database = any;

// 型定義のみエクスポート
export interface TaskNode {
  id: string;
  type: 'requirement' | 'code' | 'test';
  title?: string;
  description?: string;
  priority?: string;
  status?: 'pending' | 'implemented' | 'tested';
}

export interface TaskRelation {
  from: string;
  to: string;
  type: 'implements' | 'verifies' | 'depends_on';
}

export interface ExplorationData {
  nodes: TaskNode[];
  relations: TaskRelation[];
  insights: string[];
}

export type ExploreResult<T> = 
  | { ok: true; data: T }
  | { ok: false; error: ExploreError };

export type ExploreError = 
  | { type: "requirement_not_found"; requirementId: string }
  | { type: "database_error"; message: string }
  | { type: "invalid_input"; message: string };

// 高階関数で依存性注入
export function createExploreFromRequirement(query: (q: string, p?: any) => Promise<any[]>) {
  return async (requirementId: string): Promise<ExploreResult<ExplorationData>> => {
    const nodes: TaskNode[] = [];
    const relations: TaskRelation[] = [];
    const insights: string[] = [];

    try {
      // executeDqlの代わりに注入されたquery関数を使用
      const result = await query(
        `MATCH (r:RequirementEntity {id: $requirementId})
         OPTIONAL MATCH (r)-[impl:IS_IMPLEMENTED_BY]->(c:CodeEntity)
         OPTIONAL MATCH (r)-[ver:IS_VERIFIED_BY]->(t:CodeEntity)
         OPTIONAL MATCH (r)-[dep:DEPENDS_ON]->(d:RequirementEntity)
         RETURN r, 
                collect(DISTINCT c) as implementations,
                collect(DISTINCT t) as tests,
                collect(DISTINCT d) as dependencies`,
        { requirementId }
      );

      if (result.length === 0) {
        return { ok: false, error: { type: "requirement_not_found", requirementId }};
      }

      const data = result[0];
      
      // 要件ノード追加
      nodes.push({
        id: data.r.id,
        type: 'requirement',
        title: data.r.title,
        description: data.r.description,
        priority: data.r.priority,
        status: 'pending'
      });

      // 実装ノード
      if (data.implementations.length === 0) {
        insights.push(`要件 ${requirementId} は未実装です。実装タスクが必要です。`);
      } else {
        data.implementations.forEach((impl: any) => {
          nodes.push({
            id: impl.persistent_id || impl.id,
            type: 'code',
            title: impl.name,
            status: 'implemented'
          });
          relations.push({
            from: requirementId,
            to: impl.persistent_id || impl.id,
            type: 'implements'
          });
        });
      }

      return { ok: true, data: { nodes, relations, insights }};
    } catch (e) {
      return { ok: false, error: { type: "database_error", message: String(e) }};
    }
  };
}

export function createFindUnimplementedRequirements(query: (q: string, p?: any) => Promise<any[]>) {
  return async (): Promise<ExploreResult<TaskNode[]>> => {
    try {
      const result = await query(
        `MATCH (r:RequirementEntity)
         WHERE NOT EXISTS {
           MATCH (r)-[:IS_IMPLEMENTED_BY]->()
         }
         RETURN r.id as id, r.title as title, r.description as description, 
                r.priority as priority
         ORDER BY 
           CASE r.priority 
             WHEN 'high' THEN 1 
             WHEN 'medium' THEN 2 
             WHEN 'low' THEN 3 
             ELSE 4 
           END,
           r.id`
      );
      
      // Sort results by priority since mock doesn't do it
      result.sort((a, b) => {
        const priorityMap: Record<string, number> = { high: 1, medium: 2, low: 3 };
        return (priorityMap[a.priority] || 4) - (priorityMap[b.priority] || 4);
      });

      const nodes = result.map(r => ({
        id: r.id,
        type: 'requirement' as const,
        title: r.title,
        description: r.description,
        priority: r.priority,
        status: 'pending' as const
      }));

      return { ok: true, data: nodes };
    } catch (e) {
      return { ok: false, error: { type: "database_error", message: String(e) }};
    }
  };
}

export function createExploreByLocationURI(query: (q: string, p?: any) => Promise<any[]>) {
  return async (uriPath: string): Promise<ExploreResult<ExplorationData>> => {
    const nodes: TaskNode[] = [];
    const relations: TaskRelation[] = [];
    const insights: string[] = [];

    try {
      const result = await query(
        `MATCH (l:LocationURI)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
         WHERE l.id CONTAINS $uriPath
         OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
         OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(t:CodeEntity)
         RETURN l.id as location,
                r.id as requirement_id,
                r.title,
                EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) as is_implemented,
                EXISTS((r)-[:IS_VERIFIED_BY]->()) as has_tests`,
        { uriPath }
      );

      if (result.length === 0) {
        insights.push(`URI ${uriPath} に関連するエンティティが見つかりません。`);
        return { ok: true, data: { nodes, relations, insights }};
      }

      result.forEach((item: any) => {
        nodes.push({
          id: item.requirement_id,
          type: 'requirement',
          title: item.title,
          priority: item.priority,
          status: item.is_implemented ? 'implemented' : 'pending'
        });

        if (!item.is_implemented) {
          insights.push(`要件 ${item.requirement_id} は未実装です。`);
        }
        if (!item.has_tests) {
          insights.push(`要件 ${item.requirement_id} にテストがありません。`);
        }
      });

      return { ok: true, data: { nodes, relations, insights }};
    } catch (e) {
      return { ok: false, error: { type: "database_error", message: String(e) }};
    }
  };
}

// 実際のDB接続用のラッパー（本番用）
// export async function exploreRequirement(db: Database, requirementId: string): Promise<ExploreResult<ExplorationData>> {
//   const result = await executeDql(db, 'requirement_explore_complete_graph', { requirementId });
//   
//   if (!result.success) {
//     return { ok: false, error: { type: "database_error", message: result.error || "Unknown error" }};
//   }
//   
//   if (!result.data || result.data.length === 0) {
//     return { ok: false, error: { type: "requirement_not_found", requirementId }};
//   }
// 
//   // 簡易的な変換（実際のCypherクエリ結果に依存）
//   const data = result.data[0];
//   const nodes: TaskNode[] = [{
//     id: data.r.id,
//     type: 'requirement',
//     title: data.r.title,
//     description: data.r.description,
//     priority: data.r.priority,
//     status: 'pending'
//   }];
// 
//   return { ok: true, data: { nodes, relations: [], insights: [] }};
// }
// 
// export async function findUnimplementedRequirements(db: Database): Promise<ExploreResult<TaskNode[]>> {
//   const result = await executeDql(db, 'requirement_find_all_unimplemented', {});
//   
//   if (!result.success) {
//     return { ok: false, error: { type: "database_error", message: result.error || "Unknown error" }};
//   }
// 
//   const nodes = (result.data || []).map((r: any) => ({
//     id: r.id,
//     type: 'requirement' as const,
//     title: r.title,
//     description: r.description,
//     priority: r.priority,
//     status: 'pending' as const
//   }));
// 
//   return { ok: true, data: nodes };
// }
// 
// export async function exploreByLocation(db: Database, uriPath: string): Promise<ExploreResult<ExplorationData>> {
//   const result = await executeDql(db, 'requirement_find_by_location_uri', { uriPath });
//   
//   if (!result.success) {
//     return { ok: false, error: { type: "database_error", message: result.error || "Unknown error" }};
//   }
// 
//   const nodes: TaskNode[] = [];
//   const insights: string[] = [];
// 
//   (result.data || []).forEach((item: any) => {
//     nodes.push({
//       id: item.requirement_id,
//       type: 'requirement',
//       title: item.title,
//       priority: item.priority,
//       status: item.is_implemented ? 'implemented' : 'pending'
//     });
// 
//     if (!item.is_implemented) {
//       insights.push(`要件 ${item.requirement_id} は未実装です。`);
//     }
//     if (!item.has_tests) {
//       insights.push(`要件 ${item.requirement_id} にテストがありません。`);
//     }
//   });
// 
//   return { ok: true, data: { nodes, relations: [], insights }};
// }