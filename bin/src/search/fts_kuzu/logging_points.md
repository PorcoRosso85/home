# FTS KuzuDB Key Logging Points

Based on analysis of the FTS codebase, here are the most important locations where logging should be added for debugging and monitoring:

## 1. Entry Points & API Boundaries

### application.py: create_fts()
- **Line 503-530**: FTS instance creation
- **Purpose**: Log initialization parameters, connection mode (in-memory/persistent), existing connection reuse
- **Level**: INFO

### application.py: FTSInterpreter.index()
- **Line 436-452**: Document indexing entry
- **Purpose**: Log number of documents to index, validation results
- **Level**: INFO for success, WARN for validation failures

### application.py: FTSInterpreter.search()
- **Line 454-473**: Search query entry
- **Purpose**: Log search query, limit, additional parameters
- **Level**: INFO

## 2. Database Operations & State Changes

### infrastructure.py: create_kuzu_database()
- **Line 37-83**: Database creation
- **Purpose**: Log database path, in-memory flag, creation success/failure
- **Level**: INFO for success, ERROR for failures

### infrastructure.py: create_kuzu_connection()
- **Line 85-129**: Connection establishment
- **Purpose**: Log connection creation, reuse of existing connections
- **Level**: DEBUG

### infrastructure.py: install_fts_extension()
- **Line 190-227**: FTS extension installation
- **Purpose**: Log extension installation attempts, already-installed status
- **Level**: INFO for new installs, DEBUG for already-installed

### infrastructure.py: create_fts_index()
- **Line 335-407**: FTS index creation
- **Purpose**: Log index name, table, properties, creation success/failure
- **Level**: INFO

## 3. Error Handling & Recovery

### application.py: index_documents()
- **Line 104-116**: FTS extension installation errors
- **Line 128-137**: FTS extension availability check failures
- **Line 147-158**: Schema initialization failures
- **Line 175-189**: Index creation failures (distinguish "already exists" from real errors)
- **Line 223-227**: Document insertion failures
- **Purpose**: Log specific error types, recovery attempts, fallback strategies
- **Level**: ERROR for failures, WARN for recoverable issues

### application.py: search()
- **Line 302-332**: FTS unavailable fallback to simple search
- **Line 349-376**: FTS query failure fallback
- **Purpose**: Log fallback decisions, performance implications
- **Level**: WARN

### infrastructure.py: query_fts_index()
- **Line 622-636**: Query execution failures
- **Purpose**: Log failed queries, error details for debugging
- **Level**: ERROR

## 4. Performance-Critical Operations

### application.py: index_documents()
- **Line 62, 229**: Start/end timing for indexing operations
- **Line 192-227**: Document insertion loop
- **Purpose**: Log indexing performance metrics, per-document timing for large batches
- **Level**: DEBUG (detailed timing), INFO (summary)

### application.py: search()
- **Line 254, 393**: Start/end timing for search operations
- **Line 336-391**: FTS query execution and result processing
- **Purpose**: Log search latency, result count, query complexity
- **Level**: DEBUG (detailed timing), INFO (summary)

### domain.py: calculate_bm25_score()
- **Line 237-265**: BM25 scoring calculation
- **Purpose**: Log scoring parameters for search relevance tuning
- **Level**: DEBUG

## 5. Data Flow & Transformations

### application.py: index_documents()
- **Line 207-220**: Document transformation for insertion
- **Purpose**: Log document IDs being processed, content size
- **Level**: DEBUG

### domain.py: create_highlight_info()
- **Line 330-362**: Highlight generation
- **Purpose**: Log highlight extraction for search result quality
- **Level**: DEBUG

### infrastructure.py: query_fts_index()
- **Line 600-618**: Result assembly from FTS query
- **Purpose**: Log result transformation, missing documents
- **Level**: DEBUG

## 6. Connection Lifecycle

### application.py: create_fts()
- **Line 567-587**: Connection initialization
- **Line 654-658**: Error cleanup
- **Purpose**: Log connection lifecycle, resource cleanup
- **Level**: DEBUG

### application.py: index_documents() & search()
- **Line 76-93, 270-288**: Connection creation/reuse logic
- **Line 238-241, 405-408**: Connection cleanup in finally blocks
- **Purpose**: Log connection pooling behavior, ensure proper cleanup
- **Level**: DEBUG

## Summary of Logging Priorities

1. **Critical (Must Have)**:
   - Entry points with parameters
   - Error conditions and fallback strategies
   - Database connection lifecycle
   - Performance metrics (operation timing)

2. **Important (Should Have)**:
   - FTS extension status and installation
   - Index creation and management
   - Query execution details
   - Document processing counts

3. **Nice to Have (Could Have)**:
   - Detailed scoring calculations
   - Highlight generation
   - Internal data transformations
   - Debug-level operation details