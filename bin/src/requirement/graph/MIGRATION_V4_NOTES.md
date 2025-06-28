# Migration to v4: Removing RequirementSnapshot

## Summary of Changes

This migration removes the `RequirementSnapshot` entity and simplifies version tracking by storing the status directly in `RequirementEntity` and using `VersionState` for historical tracking.

## Schema Changes

### 1. RequirementEntity
- **Added**: `status` field with default value 'proposed'
- Now tracks the current state of requirements directly

### 2. VersionState  
- **Added**: `operation` field (CREATE, UPDATE, DELETE)
- **Added**: `author` field
- **Added**: `changed_fields` field (JSON format)
- Now tracks what changed in each version

### 3. Removed
- `RequirementSnapshot` entity completely removed
- `HAS_SNAPSHOT` relationship removed
- `SNAPSHOT_OF_VERSION` relationship removed

## Code Changes

### 1. domain/version_tracking.py
- **Removed**: `create_requirement_snapshot()` function
- **Updated**: `calculate_requirement_diff()` to work with requirements instead of snapshots

### 2. infrastructure/kuzu_repository.py
- **Updated**: `save()` function to:
  - Store status directly in RequirementEntity
  - Track changes in VersionState.changed_fields
  - Use HAS_VERSION relationship instead of snapshots
- **Updated**: `get_requirement_history()` to query versions directly
- **Updated**: `get_requirement_at_version()` to return current requirement state

### 3. application/version_service.py
- **Updated**: All functions to work without snapshots
- **Updated**: History tracking to use VersionState directly
- **Updated**: Version diff calculation to compare requirement states

### 4. infrastructure/query_validator.py
- **Removed**: RequirementSnapshot from allowed labels
- **Updated**: Allowed relationships to match new schema

## Migration Steps

1. **Update Schema**: Run the updated schema.cypher to add new fields
2. **Migrate Data**: 
   - Copy status from latest snapshot to RequirementEntity
   - Convert snapshot data to VersionState fields
3. **Remove Old Data**: Delete all RequirementSnapshot nodes and relationships
4. **Update Code**: Deploy the updated code

## Benefits

1. **Simpler Model**: One less entity to manage
2. **Better Performance**: Fewer nodes and relationships to traverse
3. **Clearer Semantics**: Current state in entity, history in versions
4. **Easier Queries**: Direct access to current status without snapshots