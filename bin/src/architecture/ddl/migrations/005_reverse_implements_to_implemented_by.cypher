-- Migration: 005_reverse_implements_to_implemented_by.cypher
-- Purpose: Reverse IMPLEMENTS relationship to IMPLEMENTED_BY with RequirementEntity as source
-- Date: 2025-08-05

-- ========================================
-- Step 1: Create IMPLEMENTED_BY relationship
-- ========================================
CREATE REL TABLE IMPLEMENTED_BY (
    FROM RequirementEntity TO ImplementationEntity
);

-- ========================================
-- Step 2: Migrate existing IMPLEMENTS relationships
-- ========================================
-- Current: ImplementationEntity --IMPLEMENTS--> RequirementEntity
-- New:     RequirementEntity --IMPLEMENTED_BY--> ImplementationEntity

MATCH (impl:ImplementationEntity)-[r:IMPLEMENTS]->(req:RequirementEntity)
CREATE (req)-[:IMPLEMENTED_BY]->(impl);

-- ========================================
-- Step 3: Drop old IMPLEMENTS relationship
-- ========================================
MATCH ()-[r:IMPLEMENTS]->()
DELETE r;

DROP TABLE IMPLEMENTS;

-- ========================================
-- Verification queries (run manually)
-- ========================================
-- Check new relationship:
-- MATCH (req:RequirementEntity)-[:IMPLEMENTED_BY]->(impl:ImplementationEntity) 
-- RETURN req.id, req.title, impl.id, impl.type
-- LIMIT 10;
--
-- Ensure no IMPLEMENTS relationships remain:
-- MATCH ()-[r:IMPLEMENTS]->() RETURN COUNT(r); -- Should return 0