// 完全な作業計画を1クエリで取得
// 現在のバージョンコンテキスト、実装可能タスク、ブロックタスク、最近の完了を統合
WITH datetime() as query_time
MATCH (vs:VersionState)
WHERE vs.progress_percentage < 1.0
WITH vs ORDER BY vs.timestamp DESC LIMIT 1

// バージョンコンテキスト
WITH vs, query_time,
     {
       versionId: vs.id,
       versionDescription: vs.description,
       progressPercentage: vs.progress_percentage
     } as version_context

// カウント取得
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
OPTIONAL MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
WITH version_context, vs, query_time,
     count(DISTINCT r) as total_requirements,
     sum(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) THEN 1 ELSE 0 END) as completed_requirements,
     sum(CASE 
       WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) 
       AND NOT EXISTS((r)-[:IS_VERIFIED_BY]->()) 
       THEN 1 ELSE 0 
     END) as in_progress_requirements

// 実装可能なタスク（依存関係が解決済み）
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
WHERE NOT EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
  AND NOT EXISTS {
    MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
    WHERE NOT EXISTS((dep)-[:IS_IMPLEMENTED_BY]->())
  }
WITH version_context, total_requirements, completed_requirements, in_progress_requirements, vs, query_time,
     collect({
       requirementId: r.id,
       title: r.title,
       description: r.description,
       priority: r.priority,
       location: loc.id,
       reason: CASE 
         WHEN r.priority = 'high' THEN '最優先度の未実装要件'
         WHEN r.priority = 'medium' THEN '中優先度の実装可能要件'
         ELSE '実装可能な要件'
       END,
       blockedBy: [],
       estimatedEffort: coalesce(r.estimated_hours * 60, 120)
     }) as ready_tasks

// ブロックされたタスク
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc2:LocationURI)
MATCH (loc2)-[:LOCATED_WITH_REQUIREMENT]->(r2:RequirementEntity)
WHERE NOT EXISTS((r2)-[:IS_IMPLEMENTED_BY]->())
  AND EXISTS {
    MATCH (r2)-[:DEPENDS_ON]->(dep2:RequirementEntity)
    WHERE NOT EXISTS((dep2)-[:IS_IMPLEMENTED_BY]->())
  }
OPTIONAL MATCH (r2)-[:DEPENDS_ON]->(blocker:RequirementEntity)
WHERE NOT EXISTS((blocker)-[:IS_IMPLEMENTED_BY]->())
WITH version_context, total_requirements, completed_requirements, in_progress_requirements, ready_tasks, vs, query_time,
     r2, loc2, collect(blocker.id) as blockers
WITH version_context, total_requirements, completed_requirements, in_progress_requirements, ready_tasks, query_time,
     collect({
       requirementId: r2.id,
       title: r2.title,
       description: r2.description,
       priority: r2.priority,
       location: loc2.id,
       reason: size(blockers) + '個の要件に依存中',
       blockedBy: blockers,
       estimatedEffort: coalesce(r2.estimated_hours * 60, 120)
     }) as blocked_tasks

// 最近完了したタスク（過去7日間）
OPTIONAL MATCH (completed_r:RequirementEntity)-[impl:IS_IMPLEMENTED_BY]->(c:CodeEntity)
WHERE impl.completed_at > datetime(query_time) - duration('P7D')
WITH version_context, total_requirements, completed_requirements, in_progress_requirements, 
     ready_tasks, blocked_tasks,
     collect(DISTINCT completed_r.id) as recently_completed

// 最終結果
RETURN {
  currentVersion: version_context + {
    totalRequirements: total_requirements,
    completedRequirements: completed_requirements,
    inProgressRequirements: in_progress_requirements
  },
  nextTasks: [task IN ready_tasks | task][0..10], // 上位10件
  blockedTasks: blocked_tasks,
  completedRecently: recently_completed
} as work_plan;