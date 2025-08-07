# Changelog for v3.0.0

Export Date: 2025-08-05 19:45:00

## Changes from v2.0.0

### Completed Migrations
- ✅ 001_unify_naming.cypher - 命名統一
- ✅ 002_add_requirement_entity.cypher - RequirementEntity追加
- ✅ 003_remove_responsibility.cypher - Responsibilityテーブル削除

### Partially Applied Migrations
- ⚠️ 004_rename_contains_and_reverse_locates.cypher
  - ❌ CONTAINS renaming failed
  - ❌ LOCATES reversal failed
  
- ⚠️ 005_reverse_implements_to_implemented_by.cypher
  - ✅ IMPLEMENTED_BY relationship created
  - ❌ Old IMPLEMENTS relationship may still exist

## Current State

### Tables Present
- LocationURI
- VersionState
- ImplementationEntity
- RequirementEntity

### Relationships Present
- DEPENDS_ON
- CONTAINS_LOCATION (should be CONTAINS)
- SIMILAR_TO
- TRACKS_STATE_OF

### Tables Removed
- Responsibility (removed in 003)
- HAS_RESPONSIBILITY (removed in 003)

## Migration Notes

Some migrations failed due to KuzuDB syntax differences. Manual intervention may be required to:
1. Rename CONTAINS_LOCATION to CONTAINS
2. Reverse LOCATES relationship direction
3. Ensure IMPLEMENTS is replaced by IMPLEMENTED_BY

## Next Steps

Consider creating fixed migration scripts or using KuzuDB's ALTER TABLE capabilities when available.