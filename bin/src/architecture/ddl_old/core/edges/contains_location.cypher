// CONTAINS_LOCATION関係エッジ定義（階層関係）
// Based on: requirement/graph/ddl/migrations/3.4.0_search_integration.cypher

CREATE REL TABLE CONTAINS_LOCATION (
    FROM LocationURI TO LocationURI
);