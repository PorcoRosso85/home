# Storage Adapters

This directory contains storage adapter implementations for the infrastructure layer.

## LogAdapter

The `LogAdapter` is a simple storage adapter that logs all storage operations to the console instead of actually persisting data. It's useful for:

- Development and debugging
- Testing storage workflows
- Understanding data flow without actual persistence

### Usage

```typescript
import { LogAdapter } from '../../infrastructure/mod.js';

const storage = new LogAdapter();

// Save simple data
await storage.save('user/profile.json', {
  name: 'John Doe',
  email: 'john@example.com'
});

// Save with metadata
await storage.save('logs/activity.json', 
  { action: 'login', userId: '123' },
  { source: 'web-app', timestamp: Date.now() }
);
```

### Output Format

The LogAdapter produces structured console output:

```
[STORAGE:2025-08-30T12:34:56.789Z] Saving to user/profile.json (45 bytes)
Data: { name: 'John Doe', email: 'john@example.com' }

[STORAGE:2025-08-30T12:34:56.790Z] Saving to logs/activity.json (32 bytes)
Data: { action: 'login', userId: '123' }
Metadata: { source: 'web-app', timestamp: 1725024896790 }
```

### Implementation Details

- Implements the `StorageAdapter` interface from the domain layer
- Calculates data size in bytes using `TextEncoder`
- Logs timestamp in ISO format
- Logs data and metadata separately for better readability
- All operations are async (returning Promise<void>) for compatibility

## R2Adapter

The `R2Adapter` is a production storage adapter that integrates with Cloudflare R2 for persistent object storage. It provides:

- Automatic JSON stringification for objects
- R2-compatible metadata formatting 
- HTTP header mapping for standard metadata
- Custom metadata support

### Usage

```typescript
import { R2Adapter } from '../../infrastructure/mod.js';

// Get R2 bucket from Cloudflare Workers environment
const ctx = getHonoContext();
const bucket = ctx.env.DATA_BUCKET;

// Create adapter
const storage = new R2Adapter(bucket);

// Save simple data
await storage.save('submissions/form-123.json', {
  name: 'John Doe',
  email: 'john@example.com',
  message: 'Hello world!'
});

// Save with metadata (will be formatted for R2)
await storage.save('uploads/file.json', 
  { data: 'content' },
  { 
    contentType: 'application/json',
    timestamp: Date.now(),
    source: 'web-form' 
  }
);
```

### Metadata Mapping

The R2Adapter automatically maps standard metadata to R2 HTTP headers:

- `contentType` → `httpMetadata.contentType`
- `contentEncoding` → `httpMetadata.contentEncoding`
- `contentLanguage` → `httpMetadata.contentLanguage`
- `contentDisposition` → `httpMetadata.contentDisposition`
- `cacheControl` → `httpMetadata.cacheControl`

All other metadata fields are stored as custom metadata in R2.

### Implementation Details

- Implements the `StorageAdapter` interface from the domain layer
- Accepts any R2 bucket object in constructor
- Handles both string and object data (objects are JSON stringified)
- Formats metadata for R2 compatibility with httpMetadata and customMetadata
- All operations are async and return Promise<void>

## MultiAdapter

The `MultiAdapter` is a composite storage adapter that saves to multiple storage backends simultaneously. This provides data redundancy and enables backup strategies across different storage systems.

### Key Features

- **Redundancy**: Saves to all configured adapters simultaneously
- **Fault tolerance**: Continues operation even if some adapters fail
- **Error handling**: Logs errors for failed adapters but doesn't throw unless all fail
- **Success guarantee**: Returns success if at least one adapter succeeds
- **Parallel execution**: Uses Promise.all for optimal performance

### Usage

```typescript
import { MultiAdapter, R2Adapter, LogAdapter } from '../../infrastructure/mod.js';

// Get R2 bucket from Cloudflare Workers environment
const ctx = getHonoContext();
const bucket = ctx.env.DATA_BUCKET;

// Create individual adapters
const r2Storage = new R2Adapter(bucket);
const logStorage = new LogAdapter();

// Create multi-adapter for redundancy
const storage = new MultiAdapter([r2Storage, logStorage]);

// Save to both R2 and logs simultaneously
await storage.save('important-data.json', {
  critical: true,
  data: 'This will be saved to both R2 and logged'
});

// Even if R2 fails, the operation succeeds because LogAdapter works
const partialFailureStorage = new MultiAdapter([
  new R2Adapter(null), // This will fail
  new LogAdapter()      // This will succeed
]);

try {
  await partialFailureStorage.save('test.json', { test: true });
  // This succeeds and logs warnings about the failed R2 adapter
} catch (error) {
  // Only thrown if ALL adapters fail
}
```

### Use Cases

1. **Production Redundancy**: Save to both R2 and a backup storage system
2. **Development Logging**: Save to production storage while also logging for debugging
3. **Multi-Cloud Backup**: Save to multiple cloud providers simultaneously
4. **Gradual Migration**: Write to both old and new storage systems during migration

### Error Handling

The MultiAdapter implements sophisticated error handling:

```typescript
// Example with mixed success/failure
const storage = new MultiAdapter([
  new R2Adapter(bucket),           // Succeeds
  new FailingAdapter(),           // Fails
  new AnotherSuccessAdapter()     // Succeeds
]);

await storage.save('data.json', { data: 'test' });
// Console output:
// [MultiAdapter:timestamp] Adapter 1 failed to save key "data.json": Error details
// [MultiAdapter:timestamp] Save to "data.json" completed with 2/3 adapters successful
// Operation completes successfully
```

### Implementation Details

- Implements the `StorageAdapter` interface from the domain layer
- Requires at least one adapter in constructor (throws error if empty array)
- Uses `Promise.allSettled()` to handle mixed success/failure scenarios
- Provides helper methods: `getAdapterCount()` and `getAdapters()`
- Detailed logging for monitoring and debugging
- Thread-safe and handles concurrent operations correctly