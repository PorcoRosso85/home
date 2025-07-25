// add_dependency.cypher
// 要件間の依存関係を原子的に追加（全チェック込み）
// 
// チェック内容:
// 1. 自己参照チェック: from_id != to_id
// 2. 重複チェック: 既存の依存関係がない
// 3. 循環依存チェック: to->from経路が存在しない
//
// 戻り値:
// - 成功時: created=true, from, to, error=null
// - 失敗時: created=false, from=null, to=null, error=理由

// 両方のノードが存在することを確認
MATCH (from:RequirementEntity {id: $from_id})
MATCH (to:RequirementEntity {id: $to_id})

// 原子的なチェックと作成
WITH from, to,
  // 自己参照チェック
  CASE 
    WHEN $from_id = $to_id THEN 'SELF_REFERENCE'
    ELSE null
  END AS self_ref_error,
  // 既存依存関係チェック
  EXISTS((from)-[:DEPENDS_ON]->(to)) AS already_exists,
  // 循環依存チェック（toからfromへの経路）
  EXISTS((to)-[:DEPENDS_ON*]->(from)) AS would_create_cycle

// エラー判定
WITH from, to,
  CASE
    WHEN self_ref_error IS NOT NULL THEN self_ref_error
    WHEN already_exists THEN 'DUPLICATE_DEPENDENCY'
    WHEN would_create_cycle THEN 'CIRCULAR_DEPENDENCY'
    ELSE null
  END AS error

// 条件付き作成（エラーがない場合のみ）
FOREACH (_ IN CASE WHEN error IS NULL THEN [1] ELSE [] END |
  CREATE (from)-[:DEPENDS_ON {dependency_type: $dependency_type, reason: $reason}]->(to)
)

// 結果を返す
RETURN 
  error IS NULL AS created,
  CASE WHEN error IS NULL THEN from ELSE null END AS from,
  CASE WHEN error IS NULL THEN to ELSE null END AS to,
  error