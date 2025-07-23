// create_requirement.cypher
// 要件エンティティの作成（重複チェック機能付き）
// 注: embeddingはNULL可能。VSS統合時に後から更新される

CREATE (r:RequirementEntity {
    id: $id,
    title: $title,
    description: $description,
    status: $status
})
RETURN r