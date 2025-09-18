-- Rollback Migration: 003_remove_responsibility_rollback.cypher
-- Purpose: Restore Responsibility table and HAS_RESPONSIBILITY relationship
-- Date: 2025-08-06

-- ========================================
-- Step 1: Recreate Responsibility node table
-- ========================================
CREATE NODE TABLE Responsibility (
    id STRING PRIMARY KEY,
    name STRING,
    description STRING,
    category STRING
);

-- ========================================
-- Step 2: Recreate HAS_RESPONSIBILITY relationship table
-- ========================================
CREATE REL TABLE HAS_RESPONSIBILITY (
    FROM LocationURI TO Responsibility
);

-- ========================================
-- Note: Data restoration would require a backup
-- ========================================
-- This rollback only recreates the schema structure.
-- Any data that existed in these tables before deletion
-- would need to be restored from a backup.