// create_requirement.cypher
// 要件エンティティの作成（重複チェック機能付き）

CREATE (r:RequirementEntity {
    id: $id,
    title: $title,
    description: $description,
    status: $status,
    embedding: NULL
})
RETURN r