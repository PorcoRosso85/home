// 特定パスの要件と実装状況
// ファイルパスやモジュールパスから関連要件を探索
MATCH (l:LocationURI)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
WHERE l.id CONTAINS $uriPath
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(t:CodeEntity)
RETURN l.id as location,
       r.id as requirement_id,
       r.title,
       EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) as is_implemented,
       EXISTS((r)-[:IS_VERIFIED_BY]->()) as has_tests;