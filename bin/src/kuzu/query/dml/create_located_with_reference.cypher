// LOCATED_WITH_REFERENCE関係を作成するクエリ（LocationURI → ReferenceEntity）
MATCH (location:LocationURI {id: $id})
MATCH (reference:ReferenceEntity {id: $reference_id})
CREATE (location)-[:LOCATED_WITH_REFERENCE {entity_type: $entity_type}]->(reference)
RETURN location.id as id, reference.id as reference_id, $entity_type as entity_type
