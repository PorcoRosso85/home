/**
 * VersionBasedExplorer - バージョン起点の最小限実装
 * Cypherクエリにロジックを委譲し、型変換のみ行う
 */

// import { executeDql } from '../../kuzu/query/application/services/unifiedQueryService';

// 型定義（テストから抽出）
export type VersionExploreResult<T> = 
  | { ok: true; data: T }
  | { ok: false; error: VersionExploreError };

export type VersionExploreError = 
  | { type: "no_active_version"; message: string }
  | { type: "version_not_found"; versionId: string }
  | { type: "database_error"; message: string };

export interface NextTask {
  requirementId: string;
  title: string;
  description?: string;
  priority: 'high' | 'medium' | 'low';
  reason: string;
  blockedBy: string[];
  location?: string;
  estimatedEffort?: number;
}

export interface VersionContext {
  versionId: string;
  versionDescription: string;
  progressPercentage: number;
  totalRequirements: number;
  completedRequirements: number;
  inProgressRequirements: number;
}

export interface WorkPlan {
  currentVersion: VersionContext;
  nextTasks: NextTask[];
  blockedTasks: NextTask[];
  completedRecently: string[];
}

// 高階関数：クエリ実行関数を受け取り、各機能を返す
export function createGetCurrentVersion(query: (q: string, p?: any) => Promise<any[]>) {
  return async (): Promise<VersionExploreResult<VersionContext>> => {
    try {
      const rows = await query(
        `MATCH (vs:VersionState)
         WHERE vs.progress_percentage < 1.0
         WITH vs ORDER BY vs.timestamp DESC LIMIT 1
         RETURN vs.id as id, vs.description as description, 
                vs.timestamp, vs.progress_percentage`
      );
      
      if (rows.length === 0) {
        return { ok: false, error: { type: "no_active_version", message: "No active version found" }};
      }
      
      // 要件カウント取得
      const countRows = await query(
        `MATCH (vs:VersionState {id: $id})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
         OPTIONAL MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
         RETURN COUNT(DISTINCT r) as total,
                SUM(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) AND NOT EXISTS((r)-[:IS_VERIFIED_BY]->()) THEN 1 ELSE 0 END) as in_progress`,
        { id: rows[0].id }
      );
      
      const counts = countRows[0] || { total: 0, completed: 0, in_progress: 0 };
      
      return {
        ok: true,
        data: {
          versionId: rows[0].id,
          versionDescription: rows[0].description,
          progressPercentage: rows[0].progress_percentage,
          totalRequirements: counts.total,
          completedRequirements: counts.completed,
          inProgressRequirements: counts.in_progress
        }
      };
    } catch (e) {
      return { ok: false, error: { type: "database_error", message: String(e) }};
    }
  };
}

export function createGetNextTask(query: (q: string, p?: any) => Promise<any[]>) {
  return async (versionId: string): Promise<VersionExploreResult<NextTask | null>> => {
    try {
      const rows = await query(
        `MATCH (vs:VersionState {id: $versionId})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
         MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
         WHERE NOT EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
         OPTIONAL MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
         WHERE NOT EXISTS((dep)-[:IS_IMPLEMENTED_BY]->())
         WITH r, loc, collect(dep.id) as blocked_by
         RETURN r.id as req_id, r.title as req_title, r.description as req_description,
                r.priority as req_priority, loc.id as location_uri,
                blocked_by, size(blocked_by) = 0 as has_dependencies
         ORDER BY has_dependencies DESC, 
                  CASE r.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
         LIMIT 1`,
        { versionId }
      );
      
      if (rows.length === 0) {
        return { ok: true, data: null };
      }
      
      const task = rows[0];
      return {
        ok: true,
        data: {
          requirementId: task.req_id,
          title: task.req_title,
          description: task.req_description,
          priority: task.req_priority,
          reason: task.blocked_by.length > 0 
            ? `${task.blocked_by.length}個の要件に依存中`
            : "最優先度の未実装要件",
          blockedBy: task.blocked_by,
          location: task.location_uri
        }
      };
    } catch (e) {
      return { ok: false, error: { type: "database_error", message: String(e) }};
    }
  };
}

