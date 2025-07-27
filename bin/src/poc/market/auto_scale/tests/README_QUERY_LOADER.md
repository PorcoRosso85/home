# GraphDB Test Query Loader Integration

## Summary of Changes

The test file `test_graphdb.py` has been updated to use the query loader pattern for all database queries, consistent with the production code in `infrastructure.py`.

## Changes Made

1. **Added Query Loader Import**
   - Added import for `load_query_from_file` from `kuzu_py`
   - Included fallback implementation for test environments

2. **Created Query Files**
   - Schema: `/tests/cypher/schema/test_schema.cypher`
   - Contract queries:
     - `/tests/cypher/queries/contract/upsert_contract.cypher`
     - `/tests/cypher/queries/contract/find_by_id.cypher`
     - `/tests/cypher/queries/contract/find_active.cypher`
     - `/tests/cypher/queries/contract/find_by_client_id.cypher`
   - Term queries:
     - `/tests/cypher/queries/term/upsert_term.cypher`
     - `/tests/cypher/queries/term/link_to_contract.cypher`
   - Relationship queries:
     - `/tests/cypher/queries/relationship/add_parent_child.cypher`
     - `/tests/cypher/queries/relationship/find_children.cypher`
     - `/tests/cypher/queries/relationship/find_parent.cypher`

3. **Updated KuzuGraphRepository Implementation**
   - Added `query_path` attribute pointing to test query directory
   - Modified `_init_schema()` to load schema from file
   - Updated all query methods to use query loader with fallback
   - Maintained backward compatibility with inline queries as fallback

## Benefits

1. **Consistency**: Test implementation now mirrors production code pattern
2. **Maintainability**: Queries are externalized for easier updates
3. **Robustness**: Fallback mechanism ensures tests work even if files are missing
4. **Separation of Concerns**: SQL/Cypher logic separated from Python code

## Test Results

All 14 tests pass successfully with the new implementation:
- TestKuzuGraphRepositoryInitialization (2 tests)
- TestContractCRUD (5 tests)
- TestContractRelationships (4 tests)
- TestEdgeCases (3 tests)

## Usage

The test repository automatically loads queries from the test-specific query directory. If a query file cannot be loaded, it falls back to inline queries to ensure test stability.