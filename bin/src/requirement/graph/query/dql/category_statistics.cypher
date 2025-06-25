// 全カテゴリの要件数統計
// パラメータ: なし
// ユースケース: 統計レポート、ダッシュボード表示

MATCH (category:LocationURI)-[:PARENT_OF*]->(leaf:LocationURI)
WHERE NOT EXISTS { MATCH (leaf)-[:PARENT_OF]->() }
  AND NOT EXISTS { MATCH (category)<-[:PARENT_OF]-() }
WITH category, count(leaf) as requirement_count
RETURN category.id as top_level_category,
       requirement_count,
       round(requirement_count * 100.0 / sum(requirement_count)) as percentage
ORDER BY requirement_count DESC;
