// DEPENDS_ON関係エッジ定義（依存関係）
// Based on: requirement/graph/ddl/migrations/3.4.0_search_integration.cypher

CREATE REL TABLE DEPENDS_ON (
    FROM RequirementEntity TO RequirementEntity,
    dependency_type STRING DEFAULT 'requires',
    reason STRING
);