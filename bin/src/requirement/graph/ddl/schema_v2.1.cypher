// 更新されたスキーマ定義 (v2.1) - 階層情報を追加
// RequirementEntityにhierarchy関連プロパティを追加

// ノードテーブル（エンティティ）
CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,
    title STRING NOT NULL,
    description STRING,
    priority STRING DEFAULT 'medium',
    requirement_type STRING DEFAULT 'functional',
    verification_required BOOLEAN DEFAULT true,
    status STRING DEFAULT 'draft',
    embedding DOUBLE[50],
    created_at STRING,
    // 新規追加：階層関連プロパティ
    hierarchy_level INT32,
    hierarchy_name STRING,
    estimated_hierarchy_type STRING
);

CREATE NODE TABLE CodeEntity (
    persistent_id STRING PRIMARY KEY,
    name STRING NOT NULL,
    type STRING NOT NULL,
    signature STRING,
    complexity INT32 DEFAULT 0,
    start_position INT32,
    end_position INT32
);

CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY
);

CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING NOT NULL,
    description STRING,
    change_reason STRING,
    progress_percentage DOUBLE DEFAULT 0.0
);

CREATE NODE TABLE ReferenceEntity (
    id STRING PRIMARY KEY,
    description STRING,
    type STRING NOT NULL,
    source_type STRING DEFAULT 'documentation'
);

// エッジテーブル（関係）
CREATE REL TABLE LOCATES_LocationURI_RequirementEntity (
    FROM LocationURI TO RequirementEntity
);

CREATE REL TABLE LOCATES_LocationURI_CodeEntity (
    FROM LocationURI TO CodeEntity
);

CREATE REL TABLE IS_IMPLEMENTED_BY (
    FROM RequirementEntity TO CodeEntity,
    confidence_score DOUBLE DEFAULT 1.0
);

CREATE REL TABLE IS_VERIFIED_BY (
    FROM RequirementEntity TO CodeEntity,
    test_coverage DOUBLE DEFAULT 0.0
);

CREATE REL TABLE DEPENDS_ON (
    FROM RequirementEntity TO RequirementEntity,
    dependency_type STRING DEFAULT 'requires',
    reason STRING
);

CREATE REL TABLE HAS_VERSION (
    FROM RequirementEntity TO VersionState
);

CREATE REL TABLE HAS_VERSION_CodeEntity (
    FROM CodeEntity TO VersionState
);

CREATE REL TABLE CONTAINS_LOCATION (
    FROM LocationURI TO LocationURI
);

CREATE REL TABLE REFERENCES (
    FROM RequirementEntity TO ReferenceEntity,
    relevance_score DOUBLE DEFAULT 1.0
);

CREATE REL TABLE CONFLICTS_WITH (
    FROM RequirementEntity TO RequirementEntity,
    conflict_reason STRING
);

CREATE REL TABLE SIMILAR_TO (
    FROM RequirementEntity TO RequirementEntity,
    similarity_score DOUBLE
);

CREATE REL TABLE EXTRACTED_FROM (
    FROM RequirementEntity TO ReferenceEntity,
    extraction_confidence DOUBLE DEFAULT 1.0
);

// インデックス（オプション - KuzuDBが自動的に主キーにインデックスを作成）
// CREATE INDEX req_title_idx ON RequirementEntity(title);
// CREATE INDEX req_priority_idx ON RequirementEntity(priority);
// CREATE INDEX req_type_idx ON RequirementEntity(requirement_type);
// CREATE INDEX req_hierarchy_idx ON RequirementEntity(hierarchy_level);
// CREATE INDEX code_name_idx ON CodeEntity(name);
// CREATE INDEX code_type_idx ON CodeEntity(type);
