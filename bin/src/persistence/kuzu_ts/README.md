# kuzu_ts - KuzuDB TypeScript/Deno Persistence Layer

## Overview

TypeScript/Deno implementation of the KuzuDB persistence layer, providing the same interface as kuzu_py but for TypeScript/Deno environments.

## Current Status

This implementation uses a mock KuzuDB adapter due to the challenges of using native Node.js modules in Deno. The interface is complete and tests are passing, but actual KuzuDB integration requires one of:

1. **Native Deno FFI binding** to KuzuDB C++ library
2. **WebAssembly build** of KuzuDB
3. **Node.js compatibility layer** improvements in Deno

## Usage

```typescript
import { createDatabase, createConnection } from "./mod.ts";

// Create in-memory database
const db = await createDatabase(":memory:");
const conn = await createConnection(db);

// Execute queries
await conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))");
await conn.execute("CREATE (:Person {name: 'Alice', age: 30})");

const result = await conn.execute("MATCH (p:Person) RETURN p.name, p.age");
const rows = await result.getAll();
```

## Features

- ✅ Database factory with caching
- ✅ In-memory and persistent database support
- ✅ Test-specific unique instances
- ✅ TypeScript type definitions
- ✅ Deno-first design

## Testing

```bash
nix run .#test
# or
deno test --allow-read --allow-write --allow-net --allow-env
```

## Structure

```
kuzu_ts/
├── flake.nix      # Nix configuration
├── deno.json      # Deno configuration
├── mod.ts         # Main entry point
├── core/
│   └── database.ts # Database factory implementation
└── tests/
    └── database_test.ts # Unit tests
```

## Future Work

1. Replace mock implementation with actual KuzuDB bindings
2. Add more comprehensive type definitions
3. Implement streaming query results
4. Add connection pooling support