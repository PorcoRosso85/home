CREATE NODE TABLE ImplementationEntity (
    id STRING PRIMARY KEY,
    type STRING,
    signature STRING,
    embedding DOUBLE[256],
    status STRING DEFAULT 'active'
);

CREATE NODE TABLE ImplementationURI (
    id STRING PRIMARY KEY
);

CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    operation STRING DEFAULT 'UPDATE',
    author STRING DEFAULT 'system'
);

CREATE NODE TABLE Responsibility (
    id STRING PRIMARY KEY,
    name STRING,
    description STRING,
    category STRING
);

CREATE REL TABLE LOCATES (
    FROM ImplementationURI TO ImplementationEntity,
    entity_type STRING DEFAULT 'implementation',
    current BOOLEAN DEFAULT false
);

CREATE REL TABLE TRACKS_STATE_OF (
    FROM VersionState TO ImplementationURI,
    entity_type STRING
);

CREATE REL TABLE CONTAINS_LOCATION (
    FROM ImplementationURI TO ImplementationURI
);

CREATE REL TABLE DEPENDS_ON (
    FROM ImplementationEntity TO ImplementationEntity,
    dependency_type STRING DEFAULT 'calls',
    reason STRING
);

CREATE REL TABLE HAS_RESPONSIBILITY (
    FROM ImplementationURI TO Responsibility
);

CREATE REL TABLE SIMILAR_TO (
    FROM ImplementationEntity TO ImplementationEntity,
    similarity_score DOUBLE,
    similarity_type STRING
);