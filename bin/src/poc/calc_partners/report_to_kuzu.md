# Kuzu WASM 0.7.0 API Documentation Discrepancy Report

## Executive Summary

There is a significant discrepancy between the official API documentation and the actual implementation of Kuzu WASM 0.7.0. The API documentation describes methods that don't exist in the actual implementation, while the most commonly used API pattern (`result.table.toString()`) is not documented at all.

## Package Information

- **NPM Package**: @kuzu/kuzu-wasm (official)
- **GitHub Repository**: unswdb/kuzu-wasm 
- **Relationship**: The NPM package @kuzu/kuzu-wasm is built from and maintained at the GitHub repository unswdb/kuzu-wasm
- **Version**: 0.7.0
- **Environment**: Browser (Vite + React)
- **Test Date**: 2025-08-19

## Issue Details

### 1. Missing `table` Property in Documentation

The most critical issue is that the `table` property, which is the primary way to access query results, is not documented in either the async or sync API documentation.

**NPM README Example** (works correctly):
```javascript
const res = await conn.execute(`MATCH (a:User) RETURN a.*;`)
const res_json = JSON.parse(res.table.toString());
```

**API Documentation**: No mention of `table` property in QueryResult class.

### 2. Non-existent Methods in Implementation

The API documentation describes several methods that don't exist in the actual implementation:

| Method | Documentation Status | Actual Implementation |
|--------|---------------------|----------------------|
| `result.getAllObjects()` | ✅ Documented | ❌ Does not exist |
| `result.getAllRows()` | ✅ Documented | ❌ Does not exist |
| `result.getColumnNames()` | ✅ Documented | ❓ Not tested |
| `result.getColumnTypes()` | ✅ Documented | ❓ Not tested |

### 3. Verification Test Results

Test conducted using the following code:
```javascript
const result = await conn.execute("RETURN 'test' AS message, 123 AS number")

// API Test Results
{
  "hasTable": true,           // ✅ Works
  "hasGetAll": false,         // ❌ Does not exist
  "hasGetAllRows": false,     // ❌ Does not exist
  "hasGetAllObjects": false,  // ❌ Does not exist
  "hasToString": true,        // ✅ Works (different format)
  "tableWorks": true,         // ✅ Works
  "toStringWorks": true       // ✅ Works
}
```

### 4. DDL vs DQL Query Behavior

Another undocumented behavior difference:

**SELECT queries (DQL)**:
- `result.table` exists and contains data
- `result.close()` method exists and should be called

**CREATE/DROP queries (DDL)**:
- `result.table` may be undefined
- `result.close()` may not exist

## Working Code Pattern

Based on empirical testing, this is the correct pattern for Kuzu WASM 0.7.0:

```javascript
const result = await conn.execute(query)

// Handle both DDL and DQL queries
let resultJson = []
if (result && result.table) {
  resultJson = JSON.parse(result.table.toString())
}

// Close if method exists
if (result && typeof result.close === 'function') {
  await result.close()
}

return resultJson
```

## Documentation Sources Comparison

| Source | `result.table.toString()` | `result.getAllRows()` | Reliability |
|--------|--------------------------|---------------------|------------|
| NPM README | ✅ Documented & Works | ❌ Not mentioned | High |
| GitHub Examples | ✅ Used & Works | ❌ Not mentioned | High |
| API Docs (async) | ❌ Not mentioned | ✅ Documented, doesn't work | Low |
| API Docs (sync) | ❌ Not mentioned | ✅ Documented, doesn't work | Low |
| Actual Implementation | ✅ Works | ❌ Does not exist | Ground Truth |

## Recommendations

1. **Update API Documentation**: The API documentation at `api-docs.kuzudb.com/wasm/` should be updated to reflect the actual implementation, particularly:
   - Document the `table` property of QueryResult
   - Remove or mark as deprecated the methods that don't exist
   - Add examples that match the NPM README

2. **Version Synchronization**: Ensure API documentation clearly indicates which version of kuzu-wasm it corresponds to.

3. **Clarify DDL vs DQL Behavior**: Document the different behaviors of query results for DDL (CREATE/DROP) vs DQL (SELECT) queries.

4. **Test Coverage**: Add integration tests that verify the documented API matches the implementation.

## Files for Reference

- Test verification script: `test-api-verify.mjs`
- Working implementation: `infrastructure.ts`
- This report: `report_to_kuzu.md`

## Contact

This report was generated while implementing a Kuzu WASM-based application. The discrepancies caused significant development delays due to the mismatch between documentation and implementation.

---

*Generated: 2025-08-19*
*Kuzu WASM Version: 0.7.0*