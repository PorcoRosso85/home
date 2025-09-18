// list_requirements.cypher
// 要件一覧取得（件数制限付き）

MATCH (r:RequirementEntity)
RETURN r
LIMIT $limit