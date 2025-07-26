# DDL Synchronization in sync/kuzu_ts

## Overview

This project now supports DDL (Data Definition Language) synchronization across distributed KuzuDB instances. DDL operations like CREATE TABLE, ALTER TABLE, and CREATE INDEX are treated as events in the causal ordering system, enabling dynamic schema evolution without downtime.

## Architecture

### Core Components

1. **DDL Types** (`event_sourcing/ddl_types.ts`)
   - Extended TemplateEvent interface with DDL support
   - Type definitions for all DDL operations
   - Schema version tracking types

2. **DDL Templates** (`event_sourcing/ddl_templates.ts`)
   - Query generation for KuzuDB DDL operations
   - Validation functions for DDL parameters
   - Template registry for DDL operations

3. **DDL Event Handler** (`event_sourcing/ddl_event_handler.ts`)
   - Manages DDL event lifecycle
   - Dependency resolution
   - Schema version management

4. **Schema Manager** (`core/schema_manager.ts`)
   - Central component for schema management
   - Tracks schema state and versions
   - Handles schema conflicts
   - Manages pending DDL operations

5. **Client Integration**
   - **ServerKuzuClient**: Full DDL support with schema persistence
   - **BrowserKuzuClient**: DDL support for in-browser KuzuDB instances

## Supported DDL Operations

### Table Operations
- `CREATE_NODE_TABLE`: Create node tables with properties
- `CREATE_EDGE_TABLE`: Create relationship tables
- `DROP_NODE_TABLE` / `DROP_EDGE_TABLE`: Remove tables
- `RENAME_TABLE`: Rename existing tables

### Column Operations
- `ADD_COLUMN`: Add new columns to existing tables
- `DROP_COLUMN`: Remove columns (with CASCADE support)
- `RENAME_COLUMN`: Rename existing columns
- `ALTER_COLUMN_TYPE`: Change column data types

### Index Operations
- `CREATE_INDEX`: Create indexes on properties
- `DROP_INDEX`: Remove indexes

### Metadata Operations
- `COMMENT_ON_TABLE`: Add table descriptions
- `COMMENT_ON_COLUMN`: Add column descriptions

## Usage Examples

### Creating a Table

```typescript
const tableEvent = await client.createDDLEvent(
  "CREATE_NODE_TABLE",
  {
    tableName: "Customer",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING" },
      { name: "email", type: "STRING" }
    ],
    primaryKey: "id"
  }
);

await client.applyEvent(tableEvent);
```

### Adding a Column

```typescript
const columnEvent = await client.createDDLEvent(
  "ADD_COLUMN",
  {
    tableName: "Customer",
    columnName: "phone",
    columnType: "STRING",
    defaultValue: "''"
  }
);

await client.applyEvent(columnEvent);
```

### Creating Relationships

```typescript
const relEvent = await client.createDDLEvent(
  "CREATE_EDGE_TABLE",
  {
    tableName: "PURCHASED",
    fromTable: "Customer",
    toTable: "Product",
    properties: "quantity INT64, purchaseDate DATE"
  }
);

await client.applyEvent(relEvent);
```

## Dependency Management

DDL operations can specify dependencies using the `dependsOn` field:

```typescript
const userTable = await client.createDDLEvent("CREATE_NODE_TABLE", {...});
const postTable = await client.createDDLEvent("CREATE_NODE_TABLE", {...});

const relationTable = await client.createDDLEvent(
  "CREATE_EDGE_TABLE",
  {
    tableName: "AUTHORED",
    fromTable: "User",
    toTable: "Post"
  }
);

// Set dependencies
relationTable.dependsOn = [userTable.id, postTable.id];
```

## Schema Versioning

Every DDL operation increments the schema version:

```typescript
const schemaState = await client.getSchemaState();
console.log(`Schema version: ${schemaState.version}`);
console.log(`Tables: ${Object.keys(schemaState.tables).join(', ')}`);
```

## Testing

The DDL sync implementation is thoroughly tested:

1. **Unit Tests**
   - `ddl_types.test.ts`: Type system tests
   - `ddl_templates.test.ts`: Template generation tests
   - `ddl_event_handler.test.ts`: Event handling tests
   - `schema_manager.test.ts`: Schema management tests

2. **Integration Tests**
   - `ddl_sync_integration.test.ts`: Integration scenarios (TypeScript)
   - `ddl_sync_python_e2e.py`: End-to-end tests (Python)

Run tests:
```bash
# TypeScript tests
nix develop -c deno test event_sourcing/ddl_*.test.ts core/schema_manager.test.ts

# Python E2E tests
nix develop -c python tests/ddl_sync_python_e2e.py
```

## Migration from Fixed Schema

If you're migrating from the previous fixed-schema approach:

1. Existing tables will continue to work
2. New tables can be added dynamically via DDL events
3. Schema changes propagate automatically to all clients
4. No downtime required for schema updates

## Best Practices

1. **Use Dependencies**: Always specify dependencies for related DDL operations
2. **Test Schema Changes**: Test DDL operations in development before production
3. **Monitor Schema Version**: Track schema versions across clients
4. **Handle Conflicts**: Implement conflict resolution for concurrent schema changes
5. **Document Changes**: Use COMMENT operations to document schema purpose

## Future Enhancements

- [ ] Schema migration rollback support
- [ ] Automatic index recommendations
- [ ] Schema diff and merge tools
- [ ] Visual schema evolution tracking
- [ ] Performance impact analysis for DDL operations