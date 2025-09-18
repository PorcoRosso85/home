// LOCATES関係エッジ定義
// Based on: requirement/graph/ddl/migrations/3.4.0_search_integration.cypher

CREATE REL TABLE LOCATES (
    FROM LocationURI TO RequirementEntity,
    entity_type STRING DEFAULT 'requirement',
    current BOOLEAN DEFAULT false
);