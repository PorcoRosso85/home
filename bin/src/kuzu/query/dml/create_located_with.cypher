// LOCATED_WITH関係を作成するクエリ（LocationURI → CodeEntity）
MATCH (location:LocationURI {uri_id: $uri_id})
MATCH (code:CodeEntity {persistent_id: $code_persistent_id})
CREATE (location)-[:LOCATED_WITH {entity_type: $entity_type}]->(code)
RETURN location.uri_id as uri_id, code.persistent_id as code_id, $entity_type as entity_type
