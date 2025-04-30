// ルートノードの取得（親ノードを持たないInitNode）
MATCH (n:InitNode)
WHERE NOT EXISTS { MATCH (parent:InitNode)-[:InitEdge]->(n) }
RETURN n.id, n.path, n.label, n.value, n.value_type
ORDER BY n.id