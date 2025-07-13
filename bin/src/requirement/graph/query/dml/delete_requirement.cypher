// delete_requirement.cypher  
// 要件とその関係の完全削除

MATCH (r:RequirementEntity {id: $id})
DETACH DELETE r