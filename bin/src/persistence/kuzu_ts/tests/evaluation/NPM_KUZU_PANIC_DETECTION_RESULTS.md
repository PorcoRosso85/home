# npm:kuzu Direct Test - Panic Detection Results

## Test Summary

The test file `npm_kuzu_direct.test.ts` was created to test npm:kuzu directly for panic detection. The test successfully identified a panic issue in the npm:kuzu package when used with Deno.

## Test Structure

1. **Basic Operations Test**: Tests fundamental database operations
   - In-memory database creation
   - Connection establishment
   - CREATE NODE TABLE query
   - Data insertion
   - MATCH query with ORDER BY
   - Result retrieval and verification
   - Proper resource cleanup

2. **Edge Case Handling Test**: Tests more complex scenarios
   - Query on non-existent table
   - Complex queries with relationships
   - Multiple table operations

## Results

### Successful Operations (Before Panic)
- ✅ Database creation
- ✅ Connection creation
- ✅ CREATE NODE TABLE execution
- ✅ Data insertion (CREATE nodes)
- ✅ MATCH query execution
- ✅ Result retrieval with proper data structure
- ✅ Resource cleanup (connection and database close)

### Panic Details
- **Error Type**: Deno panic (Fatal error)
- **Error Message**: `Check failed: heap->isolate() == Isolate::TryGetCurrent()`
- **Trigger Point**: During the edge case handling test, specifically when working with relationship queries
- **Platform**: linux x86_64
- **Deno Version**: 2.4.0

### Key Findings

1. **Async/Await Required**: The `getAll()` method returns a Promise and must be awaited
2. **Data Structure**: Query results are returned as an array of objects with column names as keys (e.g., `{ "p.name": "Bob", "p.age": 25 }`)
3. **Basic Operations Work**: Simple CREATE and MATCH queries function correctly
4. **Complex Operations Trigger Panic**: The panic occurs when dealing with more complex relationship queries

## Conclusion

The test successfully detected a panic issue in npm:kuzu when used with Deno. The panic appears to be related to V8 isolate handling and occurs during more complex database operations involving relationships. This confirms that there are stability issues with the direct npm:kuzu package in the Deno environment.

## Test Execution Command

```bash
nix develop -c deno test tests/evaluation/npm_kuzu_direct.test.ts --allow-read --allow-write --allow-ffi --unstable-ffi --no-check
```