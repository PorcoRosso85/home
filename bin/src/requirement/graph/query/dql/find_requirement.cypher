// find_requirement.cypher
// 指定IDの要件を検索

MATCH (r:RequirementEntity {id: $id})
RETURN r.id, r.title, r.description, r.status