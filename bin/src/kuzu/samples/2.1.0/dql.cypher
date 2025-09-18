MATCH (req:RequirementEntity)-[:DEPENDS_ON]->(dep:RequirementEntity)
WHERE NOT EXISTS {
  MATCH ()-[:TRACKS_STATE_OF_LOCATED_ENTITY]->()-[:LOCATED_WITH_REQUIREMENT]->(dep)
}
RETURN req.title as requirement, dep.title as missing_dependency, dep.requirement_type as type
ORDER BY dep.requirement_type, req.title;