export function createGetWorkPlan(query: (q: string, p?: any) => Promise<any[]>) {
  return async (): Promise<VersionExploreResult<WorkPlan>> => {
    try {
      // 現在のバージョン取得
      const versionRows = await query(
        `MATCH (vs:VersionState)
         WHERE vs.progress_percentage < 1.0
         WITH vs ORDER BY vs.timestamp DESC LIMIT 1
         RETURN vs.id as id, vs.description as description, vs.progress_percentage`
      );
      
      if (versionRows.length === 0) {
        return { ok: false, error: { type: "no_active_version", message: "No active version found" }};
      }
      
      const version = versionRows[0];
      
      // 実装可能タスク取得
      const readyTasks = await query(
        `MATCH (vs:VersionState {id: $versionId})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
         MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
         WHERE NOT EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
           AND NOT EXISTS {
             MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
             WHERE NOT EXISTS((dep)-[:IS_IMPLEMENTED_BY]->())
           }
         RETURN r.id as req_id, r.title as title, r.priority as priority
         ORDER BY CASE r.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END`,
        { versionId: version.id }
      );
      
      // ブロックされたタスク取得
      const blockedRows = await query(
        `MATCH (vs:VersionState {id: $versionId})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
         MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
         WHERE NOT EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
           AND EXISTS {
             MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
             WHERE NOT EXISTS((dep)-[:IS_IMPLEMENTED_BY]->())
           }
         OPTIONAL MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
         WHERE NOT EXISTS((dep)-[:IS_IMPLEMENTED_BY]->())
         WITH r, collect(dep.id) as blocked_by
         RETURN r.id as req_id, r.title as title, r.priority as priority, blocked_by`,
        { versionId: version.id }
      );
      
      // 最近完了タスク
      const recentRows = await query(
        `MATCH (r:RequirementEntity)
         WHERE EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
         RETURN r.id as req_id
         ORDER BY r.id DESC
         LIMIT 10`
      );
      
      return {
        ok: true,
        data: {
          currentVersion: {
            versionId: version.id,
            versionDescription: version.description,
            progressPercentage: version.progress_percentage,
            totalRequirements: readyTasks.length + blockedRows.length,
            completedRequirements: 0,
            inProgressRequirements: 0
          },
          nextTasks: readyTasks.map(t => ({
            requirementId: t.req_id,
            title: t.title,
            priority: t.priority,
            reason: "最優先度の未実装要件",
            blockedBy: [],
            description: ""
          })),
          blockedTasks: blockedRows.map(t => ({
            requirementId: t.req_id,
            title: t.title,
            priority: t.priority,
            reason: `${t.blocked_by.length}個の要件に依存中`,
            blockedBy: t.blocked_by,
            description: ""
          })),
          completedRecently: recentRows.map(r => r.req_id)
        }
      };
    } catch (e) {
      return { ok: false, error: { type: "database_error", message: String(e) }};
    }
  };
}

export function createExplainWhyThisTask(query: (q: string, p?: any) => Promise<any[]>) {
  return async (requirementId: string): Promise<string> => {
    const rows = await query(
      `MATCH (r:RequirementEntity {id: $requirementId})
       OPTIONAL MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
       OPTIONAL MATCH (dependent:RequirementEntity)-[:DEPENDS_ON]->(r)
       OPTIONAL MATCH (r)<-[:LOCATED_WITH_REQUIREMENT]-(loc:LocationURI)<-[:TRACKS_STATE_OF_LOCATED_ENTITY]-(vs:VersionState)
       WHERE vs.progress_percentage < 1.0
       WITH r, collect(DISTINCT dep) as deps, collect(DISTINCT dependent) as dependents, vs
       ORDER BY vs.timestamp DESC
       LIMIT 1
       RETURN {id: r.id, priority: r.priority} as requirement,
              [] as dependencies,
              [d IN dependents | d.id] as dependents,
              coalesce(vs.id + ' - ' + vs.description, '') as version_context`,
      { requirementId }
    );
    
    if (rows.length === 0) return "要件が見つかりません";
    
    const data = rows[0];
    const lines = [
      `優先度: ${data.requirement.priority}`,
      `${data.dependents.length}つの要件がこのタスクに依存しています`,
      data.version_context
    ];
    
    return lines.join('\n');
  };
}

export function createSuggestTaskOrder(query: (q: string, p?: any) => Promise<any[]>) {
  return async (versionId: string): Promise<VersionExploreResult<NextTask[]>> => {
    try {
      const rows = await query(
        `MATCH (vs:VersionState {id: $versionId})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
         MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
         WHERE NOT EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
         OPTIONAL MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
         WHERE NOT EXISTS((dep)-[:IS_IMPLEMENTED_BY]->())
         WITH r, collect(dep.id) as depends_on
         RETURN {id: r.id, priority: r.priority, depends_on: depends_on} as tasks`,
        { versionId }
      );
      
      if (rows.length === 0) {
        return { ok: true, data: [] };
      }
      
      // 簡易的なトポロジカルソート
      const tasks = rows.map(r => r.tasks);
      const sorted = tasks.sort((a, b) => {
        // 依存なしを優先
        if (a.depends_on.length === 0 && b.depends_on.length > 0) return -1;
        if (a.depends_on.length > 0 && b.depends_on.length === 0) return 1;
        
        // 優先度で並べる
        const priorityMap = { high: 1, medium: 2, low: 3 };
        return (priorityMap[a.priority] || 3) - (priorityMap[b.priority] || 3);
      });
      
      return {
        ok: true,
        data: sorted.map(t => ({
          requirementId: t.id,
          title: "",
          priority: t.priority,
          reason: "",
          blockedBy: t.depends_on
        }))
      };
    } catch (e) {
      return { ok: false, error: { type: "database_error", message: String(e) }};
    }
  };
}