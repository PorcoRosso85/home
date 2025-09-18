-- Migration: 001_unify_naming_ddl.cypher
-- Purpose: DDL part - Create new LocationURI table
-- Date: 2025-08-05

CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY
);