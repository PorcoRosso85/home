// LOCATED_WITH_REQUIREMENT関係を作成するクエリ（LocationURI → RequirementEntity）
MATCH (location:LocationURI {id: $id})
MATCH (requirement:RequirementEntity {id: $requirement_id})
CREATE (location)-[:LOCATED_WITH_REQUIREMENT {entity_type: $entity_type}]->(requirement)
RETURN location.id as id, requirement.id as requirement_id, $entity_type as entity_type
