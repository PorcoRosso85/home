-- Migration: 001_unify_naming.cypher
-- Purpose: Unify naming convention with requirement/graph by renaming ImplementationURI to LocationURI
-- Date: 2025-08-05

-- ========================================
-- Step 1: Create new LocationURI node table
-- ========================================
CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY          -- e.g., "bin.src.auth.User.login"
);

-- ========================================
-- Step 2: Copy data from ImplementationURI to LocationURI
-- ========================================
MATCH (uri:ImplementationURI)
CREATE (loc:LocationURI {id: uri.id});

-- ========================================
-- Step 3: Recreate edges with new table
-- ========================================

-- 3.1: Create new LOCATES edges pointing to LocationURI
MATCH (uri:ImplementationURI)-[r:LOCATES]->(entity:ImplementationEntity)
MATCH (loc:LocationURI {id: uri.id})
CREATE (loc)-[:LOCATES {entity_type: r.entity_type, current: r.current}]->(entity);

-- 3.2: Create new TRACKS_STATE_OF edges pointing to LocationURI
MATCH (vs:VersionState)-[r:TRACKS_STATE_OF]->(uri:ImplementationURI)
MATCH (loc:LocationURI {id: uri.id})
CREATE (vs)-[:TRACKS_STATE_OF {entity_type: r.entity_type}]->(loc);

-- 3.3: Create new CONTAINS_LOCATION edges for parent-child relationships
MATCH (parent:ImplementationURI)-[r:CONTAINS_LOCATION]->(child:ImplementationURI)
MATCH (parentLoc:LocationURI {id: parent.id})
MATCH (childLoc:LocationURI {id: child.id})
CREATE (parentLoc)-[:CONTAINS_LOCATION]->(childLoc);

-- 3.4: Create new HAS_RESPONSIBILITY edges
MATCH (uri:ImplementationURI)-[r:HAS_RESPONSIBILITY]->(resp:Responsibility)
MATCH (loc:LocationURI {id: uri.id})
CREATE (loc)-[:HAS_RESPONSIBILITY]->(resp);

-- ========================================
-- Step 4: Drop old edges
-- ========================================
MATCH (uri:ImplementationURI)-[r:LOCATES]->(entity:ImplementationEntity)
DELETE r;

MATCH (vs:VersionState)-[r:TRACKS_STATE_OF]->(uri:ImplementationURI)
DELETE r;

MATCH (parent:ImplementationURI)-[r:CONTAINS_LOCATION]->(child:ImplementationURI)
DELETE r;

MATCH (uri:ImplementationURI)-[r:HAS_RESPONSIBILITY]->(resp:Responsibility)
DELETE r;

-- ========================================
-- Step 5: Drop old ImplementationURI node table
-- ========================================
DROP TABLE ImplementationURI CASCADE;

-- ========================================
-- Verification queries (run manually)
-- ========================================
-- Check node count:
-- MATCH (loc:LocationURI) RETURN count(loc) AS location_count;
--
-- Check LOCATES relationships:
-- MATCH (loc:LocationURI)-[r:LOCATES]->(entity:ImplementationEntity) RETURN count(r) AS locates_count;
--
-- Check TRACKS_STATE_OF relationships:
-- MATCH (vs:VersionState)-[r:TRACKS_STATE_OF]->(loc:LocationURI) RETURN count(r) AS tracks_count;
--
-- Check CONTAINS_LOCATION relationships:
-- MATCH (parent:LocationURI)-[r:CONTAINS_LOCATION]->(child:LocationURI) RETURN count(r) AS contains_count;
--
-- Check HAS_RESPONSIBILITY relationships:
-- MATCH (loc:LocationURI)-[r:HAS_RESPONSIBILITY]->(resp:Responsibility) RETURN count(r) AS responsibility_count;