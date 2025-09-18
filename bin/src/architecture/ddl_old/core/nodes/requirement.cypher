// 要件エンティティノード定義
// Based on: requirement/graph/ddl/migrations/3.4.0_search_integration.cypher

CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,
    title STRING,
    description STRING,            -- メインコンテンツフィールド（search serviceで使用）
    embedding DOUBLE[256],         -- search service必須フィールド
    status STRING DEFAULT 'proposed'
);