# DDL Templates for Event Sourcing

This document describes the DDL (Data Definition Language) template system for KuzuDB event sourcing.

## Overview

The DDL template system provides a structured way to:
- Generate valid KuzuDB DDL queries from parameters
- Validate DDL operations before execution
- Track schema versions and dependencies
- Integrate DDL operations with the event sourcing system

## Components

### 1. DDL Templates (`ddl_templates.ts`)

Provides query generation functions for all DDL operations:

```typescript
import { buildDDLQuery, validateDDLParams } from "kuzu_ts";

// Generate CREATE NODE TABLE query
const query = buildDDLQuery("CREATE_NODE_TABLE", {
  tableName: "User",
  columns: [
    { name: "id", type: "STRING", nullable: false },
    { name: "email", type: "STRING", nullable: false },
    { name: "name", type: "STRING" }
  ],
  primaryKey: ["id"],
  ifNotExists: true
});
// Result: CREATE NODE TABLE IF NOT EXISTS User (id STRING NOT NULL, email STRING NOT NULL, name STRING, PRIMARY KEY (id))
```

### 2. DDL Event Handler (`ddl_event_handler.ts`)

Manages DDL events within the event sourcing system:

```typescript
import { DDLEventHandler } from "kuzu_ts";

const handler = new DDLEventHandler();

// Create a DDL event with dependencies
const event = handler.createDDLEvent(
  "CREATE_EDGE_TABLE",
  {
    tableName: "FOLLOWS",
    fromTable: "User",
    toTable: "User"
  },
  ["ddl_user_table_123"] // Dependencies
);

// Apply the event
await handler.applyDDLEvent(event, executeQuery);
```

### 3. Extended Template Registry

Unifies DDL and DML templates:

```typescript
import { ExtendedTemplateRegistry, createUnifiedEvent } from "kuzu_ts";

const registry = new ExtendedTemplateRegistry();

// Check if template exists
registry.hasTemplate("CREATE_NODE_TABLE"); // true (DDL)
registry.hasTemplate("CREATE_USER"); // true (DML)

// Create unified events
const ddlEvent = createUnifiedEvent("CREATE_NODE_TABLE", params);
const dmlEvent = createUnifiedEvent("CREATE_USER", params);
```

## Supported DDL Operations

### Node Table Operations
- `CREATE_NODE_TABLE` / `CREATE_TABLE`
- `DROP_NODE_TABLE` / `DROP_TABLE`

### Edge Table Operations
- `CREATE_EDGE_TABLE`
- `DROP_EDGE_TABLE`

### Column Operations
- `ADD_COLUMN` / `ALTER_TABLE_ADD_COLUMN`
- `DROP_COLUMN` / `ALTER_TABLE_DROP_COLUMN`
- `RENAME_COLUMN`
- `ALTER_COLUMN_TYPE`

### Table Modifications
- `RENAME_TABLE`
- `COMMENT_ON_TABLE`
- `COMMENT_ON_COLUMN`

### Index Operations
- `CREATE_INDEX`
- `DROP_INDEX`

### Constraint Operations
- `ADD_CONSTRAINT`
- `DROP_CONSTRAINT`

## Parameter Types

Each DDL operation has specific parameter requirements:

```typescript
// CREATE_NODE_TABLE parameters
interface CreateNodeTableParams {
  tableName: string;
  columns: Array<{
    name: string;
    type: KuzuDataType;
    nullable?: boolean;
    defaultValue?: any;
  }>;
  primaryKey: string[];
  ifNotExists?: boolean;
}

// ADD_COLUMN parameters
interface AddColumnParams {
  tableName: string;
  columnName: string;
  dataType: KuzuDataType;
  nullable?: boolean;
  defaultValue?: any;
  ifNotExists?: boolean;
}
```

## Validation

The system provides comprehensive validation:

```typescript
import { validateTableName, validateColumnName, validateDataType } from "kuzu_ts";

// Table name validation
validateTableName("User"); // OK
validateTableName("123Table"); // Error: Invalid table name

// Column name validation
validateColumnName("email"); // OK
validateColumnName("column-name"); // Error: Invalid column name

// Data type validation
validateDataType("STRING"); // OK
validateDataType("VARCHAR"); // Error: Invalid data type
```

## Schema Version Tracking

DDL events automatically track schema versions:

