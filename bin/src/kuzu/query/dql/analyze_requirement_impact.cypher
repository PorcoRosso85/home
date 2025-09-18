// 要件変更の影響分析
// 特定要件の変更が影響する範囲を分析
MATCH (source:RequirementEntity {id: $requirementId})
OPTIONAL MATCH (source)<-[:DEPENDS_ON]-(dependent:RequirementEntity)
OPTIONAL MATCH (source)-[:IS_IMPLEMENTED_BY]->(impl:CodeEntity)
OPTIONAL MATCH (impl)<-[:IMPORTS]-(importer:CodeEntity)
OPTIONAL MATCH (dependent)-[:IS_IMPLEMENTED_BY]->(depImpl:CodeEntity)
RETURN source.id as requirement_id,
       collect(DISTINCT dependent.id) as dependent_requirements,
       count(DISTINCT dependent) as dependent_count,
       collect(DISTINCT impl.name) as implementations,
       collect(DISTINCT importer.name) as affected_code,
       collect(DISTINCT depImpl.name) as dependent_implementations;