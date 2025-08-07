-- Snapshot v3.0.0 Schema
-- Date: 2025-08-05
-- After migrations: 001, 002, 003, 004 (partial), 005 (partial)

-- Node Tables (from current state)
CREATE NODE TABLE `LocationURI` (`id` STRING, PRIMARY KEY(`id`));
CREATE NODE TABLE `VersionState` (`id` STRING,`timestamp` STRING,`description` STRING,`change_reason` STRING,`operation` STRING,`author` STRING, PRIMARY KEY(`id`));
CREATE NODE TABLE `ImplementationEntity` (`id` STRING,`type` STRING,`signature` STRING,`embedding` DOUBLE[256],`status` STRING, PRIMARY KEY(`id`));
CREATE NODE TABLE `RequirementEntity` (`id` STRING,`title` STRING,`description` STRING,`embedding` DOUBLE[256],`status` STRING, PRIMARY KEY(`id`));

-- Relationship Tables (current state)
CREATE REL TABLE `DEPENDS_ON` (FROM `ImplementationEntity` TO `ImplementationEntity`, `dependency_type` STRING,`reason` STRING, MANY_MANY);
CREATE REL TABLE `CONTAINS_LOCATION` (FROM `LocationURI` TO `LocationURI`, MANY_MANY);
CREATE REL TABLE `SIMILAR_TO` (FROM `ImplementationEntity` TO `ImplementationEntity`, `similarity_score` DOUBLE,`similarity_type` STRING, MANY_MANY);
CREATE REL TABLE `TRACKS_STATE_OF` (FROM `VersionState` TO `LocationURI`, `entity_type` STRING, MANY_MANY);

-- Note: The following relationships were attempted but may not exist due to migration failures:
-- CONTAINS (renamed from CONTAINS_LOCATION) - migration 004 failed
-- LOCATES (reversed direction) - migration 004 failed  
-- IMPLEMENTED_BY (reversed from IMPLEMENTS) - migration 005 partially succeeded

-- Responsibility table was removed in migration 003