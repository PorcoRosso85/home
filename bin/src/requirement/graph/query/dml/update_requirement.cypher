// update_requirement.cypher
// 要件の動的フィールド更新（パラメータ化）

MATCH (r:RequirementEntity {id: $id})
SET r += $updates
RETURN r