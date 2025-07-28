/**
 * DDL Template Example
 * DDLテンプレートの使用例
 */

import { DDLEventHandler, createUnifiedEvent } from "../event_sourcing/ddl_event_handler.ts";
import { isDDLEvent } from "../event_sourcing/ddl_types.ts";
import * as telemetry from "../telemetry_log.ts";

async function runDDLExample() {
  telemetry.info("=== DDL Template Example ===\n");
  
  const handler = new DDLEventHandler();
  
  // Example 1: Create a node table
  telemetry.info("1. Creating a node table:");
  const createUserTable = handler.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "User",
    columns: [
      { name: "id", type: "STRING", nullable: false },
      { name: "email", type: "STRING", nullable: false },
      { name: "name", type: "STRING" },
      { name: "created_at", type: "TIMESTAMP", defaultValue: "CURRENT_TIMESTAMP" },
      { name: "is_active", type: "BOOL", defaultValue: true }
    ],
    primaryKey: ["id"],
    ifNotExists: true
  });
  
  telemetry.debug("DDL Event:", { event: createUserTable });
  telemetry.info("Generated Query:", { query: createUserTable.payload?.query });
  telemetry.info("");
  
  // Example 2: Create an edge table with dependencies
  telemetry.info("2. Creating an edge table with dependencies:");
  const createFollowsTable = handler.createDDLEvent(
    "CREATE_EDGE_TABLE",
    {
      tableName: "FOLLOWS",
      fromTable: "User",
      toTable: "User",
      columns: [
        { name: "followed_at", type: "TIMESTAMP", defaultValue: "CURRENT_TIMESTAMP" },
        { name: "notification_enabled", type: "BOOL", defaultValue: true }
      ],
      ifNotExists: true
    },
    [createUserTable.id] // Depends on User table being created
  );
  
  telemetry.debug("DDL Event:", { event: createFollowsTable });
  telemetry.info("Generated Query:", { query: createFollowsTable.payload?.query });
  telemetry.info("Dependencies:", { dependencies: createFollowsTable.dependsOn });
  telemetry.info("");
  
  // Example 3: Add column to existing table
  telemetry.info("3. Adding a column to existing table:");
  const addAgeColumn = handler.createDDLEvent("ADD_COLUMN", {
    tableName: "User",
    columnName: "age",
    dataType: "INT32",
    nullable: true
  });
  
  telemetry.info("Generated Query:", { query: addAgeColumn.payload?.query });
  telemetry.info("");
  
  // Example 4: Create index
  telemetry.info("4. Creating an index:");
  const createEmailIndex = handler.createDDLEvent("CREATE_INDEX", {
    indexName: "idx_user_email",
    tableName: "User",
    columns: ["email"],
    unique: true,
    ifNotExists: true
  });
  
  telemetry.info("Generated Query:", { query: createEmailIndex.payload?.query });
  telemetry.info("");
  
  // Example 5: Drop column with cascade
  telemetry.info("5. Dropping a column with cascade:");
  const dropColumn = handler.createDDLEvent("DROP_COLUMN", {
    tableName: "User",
    columnName: "temp_field",
    ifExists: true,
    cascade: true
  });
  
  telemetry.info("Generated Query:", { query: dropColumn.payload?.query });
  telemetry.info("");
  
  // Example 6: Add comments
  telemetry.info("6. Adding comments to table and column:");
  const tableComment = handler.createDDLEvent("COMMENT_ON_TABLE", {
    tableName: "User",
    comment: "Core user information table"
  });
  
  const columnComment = handler.createDDLEvent("COMMENT_ON_COLUMN", {
    tableName: "User",
    columnName: "email",
    comment: "User's primary email address"
  });
  
  telemetry.info("Table comment query:", { query: tableComment.payload?.query });
  telemetry.info("Column comment query:", { query: columnComment.payload?.query });
  telemetry.info("");
  
  // Example 7: Using unified event creation
  telemetry.info("7. Using unified event creation (DDL vs DML):");
  
  // This creates a DDL event
  const ddlEvent = createUnifiedEvent("CREATE_NODE_TABLE", {
    tableName: "Product",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING" },
      { name: "price", type: "DOUBLE" }
    ],
    primaryKey: ["id"]
  });
  
  // This creates a DML event
  const dmlEvent = createUnifiedEvent("CREATE_USER", {
    id: "user123",
    name: "Alice",
    email: "alice@example.com"
  });
  
  telemetry.info("DDL Event?", { isDDL: isDDLEvent(ddlEvent), template: ddlEvent.template });
  telemetry.info("DML Event?", { isDML: !isDDLEvent(dmlEvent), template: dmlEvent.template });
  telemetry.info("");
  
  // Example 8: Schema version tracking
  telemetry.info("8. Schema version tracking:");
  
  // Mock query executor
  const mockExecuteQuery = async (query: string) => {
    telemetry.debug(`  Executing: ${query}`);
    return {};
  };
  
  telemetry.info("Initial schema version:", { version: handler.getSchemaVersion() });
  
  // Apply schema-modifying operations
  await handler.applyDDLEvent(createUserTable, mockExecuteQuery);
  telemetry.info("After CREATE TABLE - version:", { version: handler.getSchemaVersion() });
  
  await handler.applyDDLEvent(addAgeColumn, mockExecuteQuery);
  telemetry.info("After ADD COLUMN - version:", { version: handler.getSchemaVersion() });
  
  // Apply non-schema-modifying operation (comment)
  await handler.applyDDLEvent(tableComment, mockExecuteQuery);
  telemetry.info("After COMMENT - version:", { version: handler.getSchemaVersion() });
  
  telemetry.info("\nApplied DDL events:", { count: handler.getAppliedDDLs().length });
  telemetry.info("");
  
  // Example 9: Error handling
  telemetry.info("9. Error handling examples:");
  
  try {
    // Invalid table name
    handler.createDDLEvent("CREATE_NODE_TABLE", {
      tableName: "Invalid Table Name",
      columns: [{ name: "id", type: "STRING" }],
      primaryKey: ["id"]
    });
  } catch (error) {
    telemetry.info("✓ Caught error:", { error: error.message });
  }
  
  try {
    // Invalid data type
    handler.createDDLEvent("ADD_COLUMN", {
      tableName: "User",
      columnName: "invalid_col",
      dataType: "VARCHAR" // Not a valid KuzuDB type
    });
  } catch (error) {
    telemetry.info("✓ Caught error:", { error: error.message });
  }
  
  try {
    // Missing required parameter
    handler.createDDLEvent("CREATE_NODE_TABLE", {
      tableName: "Test"
      // Missing columns and primaryKey
    });
  } catch (error) {
    telemetry.info("✓ Caught error:", { error: error.message });
  }
}

// Run the example
if (import.meta.main) {
  await runDDLExample();
}