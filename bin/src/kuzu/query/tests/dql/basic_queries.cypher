// 階層型トレーサビリティモデル - 基本クエリセット

// ノード総数カウント
// @name: count_nodes
MATCH (n) RETURN count(n) as count;

// 要件エンティティ一覧（上位3件）
// @name: list_requirements
MATCH (r:RequirementEntity) RETURN r.id, r.title LIMIT 3;

// コードエンティティ一覧（上位3件）
// @name: list_code_entities
MATCH (c:CodeEntity) RETURN c.persistent_id, c.name LIMIT 3;

// 実装関係の確認（上位3件）
// @name: check_implementation_relations
MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity) RETURN r.id, c.persistent_id LIMIT 3;

// 新規テストノード作成
// @name: create_test_node
CREATE (test:CodeEntity {
  persistent_id: 'TEST-001',
  name: 'テスト関数',
  type: 'function',
  signature: 'public void test()',
  complexity: 1,
  start_position: 1000,
  end_position: 1050
});

// 作成したテストノードの検証
// @name: verify_test_node
MATCH (c:CodeEntity {persistent_id: 'TEST-001'}) RETURN c.name, c.type;
