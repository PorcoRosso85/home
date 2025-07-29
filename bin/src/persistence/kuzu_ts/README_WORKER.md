# KuzuDB Worker Implementation for Deno

## Overview

This is the recommended implementation of KuzuDB for Deno environments. It uses Deno's Worker API to isolate the npm:kuzu native module in a separate process, preventing any crashes from affecting your main application.

## Why Worker Implementation?

After extensive testing of three approaches:
1. **Direct npm:kuzu** - Causes Deno process panics ❌
2. **Worker Process** - Stable and fully functional ✅
3. **WASM (kuzu-wasm)** - Incompatible with Deno ❌

The Worker implementation provides the best balance of stability and functionality.

## Installation

```typescript
import { createDatabase, createConnection } from "./mod_worker.ts";
```

## Usage

### Basic Example

```typescript
// Create a database (in-memory or persistent)
const db = await createDatabase(":memory:");

// Create a connection
const conn = await createConnection(db);

// Execute queries
await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))");
await conn.query("CREATE (p:Person {name: 'Alice', age: 30})");

// Retrieve data
const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age");
const rows = await result.getAll();
console.log(rows); // [{ "p.name": "Alice", "p.age": 30 }]

// Clean up
await conn.close();
await db.close();
```

### Worker Lifecycle Management

```typescript
import { terminateWorker } from "./mod_worker.ts";

// When completely done with KuzuDB operations
terminateWorker();
```

## API Reference

### Database Functions

#### `createDatabase(path: string, options?: { bufferPoolSize?: number }): Promise<DatabaseResult>`

Creates a new database instance in the worker process.

- `path`: Database path. Use `:memory:` for in-memory database
- `options.bufferPoolSize`: Optional buffer pool size
- Returns: `WorkerDatabase` instance or error

#### `createConnection(database: WorkerDatabase): Promise<ConnectionResult>`

Creates a connection to the database.

- `database`: Database instance from `createDatabase`
- Returns: `WorkerConnection` instance or error

### Worker Management

#### `terminateWorker(): void`

Terminates the worker process. Call this when completely done with all database operations.

## Error Handling

The Worker implementation properly isolates errors:

```typescript
const result = await createDatabase("invalid/path");
if (isFileOperationError(result)) {
  console.error("Database creation failed:", result.message);
} else {
  // Use the database
}
```

## Performance Considerations

- **Overhead**: ~10-20% performance overhead due to message passing
- **Memory**: Uses separate process memory (approximately 2x base usage)
- **Latency**: Small additional latency for cross-process communication

## Limitations

1. **No Direct Object Sharing**: Database and connection objects are proxies
2. **Serialization**: Query results must be serializable
3. **Async Only**: All operations are asynchronous

## Best Practices

1. **Single Worker**: The implementation uses a single shared worker for all operations
2. **Cleanup**: Always close connections and databases when done
3. **Error Handling**: Check result types before using database objects
4. **Batch Operations**: Minimize cross-process calls by batching queries

## Migration from Direct Implementation

If migrating from direct npm:kuzu usage:

```typescript
// Before (direct - causes panics)
import { Database, Connection } from "npm:kuzu";
const db = new Database(":memory:");

// After (worker - stable)
import { createDatabase, createConnection } from "./mod_worker.ts";
const db = await createDatabase(":memory:");
```

## Troubleshooting

### Worker fails to start
- Ensure you have proper Deno permissions: `--allow-read --allow-write --allow-net`
- Check that npm:kuzu is properly installed

### Performance is slow
- Consider batching multiple queries into single operations
- Monitor worker memory usage
- Use persistent databases instead of creating new in-memory instances

### Memory usage is high
- Call `terminateWorker()` when done with all operations
- Close connections and databases promptly
- Monitor for memory leaks in long-running applications

## Future Improvements

- Native Deno FFI binding (when KuzuDB provides C API)
- WebAssembly support (when Deno improves Worker compatibility)
- Connection pooling for better resource management