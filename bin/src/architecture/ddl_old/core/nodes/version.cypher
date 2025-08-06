// バージョン状態ノード定義
// Based on: requirement/graph/ddl/migrations/3.4.0_search_integration.cypher

CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    operation STRING DEFAULT 'UPDATE',
    author STRING DEFAULT 'system'
);