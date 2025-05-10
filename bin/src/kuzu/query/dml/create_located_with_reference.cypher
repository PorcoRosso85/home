// LOCATED_WITH_REFERENCE関係を作成するクエリ（LocationURI → ReferenceEntity）
MATCH (location:LocationURI {uri_id: $uri_id})
MATCH (reference:ReferenceEntity {id: $reference_id})
CREATE (location)-[:LOCATED_WITH_REFERENCE {entity_type: $entity_type}]->(reference)
RETURN location.uri_id as uri_id, reference.id as reference_id, $entity_type as entity_type
