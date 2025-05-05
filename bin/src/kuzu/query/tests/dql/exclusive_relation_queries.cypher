// 排他的関係テスト用クエリ

// @name: get_all_requirements
// すべての要件を取得
MATCH (r:RequirementEntity)
RETURN r.id, r.title, r.description;

// @name: get_requirement_by_id
// 指定IDの要件を取得
MATCH (r:RequirementEntity {id: $reqId})
RETURN r.id, r.title, r.description;

// @name: check_requirement_relations
// 要件の関連を確認
MATCH (r:RequirementEntity {id: $reqId})
OPTIONAL MATCH (r)-[impl:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[ver:VERIFIED_BY]->(v:RequirementVerification)
RETURN 
  r.id AS requirement_id,
  r.title AS requirement_title,
  CASE WHEN impl IS NOT NULL THEN 'IS_IMPLEMENTED_BY' ELSE NULL END AS implementation_relation,
  CASE WHEN c IS NOT NULL THEN c.persistent_id ELSE NULL END AS code_id,
  CASE WHEN ver IS NOT NULL THEN 'VERIFIED_BY' ELSE NULL END AS verification_relation,
  CASE WHEN v IS NOT NULL THEN v.id ELSE NULL END AS verification_id;

// @name: add_exclusive_verification
// 排他的に検証関係を追加（実装がない場合のみ）
MATCH (a:RequirementEntity {id: $reqId}), (b:RequirementVerification {id: $verificationId})
WHERE NOT EXISTS { MATCH (a)-[:IS_IMPLEMENTED_BY|VERIFIED_BY]->() }
CREATE (a)-[:VERIFIED_BY]->(b)
RETURN a.id AS requirement_id, b.id AS verification_id;

// @name: add_verification_for_testing
// テスト用：強制的に検証関係を追加
MATCH (a:RequirementEntity {id: $reqId}), (b:RequirementVerification {id: $verificationId})
CREATE (a)-[:VERIFIED_BY]->(b)
RETURN a.id AS requirement_id, b.id AS verification_id;
