// 要件の完全な情報取得
// 要件とその実装状態、テスト状態を包括的に取得
MATCH (r:RequirementEntity {id: $requirementId})
OPTIONAL MATCH (r)-[impl:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[ver:IS_VERIFIED_BY]->(t:CodeEntity)
OPTIONAL MATCH (r)-[dep:DEPENDS_ON]->(d:RequirementEntity)
RETURN r, 
       collect(DISTINCT c) as implementations,
       collect(DISTINCT t) as tests,
       collect(DISTINCT d) as dependencies;