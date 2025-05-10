// CodeEntityノードを作成するクエリ
CREATE (codeentity:CodeEntity {persistent_id: $persistent_id, name: $name, type: $type, signature: $signature, complexity: $complexity, start_position: $start_position, end_position: $end_position})
RETURN codeentity
