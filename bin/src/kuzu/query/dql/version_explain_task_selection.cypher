// タスク選択理由の説明
// なぜこの要件が次のタスクとして選ばれたかを説明
MATCH (r:RequirementEntity {id: $requirementId})
OPTIONAL MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
OPTIONAL MATCH (dependent:RequirementEntity)-[:DEPENDS_ON]->(r)
OPTIONAL MATCH (r)<-[:LOCATED_WITH_REQUIREMENT]-(loc:LocationURI)<-[:TRACKS_STATE_OF_LOCATED_ENTITY]-(vs:VersionState)
WHERE vs.progress_percentage < 1.0
WITH r, 
     collect(DISTINCT dep.id) as dependencies,
     collect(DISTINCT dependent.id) as dependents,
     vs
ORDER BY vs.timestamp DESC LIMIT 1
RETURN {
  requirement: {
    id: r.id,
    title: r.title,
    priority: r.priority,
    description: r.description
  },
  dependencies: dependencies,
  dependents: dependents,
  dependent_count: size(dependents),
  version_context: coalesce(vs.id + ' - ' + vs.description, '現在のバージョン外'),
  explanation: 
    '優先度: ' + r.priority + '\n' +
    CASE 
      WHEN size(dependencies) = 0 THEN '依存関係なし - すぐに実装可能\n'
      ELSE '依存要件: ' + size(dependencies) + '個\n'
    END +
    CASE
      WHEN size(dependents) = 0 THEN 'このタスクに依存する要件なし\n'
      ELSE size(dependents) + 'つの要件がこのタスクに依存しています\n'
    END +
    CASE
      WHEN r.priority = 'high' AND size(dependencies) = 0 THEN 
        '=> 最優先で実装すべきタスクです'
      WHEN r.priority = 'high' THEN
        '=> 優先度は高いですが、依存関係の解決が必要です'
      WHEN size(dependents) > 2 THEN
        '=> 多くの要件のブロッカーとなっているため、優先的に実装を推奨'
      ELSE
        '=> 標準的な優先順位で実装'
    END
} as task_explanation;