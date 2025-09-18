CREATE NODE TABLE LocationURI (
  id STRING PRIMARY KEY
);
CREATE NODE TABLE CodeEntity (
  persistent_id STRING PRIMARY KEY,
  name STRING,
  type STRING,
  signature STRING,
  complexity INT64,
  start_position INT64,
  end_position INT64
);
CREATE NODE TABLE RequirementEntity (
  id STRING PRIMARY KEY,
  title STRING,
  description STRING,
  priority STRING,
  requirement_type STRING,
  verification_required BOOLEAN DEFAULT true
);
CREATE NODE TABLE VersionState (
  id STRING PRIMARY KEY,
  timestamp STRING,
  description STRING,
  change_reason STRING,
  progress_percentage FLOAT
);
CREATE NODE TABLE ReferenceEntity (
  id STRING PRIMARY KEY,
  description STRING,
  // DEPRECATED: uriプロパティとurlプロパティは使用禁止となりました
  // uri STRING, -- 削除
  type STRING,
  source_type STRING
);
CREATE NODE TABLE EntityAggregationView (
  id STRING PRIMARY KEY,
  view_type STRING
);
CREATE REL TABLE LOCATED_WITH (
  FROM LocationURI TO CodeEntity,
  entity_type STRING
);
CREATE REL TABLE LOCATED_WITH_REQUIREMENT (
  FROM LocationURI TO RequirementEntity,
  entity_type STRING
);
CREATE REL TABLE LOCATED_WITH_REFERENCE (
  FROM LocationURI TO ReferenceEntity,
  entity_type STRING
);
CREATE REL TABLE IS_IMPLEMENTED_BY (
  FROM RequirementEntity TO CodeEntity,
  implementation_type STRING
);
CREATE REL TABLE IS_VERIFIED_BY (
  FROM RequirementEntity TO CodeEntity,
  test_type STRING -- 'unit' | 'integration' | 'e2e'
);
CREATE REL TABLE DEPENDS_ON (
  FROM RequirementEntity TO RequirementEntity,
  dependency_type STRING
);
CREATE REL TABLE REFERENCES_CODE (
  FROM CodeEntity TO CodeEntity,
  ref_type STRING
);
CREATE REL TABLE REFERS_TO (
  FROM CodeEntity TO ReferenceEntity,
  ref_type STRING
);
CREATE REL TABLE TESTS (
  FROM CodeEntity TO CodeEntity,
  test_type STRING -- 'unit' | 'integration' | 'e2e'
);
CREATE REL TABLE CONTAINS_LOCATION (
  FROM LocationURI TO LocationURI,
  relation_type STRING
);
CREATE REL TABLE CONTAINS_CODE (
  FROM CodeEntity TO CodeEntity
);
CREATE REL TABLE FOLLOWS (
  FROM VersionState TO VersionState
);
CREATE REL TABLE TRACKS_STATE_OF_LOCATED_ENTITY (
  FROM VersionState TO LocationURI
);
CREATE REL TABLE USES (
  FROM EntityAggregationView TO LocationURI
);
CREATE REL TABLE AGGREGATES_REQ (
  FROM EntityAggregationView TO RequirementEntity,
  aggregation_method STRING
);
CREATE REL TABLE AGGREGATES_CODE (
  FROM EntityAggregationView TO CodeEntity,
  aggregation_method STRING
);
