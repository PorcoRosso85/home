// 階層型トレーサビリティモデル - パラメータ化サンプルクエリ

// 特定のIDでノードを検索
// @name: find_by_id
MATCH (n:CodeEntity {persistent_id: $id})
RETURN n.persistent_id, n.name, n.type;

// 特定のタイプのノードをカウント
// @name: count_by_type
MATCH (n:CodeEntity)
WHERE n.type = $type
RETURN count(n) as count;

// 特定の要件に関連するコードを検索
// @name: find_code_for_requirement
MATCH (r:RequirementEntity {id: $req_id})-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
RETURN c.persistent_id, c.name, c.type;

// 複数の優先度による要件の検索
// @name: find_requirements_by_priorities
MATCH (r:RequirementEntity)
WHERE r.priority IN $priorities
RETURN r.id, r.title, r.priority
ORDER BY r.priority;

// 新規テスト用ノードの作成
// @name: create_test_node
CREATE (test:CodeEntity {
  persistent_id: $id,
  name: $name,
  type: $type,
  signature: $signature,
  complexity: $complexity,
  start_position: $start_position,
  end_position: $end_position
})
RETURN test.persistent_id, test.name;

// 特定の関連付けを持つノードの検索
// @name: find_related_nodes
MATCH (c1:CodeEntity)-[:$relation_type]->(c2:CodeEntity)
WHERE c1.persistent_id = $source_id
RETURN c2.persistent_id, c2.name, c2.type;

// 日付範囲でのイベント検索 (例として)
// @name: find_events_in_range
MATCH (vs:VersionState)
WHERE vs.timestamp >= $start_date AND vs.timestamp <= $end_date
RETURN vs.id, vs.timestamp, vs.commit_id
ORDER BY vs.timestamp;

// ページネーション用クエリ
// @name: paginated_list
MATCH (c:CodeEntity)
RETURN c.persistent_id, c.name, c.type
ORDER BY c.name
SKIP $offset
LIMIT $limit;
