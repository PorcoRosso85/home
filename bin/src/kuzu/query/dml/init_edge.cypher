// InitEdgeの挿入クエリ
// MATCHとCREATEを組み合わせた構文
MATCH (source:InitNode), (target:InitNode)
WHERE source.id = $1 AND target.id = $2
CREATE (source)-[:InitEdge {
  id: $3,
  relation_type: $4
}]->(target)