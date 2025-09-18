// CodeEntityノードを作成するクエリ
CREATE (codeentity:CodeEntity {
  persistent_id: $persistent_id, 
  name: $name, 
  type: $type, 
  signature: COALESCE($signature, ''),
  complexity: COALESCE($complexity, 0),
  start_position: COALESCE($start_position, 0),
  end_position: COALESCE($end_position, 0)
})
RETURN codeentity
