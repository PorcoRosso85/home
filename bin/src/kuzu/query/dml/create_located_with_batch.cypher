// LOCATED_WITH系関係の一括作成DML（複数のエンティティタイプを一度に処理）
// 入力形式: {uri_id: string, entities: [{type: 'code'|'requirement'|'reference', id: string, entity_type: string}]}

WITH $location_entities AS data
UNWIND data AS location_data
MATCH (location:LocationURI {uri_id: location_data.uri_id})

// CodeEntityとの関係を作成
FOREACH (entity IN [e IN location_data.entities WHERE e.type = 'code'] |
  FOREACH (code IN (MATCH (c:CodeEntity {persistent_id: entity.id}) RETURN c) |
    CREATE (location)-[:LOCATED_WITH {entity_type: entity.entity_type}]->(code)
  )
)

// RequirementEntityとの関係を作成
FOREACH (entity IN [e IN location_data.entities WHERE e.type = 'requirement'] |
  FOREACH (req IN (MATCH (r:RequirementEntity {id: entity.id}) RETURN r) |
    CREATE (location)-[:LOCATED_WITH_REQUIREMENT {entity_type: entity.entity_type}]->(req)
  )
)

// ReferenceEntityとの関係を作成
FOREACH (entity IN [e IN location_data.entities WHERE e.type = 'reference'] |
  FOREACH (ref IN (MATCH (r:ReferenceEntity {id: entity.id}) RETURN r) |
    CREATE (location)-[:LOCATED_WITH_REFERENCE {entity_type: entity.entity_type}]->(ref)
  )
)

RETURN location.uri_id as uri_id,
       size([e IN location_data.entities WHERE e.type = 'code']) as code_relations,
       size([e IN location_data.entities WHERE e.type = 'requirement']) as requirement_relations,
       size([e IN location_data.entities WHERE e.type = 'reference']) as reference_relations
