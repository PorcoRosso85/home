// InitNodeの挿入クエリ
// 標準的なCypher CREATE構文を使用
CREATE (:InitNode {
  id: $1,
  path: $2,
  label: $3,
  value: $4,
  value_type: $5
})