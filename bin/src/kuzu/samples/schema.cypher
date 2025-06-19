CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY);
CREATE NODE TABLE RequirementEntity (id STRING PRIMARY KEY, title STRING, priority STRING, requirement_type STRING, resource STRING);
CREATE NODE TABLE VersionState (id STRING PRIMARY KEY, timestamp STRING, description STRING, progress_percentage FLOAT);
CREATE REL TABLE TRACKS_STATE_OF_LOCATED_ENTITY (FROM VersionState TO LocationURI);
CREATE REL TABLE LOCATED_WITH_REQUIREMENT (FROM LocationURI TO RequirementEntity);
CREATE REL TABLE DEPENDS_ON (FROM RequirementEntity TO RequirementEntity, dependency_type STRING);
CREATE REL TABLE FOLLOWS (FROM VersionState TO VersionState);