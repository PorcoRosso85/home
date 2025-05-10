// CodeEntityノードを検索するクエリ
MATCH (codeentity:CodeEntity {persistent_id: $persistent_id})
RETURN codeentity