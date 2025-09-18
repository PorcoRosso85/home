-- Migration: 002_add_requirement_entity.cypher
-- Purpose: Add RequirementEntity node table and IMPLEMENTS relationship to connect implementations to requirements
-- Date: 2025-08-06

-- ========================================
-- Step 1: Create RequirementEntity node table
-- ========================================
CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,          -- Unique identifier for the requirement
    title STRING,                   -- Human-readable title of the requirement
    description STRING,             -- Detailed description of what needs to be implemented
    embedding DOUBLE[256],          -- Vector embedding for semantic search
    status STRING DEFAULT 'proposed' -- Status of the requirement (proposed, approved, implemented, deprecated)
);

-- ========================================
-- Step 2: Create IMPLEMENTS relationship table
-- ========================================
CREATE REL TABLE IMPLEMENTS (
    FROM ImplementationEntity TO RequirementEntity
);

-- ========================================
-- Verification queries (run manually)
-- ========================================
-- Check RequirementEntity table creation:
-- MATCH (req:RequirementEntity) RETURN count(req) AS requirement_count;
--
-- Check IMPLEMENTS relationship creation:
-- MATCH (impl:ImplementationEntity)-[r:IMPLEMENTS]->(req:RequirementEntity) RETURN count(r) AS implements_count;
--
-- Verify status default value:
-- CREATE (req:RequirementEntity {id: 'test_req', title: 'Test', description: 'Test requirement'});
-- MATCH (req:RequirementEntity {id: 'test_req'}) RETURN req.status;
-- DELETE (req:RequirementEntity {id: 'test_req'});