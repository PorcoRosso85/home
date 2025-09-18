// CodeEntityノードを更新するクエリ
MATCH (codeentity:CodeEntity {persistent_id: $persistent_id})
SET codeentity.name = $name,
    codeentity.type = $type,
    codeentity.signature = $signature,
    codeentity.complexity = $complexity,
    codeentity.start_position = $start_position,
    codeentity.end_position = $end_position
RETURN codeentity