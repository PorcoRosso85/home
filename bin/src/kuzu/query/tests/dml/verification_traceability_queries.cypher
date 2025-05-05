// 検証トレーサビリティテスト用クエリ

// @name: get_all_verifications
MATCH (v:RequirementVerification)
RETURN v.id, v.name, v.description, v.verification_type;

// @name: create_req_and_verification
// 新しい要件を作成
CREATE (r:RequirementEntity {
  id: 'REQ-TRACE-001',
  title: 'ユーザー認証要件',
  description: 'ユーザーはIDとパスワードで認証できること',
  priority: 'high',
  requirement_type: 'functional'
})

// 新しい検証を作成
CREATE (v1:RequirementVerification {
  id: 'VERIFY-001',
  name: 'ユーザー認証テスト',
  description: '有効なIDとパスワードで認証できることを確認',
  verification_type: 'automated_test'
})

CREATE (v2:RequirementVerification {
  id: 'VERIFY-002',
  name: 'ユーザー認証エラーテスト',
  description: '無効なIDとパスワードでエラーになることを確認',
  verification_type: 'automated_test'
})

// 要件と検証の関連付け
CREATE (r)-[:VERIFIED_BY]->(v1)
CREATE (r)-[:VERIFIED_BY]->(v2)

RETURN r.id, v1.id, v2.id;

// @name: get_verifications_for_requirement
MATCH (r:RequirementEntity {id: 'REQ-TRACE-001'})-[:VERIFIED_BY]->(v:RequirementVerification)
RETURN r.id, r.title, collect(v.id) AS verification_ids, collect(v.name) AS verification_names;

// @name: get_requirements_for_verification
MATCH (v:RequirementVerification {id: 'VERIFY-001'})<-[:VERIFIED_BY]-(r:RequirementEntity)
RETURN v.id, v.name, collect(r.id) AS requirement_ids, collect(r.title) AS requirement_titles;

// @name: create_unverified_requirement
CREATE (r:RequirementEntity {
  id: 'REQ-UNVERIFIED',
  title: '未検証の要件',
  description: 'これはまだ検証が作成されていない要件です',
  priority: 'medium',
  requirement_type: 'functional'
})
RETURN r.id, r.title;

// @name: find_unverified_requirements
MATCH (r:RequirementEntity)
WHERE NOT EXISTS { MATCH (r)-[:VERIFIED_BY]->() }
RETURN r.id, r.title, r.priority;

// @name: create_verification_code
CREATE (c:CodeEntity {
  persistent_id: 'TEST-AUTH-001',
  name: 'testUserAuthentication',
  type: 'function',
  signature: 'void testUserAuthentication()',
  complexity: 2,
  start_position: 100,
  end_position: 150
})
WITH c
MATCH (v:RequirementVerification {id: 'VERIFY-001'})
CREATE (v)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'unit_test'}]->(c)
RETURN v.id, c.persistent_id;

// @name: get_traceability_chain
MATCH (r:RequirementEntity)-[:VERIFIED_BY]->(v:RequirementVerification)-[:VERIFICATION_IS_IMPLEMENTED_BY]->(c:CodeEntity)
RETURN r.id, r.title, v.id, v.name, c.persistent_id, c.name;

// @name: find_unimplemented_verifications
MATCH (v:RequirementVerification)
WHERE NOT EXISTS { MATCH (v)-[:VERIFICATION_IS_IMPLEMENTED_BY]->() }
RETURN v.id, v.name, v.verification_type;
