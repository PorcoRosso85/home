// LOCATED_WITH関係を作成するクエリ（LocationURI → CodeEntity）
// REFACTORED: uri_id -> id に変更
MATCH (location:LocationURI {id: $id})
MATCH (code:CodeEntity {persistent_id: $code_persistent_id})
CREATE (location)-[:LOCATED_WITH {entity_type: $entity_type}]->(code)
RETURN location.id as id, code.persistent_id as code_id, $entity_type as entity_type
