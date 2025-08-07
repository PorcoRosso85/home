-- Migration: 004_rename_contains_and_reverse_locates.cypher
-- Purpose: Rename CONTAINS_LOCATION to CONTAINS and reverse LOCATES direction
-- Date: 2025-08-05

-- ========================================
-- Step 1: Create new CONTAINS relationship (rename from CONTAINS_LOCATION)
-- ========================================
CREATE REL TABLE CONTAINS (
    FROM LocationURI TO LocationURI
);

-- Migrate existing data
MATCH (from:LocationURI)-[r:CONTAINS_LOCATION]->(to:LocationURI)
CREATE (from)-[:CONTAINS]->(to);

-- ========================================
-- Step 2: Create new LOCATES with reversed direction
-- ========================================
CREATE REL TABLE LOCATES_NEW (
    FROM LocationURI TO ImplementationEntity,
    entity_type STRING,
    current BOOL
);

-- Migrate existing data with reversed direction
MATCH (uri:LocationURI)<-[r:LOCATES]-(impl:ImplementationEntity)
CREATE (uri)-[:LOCATES_NEW {
    entity_type: r.entity_type,
    current: r.current
}]->(impl);

-- ========================================
-- Step 3: Drop old relationships
-- ========================================
DROP TABLE CONTAINS_LOCATION;
DROP TABLE LOCATES;

-- ========================================
-- Step 4: Rename LOCATES_NEW to LOCATES
-- ========================================
-- Note: KuzuDB may not support direct rename, so we recreate
CREATE REL TABLE LOCATES (
    FROM LocationURI TO ImplementationEntity,
    entity_type STRING,
    current BOOL
);

MATCH (uri:LocationURI)-[r:LOCATES_NEW]->(impl:ImplementationEntity)
CREATE (uri)-[:LOCATES {
    entity_type: r.entity_type,
    current: r.current
}]->(impl);

DROP TABLE LOCATES_NEW;

-- ========================================
-- Verification queries (run manually)
-- ========================================
-- Check new relationships exist:
-- MATCH (uri:LocationURI)-[:CONTAINS]->(child:LocationURI) RETURN COUNT(*);
-- MATCH (uri:LocationURI)-[:LOCATES]->(impl:ImplementationEntity) RETURN COUNT(*);