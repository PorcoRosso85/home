-- ノードテーブル
CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY
);

CREATE NODE TABLE App (
    id STRING PRIMARY KEY
);

CREATE NODE TABLE Schema (
    id STRING PRIMARY KEY,
    schema_content STRING,
    version STRING DEFAULT '1.0'
);

CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    operation STRING DEFAULT 'UPDATE',
    author STRING DEFAULT 'system'
);

-- エッジテーブル
CREATE REL TABLE LOCATES (
    FROM LocationURI TO App,
    entity_type STRING DEFAULT 'app',
    current BOOLEAN DEFAULT true
);

CREATE REL TABLE PROVIDES (
    FROM App TO Schema,
    schema_role STRING,      -- 'input' or 'output'
    active BOOLEAN DEFAULT true,
    since_timestamp STRING
);

CREATE REL TABLE EXPECTS (
    FROM App TO Schema,
    schema_role STRING,      -- 'input' or 'output'
    active BOOLEAN DEFAULT true,
    since_timestamp STRING
);

CREATE REL TABLE CAN_COMMUNICATE_WITH (
    FROM App TO App,
    transform_rules STRING,
    compatibility_score DOUBLE DEFAULT 1.0
);

CREATE REL TABLE TRACKS_STATE_OF (
    FROM VersionState TO LocationURI,
    entity_type STRING DEFAULT 'app'
);

CREATE REL TABLE CONTAINS_LOCATION (
    FROM LocationURI TO LocationURI
);