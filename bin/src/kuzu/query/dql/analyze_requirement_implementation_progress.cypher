// プロジェクト全体の実装進捗
// 要件タイプ別の実装状況を集計
MATCH (r:RequirementEntity)
RETURN r.requirement_type as type,
       count(*) as total,
       sum(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) THEN 1 ELSE 0 END) as implemented,
       sum(CASE WHEN EXISTS((r)-[:IS_VERIFIED_BY]->()) THEN 1 ELSE 0 END) as tested,
       round(100.0 * sum(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) THEN 1 ELSE 0 END) / count(*), 1) as implementation_rate;