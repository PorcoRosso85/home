-- Rollback for Migration: 001_unify_naming.cypher
-- Purpose: Revert LocationURI back to ImplementationURI
-- Date: 2025-08-05

-- ========================================
-- Step 1: Create original ImplementationURI node table
-- ========================================
CREATE NODE TABLE ImplementationURI (
    id STRING PRIMARY KEY          -- e.g., "bin.src.auth.User.login"
);

-- ========================================
-- Step 2: Copy data from LocationURI to ImplementationURI
-- ========================================
MATCH (loc:LocationURI)
CREATE (uri:ImplementationURI {id: loc.id});

-- ========================================
-- Step 3: Recreate original edges
-- ========================================

-- 3.1: Restore LOCATES edges
MATCH (loc:LocationURI)-[r:LOCATES]->(entity:ImplementationEntity)
MATCH (uri:ImplementationURI {id: loc.id})
CREATE (uri)-[:LOCATES {entity_type: r.entity_type, current: r.current}]->(entity);

-- 3.2: Restore TRACKS_STATE_OF edges
MATCH (vs:VersionState)-[r:TRACKS_STATE_OF]->(loc:LocationURI)
MATCH (uri:ImplementationURI {id: loc.id})
CREATE (vs)-[:TRACKS_STATE_OF {entity_type: r.entity_type}]->(uri);

-- 3.3: Restore CONTAINS_LOCATION edges
MATCH (parentLoc:LocationURI)-[r:CONTAINS_LOCATION]->(childLoc:LocationURI)
MATCH (parent:ImplementationURI {id: parentLoc.id})
MATCH (child:ImplementationURI {id: childLoc.id})
CREATE (parent)-[:CONTAINS_LOCATION]->(child);

-- 3.4: Restore HAS_RESPONSIBILITY edges
MATCH (loc:LocationURI)-[r:HAS_RESPONSIBILITY]->(resp:Responsibility)
MATCH (uri:ImplementationURI {id: loc.id})
CREATE (uri)-[:HAS_RESPONSIBILITY]->(resp);

-- ========================================
-- Step 4: Drop edges from LocationURI
-- ========================================
MATCH (loc:LocationURI)-[r:LOCATES]->(entity:ImplementationEntity)
DELETE r;

MATCH (vs:VersionState)-[r:TRACKS_STATE_OF]->(loc:LocationURI)
DELETE r;

MATCH (parent:LocationURI)-[r:CONTAINS_LOCATION]->(child:LocationURI)
DELETE r;

MATCH (loc:LocationURI)-[r:HAS_RESPONSIBILITY]->(resp:Responsibility)
DELETE r;

-- ========================================
-- Step 5: Drop LocationURI node table
-- ========================================
DROP TABLE LocationURI CASCADE;

-- ========================================
-- Verification queries (run manually)
-- ========================================
-- Check node count:
-- MATCH (uri:ImplementationURI) RETURN count(uri) AS uri_count;
--
-- Check LOCATES relationships:
-- MATCH (uri:ImplementationURI)-[r:LOCATES]->(entity:ImplementationEntity) RETURN count(r) AS locates_count;
--
-- Check TRACKS_STATE_OF relationships:
-- MATCH (vs:VersionState)-[r:TRACKS_STATE_OF]->(uri:ImplementationURI) RETURN count(r) AS tracks_count;
--
-- Check CONTAINS_LOCATION relationships:
-- MATCH (parent:ImplementationURI)-[r:CONTAINS_LOCATION]->(child:ImplementationURI) RETURN count(r) AS contains_count;
--
-- Check HAS_RESPONSIBILITY relationships:
-- MATCH (uri:ImplementationURI)-[r:HAS_RESPONSIBILITY]->(resp:Responsibility) RETURN count(r) AS responsibility_count;