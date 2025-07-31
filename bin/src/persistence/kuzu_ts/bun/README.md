# KuzuDB Bun Implementation

## Purpose

This directory provides a Bun-specific entry point for the KuzuDB TypeScript implementation. Bun is a fast all-in-one JavaScript runtime that can directly execute TypeScript without transpilation.

## Implementation Approach

Unlike Deno or Node.js, Bun doesn't require special adaptations for most TypeScript code. This implementation simply re-exports the classic implementation, taking advantage of Bun's native TypeScript support and compatibility with standard JavaScript/TypeScript modules.

## Key Differences from Other Implementations

- **No Worker Threads**: Unlike the worker implementation, this uses direct synchronous execution
- **No Special Imports**: Unlike Deno, Bun doesn't require import maps or special module resolution
- **Native TypeScript**: No transpilation step required, Bun executes TypeScript directly
- **Performance**: Leverages Bun's optimized runtime for potentially faster execution

## Usage

```typescript
import { createDatabase, createConnection } from "./mod.ts";

// Create database
const dbResult = await createDatabase("./test.db");
if (dbResult.success) {
  const db = dbResult.value;
  
  // Create connection
  const connResult = await createConnection(db);
  if (connResult.success) {
    const conn = connResult.value;
    // Use connection for queries
  }
}
```

## Running with Bun

```bash
# Install Bun if not already installed
curl -fsSL https://bun.sh/install | bash

# Run your script
bun run your-script.ts
```

## Requirements

- Bun runtime (latest version recommended)
- KuzuDB native library must be available in the system