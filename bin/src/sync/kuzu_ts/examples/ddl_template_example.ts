/**
 * DDL Template Example
 * DDLテンプレートの使用例
 */

import { DDLEventHandler, createUnifiedEvent } from "../event_sourcing/ddl_event_handler.ts";
import { isDDLEvent } from "../event_sourcing/ddl_types.ts";

async function runDDLExample() {
  console.log("=== DDL Template Example ===\n");
  
  const handler = new DDLEventHandler();
  
  // Example 1: Create a node table
  console.log("1. Creating a node table:");
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
  
  console.log("DDL Event:", createUserTable);
  console.log("Generated Query:", createUserTable.payload?.query);
  console.log();
  
  // Example 2: Create an edge table with dependencies
  console.log("2. Creating an edge table with dependencies:");
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
  
  console.log("DDL Event:", createFollowsTable);
  console.log("Generated Query:", createFollowsTable.payload?.query);
  console.log("Dependencies:", createFollowsTable.dependsOn);
  console.log();
  
  // Example 3: Add column to existing table
  console.log("3. Adding a column to existing table:");
  const addAgeColumn = handler.createDDLEvent("ADD_COLUMN", {
    tableName: "User",
    columnName: "age",
    dataType: "INT32",
    nullable: true
  });
  
  console.log("Generated Query:", addAgeColumn.payload?.query);
  console.log();
  
  // Example 4: Create index
  console.log("4. Creating an index:");
  const createEmailIndex = handler.createDDLEvent("CREATE_INDEX", {
    indexName: "idx_user_email",
    tableName: "User",
    columns: ["email"],
    unique: true,
    ifNotExists: true
  });
  
  console.log("Generated Query:", createEmailIndex.payload?.query);
  console.log();
  
  // Example 5: Drop column with cascade
  console.log("5. Dropping a column with cascade:");
  const dropColumn = handler.createDDLEvent("DROP_COLUMN", {
    tableName: "User",
    columnName: "temp_field",
    ifExists: true,
    cascade: true
  });
  
  console.log("Generated Query:", dropColumn.payload?.query);
  console.log();
  
  // Example 6: Add comments
  console.log("6. Adding comments to table and column:");
  const tableComment = handler.createDDLEvent("COMMENT_ON_TABLE", {
    tableName: "User",
    comment: "Core user information table"
  });
  
  const columnComment = handler.createDDLEvent("COMMENT_ON_COLUMN", {
    tableName: "User",
    columnName: "email",
    comment: "User's primary email address"
  });
  
  console.log("Table comment query:", tableComment.payload?.query);
  console.log("Column comment query:", columnComment.payload?.query);
  console.log();
  
  // Example 7: Using unified event creation
  console.log("7. Using unified event creation (DDL vs DML):");
  
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
  
  console.log("DDL Event?", isDDLEvent(ddlEvent), "- Template:", ddlEvent.template);
  console.log("DML Event?", !isDDLEvent(dmlEvent), "- Template:", dmlEvent.template);
  console.log();
  
  // Example 8: Schema version tracking
  console.log("8. Schema version tracking:");
  
  // Mock query executor
  const mockExecuteQuery = async (query: string) => {
    console.log(`  Executing: ${query}`);
    return {};
  };
  
  console.log("Initial schema version:", handler.getSchemaVersion());
  
  // Apply schema-modifying operations
  await handler.applyDDLEvent(createUserTable, mockExecuteQuery);
  console.log("After CREATE TABLE - version:", handler.getSchemaVersion());
  
  await handler.applyDDLEvent(addAgeColumn, mockExecuteQuery);
  console.log("After ADD COLUMN - version:", handler.getSchemaVersion());
  
  // Apply non-schema-modifying operation (comment)
  await handler.applyDDLEvent(tableComment, mockExecuteQuery);
  console.log("After COMMENT - version:", handler.getSchemaVersion());
  
  console.log("\nApplied DDL events:", handler.getAppliedDDLs().length);
  console.log();
  
  // Example 9: Error handling
  console.log("9. Error handling examples:");
  
  try {
    // Invalid table name
    handler.createDDLEvent("CREATE_NODE_TABLE", {
      tableName: "Invalid Table Name",
      columns: [{ name: "id", type: "STRING" }],
      primaryKey: ["id"]
    });
  } catch (error) {
    console.log("✓ Caught error:", error.message);
  }
  
  try {
    // Invalid data type
    handler.createDDLEvent("ADD_COLUMN", {
      tableName: "User",
      columnName: "invalid_col",
      dataType: "VARCHAR" // Not a valid KuzuDB type
    });
  } catch (error) {
    console.log("✓ Caught error:", error.message);
  }
  
  try {
    // Missing required parameter
    handler.createDDLEvent("CREATE_NODE_TABLE", {
      tableName: "Test"
      // Missing columns and primaryKey
    });
  } catch (error) {
    console.log("✓ Caught error:", error.message);
  }
}

// Run the example
if (import.meta.main) {
  await runDDLExample();
}