```typescript
const handler = new DDLEventHandler();

console.log(handler.getSchemaVersion()); // 0

// Schema-modifying operations increment version
await handler.applyDDLEvent(createTableEvent, executeQuery);
console.log(handler.getSchemaVersion()); // 1

// Non-modifying operations don't increment
await handler.applyDDLEvent(commentEvent, executeQuery);
console.log(handler.getSchemaVersion()); // 1
```

## Dependency Management

DDL events can specify dependencies:

```typescript
// User table must be created first
const userTable = handler.createDDLEvent("CREATE_NODE_TABLE", {
  tableName: "User",
  columns: [...],
  primaryKey: ["id"]
});

// Post table depends on User table
const postTable = handler.createDDLEvent("CREATE_NODE_TABLE", {
  tableName: "Post",
  columns: [...],
  primaryKey: ["id"]
}, [userTable.id]);

// LIKES edge table depends on both
const likesTable = handler.createDDLEvent("CREATE_EDGE_TABLE", {
  tableName: "LIKES",
  fromTable: "User",
  toTable: "Post"
}, [userTable.id, postTable.id]);
```

## Integration with Event Sourcing

DDL events are fully integrated with the event sourcing system:

```typescript
// DDL events have special type
const event: DDLTemplateEvent = {
  id: "ddl_123",
  template: "CREATE_NODE_TABLE",
  params: {...},
  timestamp: Date.now(),
  type: "DDL", // Distinguishes from DML
  dependsOn: [],
  payload: {
    ddlType: "CREATE_NODE_TABLE",
    query: "CREATE NODE TABLE ...",
    metadata: {...}
  }
};

// Check if event is DDL
import { isDDLEvent } from "kuzu_ts";
if (isDDLEvent(event)) {
  // Handle DDL-specific logic
}
```

## Error Handling

The system provides detailed error messages:

```typescript
try {
  handler.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Invalid Table",
    columns: [{ name: "id", type: "INVALID_TYPE" }],
    primaryKey: ["id"]
  });
} catch (error) {
  // Error: Invalid table name: Invalid Table. Must start with letter or underscore...
  // Error: Invalid data type: INVALID_TYPE. Valid types are: BOOL, INT8, ...
}
```

## Best Practices

1. **Always validate parameters** before creating DDL events
2. **Use dependencies** to ensure correct execution order
3. **Use IF NOT EXISTS/IF EXISTS** clauses for idempotency
4. **Track schema versions** for migration management
5. **Handle errors gracefully** with appropriate fallbacks

## Example: Complete Schema Creation

```typescript
async function createSchema() {
  const handler = new DDLEventHandler();
  const events: DDLTemplateEvent[] = [];
  
  // 1. Create User table
  const userTable = handler.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "User",
    columns: [
      { name: "id", type: "STRING", nullable: false },
      { name: "email", type: "STRING", nullable: false },
      { name: "name", type: "STRING" },
      { name: "created_at", type: "TIMESTAMP", defaultValue: "CURRENT_TIMESTAMP" }
    ],
    primaryKey: ["id"],
    ifNotExists: true
  });
  events.push(userTable);
  
  // 2. Create Post table
  const postTable = handler.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Post",
    columns: [
      { name: "id", type: "STRING", nullable: false },
      { name: "content", type: "STRING", nullable: false },
      { name: "author_id", type: "STRING", nullable: false },
      { name: "created_at", type: "TIMESTAMP", defaultValue: "CURRENT_TIMESTAMP" }
    ],
    primaryKey: ["id"],
    ifNotExists: true
  }, [userTable.id]);
  events.push(postTable);
  
  // 3. Create FOLLOWS edge table
  const followsTable = handler.createDDLEvent("CREATE_EDGE_TABLE", {
    tableName: "FOLLOWS",
    fromTable: "User",
    toTable: "User",
    columns: [
      { name: "followed_at", type: "TIMESTAMP", defaultValue: "CURRENT_TIMESTAMP" }
    ],
    ifNotExists: true
  }, [userTable.id]);
  events.push(followsTable);
  
  // 4. Create email index
  const emailIndex = handler.createDDLEvent("CREATE_INDEX", {
    indexName: "idx_user_email",
    tableName: "User",
    columns: ["email"],
    unique: true,
    ifNotExists: true
  }, [userTable.id]);
  events.push(emailIndex);
  
  // Apply all events in order
  for (const event of events) {
    await handler.applyDDLEvent(event, executeQuery);
  }
  
  console.log(`Schema created with version: ${handler.getSchemaVersion()}`);
}
```