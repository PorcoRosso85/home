-- Migration: 001_unify_naming_v2.cypher
-- Purpose: Rename ImplementationURI to LocationURI using safer approach
-- Date: 2025-08-05
-- Note: This version uses ALTER TABLE if supported by KuzuDB

-- ========================================
-- Option A: If KuzuDB supports ALTER TABLE RENAME
-- ========================================
-- ALTER TABLE ImplementationURI RENAME TO LocationURI;

-- ========================================
-- Option B: If ALTER TABLE RENAME is not supported
-- Use the data migration approach from 001_unify_naming.cypher
-- ========================================

-- First, let's check what exists:
-- CALL show_tables() RETURN *;

-- Check if ALTER TABLE RENAME works:
-- This is a test that should be run manually first
-- CREATE NODE TABLE TestTable (id STRING PRIMARY KEY);
-- ALTER TABLE TestTable RENAME TO TestTableRenamed;
-- DROP TABLE TestTableRenamed;

-- ========================================
-- Safe execution steps:
-- ========================================
-- 1. Backup database: EXPORT DATABASE './backup_before_rename';
-- 2. Try ALTER TABLE RENAME first
-- 3. If that fails, use the full migration from 001_unify_naming.cypher
-- 4. Verify with queries at the end