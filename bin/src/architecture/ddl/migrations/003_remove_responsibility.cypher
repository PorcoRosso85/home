-- Migration: 003_remove_responsibility.cypher
-- Purpose: Remove Responsibility table and HAS_RESPONSIBILITY relationship
-- Date: 2025-08-06

-- ========================================
-- Step 1: Delete all HAS_RESPONSIBILITY relationships
-- ========================================
MATCH ()-[r:HAS_RESPONSIBILITY]->()
DELETE r;

-- ========================================
-- Step 2: Drop HAS_RESPONSIBILITY relationship table
-- ========================================
DROP TABLE HAS_RESPONSIBILITY CASCADE;

-- ========================================
-- Step 3: Drop Responsibility node table
-- ========================================
DROP TABLE Responsibility CASCADE;

-- ========================================
-- Verification queries (run manually)
-- ========================================
-- Check that Responsibility table no longer exists:
-- CALL show_tables() RETURN * WHERE name = 'Responsibility';
--
-- Check that HAS_RESPONSIBILITY relationship no longer exists:
-- CALL show_tables() RETURN * WHERE name = 'HAS_RESPONSIBILITY';