-- Rollback for Migration: 002_add_requirement_entity.cypher
-- Purpose: Remove RequirementEntity node table and IMPLEMENTS relationships
-- Date: 2025-08-06

-- ========================================
-- Step 1: Drop IMPLEMENTS relationship table
-- ========================================
MATCH (loc:LocationURI)-[r:IMPLEMENTS]->(req:RequirementEntity)
DELETE r;

-- ========================================
-- Step 2: Drop RequirementEntity node table
-- ========================================
DROP TABLE RequirementEntity CASCADE;

-- ========================================
-- Verification queries (run manually)
-- ========================================
-- Check that RequirementEntity no longer exists:
-- MATCH (req:RequirementEntity) RETURN count(req) AS req_count;
--
-- Check that IMPLEMENTS relationships no longer exist:
-- MATCH ()-[r:IMPLEMENTS]->() RETURN count(r) AS implements_count;