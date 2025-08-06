// TRACKS_STATE_OF関係エッジ定義
// Based on: requirement/graph/ddl/migrations/3.4.0_search_integration.cypher

CREATE REL TABLE TRACKS_STATE_OF (
    FROM VersionState TO LocationURI,
    entity_type STRING
);